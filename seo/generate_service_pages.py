#!/usr/bin/env python3
"""Generate static, indexable service pages + sitemap for georgeai.dev.

Called by deploy.sh on every deploy:
    python3 seo/generate_service_pages.py georgeai_services.json site/

Reads the canonical service catalog (georgeai_services.json) and writes:
    site/services/index.html          — services hub page
    site/services/<slug>/index.html   — one page per service
    site/sitemap.xml                  — homepage + hub + all service pages

The SPA homepage stays untouched: these pages exist so every service has a
real, crawlable URL with its own title/description/JSON-LD (the "biggest
GEO/SEO win" noted in the original sitemap). Content is English; the SPA
handles i18n interactively.
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

BASE = "https://georgeai.dev"
OG_IMAGE = f"{BASE}/assets/SEO_AI.png"
EMAIL = "contact@georgeai.dev"
PHONE = "+49 160 4155546"
PHONE_HREF = "tel:+491604155546"

# design tokens from DESIGN-claude.md
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#faf9f5;color:#3d3d3a;font-family:Inter,system-ui,sans-serif;line-height:1.6}
a{color:#cc785c}
.wrap{max-width:840px;margin:0 auto;padding:0 24px}
header.site{border-bottom:1px solid #e6dfd8;padding:18px 0}
header.site .wrap{display:flex;align-items:center;justify-content:space-between}
.wordmark{font-family:Newsreader,Georgia,serif;font-size:22px;color:#141413;text-decoration:none}
.wordmark b{color:#cc785c;font-weight:500}
nav.crumbs{font-family:'JetBrains Mono',monospace;font-size:12px;margin:28px 0 8px;color:#8e8b82}
nav.crumbs a{color:#6c6a64;text-decoration:none}
nav.crumbs a:hover{color:#cc785c}
.cat{display:inline-block;font-family:'JetBrains Mono',monospace;font-size:12px;color:#cc785c;border:1px solid #e6dfd8;border-radius:9999px;padding:4px 12px;margin:14px 0 10px}
h1{font-family:Newsreader,Georgia,serif;font-weight:500;font-size:44px;color:#141413;line-height:1.15;margin:6px 0 10px}
.tagline{font-family:Newsreader,Georgia,serif;font-size:22px;color:#6c6a64;font-style:italic;margin-bottom:18px}
.intro{font-size:17px;color:#252523;margin-bottom:34px;max-width:64ch}
h2{font-family:Newsreader,Georgia,serif;font-weight:500;font-size:26px;color:#141413;margin:34px 0 12px}
ul.list{list-style:none;margin-bottom:8px}
ul.list li{padding:9px 0 9px 26px;position:relative;border-bottom:1px solid #ebe6df}
ul.list li::before{content:"";position:absolute;left:2px;top:17px;width:8px;height:8px;background:#cc785c;clip-path:polygon(50% 0,61% 39%,100% 50%,61% 61%,50% 100%,39% 61%,0 50%,39% 39%)}
ol.steps{counter-reset:s;list-style:none}
ol.steps li{counter-increment:s;padding:9px 0 9px 38px;position:relative;border-bottom:1px solid #ebe6df}
ol.steps li::before{content:counter(s,decimal-leading-zero);position:absolute;left:0;top:11px;font-family:'JetBrains Mono',monospace;font-size:12px;color:#cc785c}
.outcome{background:#181715;color:#faf9f5;border-radius:14px;padding:24px 26px;margin:36px 0;font-family:Newsreader,Georgia,serif;font-size:20px}
.outcome small{display:block;font-family:'JetBrains Mono',monospace;font-size:11px;color:#a09d96;letter-spacing:.12em;text-transform:uppercase;margin-bottom:8px}
.stack{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 30px}
.stack span{font-family:'JetBrains Mono',monospace;font-size:12px;background:#f5f0e8;border:1px solid #e6dfd8;border-radius:8px;padding:5px 11px;color:#3d3d3a}
.cta{background:#efe9de;border-radius:14px;padding:26px;margin:36px 0}
.cta h2{margin-top:0}
.cta .btn{display:inline-block;background:#cc785c;color:#fff;text-decoration:none;border-radius:9999px;padding:11px 22px;font-weight:600;margin:6px 12px 0 0}
.cta .btn.alt{background:transparent;color:#141413;border:1px solid #cc785c}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px;margin:18px 0 40px}
.card{background:#fff;border:1px solid #e6dfd8;border-radius:14px;padding:20px;text-decoration:none;display:block}
.card:hover{border-color:#cc785c}
.card h3{font-family:Newsreader,Georgia,serif;font-weight:500;font-size:20px;color:#141413;margin-bottom:6px}
.card p{font-size:14px;color:#6c6a64}
.cathead{font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#8e8b82;margin:34px 0 4px}
footer.site{border-top:1px solid #e6dfd8;margin-top:56px;padding:26px 0 40px;font-size:14px;color:#6c6a64}
footer.site a{text-decoration:none}
article p{margin:0 0 16px;max-width:68ch}
article .lead{font-size:19px;color:#252523}
.post-meta{font-family:'JetBrains Mono',monospace;font-size:12px;color:#8e8b82;margin:4px 0 22px}
.takeaways{background:#f5f0e8;border:1px solid #e6dfd8;border-radius:14px;padding:20px 24px;margin:26px 0}
.takeaways ul{margin:10px 0 0 18px}
.takeaways li{margin-bottom:6px}
.from-practice{border-left:3px solid #cc785c;padding:2px 0 2px 16px;color:#252523}
.faq h3{font-family:Newsreader,Georgia,serif;font-weight:500;font-size:20px;color:#141413;margin:20px 0 6px}
article code{font-family:'JetBrains Mono',monospace;font-size:.88em;background:#f5f0e8;border:1px solid #ebe6df;border-radius:5px;padding:1px 5px}
@media(max-width:600px){h1{font-size:32px}.tagline{font-size:19px}}
"""

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">'
)


def slugify(name: str) -> str:
    s = name.lower().replace("&", " ").replace("/", " ")
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", s)).strip("-")


def meta_desc(svc: dict) -> str:
    text = f"{svc['tagline']} {svc['intro']}"
    if len(text) <= 158:
        return text
    return text[:155].rsplit(" ", 1)[0].rstrip(",.;:") + "…"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def page_shell(title, description, canonical, body, jsonld) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<link rel="canonical" href="{canonical}">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<meta property="og:type" content="website">
<meta property="og:site_name" content="GeorgeAI">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{OG_IMAGE}">
<meta name="twitter:card" content="summary_large_image">
{FONTS}
<style>{CSS}</style>
<script type="application/ld+json">
{json.dumps(jsonld, ensure_ascii=False, indent=1)}
</script>
</head>
<body>
<header class="site"><div class="wrap">
<a class="wordmark" href="/">George<b>AI</b></a>
<a href="/" style="font-family:'JetBrains Mono',monospace;font-size:13px;text-decoration:none">← back to site</a>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="site"><div class="wrap">
GeorgeAI — AI automation &amp; software · <a href="{PHONE_HREF}">{PHONE}</a> · <a href="mailto:{EMAIL}">{EMAIL}</a> · <a href="/services/">All services</a> · <a href="/blog/">Blog</a>
</div></footer>
</body>
</html>
"""


def service_jsonld(svc, slug, canonical):
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Service",
                "@id": f"{canonical}#service",
                "name": svc["name"],
                "serviceType": svc["name"],
                "category": svc["category"],
                "description": f"{svc['tagline']} {svc['intro']}",
                "url": canonical,
                "provider": {"@id": f"{BASE}/#organization"},
                "areaServed": "Worldwide",
                "availableChannel": {
                    "@type": "ServiceChannel",
                    "serviceUrl": f"{BASE}/",
                    "availableLanguage": ["en", "de", "fr", "ro", "ar"],
                },
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{canonical}#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
                    {"@type": "ListItem", "position": 2, "name": "Services", "item": f"{BASE}/services/"},
                    {"@type": "ListItem", "position": 3, "name": svc["name"]},
                ],
            },
            {
                "@type": "WebPage",
                "@id": canonical,
                "url": canonical,
                "name": f"{svc['name']} — GeorgeAI",
                "isPartOf": {"@id": f"{BASE}/#website"},
                "breadcrumb": {"@id": f"{canonical}#breadcrumb"},
                "mainEntity": {"@id": f"{canonical}#service"},
                "inLanguage": "en",
            },
        ],
    }


def service_body(svc):
    crumbs = (
        '<nav class="crumbs"><a href="/">Home</a> / '
        f'<a href="/services/">Services</a> / {esc(svc["name"])}</nav>'
    )
    includes = "".join(f"<li>{esc(i)}</li>" for i in svc.get("includes", []))
    steps = "".join(f"<li>{esc(s)}</li>" for s in svc.get("steps", []))
    stack = "".join(f"<span>{esc(t)}</span>" for t in svc.get("stack", []))
    return f"""{crumbs}
<span class="cat">{esc(svc["category"])}</span>
<h1>{esc(svc["name"])}</h1>
<p class="tagline">{esc(svc["tagline"])}</p>
<p class="intro">{esc(svc["intro"])}</p>
<h2>What's included</h2>
<ul class="list">{includes}</ul>
<h2>How it works</h2>
<ol class="steps">{steps}</ol>
<div class="outcome"><small>Outcome</small>{esc(svc["outcome"])}</div>
<h2>Stack</h2>
<div class="stack">{stack}</div>
<div class="cta">
<h2>Get a quote</h2>
<p>Configure this service on the main site, or reach out directly — replies within one business day.</p>
<a class="btn" href="/">Open the configurator</a>
<a class="btn alt" href="mailto:{EMAIL}">{EMAIL}</a>
</div>"""


def hub_body(data, slugs):
    cats = data["categories"]
    sections = []
    for ci, cat in enumerate(cats):
        cards = "".join(
            f'<a class="card" href="/services/{slugs[s["name"]]}/">'
            f'<h3>{esc(s["name"])}</h3><p>{esc(s["tagline"])}</p></a>'
            for s in data["services"]
            if s["cat"] == ci
        )
        sections.append(f'<p class="cathead">{esc(cat)}</p><div class="grid">{cards}</div>')
    return (
        '<nav class="crumbs"><a href="/">Home</a> / Services</nav>'
        "<h1>Services</h1>"
        '<p class="intro">AI automation, chatbots, AI phone agents, growth systems and custom '
        "Python &amp; Django software — every service below has a fixed, transparent scope. "
        'Pick one to see what\'s included, or <a href="/">use the configurator</a> for a bundled quote.</p>'
        + "".join(sections)
    )


def hub_jsonld(data, slugs):
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": f"{BASE}/services/",
                "url": f"{BASE}/services/",
                "name": "Services — GeorgeAI",
                "isPartOf": {"@id": f"{BASE}/#website"},
                "inLanguage": "en",
            },
            {
                "@type": "ItemList",
                "@id": f"{BASE}/services/#list",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i + 1,
                        "name": s["name"],
                        "url": f"{BASE}/services/{slugs[s['name']]}/",
                    }
                    for i, s in enumerate(data["services"])
                ],
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{BASE}/services/#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
                    {"@type": "ListItem", "position": 2, "name": "Services"},
                ],
            },
        ],
    }


def parse_post(path: Path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"<!--meta\n(.*?)\n-->\n?", raw, re.S)
    if not m:
        raise ValueError(f"{path}: missing <!--meta --> header")
    meta = json.loads(m.group(1))
    meta["slug"] = path.stem
    meta["body"] = raw[m.end():]
    return meta


def post_jsonld(post, canonical):
    graph = [
        {
            "@type": "BlogPosting",
            "@id": f"{canonical}#article",
            "headline": post["title"],
            "description": post["description"],
            "datePublished": post["date"],
            "dateModified": post.get("updated", post["date"]),
            "author": {"@id": f"{BASE}/#george"},
            "publisher": {"@id": f"{BASE}/#organization"},
            "image": OG_IMAGE,
            "url": canonical,
            "mainEntityOfPage": canonical,
            "keywords": ", ".join(post.get("tags", [])),
            "inLanguage": "en",
            "isPartOf": {"@id": f"{BASE}/#website"},
        },
        {
            "@type": "BreadcrumbList",
            "@id": f"{canonical}#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
                {"@type": "ListItem", "position": 2, "name": "Blog", "item": f"{BASE}/blog/"},
                {"@type": "ListItem", "position": 3, "name": post["title"]},
            ],
        },
    ]
    if post.get("faq"):
        graph.append(
            {
                "@type": "FAQPage",
                "@id": f"{canonical}#faq",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f["q"],
                        "acceptedAnswer": {"@type": "Answer", "text": f["a"]},
                    }
                    for f in post["faq"]
                ],
            }
        )
    return {"@context": "https://schema.org", "@graph": graph}


def post_body(post):
    faq_html = ""
    if post.get("faq"):
        items = "".join(
            f"<h3>{esc(f['q'])}</h3><p>{esc(f['a'])}</p>" for f in post["faq"]
        )
        faq_html = f'<section class="faq"><h2>Frequently asked questions</h2>{items}</section>'
    tags = " · ".join(esc(t) for t in post.get("tags", []))
    return f"""<nav class="crumbs"><a href="/">Home</a> / <a href="/blog/">Blog</a> / {esc(post["title"])}</nav>
<article>
<h1>{esc(post["title"])}</h1>
<p class="post-meta">{esc(post["date"])} · George Sebastian Cucuiet · {tags}</p>
{post["body"]}
{faq_html}
</article>"""


def blog_hub_body(posts):
    cards = "".join(
        f'<a class="card" href="/blog/{p["slug"]}/"><h3>{esc(p["title"])}</h3>'
        f'<p>{esc(p["description"])}</p>'
        f'<p class="post-meta" style="margin:10px 0 0">{esc(p["date"])}</p></a>'
        for p in posts
    )
    return (
        '<nav class="crumbs"><a href="/">Home</a> / Blog</nav>'
        "<h1>Blog</h1>"
        '<p class="intro">Practical notes on AI automation, GEO/AIO and software for small and '
        "mid-sized businesses — written from client work, with sources you can check. "
        "No news reposts, no filler.</p>"
        f'<div class="grid" style="grid-template-columns:1fr">{cards}</div>'
    )


def blog_hub_jsonld(posts):
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Blog",
                "@id": f"{BASE}/blog/",
                "url": f"{BASE}/blog/",
                "name": "GeorgeAI Blog",
                "publisher": {"@id": f"{BASE}/#organization"},
                "isPartOf": {"@id": f"{BASE}/#website"},
                "inLanguage": "en",
                "blogPost": [
                    {"@id": f"{BASE}/blog/{p['slug']}/#article"} for p in posts
                ],
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{BASE}/blog/#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
                    {"@type": "ListItem", "position": 2, "name": "Blog"},
                ],
            },
        ],
    }


def sitemap(urls, today):
    entries = "".join(
        f"\n  <url>\n    <loc>{u}</loc>\n    <lastmod>{today}</lastmod>\n"
        f"    <changefreq>{'weekly' if u.rstrip('/') == BASE.rstrip('/') else 'monthly'}</changefreq>\n"
        f"    <priority>{p}</priority>\n  </url>"
        for u, p in urls
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{entries}\n</urlset>\n"
    )


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit("usage: generate_service_pages.py <georgeai_services.json> <site_dir> [blog_dir]")
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    site = Path(sys.argv[2])
    slugs = {s["name"]: slugify(s["name"]) for s in data["services"]}
    today = date.today().isoformat()

    urls = [(f"{BASE}/", "1.0"), (f"{BASE}/services/", "0.9")]
    for svc in data["services"]:
        slug = slugs[svc["name"]]
        canonical = f"{BASE}/services/{slug}/"
        out = site / "services" / slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        title = f"{svc['name']} — GeorgeAI"
        out.write_text(
            page_shell(title, meta_desc(svc), canonical, service_body(svc),
                       service_jsonld(svc, slug, canonical)),
            encoding="utf-8",
        )
        urls.append((canonical, "0.8"))

    hub = site / "services" / "index.html"
    hub.write_text(
        page_shell(
            "Services — AI Automation, Chatbots, GEO/SEO & Software | GeorgeAI",
            "All GeorgeAI services: AI automation, chatbots, AI phone agents, SEO/AIO/GEO, "
            "email marketing, lead generation, Python, Django, ERP/CRM and web design.",
            f"{BASE}/services/",
            hub_body(data, slugs),
            hub_jsonld(data, slugs),
        ),
        encoding="utf-8",
    )

    # blog: optional third arg = directory of post fragments (blog/*.html)
    n_posts = 0
    if len(sys.argv) > 3 and Path(sys.argv[3]).is_dir():
        posts = sorted(
            (parse_post(p) for p in Path(sys.argv[3]).glob("*.html")),
            key=lambda p: p["date"],
            reverse=True,
        )
        for post in posts:
            canonical = f"{BASE}/blog/{post['slug']}/"
            out = site / "blog" / post["slug"] / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(
                page_shell(f"{post['title']} | GeorgeAI Blog", post["description"],
                           canonical, post_body(post), post_jsonld(post, canonical)),
                encoding="utf-8",
            )
            urls.append((canonical, "0.7"))
        if posts:
            (site / "blog" / "index.html").write_text(
                page_shell(
                    "Blog — AI Automation & GEO Notes | GeorgeAI",
                    "Practical, sourced articles on AI automation, GEO/AIO and software "
                    "for small and mid-sized businesses. Written from client work.",
                    f"{BASE}/blog/",
                    blog_hub_body(posts),
                    blog_hub_jsonld(posts),
                ),
                encoding="utf-8",
            )
            urls.insert(2, (f"{BASE}/blog/", "0.8"))
        n_posts = len(posts)

    (site / "sitemap.xml").write_text(sitemap(urls, today), encoding="utf-8")
    print(f"generated {len(data['services'])} service pages + {n_posts} blog posts + sitemap ({len(urls)} urls)")


if __name__ == "__main__":
    main()
