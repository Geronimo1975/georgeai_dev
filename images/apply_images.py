#!/usr/bin/env python3
"""
apply_images.py — inject the mockup SVGs into the design-tool export.

The export ships empty placeholder slots (diagonal-hatch divs with a `[ label ]`)
on the About page, the three News cards and every service-detail view. This
script rewrites those placeholders to real <img> elements pointing at the
committed mockups in images/mock/ (copied into site/assets/mock/ by deploy.sh).

Same rationale as brand/apply_brand.py: the export is regenerated on every
re-export, so this runs at deploy time and is fully idempotent — a second run is
a no-op. Every transform is guarded: if the placeholder markup isn't found (e.g.
the design tool changed its shape) the file is left untouched and a note is
printed, so a drifted export can never break the deploy.

Usage:  python3 images/apply_images.py site/index.html [more.html ...]
"""
import os
import re
import sys

# service slug ↔ svcMeta `name` — kept in one place so the <img> src matches the
# generated filenames. Mirrors images/gen_mockups.py:SERVICES.
try:
    from gen_mockups import SERVICES
    NAME_TO_SLUG = {name: slug for slug, name, _fn, _lbl in SERVICES}
except Exception:  # imported without the generator on path — inline fallback
    NAME_TO_SLUG = {
        "Automation": "automation", "AI Chatbot": "ai-chatbot",
        "AI Phone Calls": "ai-phone-calls", "SEO / AIO / GEO": "seo-aio-geo",
        "Email Marketing": "email-marketing", "Lead Generation": "lead-generation",
        "Python Programming": "python-programming", "Django": "django",
        "Micro ERP": "micro-erp", "CRM": "crm", "Web Design": "web-design",
        "RAG": "rag", "Web Design Optimization": "web-design-optimization",
        "SaaS Projects": "saas-projects",
        "API Integration & Data Analytics": "api-integration-data-analytics",
        "AI Consultant": "ai-consultant",
    }

MOCK = "/assets/mock"
IMG_BASE = ("width:100%;display:block;object-fit:cover;"
            "border:1px solid var(--cardBorder)")


def add_svcmeta_img(html, notes):
    """Append `img: "<mock>"` to each svcMeta entry, keyed by its stable name."""
    if 'img: "/assets/mock/svc-' in html:
        return html  # already applied
    changed = [0]

    def repl(m):
        name = m.group("name")
        slug = NAME_TO_SLUG.get(name)
        if not slug:
            return m.group(0)
        changed[0] += 1
        # insert before the closing ` }` of the object literal
        return m.group("body") + f', img: "{MOCK}/svc-{slug}.svg"' + m.group("tail")

    # matches:  { name: "X", cat: N, stack: [...], label: "..." }
    pat = re.compile(
        r'(?P<body>\{\s*name:\s*"(?P<name>[^"]+)",[^\n{}]*?label:\s*"[^"]*")'
        r'(?P<tail>\s*\})'
    )
    html = pat.sub(repl, html)
    if changed[0]:
        notes.append(f"svcMeta: +img on {changed[0]} services")
    else:
        notes.append("svcMeta: no entries matched (export shape changed?)")
    return html


def propagate_servicesfull(html, notes):
    """Carry the img field through the servicesFull object literal."""
    if "img: m.img" in html:
        return html
    new = html.replace("name: m.name, cat: m.cat,",
                       "name: m.name, cat: m.cat, img: m.img,", 1)
    notes.append("servicesFull: img propagated" if new != html
                 else "servicesFull: anchor not found")
    return new


def swap_detail(html, notes):
    """Service-detail placeholder → <img src="{{ detail.img }}">."""
    if 'src="{{ detail.img }}"' in html:
        return html
    pat = re.compile(
        r'<div style="background:repeating-linear-gradient\([^"]*?\);'
        r'border-radius:16px;aspect-ratio:4/3;[^"]*?">'
        r'<span[^>]*>\{\{ detail\.label \}\}</span></div>'
    )
    img = (f'<img src="{{{{ detail.img }}}}" alt="{{{{ detail.name }}}} — interface preview" '
           f'loading="lazy" decoding="async" '
           f'style="aspect-ratio:4/3;border-radius:16px;{IMG_BASE}"/>')
    new, n = pat.subn(img, html, count=1)
    notes.append("detail: image bound" if n else "detail: placeholder not found")
    return new


def swap_about(html, notes):
    """About portrait placeholder → static about.svg."""
    if f'{MOCK}/about.svg' in html:
        return html
    pat = re.compile(
        r'<div style="background:repeating-linear-gradient\([^"]*?\);'
        r'border-radius:16px;aspect-ratio:4/5;[^"]*?">'
        r'<span[^>]*>\[ portrait[^<]*\]</span></div>'
    )
    img = (f'<img src="{MOCK}/about.svg" alt="George — building AI systems" '
           f'loading="lazy" decoding="async" '
           f'style="aspect-ratio:4/5;border-radius:16px;{IMG_BASE}"/>')
    new, n = pat.subn(img, html, count=1)
    notes.append("about: portrait bound" if n else "about: placeholder not found")
    return new


def swap_news(html, notes):
    """News card placeholders → /assets/mock/news-{{ $index }}.svg (order-stable,
    language-independent)."""
    if f'{MOCK}/news-' in html:
        return html
    pat = re.compile(
        r'<div style="aspect-ratio:16/9;background:repeating-linear-gradient\([^"]*?\);'
        r'[^"]*?border-bottom:1px solid var\(--cardBorder\)">'
        r'<span[^>]*>\[ \{\{ a\.cat \}\} \]</span></div>'
    )
    img = (f'<img src="{MOCK}/news-{{{{ $index }}}}.svg" alt="{{{{ a.title }}}}" '
           f'loading="lazy" decoding="async" '
           f'style="aspect-ratio:16/9;{IMG_BASE};'
           f'border:none;border-bottom:1px solid var(--cardBorder)"/>')
    new, n = pat.subn(img, html, count=1)
    notes.append("news: card image bound" if n else "news: placeholder not found")
    return new


def hide_template(html, notes):
    """Hide the raw <x-dc> template until support.js renders over it.

    <x-dc> holds the design tool's template source, which support.js reads via
    innerHTML — but the browser also parses it as live DOM, so until hydration
    finishes it paints as a ~12,000px block of visible `{{ }}` markup. Hiding it
    costs nothing (support.js renders into its own root; the crawl fallback is
    the <noscript> block) and removes that flash on a slow connection or when
    support.js fails outright.
    """
    if 'x-dc[data-dc-hidden]' in html:
        return html
    css = "<style>x-dc[data-dc-hidden]{display:none}</style>"
    new, n = re.subn(r'<x-dc(?=[\s>])', '<x-dc data-dc-hidden', html, count=1)
    if not n:
        notes.append("template: <x-dc> not found")
        return html
    new = new.replace("</head>", css + "</head>", 1)
    notes.append("template: raw <x-dc> hidden pre-hydration")
    return new


def process(path):
    with open(path, encoding="utf-8") as fh:
        html = fh.read()
    if "svcMeta" not in html and "detail.label" not in html:
        return None  # not the SPA homepage — skip silently
    notes = []
    orig = html
    html = add_svcmeta_img(html, notes)
    html = propagate_servicesfull(html, notes)
    html = swap_detail(html, notes)
    html = swap_about(html, notes)
    html = swap_news(html, notes)
    html = hide_template(html, notes)
    if html != orig:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
    return notes


def main(argv):
    if len(argv) < 2:
        print("usage: apply_images.py <html> [html ...]", file=sys.stderr)
        return 2
    any_done = False
    for p in argv[1:]:
        if not os.path.isfile(p):
            continue
        notes = process(p)
        if notes is None:
            continue
        any_done = True
        print(f"{os.path.basename(p)}: " + "; ".join(notes))
    if not any_done:
        print("apply_images: no SPA homepage found among inputs")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
