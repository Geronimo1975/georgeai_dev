#!/usr/bin/env python3
"""Inject repo-owned copy into the design-tool export.

site/ is wiped and regenerated from the export on every deploy, so positioning
and compliance work done inside the export is silently lost at the next
re-export. This script re-applies it from seo/*.json on every deploy.

  seo/hero.json          -> the hero object of every language block
  seo/testimonials.json  -> GA_EXTRA.testi.items, and hides the whole
                            testimonials section for languages with none

Nothing is written unless every edit succeeds, so a bad patch cannot ship a
half-modified page.

Usage: apply_content.py SITE_DIR SEO_DIR PAGE [PAGE ...]
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import contact_page  # noqa: E402

HERO_FIELDS = ("eyebrow", "title", "sub", "cta1", "cta2")
LANGS = ("en", "de", "fr", "ro", "ar")


class PatchError(Exception):
    pass


def load(path: Path) -> dict:
    """Read a copy file, dropping _-prefixed keys (notes for the reader)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


# ---------------------------------------------------------------------------
# hero — one object literal per language block of the T() table
# ---------------------------------------------------------------------------
def patch_hero(html: str, heroes: dict) -> str:
    for lang, hero in heroes.items():
        missing = [k for k in HERO_FIELDS if k not in hero]
        if missing:
            raise PatchError(f"hero.json[{lang}] missing {', '.join(missing)}")
        block = re.search(r"^ {6}%s: \{" % re.escape(lang), html, re.M)
        if not block:
            raise PatchError(f"no '{lang}: {{' language block found")
        # the hero literal is single-line and brace-free, so [^{}]* is bounded
        obj = re.compile(r"hero:\s*\{[^{}]*\}").search(html, block.end())
        if not obj:
            raise PatchError(f"no hero object inside the {lang} block")
        fields = ", ".join(
            "%s: %s" % (k, json.dumps(hero[k], ensure_ascii=False)) for k in HERO_FIELDS
        )
        html = html[: obj.start()] + "hero: { " + fields + " }" + html[obj.end():]
    return html


# ---------------------------------------------------------------------------
# testimonials — the items map inside GA_EXTRA.testi
# ---------------------------------------------------------------------------
def _brace_span(src: str, open_at: int) -> tuple[int, int]:
    """Span of the {...} whose opening brace is at or after open_at."""
    start = src.index("{", open_at)
    depth = 0
    for i in range(start, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
    raise PatchError("unbalanced braces while reading the testimonials block")


def patch_testimonials(js: str, testis: dict) -> str:
    testi = re.search(r"\n\s*testi:\s*\{", js)
    if not testi:
        raise PatchError("no 'testi:' block in services-data.js")
    items = re.compile(r"items:\s*\{").search(js, testi.start())
    if not items:
        raise PatchError("no 'items:' map inside the testi block")
    start, end = _brace_span(js, items.end() - 1)

    langs = []
    for lang in LANGS:
        entries = testis.get(lang, [])
        for e in entries:
            for k in ("quote", "name", "role"):
                if k not in e:
                    raise PatchError(f"testimonials.json[{lang}] entry missing '{k}'")
        rendered = "".join(
            "\n        { quote: %s, name: %s, role: %s },"
            % tuple(json.dumps(e[k], ensure_ascii=False) for k in ("quote", "name", "role"))
            for e in entries
        )
        langs.append("      %s: [%s\n      ]," % (lang, rendered))

    block = "items: {\n" + "\n".join(langs) + "\n    }"
    return js[: items.start()] + block + js[end:]


# ---------------------------------------------------------------------------
# testimonials section visibility — the export renders a blank card with a "?"
# avatar when the list is empty, because testiCur falls back to empty strings.
# Wire a hasTesti flag and gate the whole section on it, so emptying the JSON
# removes the section instead of leaving a hollow one.
# ---------------------------------------------------------------------------
def wire_testi_visibility(html: str) -> str:
    if "hasTesti" not in html:
        decl = re.search(r"^(\s*)const testiAll = [^\n]*\n", html, re.M)
        if not decl:
            raise PatchError("no 'const testiAll =' declaration to hook")
        indent = decl.group(1)
        html = (
            html[: decl.end()]
            + f"{indent}const hasTesti = testiAll.length > 0;\n"
            + html[decl.end():]
        )
        ctx = "testiT, testiCur,"
        if ctx not in html:
            raise PatchError("no render context listing testiT/testiCur")
        html = html.replace(ctx, "hasTesti, " + ctx, 1)

    if "<!-- TESTIMONIALS -->" in html and 'value="{{ hasTesti }}"' not in html:
        html = html.replace(
            "  <!-- TESTIMONIALS -->\n",
            '  <!-- TESTIMONIALS -->\n  <sc-if value="{{ hasTesti }}">\n',
            1,
        )
        if "  <!-- FAQ -->" not in html:
            raise PatchError("no '<!-- FAQ -->' marker to close the sc-if before")
        html = html.replace("  <!-- FAQ -->", "  </sc-if>\n\n  <!-- FAQ -->", 1)
    return html


# ---------------------------------------------------------------------------
# hero markup — the export renders NO headline. Both hero variants (panels and
# video) draw the background, the flag strip and the service panels, then jump
# straight to the two CTA buttons, so t.hero.eyebrow / .title / .sub sit unused
# in the T() table. Insert the missing eyebrow + h1 + sub ahead of the CTA row
# in each variant, styled from the export's own conventions so it matches the
# rest of the page. Marker-guarded, so re-running is a no-op.
# ---------------------------------------------------------------------------
HERO_MARKUP = (
    '<!-- seo:hero-copy -->\n'
    '{i}<div style="position:relative;z-index:1;max-width:820px">\n'
    '{i}  <div style="display:inline-block;font-family:\'JetBrains Mono\',\'Noto Sans Arabic\',monospace;'
    'font-size:11px;letter-spacing:1.5px;text-transform:uppercase;color:var(--accent);'
    'border:1px solid var(--cardBorder);border-radius:9999px;padding:6px 14px">{{{{ t.hero.eyebrow }}}}</div>\n'
    '{i}  <h1 style="font-family:{{{{ fontDisplay }}}};font-weight:400;font-size:{{{{ heroTitleSize }}}};'
    'line-height:1.04;letter-spacing:-1.5px;color:var(--ink);margin-top:18px;text-wrap:balance">'
    '{{{{ t.hero.title }}}}</h1>\n'
    '{i}  <p style="font-size:17px;line-height:1.6;color:var(--muted);max-width:620px;margin-top:16px">'
    '{{{{ t.hero.sub }}}}</p>\n'
    '{i}</div>\n'
)

# The opening <div> of the row holding the hero CTAs, in either variant. Anchor
# on t.hero.cta1 specifically: goServices alone also matches the services-page
# and CTA-band buttons, which would scatter four headlines across the document.
_CTA_ROW = re.compile(
    r'\n([ \t]*)<div style="[^"]*">\n'
    r'[ \t]*<span onClick="\{\{ goServices \}\}"[^>]*>\{\{ t\.hero\.cta1 \}\}</span>'
)


def render_hero_markup(html: str) -> str:
    if "seo:hero-copy" in html:
        return html
    matches = list(_CTA_ROW.finditer(html))
    if not matches:
        raise PatchError("no hero CTA row found to anchor the headline to")
    # walk backwards so earlier offsets stay valid
    for m in reversed(matches):
        indent = m.group(1)
        block = "\n" + indent + HERO_MARKUP.format(i=indent)
        html = html[: m.start()] + block + html[m.start():]
    return html


# ---------------------------------------------------------------------------
# social stubs — Facebook / Instagram / TikTok / YouTube point at bare platform
# domains, not profiles. They sit in the sticky header next to the real
# WhatsApp / LinkedIn / GitHub links, so tapping one lands on a login wall and
# demotes the real profiles to decoration. Drop the four, keep the three.
# ---------------------------------------------------------------------------
STUB_SOCIALS = ("facebook", "instagram", "tiktok", "youtube")


def strip_social_stubs(html: str) -> str:
    pattern = re.compile(
        r'\n\s*\{ name: "(?:Facebook|Instagram|TikTok|YouTube)", url: [^\n]*?'
        r'href: "https://(?:facebook|instagram|tiktok|youtube)\.com" \},'
    )
    if not pattern.search(html):
        return html  # already stripped, or the export dropped them
    html = pattern.sub("", html)
    left = [s for s in STUB_SOCIALS if f'href: "https://{s}.com"' in html]
    if left:
        raise PatchError("social stubs still present after strip: " + ", ".join(left))
    return html


# ---------------------------------------------------------------------------
# "Read the case study →" — the label renders inside the featured-project card
# in both hero variants, but the parent handler only re-selects the panel that
# is already active, and no case study exists anywhere on the site. A warm
# contact reads a dead proof link as "there is no proof". Remove the label
# until a real case study exists to point it at.
# ---------------------------------------------------------------------------
def strip_dead_case_study_cta(html: str) -> str:
    if "t.featured.cta" not in html:
        return html
    html = re.sub(
        r"\n\s*<(span|div)[^>]*>\{\{ t\.featured\.cta \}\}[^<]*</\1>", "", html
    )
    if "t.featured.cta" in html.split("featured: {")[0]:
        raise PatchError("a rendered {{ t.featured.cta }} node survived the strip")
    return html


# ---------------------------------------------------------------------------
# CTA band — the coral "Start a project" button is the largest call to action
# on the homepage and carries no handler at all: a tap does nothing. On a phone
# that reads as a broken site, which is the worst possible signal from someone
# selling production systems.
# ---------------------------------------------------------------------------
def wire_cta_band(html: str) -> str:
    if "{{ t.cta.btn }}" not in html:
        return html  # CTA band not in this page
    span = re.search(r"<span(?![^>]*onClick)([^>]*)>\{\{ t\.cta\.btn \}\}</span>", html)
    if not span:
        return html  # already wired
    if "goContact" not in html:
        raise PatchError("no goContact binding to wire the CTA band to")
    html = (
        html[: span.start()]
        + '<span onClick="{{ goContact }}"' + span.group(1) + ">{{ t.cta.btn }}</span>"
        + html[span.end():]
    )
    return html


# ---------------------------------------------------------------------------
# booking form and quote configurator — both showed a success screen and
# transmitted nothing: no fetch, no <form>, no action. A warm contact picked a
# slot, saw "Request sent.", and waited for a confirmation that could never
# arrive. Until a real endpoint exists, hand the enquiry to the visitor's own
# mail client with the chosen slot / services prefilled, and say so honestly.
#
# The inputs are unbound in the export (placeholder only, no value/onChange),
# so name, email and message are typed in the mail client rather than read from
# the page. bookDate/bookTime and cfgServices are real state and do carry over.
# ---------------------------------------------------------------------------
CONTACT_EMAIL = "contact@georgeai.dev"

OLD_BOOKING = (
    "const submitBooking = () => { if (this.state.bookDate && this.state.bookTime)"
    " this.setState({ bookDone: true }); };"
)
NEW_BOOKING = """const submitBooking = () => {
      if (!(this.state.bookDate && this.state.bookTime)) return;
      const when = (chosen ? chosen + ", " : "") + this.state.bookTime;
      const body = "Hi George,\\n\\nI would like to book the " + when + " slot."
        + "\\n\\nName:\\nEmail:\\nWhat it is about:\\n\\nThanks,";
      window.location.href = "mailto:%s?subject="
        + encodeURIComponent("Booking request: " + when)
        + "&body=" + encodeURIComponent(body);
      this.setState({ bookDone: true });
    };""" % CONTACT_EMAIL

OLD_CONFIG = (
    "const submitConfig = () => { if (Object.keys(this.state.cfgServices || {}).length > 0)"
    " this.setState({ cfgDone: true }); };"
)
NEW_CONFIG = """const submitConfig = () => {
      if (!(Object.keys(this.state.cfgServices || {}).length > 0)) return;
      const picked = (selectedNames || []).join(", ");
      const body = "Hi George,\\n\\nI am interested in: " + picked
        + "\\nScale: " + scaleName + "\\n\\nName:\\nCompany:\\nWhat I need:\\n\\nThanks,";
      window.location.href = "mailto:%s?subject="
        + encodeURIComponent("Project enquiry: " + picked)
        + "&body=" + encodeURIComponent(body);
      this.setState({ cfgDone: true });
    };""" % CONTACT_EMAIL

# the confirmation screen has to describe what actually happened
BOOKING_DONE = {
    'doneTitle: "Request sent.", doneMsg: "Thanks — I\'ll confirm your slot by email shortly."':
        'doneTitle: "Your email is open.", doneMsg: "Send the message that just opened and I\'ll confirm your slot."',
    'doneTitle: "Anfrage gesendet.", doneMsg: "Danke — ich bestätige Ihren Termin in Kürze per E-Mail."':
        'doneTitle: "Ihre E-Mail ist offen.", doneMsg: "Senden Sie die geöffnete Nachricht ab — ich bestätige den Termin."',
    'doneTitle: "Demande envoyée.", doneMsg: "Merci — je confirme votre créneau par e-mail très vite."':
        'doneTitle: "Votre e-mail est ouvert.", doneMsg: "Envoyez le message qui vient de s\'ouvrir et je confirme le créneau."',
    'doneTitle: "Solicitare trimisă.", doneMsg: "Mulțumesc — îți confirm intervalul prin email în scurt timp."':
        'doneTitle: "Ți s-a deschis emailul.", doneMsg: "Trimite mesajul care tocmai s-a deschis și îți confirm intervalul."',
    'doneTitle: "تم إرسال الطلب.", doneMsg: "شكرًا — سأؤكّد موعدك عبر البريد قريبًا."':
        'doneTitle: "فُتح بريدك.", doneMsg: "أرسل الرسالة التي فُتحت وسأؤكّد موعدك."',
}


def fix_lying_forms(html: str) -> str:
    if "Booking request: " in html:
        return html  # already patched

    if OLD_BOOKING not in html and "const submitBooking" in html:
        raise PatchError("submitBooking found but not in the expected shape")
    if OLD_CONFIG not in html and "const submitConfig" in html:
        raise PatchError("submitConfig found but not in the expected shape")
    if OLD_BOOKING not in html and OLD_CONFIG not in html:
        return html  # neither handler on this page

    html = html.replace(OLD_BOOKING, NEW_BOOKING, 1)
    html = html.replace(OLD_CONFIG, NEW_CONFIG, 1)

    hits = 0
    for old, new in BOOKING_DONE.items():
        if old in html:
            html = html.replace(old, new, 1)
            hits += 1
    if hits != len(LANGS):
        raise PatchError(
            "rewrote %d of %d booking confirmation messages; the form would still "
            "claim the request was sent" % (hits, len(LANGS))
        )
    return html


# ---------------------------------------------------------------------------
# dead hero video — the export ships a 6.9 MB assets/hero.mp4 inside a
# `heroIsVideo` branch, plus a "featured project" block gated on the same
# state. heroMode initialises to "panels" and setHeroVideo/setHeroPanels have
# zero onClick bindings anywhere: the <!-- HERO MODE SWITCH --> marker has no
# markup under it at all, so the switch was never built. The browser still
# fetches the full 6.9 MB body on every homepage load — verified against the
# live host — and no visitor can ever see a frame of it. Remove both blocks;
# deploy.sh then prunes the file itself.
#
# The heroIsVideo / showFeaturedBelow keys stay in the render context. They are
# a few bytes of dead data, and rewriting the returned object is a much larger
# blast radius than deleting markup.
# ---------------------------------------------------------------------------
def strip_dead_hero_video(html: str) -> str:
    if "{{ heroIsVideo }}" not in html:
        return html  # already stripped

    for start_marker, end_marker in (
        ("  <!-- HERO — VIDEO -->", "  <!-- LOGO CAROUSEL -->"),
        ("  <!-- FEATURED PROJECT", "  <!-- HOW IT WORKS -->"),
    ):
        start = html.find("\n" + start_marker)
        end = html.find("\n" + end_marker)
        if start == -1 or end == -1 or end <= start:
            raise PatchError(
                "cannot bound %r ... %r — the export's section markers moved"
                % (start_marker.strip(), end_marker.strip())
            )
        html = html[:start] + html[end:]

    # the mode switch never existed; the marker only documents a feature that is
    # now definitively gone
    html = html.replace("  <!-- HERO MODE SWITCH -->\n", "", 1)

    for leftover in ("assets/hero.mp4", "{{ heroIsVideo }}", "{{ showFeaturedBelow }}"):
        if leftover in html:
            raise PatchError("%s survived the hero-video strip" % leftover)
    return html


# ---------------------------------------------------------------------------
# third-party assets — the export pulls every brand/stack icon from
# cdn.simpleicons.org and one logo from assets.streamlinehq.com at runtime.
# Measured on the live homepage: 47 of 67 requests went to those two US CDNs,
# each one handing a German visitor's IP to a third party the privacy policy
# does not name. They are also the first thing to break when the CSP flips from
# Report-Only. Serve them from our own origin instead; the files live in
# seo/vendor/icons/ and are copied to site/assets/icons/ by main().
# ---------------------------------------------------------------------------
ICON_PATH = "/assets/icons/"

_THIRD_PARTY = (
    ('const _si = (s) => "https://cdn.simpleicons.org/" + s;',
     'const _si = (s) => "' + ICON_PATH + '" + s + ".svg";'),
    ('const _soc = (s) => "https://cdn.simpleicons.org/" + s + "/8e8b82";',
     'const _soc = (s) => "' + ICON_PATH + '" + s + "-8e8b82.svg";'),
    ('"https://cdn.simpleicons.org/google"', '"' + ICON_PATH + 'google.svg"'),
    ('"https://cdn.simpleicons.org/github/cc785c"', '"' + ICON_PATH + 'github-cc785c.svg"'),
)

_STREAMLINE = re.compile(r'https://assets\.streamlinehq\.com/[^"\']+')


def localize_third_party_assets(html: str, vendor: Path) -> str:
    if "cdn.simpleicons.org" not in html and "streamlinehq" not in html:
        return html
    if not vendor.is_dir():
        raise PatchError(f"{vendor} missing — refusing to point icons at files that do not exist")

    for old, new in _THIRD_PARTY:
        html = html.replace(old, new)
    html = _STREAMLINE.sub(ICON_PATH + "openai.png", html)

    leftover = re.findall(r"https://cdn\.simpleicons\.org/[a-z0-9/]*", html)
    if leftover:
        raise PatchError("un-localised icon URLs remain: " + ", ".join(sorted(set(leftover))[:5]))
    return html


# ---------------------------------------------------------------------------
# Google Fonts — the export loads five families from fonts.googleapis.com,
# which pulls the faces themselves from fonts.gstatic.com: five requests to two
# Google hosts, each carrying the visitor's IP, on a site whose
# Datenschutzerklärung names no processors. Embedding Google Fonts without
# consent has been an Abmahnung target in Germany since LG München I,
# 3 O 17493/20 (2022) — the one item in this cleanup with case law behind it.
#
# seo/vendor/fonts.css + seo/vendor/fonts/ carry latin, latin-ext and arabic
# subsets only; the site serves en/de/fr/ro/ar, so cyrillic, greek, vietnamese,
# math and symbols were dropped. unicode-range is preserved, so a browser still
# fetches only the subsets it actually needs.
# ---------------------------------------------------------------------------
FONT_CSS_HREF = "/assets/fonts.css"
_GF_PRECONNECT = re.compile(
    r'\n\s*<link rel="preconnect" href="https://fonts\.(?:googleapis|gstatic)\.com"[^>]*>'
)
_GF_STYLESHEET = re.compile(
    r'<link href="https://fonts\.googleapis\.com/css2\?[^"]*"[^>]*>'
)


def localize_fonts(html: str, vendor_css: Path, vendor_dir: Path) -> str:
    if "fonts.googleapis.com" not in html:
        return html
    if not vendor_css.is_file() or not vendor_dir.is_dir():
        raise PatchError(
            "seo/vendor/fonts.css or seo/vendor/fonts/ missing — refusing to point "
            "@font-face at files that do not exist"
        )

    html = _GF_PRECONNECT.sub("", html)
    html, n = _GF_STYLESHEET.subn(
        '<link href="%s" rel="stylesheet">' % FONT_CSS_HREF, html
    )
    if n == 0:
        raise PatchError("no fonts.googleapis.com stylesheet link to rewrite")

    for host in ("fonts.googleapis.com", "fonts.gstatic.com"):
        if host in html:
            raise PatchError("%s still referenced after localising fonts" % host)
    return html


# ---------------------------------------------------------------------------
# React from unpkg — support.js fetches React and ReactDOM EAGERLY on first
# paint (loadReactUmd, called before the app renders), so every visitor's page
# render depends on a third-party CDN staying up and serving honest bytes. The
# page hides its own raw template before this resolves and <noscript> does not
# fire when JS is enabled, so a bad response is a blank page, not a fallback.
# On a site that is meant to take payments that is a live supply-chain path.
#
# The vendored files are byte-identical to what unpkg serves — verified against
# the export's own REACT_SRI / REACT_DOM_SRI sha384 constants — so the existing
# integrity attributes stay valid and now protect the local copy too.
#
# BABEL_URL is deliberately left alone: it loads lazily, only for "jsx" external
# modules, and vendoring ~2.5 MB for a feature that may never fire is the wrong
# trade. It does mean script-src cannot drop unpkg.com yet.
# ---------------------------------------------------------------------------
JS_PATH = "/assets/js/"
_REACT_URLS = (
    ("https://unpkg.com/react@18.3.1/umd/react.production.min.js",
     JS_PATH + "react.production.min.js"),
    ("https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js",
     JS_PATH + "react-dom.production.min.js"),
)


def localize_react(js: str, vendor: Path) -> str:
    if not any(old in js for old, _ in _REACT_URLS):
        return js  # already localised
    for name in ("react.production.min.js", "react-dom.production.min.js"):
        if not (vendor / name).is_file():
            raise PatchError(
                "seo/vendor/js/%s missing — refusing to point the render path at a "
                "file that does not exist (a miss here is a blank page)" % name
            )
    for old, new in _REACT_URLS:
        js = js.replace(old, new)
    leftover = re.findall(r"https://unpkg\.com/react[^\"']*", js)
    if leftover:
        raise PatchError("un-localised React URLs remain: " + ", ".join(sorted(set(leftover))))
    return js


# ---------------------------------------------------------------------------
# Babel from unpkg — the last third-party script host on the page. It loads
# lazily, only to transpile "jsx" external modules for the generated-page
# feature, which the user confirmed is unused (its one consumer,
# uploads/generated-page.html, is pruned from the web root at deploy time).
#
# ensureBabel() is neutered rather than surgically excised: the surrounding
# module loader still serves non-jsx kinds, so leaving its shape intact keeps
# the diff small and the blast radius near zero. With this gone, script-src can
# drop unpkg.com entirely and the page has no third-party hosts left at all.
# ---------------------------------------------------------------------------
_BABEL_DECL = re.compile(r'\n\s*var BABEL_URL = "https://unpkg\.com/@babel/[^"]*";')
_ENSURE_BABEL = re.compile(
    r"    function ensureBabel\(\) \{.*?\n    \}\n", re.S
)
_ENSURE_BABEL_STUB = """    function ensureBabel() {
      // The generated-page (jsx) feature is disabled; Babel was the last
      // third-party script host on the page. Fail loudly rather than silently
      // producing an untranspiled module.
      return Promise.reject(new Error("jsx external modules are not enabled"));
    }
"""


def strip_babel_loader(js: str) -> str:
    if "unpkg.com/@babel" not in js:
        return js  # already stripped

    js, n = _ENSURE_BABEL.subn(_ENSURE_BABEL_STUB, js, count=1)
    if n != 1:
        raise PatchError("could not locate ensureBabel() to neutralise")
    js, n = _BABEL_DECL.subn("", js, count=1)
    if n != 1:
        raise PatchError("could not locate the BABEL_URL declaration")

    if "unpkg.com" in js:
        leftover = sorted(set(re.findall(r"https://unpkg\.com[^\"']*", js)))
        raise PatchError("unpkg URLs remain after stripping Babel: " + ", ".join(leftover))
    return js


# ---------------------------------------------------------------------------
# stale and dead-end copy that survives a re-export. Three separate defects,
# grouped because each is a handful of string swaps across the five language
# blocks:
#
#   "Eleven ways"   — the copy says eleven, the data ships fifteen. Correcting
#                     the numeral is the wrong fix: to someone who knew George
#                     as Head of Infrastructure, a fifteen-item menu reads as a
#                     freelancer who does anything. Drop the count entirely.
#   "from Q3"       — undated availability that is stale on the day it is read.
#                     Made absolute instead of moved forward, so it cannot rot
#                     again. His actual availability window is his to set.
#   the Sign up pill — the most prominent interactive element in the mobile
#                     header, opening a modal whose submit can never fire, for
#                     a /api/auth/* backend that nginx does not serve. On a
#                     portfolio it is pure friction: a warm contact wants to
#                     reply, not to create an account.
# ---------------------------------------------------------------------------
_SERVICES_SUB = (
    ("Eleven ways I help teams move faster",
     "How I help teams move faster"),
    ("Elf Wege, wie ich Teams schneller mache",
     "So mache ich Teams schneller"),
    ("Onze façons d'aider les équipes à aller plus vite",
     "Comment j'aide les équipes à aller plus vite"),
    ("Unsprezece moduri prin care ajut echipele să avanseze mai repede",
     "Cum ajut echipele să avanseze mai repede"),
    ("إحدى عشرة طريقة أساعد بها الفرق على التحرّك أسرع",
     "كيف أساعد الفرق على التحرّك أسرع"),
)

_AVAILABILITY = (
    ("Available for new projects from Q3.", "Taking on new projects now."),
    ("Verfügbar für neue Projekte ab Q3.", "Ich nehme aktuell neue Projekte an."),
    ("Disponible pour de nouveaux projets dès le T3.", "Je prends de nouveaux projets en ce moment."),
    ("Disponibil pentru proiecte noi din T3.", "Preiau proiecte noi acum."),
    ("متاح لمشاريع جديدة من الربع الثالث.", "أقبل مشاريع جديدة الآن."),
)

_AUTH_PILL = re.compile(
    r'\n\s*<span onClick="\{\{ openAuth \}\}"[^>]*>\{\{ authLabel \}\}</span>'
)


def fix_stale_copy(html: str) -> str:
    for old, new in _SERVICES_SUB + _AVAILABILITY:
        html = html.replace(old, new)

    for stale in ("Eleven ways", "Elf Wege", "Onze façons", "Unsprezece moduri", "from Q3", "ab Q3"):
        if stale in html:
            raise PatchError("stale copy survived: %r" % stale)
    return html


def strip_auth_pill(html: str) -> str:
    if "{{ authLabel }}" not in html:
        return html
    html, n = _AUTH_PILL.subn("", html, count=1)
    if n != 1:
        raise PatchError("could not locate the header Sign up pill")
    return html


# ---------------------------------------------------------------------------
# Portfolio links — the export ships the "Selected work" section as a dead end:
# the "view all" label and every project card are styled to look clickable
# (cursor:pointer, a trailing arrow) but carry no handler and no href at all,
# so a click does nothing. The hero showcase panels are the same story one
# level up: the T() table even defines t.featured.cta ("Read the case study")
# but no variant ever renders it.
#
# seo/generate_service_pages.py now builds a real page per project from
# georgeai_work.json (/work/<slug>/), so both surfaces get wired to it here —
# in the content layer, because site/ is regenerated from the export.
#
# Slugs mirror slugify() in generate_service_pages.py; WORK_SLUGS is ordered
# as the export's own `works` array, and PANEL_SLUGS as its `flagData` array.
# ---------------------------------------------------------------------------
WORK_SLUGS = (
    "medical-ai-agent",
    "smart-facility-automation",
    "containerized-infrastructure",
    "full-stack-web-platform",
)
PANEL_SLUGS = ("ai-seo-automation-system",) + WORK_SLUGS

_WORK_ALL = (
    '<span style="font-size:14px;font-weight:500;color:var(--accent);'
    'cursor:pointer;white-space:nowrap">{{ t.workAll }} &rarr;</span>'
).replace("&rarr;", "→")
_WORK_ALL_LINK = (
    '<a href="/work/" style="font-size:14px;font-weight:500;color:var(--accent);'
    'text-decoration:none;cursor:pointer;white-space:nowrap">{{ t.workAll }} →</a>'
)
_WORK_CARD_OPEN = '<div style="cursor:pointer">\n          {{ w.thumb }}'
_WORK_CARD_LINK = (
    '<a href="{{ w.href }}" style="display:block;cursor:pointer;color:inherit;'
    'text-decoration:none">\n          {{ w.thumb }}'
)
_WORKS_MAP = re.compile(
    r'(const works = \[[^\]]*\]\.map\(\(name, i\) => \(\{)'
)
_PANEL_DESC = (
    '<p style="font-size:15px;line-height:1.55;color:rgba(255,255,255,.9);'
    'margin-top:8px;max-width:460px">{{ s.desc }}</p>'
)
_PANEL_LINK = (
    '\n              <a href="{{ s.href }}" style="display:inline-block;margin-top:14px;'
    'font-size:13px;font-weight:500;color:#fff;text-decoration:underline;'
    'text-underline-offset:3px;position:relative;z-index:1">{{ s.cta }} →</a>'
)


def wire_work_links(html: str) -> str:
    """Point the Selected Work grid and the hero panels at /work/<slug>/."""
    if "{{ w.href }}" in html and "{{ s.href }}" in html:
        return html

    # --- Selected Work grid -------------------------------------------------
    if "{{ w.href }}" not in html:
        if _WORK_ALL not in html:
            raise PatchError("no dead 'view all' label in the Selected Work header")
        html = html.replace(_WORK_ALL, _WORK_ALL_LINK, 1)

        if _WORK_CARD_OPEN not in html:
            raise PatchError("no dead project card wrapper in the Selected Work grid")
        start = html.index(_WORK_CARD_OPEN)
        html = html.replace(_WORK_CARD_OPEN, _WORK_CARD_LINK, 1)
        # close the same element: its </div> is the one right before </sc-for>
        end = html.index("</sc-for>", start)
        tail = html.rindex("</div>", start, end)
        html = html[:tail] + "</a>" + html[tail + len("</div>"):]

        m = _WORKS_MAP.search(html)
        if not m:
            raise PatchError("no 'const works = [...].map(' to add hrefs to")
        slugs = ", ".join('"%s"' % s for s in WORK_SLUGS)
        html = (
            html[: m.start()]
            + "const workSlugs = [%s];\n    " % slugs
            + m.group(1)
            + "\n      href: `/work/${workSlugs[i]}/`,"
            + html[m.end():]
        )

    # --- hero showcase panels ----------------------------------------------
    if "{{ s.href }}" not in html:
        if _PANEL_DESC not in html:
            raise PatchError("no hero panel description to anchor the case-study link to")
        html = html.replace(_PANEL_DESC, _PANEL_DESC + _PANEL_LINK, 1)

        anchor = '...s, active, num: String(i + 1).padStart(2, "0"),'
        if anchor not in html:
            raise PatchError("no flagSlides map to add the case-study href to")
        slugs = ", ".join('"%s"' % s for s in PANEL_SLUGS)
        html = html.replace(
            anchor,
            anchor
            + ' href: `/work/${[%s][i]}/`, cta: t.featured.cta,' % slugs,
            1,
        )
    return html


# ---------------------------------------------------------------------------
# Brand mark — the export draws the logo as a generic 8-point coral polygon
# (clip-path) in three places: the header wordmark, the auth modal and the
# footer. The real GeorgeAI mark is a raster asset (seo/logo-mark.png, copied
# to /logo-mark.png by deploy.sh), so the placeholders are swapped here rather
# than in site/, which every re-export overwrites.
#
# Only the 14px instances are the logo. The same polygon is used deliberately
# as a 7px bullet (WhatsApp line) and as an 18px success glyph inside the
# booking/configurator confirmation badges — those are left alone.
# ---------------------------------------------------------------------------
_MARK_DIV = re.compile(
    r'<div style="width:14px;height:14px;background:#cc785c;'
    r'clip-path:polygon\(50% 0,61% 39%,100% 50%,61% 61%,50% 100%,39% 61%,'
    r'0 50%,39% 39%\)"></div>'
)
_MARK_STYLE = 'style="display:block;width:22px;height:22px;flex:none"'
# The footer and the auth modal are dark in BOTH themes, so they always take
# the neon mark. The header follows the page theme, so it takes the same
# two-tier treatment as the accent itself: neon on the dark canvas, the
# darker companion on cream, where neon washes out (2.91:1).
_MARK_IMG_NEON = f'<img src="/logo-mark.png" alt="" width="22" height="22" {_MARK_STYLE}>'
_MARK_IMG_THEMED = f'<img src="{{{{ markSrc }}}}" alt="" width="22" height="22" {_MARK_STYLE}>'

_CTX_ANCHOR = "rootStyle, langs, works,"
_MARK_SRC = ' markSrc: dark ? "/logo-mark.png" : "/logo-mark-ink.png",'


def _ensure_mark_src(html: str) -> str:
    if "markSrc:" in html:
        return html
    if _CTX_ANCHOR not in html:
        raise PatchError("no render context to expose markSrc on")
    return html.replace(_CTX_ANCHOR, _CTX_ANCHOR + _MARK_SRC, 1)


def brand_mark(html: str) -> str:
    if _MARK_IMG_THEMED in html:
        return html
    # upgrade an earlier, uniformly-neon application
    if _MARK_IMG_NEON in html:
        return _ensure_mark_src(html.replace(_MARK_IMG_NEON, _MARK_IMG_THEMED, 1))

    n = len(_MARK_DIV.findall(html))
    if n != 3:
        raise PatchError(
            f"expected 3 brand-mark placeholders (header, auth modal, footer), "
            f"found {n} — the export changed shape"
        )
    html = _MARK_DIV.sub(_MARK_IMG_THEMED, html, count=1)   # header: theme-aware
    html = _MARK_DIV.sub(_MARK_IMG_NEON, html)              # modal + footer: always dark
    return _ensure_mark_src(html)


# ---------------------------------------------------------------------------
# Impressum — legal-data.js shipped unfilled placeholders in all five
# languages, publicly, linked from the footer of every page:
# "[Straße und Hausnummer]", "[PLZ] Hanstedt". The Impressum is the first page
# a German professional checks to decide whether a business is real, and it is
# also a § 5 TMG obligation. Values live in seo/impressum.json so a re-export
# cannot revert them.
#
# The VAT section is deliberately REMOVED when no USt-IdNr. exists rather than
# left as a placeholder. § 5 Abs. 1 Nr. 6 TMG requires it only "sofern
# vorhanden", so omitting the line is correct and complete when there is none.
# A Steuernummer is NOT a substitute: different identifier, not required by
# § 5 TMG, and publishing one is widely advised against.
# ---------------------------------------------------------------------------
_ADDRESS_SLOTS = (
    ("[Street and house number]", "[ZIP] Hanstedt"),
    ("[Straße und Hausnummer]", "[PLZ] Hanstedt"),
    ("[Rue et numéro]", "[Code postal] Hanstedt"),
    ("[Strada și numărul]", "[Cod poștal] Hanstedt"),
    ("[الشارع والرقم]", "[الرمز البريدي] هانشتيت"),
)
# whole { h: ..., p: ... } entries for the VAT section, one per language
_VAT_ENTRY = re.compile(
    r"\n\s*\{ h: \"[^\"]*\", p: \"[^\"]*\[(?:VAT ID, if applicable|USt-IdNr\., falls vorhanden|"
    r"N° de TVA, le cas échéant|Cod TVA, dacă există|الرقم، إن وُجد)\][^\"]*\" \},"
)
_VAT_LABELS = {
    "en": "VAT identification number pursuant to § 27a German VAT Act: %s",
    "de": "Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG: %s",
    "fr": "Numéro d'identification TVA : %s",
    "ro": "Număr de identificare TVA: %s",
    "ar": "رقم تعريف ضريبة القيمة المضافة: %s",
}


def fix_impressum(js: str, data: dict) -> str:
    street = data.get("street")
    postal = data.get("postal_code")
    if not street or not postal:
        raise PatchError("seo/impressum.json needs both 'street' and 'postal_code'")

    for street_slot, zip_slot in _ADDRESS_SLOTS:
        js = js.replace(street_slot, street)
        js = js.replace(zip_slot, "%s %s" % (postal, zip_slot.split("] ", 1)[1]))

    vat_id = data.get("vat_id")
    if vat_id:
        if not re.fullmatch(r"DE\d{9}", vat_id):
            raise PatchError(
                "vat_id %r is not a German USt-IdNr. (DE followed by 9 digits). "
                "A Steuernummer is a different identifier and must not go here." % vat_id
            )
        for lang, template in _VAT_LABELS.items():
            js = js.replace(template % ("[%s]" % {
                "en": "VAT ID, if applicable", "de": "USt-IdNr., falls vorhanden",
                "fr": "N° de TVA, le cas échéant", "ro": "Cod TVA, dacă există",
                "ar": "الرقم، إن وُجد"}[lang]), template % vat_id)
    else:
        js, n = _VAT_ENTRY.subn("", js)
        if n == 0 and "falls vorhanden" in js:
            raise PatchError("could not remove the empty VAT sections from the Impressum")

    # only the placeholders this function owns — legal prose legitimately
    # contains other bracketed text
    known = [slot for pair in _ADDRESS_SLOTS for slot in pair] + [
        "[VAT ID, if applicable]", "[USt-IdNr., falls vorhanden]",
        "[N° de TVA, le cas échéant]", "[Cod TVA, dacă există]", "[الرقم، إن وُجد]",
    ]
    leftover = [k for k in known if k in js]
    if leftover:
        raise PatchError("unfilled Impressum placeholders remain: " + ", ".join(leftover[:5]))
    return js


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        sys.stderr.write(__doc__)
        return 2
    site, seo, pages = Path(argv[1]), Path(argv[2]), argv[3:]

    hero_p, testi_p = seo / "hero.json", seo / "testimonials.json"
    heroes = load(hero_p) if hero_p.exists() else {}
    imp_p = seo / "impressum.json"
    impressum = load(imp_p) if imp_p.exists() else None
    contact_p = seo / "contact.json"
    contact = load(contact_p) if contact_p.exists() else None
    testis = load(testi_p) if testi_p.exists() else None

    writes: list[tuple[Path, str]] = []
    try:
        for name in pages:
            page = site / name
            if not page.exists():
                continue
            html = page.read_text(encoding="utf-8")
            if heroes:
                html = patch_hero(html, heroes)
                html = render_hero_markup(html)
            if testis is not None:
                html = wire_testi_visibility(html)
            # structural repairs — independent of the JSON sources above
            html = strip_social_stubs(html)
            html = strip_dead_case_study_cta(html)
            html = wire_cta_band(html)
            html = fix_lying_forms(html)
            html = strip_dead_hero_video(html)
            html = fix_stale_copy(html)
            html = strip_auth_pill(html)
            html = brand_mark(html)
            html = wire_work_links(html)
            if contact is not None:
                html = contact_page.patch_contact_page(html, contact)
            html = localize_third_party_assets(html, seo / "vendor" / "icons")
            html = localize_fonts(html, seo / "vendor" / "fonts.css", seo / "vendor" / "fonts")
            writes.append((page, html))

        legal = site / "legal-data.js"
        if impressum is not None and legal.exists():
            writes.append((legal, fix_impressum(
                legal.read_text(encoding="utf-8"), impressum)))

        support = site / "support.js"
        if support.exists():
            support_js = localize_react(
                support.read_text(encoding="utf-8"), seo / "vendor" / "js")
            writes.append((support, strip_babel_loader(support_js)))

        data = site / "services-data.js"
        if testis is not None and data.exists():
            writes.append((data, patch_testimonials(data.read_text(encoding="utf-8"), testis)))
    except (PatchError, contact_page.PatchError) as exc:
        sys.stderr.write(f"content layer: {exc}\n")
        return 1

    for path, text in writes:
        path.write_text(text, encoding="utf-8")

    vendor_js = seo / "vendor" / "js"
    if vendor_js.is_dir():
        jdest = site / "assets" / "js"
        jdest.mkdir(parents=True, exist_ok=True)
        for lib in sorted(vendor_js.glob("*.js")):
            shutil.copy2(lib, jdest / lib.name)

    fonts_css = seo / "vendor" / "fonts.css"
    if fonts_css.is_file():
        (site / "assets").mkdir(parents=True, exist_ok=True)
        shutil.copy2(fonts_css, site / "assets" / "fonts.css")
        fdest = site / "assets" / "fonts"
        fdest.mkdir(parents=True, exist_ok=True)
        for face in sorted((seo / "vendor" / "fonts").glob("*.woff2")):
            shutil.copy2(face, fdest / face.name)

    vendor = seo / "vendor" / "icons"
    if vendor.is_dir():
        dest = site / "assets" / "icons"
        dest.mkdir(parents=True, exist_ok=True)
        for icon in vendor.iterdir():
            if icon.is_file():
                shutil.copy2(icon, dest / icon.name)

    n = sum(1 for lang in testis or {} if testis[lang]) if testis else 0
    sys.stderr.write(
        "content layer: hero in %d languages, testimonials in %d\n" % (len(heroes), n)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
