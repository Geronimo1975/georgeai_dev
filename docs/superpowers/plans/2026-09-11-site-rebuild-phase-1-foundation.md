# Site Rebuild, Phase 1: Foundation, Home and Contact — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A repo-owned static generator (`build.py`) that renders the German and English home and contact pages from JSON content and Jinja2 templates into `site/`, with the design tokens, header/footer, theme/menu/hero/booking JavaScript, sitemap/robots/llms output and an automated test suite. Phases 2 (remaining page types, German drafts) and 3 (nginx 301s, CSP, `next.georgeai.dev`, cutover) are separate plans.

**Architecture:** `build.py` loads `content/site.json` plus one JSON file per page per language, computes a page inventory with translated section slugs, renders each page with Jinja2 (`autoescape` on) into `site/<path>/index.html`, copies `assets/`, and writes `sitemap.xml`, `robots.txt`, `llms.txt`. Templates extend `templates/base.html`; visual rules live only in `assets/site.css` (no inline styles); behaviour lives only in `assets/site.js` (ES module, no dependencies).

**Tech Stack:** Python 3.10+ (the VPS deploy already requires `python3`), Jinja2 3.x, pytest, Playwright 1.63 (already installed globally with Chromium; tests use it through `npx`-free `node` with the global module linked), vanilla CSS and JavaScript.

**Spec:** `docs/superpowers/specs/2026-09-11-site-rebuild-design.md` (read it first; every task below argues from it).

## Global Constraints

- Languages: exactly `de` (root, `/`) and `en` (`/en/`). No FR/RO/AR, no RTL.
- German section slugs: `leistungen`, `projekte`, `blog`, `preise`, `kontakt`, `ueber-mich`, `konfigurator`, `impressum`, `datenschutz`, `agb`, `cookies`. English: `services`, `work`, `blog`, `pricing`, `contact`, `about`, `configurator`, `legal/imprint`, `legal/privacy`, `legal/terms`, `legal/cookies`.
- Every page: `<html lang>`, one `<h1>`, `hreflang` `de`, `en` and `x-default` (x-default = the German URL), canonical `https://georgeai.dev<path>`.
- No `style=""` attributes, no `onclick=` attributes, no external font or script hosts, no em dash (U+2014) in rendered pages. Tests enforce all four.
- Colour tokens are the exact values from `DESIGN.md` (repeated in Task 4). Display type is Newsreader weight 400 with negative tracking; body Inter; JetBrains Mono only for uppercase eyebrows/metadata.
- Copy claims allowed: 8+ years, 40+ projects, five languages spoken, pilot in about two weeks, reply usually within two days, free 30-minute call. Nothing else.
- `site/` and `frontend/template/` stay gitignored build outputs. Never hand-edit them.
- Commit after every task with the attribution trailer `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.
- Work only inside this worktree (`.claude/worktrees/site-rebuild`, branch `worktree-site-rebuild`). Do not touch `seo/`, `deploy.sh`, `brand/` in this phase (Phase 3 retires them).

---

## File structure for this phase

| Path | Responsibility |
|---|---|
| `build.py` | CLI and library: load content, inventory pages, render, copy assets, write sitemap/robots/llms, print report |
| `requirements-site.txt` | `jinja2`, `pytest` |
| `content/site.json` | brand, contact data, per-language nav/footer/ui strings, analytics id (empty) |
| `content/{de,en}/home.json` | home page content |
| `content/{de,en}/contact.json` | contact page content (ported from the 2026-09-11 contact rebuild) |
| `templates/base.html` | document shell, head (meta, hreflang, canonical, fonts, JSON-LD block), skip link, header, footer, cookie banner, auth modal, scripts |
| `templates/partials/header.html`, `footer.html` | navigation, language switch, theme toggle, footer columns |
| `templates/pages/home.html` | hero, how-it-works, selected work, services, FAQ, CTA band |
| `templates/pages/contact.html` | the contact page |
| `assets/site.css` | tokens, base, components, responsive |
| `assets/site.js` | `theme`, `menu`, `hero`, `booking`, `cookie` modules |
| `assets/fonts/`, `assets/fonts.css`, `assets/icons/`, `assets/img/` | moved from `seo/vendor` and `Media/` (copies; originals untouched until Phase 3) |
| `tests/test_build.py` | build determinism, validation errors, inventory, hreflang, forbidden patterns |
| `tests/browser/check_pages.mjs` | Playwright: overflow, console, links, h1, focus, axe, flows |
| `tests/test_browser.py` | pytest wrapper that builds, serves `site/` and runs `check_pages.mjs` |

---

### Task 1: Generator skeleton with content loading and page inventory

**Files:**
- Create: `build.py`
- Create: `requirements-site.txt`
- Create: `content/site.json`
- Create: `content/de/home.json`, `content/en/home.json` (minimal, extended in Task 5)
- Create: `tests/test_build.py`
- Create: `tests/__init__.py` (empty)

**Interfaces:**
- Produces: `build.LANGS = ("de", "en")`; `build.SECTIONS: dict[str, dict[str, str]]`; `build.Page` dataclass with fields `lang: str`, `key: str`, `slug: str | None`, `template: str`, `path: str`, `content: dict`, `pair: str | None`, `draft: bool`; `build.load_site(root: Path) -> dict`; `build.load_lang(root: Path, lang: str) -> dict[str, dict]`; `build.page_path(lang: str, key: str, slug: str | None = None) -> str`; `build.inventory(site: dict, langs: dict[str, dict]) -> list[Page]`; `build.ContentError(Exception)`.

- [ ] **Step 1: Install dependencies**

```bash
printf 'jinja2>=3.1\npytest>=8\n' > requirements-site.txt
python3 -m pip install -r requirements-site.txt
python3 -c "import jinja2, pytest; print('ok')"
```
Expected: `ok`

- [ ] **Step 2: Write the failing tests**

`tests/__init__.py` is empty. `tests/test_build.py`:

```python
import json
from pathlib import Path

import pytest

import build

ROOT = Path(__file__).resolve().parents[1]


def test_page_path_translates_sections():
    assert build.page_path("de", "home") == "/"
    assert build.page_path("en", "home") == "/en/"
    assert build.page_path("de", "contact") == "/kontakt/"
    assert build.page_path("en", "contact") == "/en/contact/"
    assert build.page_path("de", "service", "automation") == "/leistungen/automation/"
    assert build.page_path("en", "service", "automation") == "/en/services/automation/"


def test_inventory_pairs_languages():
    site = build.load_site(ROOT)
    langs = {lang: build.load_lang(ROOT, lang) for lang in build.LANGS}
    pages = build.inventory(site, langs)
    by = {(p.lang, p.key): p for p in pages}
    assert by[("de", "home")].path == "/"
    assert by[("de", "home")].pair == "/en/"
    assert by[("en", "home")].pair == "/"


def test_missing_required_key_names_file_and_key(tmp_path):
    (tmp_path / "content" / "de").mkdir(parents=True)
    (tmp_path / "content" / "en").mkdir(parents=True)
    (tmp_path / "content" / "site.json").write_text(json.dumps({"brand": "x"}), encoding="utf-8")
    (tmp_path / "content" / "de" / "home.json").write_text(json.dumps({"meta": {"title": "t"}}), encoding="utf-8")
    with pytest.raises(build.ContentError) as exc:
        build.load_lang(tmp_path, "de")
    assert "content/de/home.json" in str(exc.value)
    assert "meta.description" in str(exc.value)
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python3 -m pytest tests/test_build.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build'`

- [ ] **Step 4: Write `build.py` (loading and inventory only)**

```python
#!/usr/bin/env python3
"""Build georgeai.dev: content/ + templates/ -> site/.

Usage: python3 build.py [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LANGS = ("de", "en")
DOMAIN = "https://georgeai.dev"

# section segment per language; None = the page has no own segment (home)
SECTIONS = {
    "de": {"home": "", "services": "leistungen", "service": "leistungen", "work": "projekte", "project": "projekte",
           "blog": "blog", "post": "blog", "pricing": "preise", "contact": "kontakt", "about": "ueber-mich",
           "configurator": "konfigurator", "imprint": "impressum", "privacy": "datenschutz", "terms": "agb",
           "cookies": "cookies"},
    "en": {"home": "", "services": "services", "service": "services", "work": "work", "project": "work",
           "blog": "blog", "post": "blog", "pricing": "pricing", "contact": "contact", "about": "about",
           "configurator": "configurator", "imprint": "legal/imprint", "privacy": "legal/privacy",
           "terms": "legal/terms", "cookies": "legal/cookies"},
}
PREFIX = {"de": "/", "en": "/en/"}

# required keys per page file, dotted paths
REQUIRED = {
    "home": ["meta.title", "meta.description", "hero.eyebrow", "hero.title", "hero.sub", "hero.cta1", "hero.cta2"],
    "contact": ["meta.title", "meta.description", "eyebrow", "title", "lead"],
}
TEMPLATES = {"home": "pages/home.html", "contact": "pages/contact.html"}


class ContentError(Exception):
    pass


@dataclass
class Page:
    lang: str
    key: str
    template: str
    path: str
    content: dict
    slug: str | None = None
    pair: str | None = None
    draft: bool = False
    site: dict = field(default_factory=dict)


def _get(d: dict, dotted: str):
    cur = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContentError(f"{path.relative_to(path.parents[2])}: invalid JSON ({exc})") from exc


def load_site(root: Path) -> dict:
    return _read_json(root / "content" / "site.json")


def load_lang(root: Path, lang: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for key, required in REQUIRED.items():
        path = root / "content" / lang / f"{key}.json"
        if not path.exists():
            continue
        data = _read_json(path)
        missing = [k for k in required if _get(data, k) in (None, "")]
        if missing:
            rel = f"content/{lang}/{key}.json"
            raise ContentError(f"{rel}: missing {', '.join(missing)}")
        out[key] = data
    return out


def page_path(lang: str, key: str, slug: str | None = None) -> str:
    section = SECTIONS[lang][key]
    path = PREFIX[lang]
    if section:
        path += section + "/"
    if slug:
        path += slug + "/"
    return path


def inventory(site: dict, langs: dict[str, dict]) -> list[Page]:
    pages: list[Page] = []
    for lang in LANGS:
        for key, content in langs.get(lang, {}).items():
            pages.append(Page(lang=lang, key=key, template=TEMPLATES[key], path=page_path(lang, key),
                              content=content, draft=content.get("_status") == "draft", site=site))
    index = {(p.lang, p.key, p.slug): p.path for p in pages}
    for p in pages:
        other = "en" if p.lang == "de" else "de"
        p.pair = index.get((other, p.key, p.slug))
    return pages


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "site"))
    args = ap.parse_args(argv)
    try:
        site = load_site(ROOT)
        langs = {lang: load_lang(ROOT, lang) for lang in LANGS}
        pages = inventory(site, langs)
    except ContentError as exc:
        sys.stderr.write(f"build: {exc}\n")
        return 1
    for lang in LANGS:
        n = sum(1 for p in pages if p.lang == lang)
        d = sum(1 for p in pages if p.lang == lang and p.draft)
        sys.stderr.write(f"build: {lang}: {n} pages, {d} draft\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 5: Write the minimal content files**

`content/site.json`:

```json
{
  "brand": "GeorgeAI",
  "domain": "https://georgeai.dev",
  "person": "George Cucuiet",
  "phone": "+49 160 4155546",
  "phoneHref": "tel:+491604155546",
  "email": "contact@georgeai.dev",
  "whatsapp": "https://wa.me/491604155546",
  "location": {"de": "Hanstedt, Deutschland", "en": "Hanstedt, Germany"},
  "socials": [
    {"name": "GitHub", "href": "https://github.com/Geronimo1975", "icon": "github-8e8b82.svg"},
    {"name": "LinkedIn", "href": "https://www.linkedin.com/in/george-cucuiet/", "icon": "linkedin.svg"},
    {"name": "WhatsApp", "href": "https://wa.me/491604155546", "icon": "whatsapp-8e8b82.svg"}
  ],
  "analyticsId": "",
  "ui": {
    "de": {
      "nav": {"services": "Leistungen", "work": "Projekte", "about": "Über mich", "blog": "Blog", "contact": "Kontakt", "configurator": "Konfigurator", "pricing": "Preise"},
      "cta": "Kontakt aufnehmen",
      "menu": "Menü", "close": "Schließen", "skip": "Zum Inhalt springen",
      "theme": {"light": "Helles Design", "dark": "Dunkles Design"},
      "lang": {"label": "Sprache", "de": "Deutsch", "en": "English"},
      "footer": {"tag": "KI-Automatisierung, Python-Backend und Infrastruktur. Hanstedt, Deutschland, remote tätig.", "services": "Leistungen", "site": "Seite", "elsewhere": "Anderswo", "rights": "Alle Rechte vorbehalten."},
      "legal": {"imprint": "Impressum", "privacy": "Datenschutz", "terms": "AGB", "cookies": "Cookie-Richtlinie"},
      "cookie": {"title": "Ihre Privatsphäre", "text": "Ich nutze essenzielle Cookies für den Betrieb und optionale Analyse-Cookies zur Verbesserung. Sie entscheiden.", "essential": "Nur essenzielle", "all": "Alle akzeptieren", "policy": "Cookie-Richtlinie"}
    },
    "en": {
      "nav": {"services": "Services", "work": "Work", "about": "About", "blog": "Blog", "contact": "Contact", "configurator": "Configurator", "pricing": "Pricing"},
      "cta": "Get in touch",
      "menu": "Menu", "close": "Close", "skip": "Skip to content",
      "theme": {"light": "Light theme", "dark": "Dark theme"},
      "lang": {"label": "Language", "de": "Deutsch", "en": "English"},
      "footer": {"tag": "AI automation, Python backend and infrastructure. Hanstedt, Germany, working remotely.", "services": "Services", "site": "Site", "elsewhere": "Elsewhere", "rights": "All rights reserved."},
      "legal": {"imprint": "Imprint", "privacy": "Privacy", "terms": "Terms", "cookies": "Cookie policy"},
      "cookie": {"title": "Your privacy", "text": "I use essential cookies to run this site and optional analytics cookies to improve it. You choose.", "essential": "Essential only", "all": "Accept all", "policy": "Cookie policy"}
    }
  }
}
```

Check the LinkedIn URL against the current footer of `https://georgeai.dev` before committing; if it differs, use the live one. If no `linkedin.svg` exists in `seo/vendor/icons`, Task 4 adds one.

`content/de/home.json` (minimal for now):

```json
{
  "meta": {"title": "GeorgeAI | KI-Telefonagent und Website-Assistent für Handwerk, Praxen und Dienstleister", "description": "Der Anruf, den Sie samstags verpassen, steht montags in Ihrem Kalender. KI-Telefonagent und Website-Assistent für Handwerk, Praxen und Dienstleister in Deutschland. Pilot in rund zwei Wochen."},
  "hero": {"eyebrow": "Für Handwerk, Praxen und Dienstleister im Mittelstand", "title": "Der Anruf, den Sie samstags verpassen, steht montags in Ihrem Kalender.", "sub": "Ein KI-Assistent geht ans Telefon und antwortet auf Ihrer Website, Tag und Nacht, in der Sprache des Kunden: Anliegen notiert, Termin gebucht. 8+ Jahre Erfahrung, 40+ Projekte, fünf Sprachen. Nach rund zwei Wochen läuft Ihr Pilotprojekt.", "cta1": "Leistungen ansehen", "cta2": "Pilotprojekt anfragen"}
}
```

`content/en/home.json`:

```json
{
  "meta": {"title": "GeorgeAI | AI voice agent and website assistant for trades, clinics and service firms", "description": "The enquiry you miss on a Saturday still ends up in your calendar. AI voice agent and website assistant for owner-run trades, clinics and service firms in Germany. Pilot live in about two weeks."},
  "hero": {"eyebrow": "For owner-run trades, clinics and service firms in Germany", "title": "The enquiry you miss on a Saturday still ends up in your calendar.", "sub": "An AI voice agent picks up the phone and an assistant answers on your website, day or night, in the caller's own language: every enquiry qualified and booked in. 8+ years, 40+ projects delivered, five languages. Your pilot goes live in about two weeks.", "cta1": "See the services", "cta2": "Ask about a pilot"}
}
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python3 -m pytest tests/test_build.py -v`
Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
git add build.py requirements-site.txt content tests/__init__.py tests/test_build.py
git commit -m "Add the static generator skeleton: content loading, validation and page inventory

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Rendering, asset copy, sitemap/robots/llms and the build report

**Files:**
- Modify: `build.py`
- Create: `templates/base.html` (minimal shell; Task 4 fills header/footer)
- Create: `templates/pages/home.html` (minimal; Task 5 fills)
- Modify: `tests/test_build.py`

**Interfaces:**
- Consumes: `Page`, `inventory`, `load_site`, `load_lang` from Task 1.
- Produces: `build.build(out: Path) -> BuildReport` with `BuildReport.pages: dict[str, int]`, `BuildReport.drafts: dict[str, int]`; `build.render_page(env, page, pages) -> str`; `build.write_sitemap(pages, out)`; `build.write_robots(out)`; `build.write_llms(pages, out)`; template context variables `page`, `site`, `ui` (the `site["ui"][lang]` dict), `c` (page content), `lang`, `path`, `canonical`, `pair`, `alternates` (list of `{"hreflang": str, "href": str}`), `nav` (list of `{"label": str, "href": str, "key": str}`), `url(key, slug=None)` callable.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_build.py`:

```python
import re
import subprocess
import sys


def _build(tmp_path):
    out = tmp_path / "site"
    report = build.build(out)
    return out, report


def test_build_writes_both_home_pages(tmp_path):
    out, report = _build(tmp_path)
    assert (out / "index.html").exists()
    assert (out / "en" / "index.html").exists()
    assert report.pages["de"] >= 1 and report.pages["en"] >= 1


def test_build_is_deterministic(tmp_path):
    a, _ = _build(tmp_path / "a")
    b, _ = _build(tmp_path / "b")
    for f in sorted(a.rglob("*")):
        if f.is_file():
            assert f.read_bytes() == (b / f.relative_to(a)).read_bytes(), f


def test_head_has_lang_canonical_and_hreflang(tmp_path):
    out, _ = _build(tmp_path)
    de = (out / "index.html").read_text(encoding="utf-8")
    en = (out / "en" / "index.html").read_text(encoding="utf-8")
    assert '<html lang="de"' in de and '<html lang="en"' in en
    assert '<link rel="canonical" href="https://georgeai.dev/">' in de
    assert '<link rel="alternate" hreflang="en" href="https://georgeai.dev/en/">' in de
    assert '<link rel="alternate" hreflang="de" href="https://georgeai.dev/">' in en
    assert '<link rel="alternate" hreflang="x-default" href="https://georgeai.dev/">' in en


def test_sitemap_robots_llms(tmp_path):
    out, _ = _build(tmp_path)
    sm = (out / "sitemap.xml").read_text(encoding="utf-8")
    assert "<loc>https://georgeai.dev/</loc>" in sm and "<loc>https://georgeai.dev/en/</loc>" in sm
    assert 'hreflang="en" href="https://georgeai.dev/en/"' in sm
    assert "Sitemap: https://georgeai.dev/sitemap.xml" in (out / "robots.txt").read_text(encoding="utf-8")
    assert "# GeorgeAI" in (out / "llms.txt").read_text(encoding="utf-8")


def test_rendered_pages_have_no_forbidden_patterns(tmp_path):
    out, _ = _build(tmp_path)
    for f in out.rglob("*.html"):
        html = f.read_text(encoding="utf-8")
        assert " style=" not in html, f
        assert "onclick=" not in html.lower(), f
        assert "—" not in html, f
        assert "fonts.googleapis.com" not in html and "cdn." not in html, f
        assert len(re.findall(r"<h1[\s>]", html)) == 1, f


def test_cli_exit_code_on_broken_content(tmp_path, monkeypatch):
    bad = tmp_path / "root"
    (bad / "content" / "de").mkdir(parents=True)
    (bad / "content" / "en").mkdir(parents=True)
    (bad / "content" / "site.json").write_text("{}", encoding="utf-8")
    (bad / "content" / "de" / "home.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(build, "ROOT", bad)
    assert build.main(["--out", str(tmp_path / "out")]) == 1
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest tests/test_build.py -v`
Expected: the six new tests FAIL with `AttributeError: module 'build' has no attribute 'build'`

- [ ] **Step 3: Add rendering and outputs to `build.py`**

Add after the imports:

```python
import shutil
from datetime import date

from jinja2 import Environment, FileSystemLoader, select_autoescape
```

Add after `Page`:

```python
@dataclass
class BuildReport:
    pages: dict[str, int]
    drafts: dict[str, int]


def _env(root: Path) -> Environment:
    env = Environment(loader=FileSystemLoader(str(root / "templates")),
                      autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)
    return env


def _nav(site: dict, lang: str) -> list[dict]:
    labels = site["ui"][lang]["nav"]
    order = ("services", "work", "about", "blog", "contact")
    return [{"key": k, "label": labels[k], "href": page_path(lang, k)} for k in order]


def render_page(env: Environment, page: Page, pages: list[Page]) -> str:
    site = page.site
    alternates = [{"hreflang": page.lang, "href": DOMAIN + page.path}]
    if page.pair:
        other = "en" if page.lang == "de" else "de"
        alternates.append({"hreflang": other, "href": DOMAIN + page.pair})
    de_url = page.path if page.lang == "de" else page.pair
    alternates.append({"hreflang": "x-default", "href": DOMAIN + (de_url or page.path)})
    tpl = env.get_template(page.template)
    return tpl.render(
        page=page, site=site, ui=site["ui"][page.lang], c=page.content, lang=page.lang,
        path=page.path, canonical=DOMAIN + page.path, pair=page.pair, alternates=alternates,
        nav=_nav(site, page.lang), url=lambda key, slug=None: page_path(page.lang, key, slug),
        other_lang=("en" if page.lang == "de" else "de"),
    )


def write_sitemap(pages: list[Page], out: Path) -> None:
    today = date.today().isoformat()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for p in sorted(pages, key=lambda p: p.path):
        if p.draft:
            continue
        lines.append("  <url>")
        lines.append(f"    <loc>{DOMAIN}{p.path}</loc>")
        lines.append(f"    <lastmod>{today}</lastmod>")
        lines.append(f'    <xhtml:link rel="alternate" hreflang="{p.lang}" href="{DOMAIN}{p.path}"/>')
        if p.pair:
            other = "en" if p.lang == "de" else "de"
            lines.append(f'    <xhtml:link rel="alternate" hreflang="{other}" href="{DOMAIN}{p.pair}"/>')
        lines.append("  </url>")
    lines.append("</urlset>")
    (out / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_robots(out: Path) -> None:
    (out / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: https://georgeai.dev/sitemap.xml\n", encoding="utf-8")


def write_llms(pages: list[Page], out: Path) -> None:
    lines = ["# GeorgeAI", "",
             "> George Cucuiet, AI automation engineer in Hanstedt, Germany. AI voice agents and website "
             "assistants for owner-run trades, clinics and service firms. 8+ years, 40+ projects, five languages, "
             "pilot live in about two weeks.", ""]
    for lang in LANGS:
        lines.append(f"## Pages ({lang})")
        for p in sorted((p for p in pages if p.lang == lang and not p.draft), key=lambda p: p.path):
            title = _get(p.content, "meta.title") or p.key
            lines.append(f"- [{title}]({DOMAIN}{p.path})")
        lines.append("")
    (out / "llms.txt").write_text("\n".join(lines), encoding="utf-8")


def copy_assets(root: Path, out: Path) -> None:
    src = root / "assets"
    dst = out / "assets"
    if dst.exists():
        shutil.rmtree(dst)
    if src.exists():
        shutil.copytree(src, dst)
    auth = root / "backend" / "assets" / "auth.js"
    if auth.exists():
        shutil.copy2(auth, out / "auth.js")
    for name in ("favicon.svg", "favicon.ico", "favicon-32.png", "apple-touch-icon.png", "logo-mark.png", "logo-512.png"):
        f = root / "assets" / "img" / name
        if f.exists():
            shutil.copy2(f, out / name)


def build(out: Path) -> BuildReport:
    site = load_site(ROOT)
    langs = {lang: load_lang(ROOT, lang) for lang in LANGS}
    pages = inventory(site, langs)
    env = _env(ROOT)
    out.mkdir(parents=True, exist_ok=True)
    for p in pages:
        target = out / p.path.strip("/") / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_page(env, p, pages), encoding="utf-8")
    copy_assets(ROOT, out)
    write_sitemap(pages, out)
    write_robots(out)
    write_llms(pages, out)
    return BuildReport(
        pages={lang: sum(1 for p in pages if p.lang == lang) for lang in LANGS},
        drafts={lang: sum(1 for p in pages if p.lang == lang and p.draft) for lang in LANGS},
    )
```

Replace `main` with:

```python
def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "site"))
    args = ap.parse_args(argv)
    try:
        report = build(Path(args.out))
    except ContentError as exc:
        sys.stderr.write(f"build: {exc}\n")
        return 1
    for lang in LANGS:
        sys.stderr.write(f"build: {lang}: {report.pages[lang]} pages, {report.drafts[lang]} draft\n")
    return 0
```

Note: `write_sitemap` uses `date.today()`; the determinism test runs both builds on the same day, which is acceptable. `copy_assets` deletes and recreates `out/assets` so a stale file cannot survive.

- [ ] **Step 4: Write the minimal templates**

`templates/base.html`:

```html
<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ c.meta.title }}</title>
<meta name="description" content="{{ c.meta.description }}">
<link rel="canonical" href="{{ canonical }}">
{% for a in alternates %}
<link rel="alternate" hreflang="{{ a.hreflang }}" href="{{ a.href }}">
{% endfor %}
<link rel="stylesheet" href="/assets/fonts.css">
<link rel="stylesheet" href="/assets/site.css">
{% block head %}{% endblock %}
</head>
<body>
{% block body %}{% endblock %}
</body>
</html>
```

`templates/pages/home.html`:

```html
{% extends "base.html" %}
{% block body %}
<main id="main">
  <h1>{{ c.hero.title }}</h1>
</main>
{% endblock %}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python3 -m pytest tests/test_build.py -v`
Expected: 9 passed

- [ ] **Step 6: Run the CLI once and confirm `site/` is ignored**

```bash
python3 build.py && git status --short
```
Expected: stderr shows `build: de: 1 pages, 0 draft` and `build: en: 1 pages, 0 draft`; `git status` does not list `site/`.

- [ ] **Step 7: Commit**

```bash
git add build.py templates tests/test_build.py
git commit -m "Render pages with Jinja2 and write sitemap, robots and llms.txt

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Design tokens and base stylesheet

**Files:**
- Create: `assets/site.css`
- Create: `assets/fonts.css`, `assets/fonts/*.woff2` (copied from `seo/vendor`), `assets/icons/*` (copied), `assets/img/*` (copied from `Media/` and the favicon set)
- Modify: `tests/test_build.py`

**Interfaces:**
- Produces: CSS custom properties listed below; layout classes `.wrap` (gutter), `.section` (vertical rhythm), `.eyebrow`, `.display`, `.btn`, `.btn--primary`, `.btn--secondary`, `.card`, `.hairline`, `.grid-2`, `.visually-hidden`, `.skip-link`.

- [ ] **Step 1: Copy the vendored assets**

```bash
mkdir -p assets/fonts assets/icons assets/img
cp seo/vendor/fonts/inter-*.woff2 seo/vendor/fonts/jetbrainsmono-*.woff2 seo/vendor/fonts/newsreader-*.woff2 assets/fonts/
cp seo/vendor/icons/* assets/icons/
cp Media/SEO_AI.png Media/clouddienste.jpg Media/concept_smart_home.png Media/medical_ai.png assets/img/
cp "Media/Full stack.png" assets/img/full_stack.png
for f in favicon.svg favicon.ico favicon-32.png apple-touch-icon.png logo-mark.png logo-512.png; do
  [ -f "seo/$f" ] && cp "seo/$f" assets/img/ || echo "missing seo/$f (copy from the main checkout's seo/ if it exists there)"
done
ls assets/fonts | wc -l
```
Expected: 6 font files (Inter 400/500 latin + latin-ext, JetBrains Mono 400 latin + latin-ext, Newsreader 400 latin + latin-ext; if `inter-500-*` files do not exist under those names, check `seo/vendor/fonts.css` for the exact filenames of the weight-500 faces and copy those). If a favicon file is missing here, copy it from `/Users/get-hub/Portofolio/georgeai_dev/seo/` (the main checkout has the untracked raster set) and note it in the commit message.

- [ ] **Step 2: Write `assets/fonts.css`**

Take `seo/vendor/fonts.css`, delete every `@font-face` block whose `font-family` is `Amiri` or `Noto Sans Arabic`, keep the rest verbatim (Inter 400 and 500, JetBrains Mono 400, Newsreader 400, `font-display: swap`, `src: url(/assets/fonts/...)`).

```bash
python3 - <<'EOF'
import re
src = open("seo/vendor/fonts.css", encoding="utf-8").read()
blocks = re.findall(r"@font-face\s*\{[^}]*\}", src)
keep = [b for b in blocks if "Amiri" not in b and "Noto Sans Arabic" not in b]
open("assets/fonts.css", "w", encoding="utf-8").write("\n\n".join(keep) + "\n")
print(len(blocks), "->", len(keep))
EOF
```
Expected: something like `13 -> 6`.

- [ ] **Step 3: Write the failing test**

Append to `tests/test_build.py`:

```python
def test_site_css_has_design_tokens_for_both_themes():
    css = (ROOT / "assets" / "site.css").read_text(encoding="utf-8")
    for token, light, dark in [("--canvas", "#faf9f5", "#181715"), ("--ink", "#141413", "#faf9f5"),
                               ("--accent", "#a9583e", "#cc785c"), ("--accentBtn", "#a9583e", "#a9583e"),
                               ("--card", "#faf9f5", "#201f1c"), ("--footerBg", "#181715", "#0f0e0d")]:
        assert f"{token}: {light}" in css, token
        assert f"{token}: {dark}" in css, token
    assert 'html[data-theme="dark"]' in css
    assert "prefers-color-scheme: dark" in css
    assert "prefers-reduced-motion" in css
```

Run: `python3 -m pytest tests/test_build.py::test_site_css_has_design_tokens_for_both_themes -v`
Expected: FAIL (file not found)

- [ ] **Step 4: Write `assets/site.css`**

```css
/* georgeai.dev — tokens from DESIGN.md, components, responsive rules.
   Light is the default; dark via html[data-theme="dark"], with the OS
   preference as fallback when no choice is stored. */

:root {
  --canvas: #faf9f5; --surface: #f5f0e8; --card: #faf9f5; --cardBorder: #e6dfd8;
  --ink: #141413; --accent: #a9583e; --accentBtn: #a9583e; --body: #3d3d3a; --muted: #6c6a64;
  --hairline: #ebe6df; --navBg: rgba(250,249,245,.85); --pillBg: #f5f0e8;
  --footerBg: #181715; --footerText: #a09d96; --footerHead: #faf9f5; --gridline: rgba(20,20,19,.06);
  --coral: #cc785c; --onAccent: #fff;
  --display: 'Newsreader', Georgia, serif; --sans: 'Inter', system-ui, sans-serif; --mono: 'JetBrains Mono', ui-monospace, monospace;
  --padX: 56px; --sectionY: 88px; --heroY: 84px;
  --r-btn: 8px; --r-card: 16px; --r-pill: 9999px;
  --ease-out: cubic-bezier(.22,1,.36,1);
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  html:not([data-theme="light"]) {
    --canvas: #181715; --surface: #1f1e1b; --card: #201f1c; --cardBorder: #2f2c28;
    --ink: #faf9f5; --accent: #cc785c; --accentBtn: #a9583e; --body: #cfccc4; --muted: #a09d96;
    --hairline: #2a2824; --navBg: rgba(24,23,21,.85); --pillBg: #252320;
    --footerBg: #0f0e0d; --footerText: #8e8b82; --footerHead: #faf9f5; --gridline: rgba(250,249,245,.06);
    color-scheme: dark;
  }
}
html[data-theme="dark"] {
  --canvas: #181715; --surface: #1f1e1b; --card: #201f1c; --cardBorder: #2f2c28;
  --ink: #faf9f5; --accent: #cc785c; --accentBtn: #a9583e; --body: #cfccc4; --muted: #a09d96;
  --hairline: #2a2824; --navBg: rgba(24,23,21,.85); --pillBg: #252320;
  --footerBg: #0f0e0d; --footerText: #8e8b82; --footerHead: #faf9f5; --gridline: rgba(250,249,245,.06);
  color-scheme: dark;
}
@media (max-width: 859px) { :root { --padX: 28px; --sectionY: 56px; --heroY: 48px; } }
@media (max-width: 559px) { :root { --padX: 20px; } }

/* base */
*, *::before, *::after { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; background: var(--canvas); color: var(--body); font: 400 16px/1.6 var(--sans); }
h1, h2, h3, h4 { margin: 0; font-family: var(--display); font-weight: 400; color: var(--ink); text-wrap: balance; }
h1 { font-size: 64px; line-height: 1.04; letter-spacing: -1.5px; }
h2 { font-size: 38px; line-height: 1.12; letter-spacing: -.6px; }
h3 { font-size: 24px; line-height: 1.18; letter-spacing: -.35px; }
@media (max-width: 859px) { h1 { font-size: 50px; } h2 { font-size: 30px; } }
@media (max-width: 559px) { h1 { font-size: 38px; } }
p { margin: 0; }
a { color: var(--accent); }
img { max-width: 100%; height: auto; display: block; }
button { font: inherit; color: inherit; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; border-radius: 6px; }
.visually-hidden { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.skip-link { position: absolute; left: 16px; top: -48px; z-index: 100; background: var(--accentBtn); color: var(--onAccent); padding: 10px 14px; border-radius: var(--r-btn); text-decoration: none; }
.skip-link:focus { top: 16px; }
.wrap { padding-inline: var(--padX); }
.section { padding-block: var(--sectionY); }
.section--band { background: var(--surface); }
.eyebrow { font-family: var(--mono); font-size: 12px; letter-spacing: 2px; text-transform: uppercase; color: var(--accent); }
.eyebrow--muted { color: var(--muted); font-size: 11px; letter-spacing: 1.5px; }
.lead { font-size: 18px; line-height: 1.6; color: var(--body); max-width: 60ch; }
.measure { max-width: 68ch; }
.hairline { border: 0; border-top: 1px solid var(--hairline); margin: 0; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
@media (max-width: 859px) { .grid-2 { grid-template-columns: 1fr; } }

/* buttons */
.btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 15px 26px; border-radius: var(--r-btn); font-size: 15px; font-weight: 500; text-decoration: none; border: 1px solid transparent; cursor: pointer; white-space: nowrap; transition: background-color .15s ease, border-color .15s ease, opacity .15s ease; }
.btn--primary { background: var(--accentBtn); color: var(--onAccent); }
.btn--primary:hover { opacity: .92; }
.btn--secondary { background: var(--card); color: var(--ink); border-color: var(--cardBorder); }
.btn--secondary:hover { border-color: var(--accent); }
.btn--cream { background: #faf9f5; color: #141413; }
.btn--small { padding: 10px 18px; font-size: 14px; }
.btn--block { width: 100%; }

/* cards */
.card { background: var(--card); border: 1px solid var(--cardBorder); border-radius: var(--r-card); padding: 30px; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; scroll-behavior: auto !important; }
}
```

- [ ] **Step 5: Run the tests**

Run: `python3 -m pytest tests/test_build.py -v`
Expected: 10 passed

- [ ] **Step 6: Commit**

```bash
git add assets tests/test_build.py
git commit -m "Add the design tokens, base stylesheet and self-hosted assets

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Document shell: header, footer, cookie banner, auth modal, theme and menu scripts

**Files:**
- Modify: `templates/base.html`
- Create: `templates/partials/header.html`, `templates/partials/footer.html`, `templates/partials/cookie.html`, `templates/partials/auth-modal.html`
- Create: `assets/site.js`
- Modify: `assets/site.css`
- Modify: `tests/test_build.py`

**Interfaces:**
- Consumes: template context from Task 2 (`site`, `ui`, `nav`, `pair`, `other_lang`, `url`), CSS classes from Task 3.
- Produces: `base.html` blocks `head`, `body_class`, `content`, `jsonld`; DOM hooks used by `site.js`: `[data-theme-toggle]`, `[data-menu-toggle]`, `#site-menu`, `[data-cookie]`, `[data-cookie-accept]`, `[data-cookie-essential]`, `#ga-auth-email`, `#ga-auth-password`, `#ga-auth-name`; `localStorage` keys `ga_theme` (`"light"|"dark"`), `ga_cookie` (`"essential"|"all"`).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_build.py`:

```python
def test_shell_has_nav_language_switch_and_landmarks(tmp_path):
    out, _ = _build(tmp_path)
    de = (out / "index.html").read_text(encoding="utf-8")
    en = (out / "en" / "index.html").read_text(encoding="utf-8")
    assert '<a class="skip-link" href="#main">' in de
    assert "<header" in de and "<footer" in de and '<main id="main"' in de
    assert 'href="/kontakt/"' in de and 'href="/en/contact/"' in en
    assert 'hreflang="en" href="/en/"' in de          # language switch to the pair
    assert 'hreflang="de" href="/"' in en
    assert 'data-theme-toggle' in de and 'data-menu-toggle' in de
    assert '<script type="module" src="/assets/site.js"></script>' in de
    assert 'src="/auth.js"' in de and 'id="ga-auth-email"' in de
    assert "data-cookie" not in de  # analyticsId is empty, so no banner
```

Run: `python3 -m pytest tests/test_build.py::test_shell_has_nav_language_switch_and_landmarks -v`
Expected: FAIL

- [ ] **Step 2: Write `templates/base.html`**

```html
<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ c.meta.title }}</title>
<meta name="description" content="{{ c.meta.description }}">
<link rel="canonical" href="{{ canonical }}">
{% for a in alternates %}
<link rel="alternate" hreflang="{{ a.hreflang }}" href="{{ a.href }}">
{% endfor %}
<meta property="og:type" content="website">
<meta property="og:site_name" content="{{ site.brand }}">
<meta property="og:title" content="{{ c.meta.title }}">
<meta property="og:description" content="{{ c.meta.description }}">
<meta property="og:url" content="{{ canonical }}">
<meta property="og:image" content="{{ site.domain }}/logo-512.png">
<meta property="og:locale" content="{{ 'de_DE' if lang == 'de' else 'en_GB' }}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/fonts.css">
<link rel="stylesheet" href="/assets/site.css">
<script src="/assets/theme-boot.js"></script>
<script type="application/ld+json">
{{ jsonld_site | safe }}
</script>
{% block jsonld %}{% endblock %}
{% block head %}{% endblock %}
</head>
<body class="{% block body_class %}{% endblock %}">
<a class="skip-link" href="#main">{{ ui.skip }}</a>
{% include "partials/header.html" %}
<main id="main">
{% block content %}{% endblock %}
</main>
{% include "partials/footer.html" %}
{% if site.analyticsId %}{% include "partials/cookie.html" %}{% endif %}
{% include "partials/auth-modal.html" %}
<script type="module" src="/assets/site.js"></script>
<script src="/auth.js" defer></script>
</body>
</html>
```

`jsonld_site` is added to the render context in Step 6. The theme bootstrap is a separate tiny classic script (`/assets/theme-boot.js`) rather than inline, so the strict CSP of Phase 3 needs no nonce (spec section 11, decided here).

- [ ] **Step 3: Write the partials**

`templates/partials/header.html`:

```html
<header class="hdr">
  <div class="hdr__util wrap">
    <div class="hdr__contact">
      <a href="{{ site.phoneHref }}"><span class="dot" aria-hidden="true"></span>{{ site.phone }}</a>
      <span class="hdr__sep" aria-hidden="true">/</span>
      <a href="mailto:{{ site.email }}">{{ site.email }}</a>
    </div>
    <ul class="hdr__social" aria-label="Social">
      {% for s in site.socials %}
      <li><a href="{{ s.href }}" rel="me noopener" target="_blank" aria-label="{{ s.name }}"><img src="/assets/icons/{{ s.icon }}" alt="" width="18" height="18"></a></li>
      {% endfor %}
    </ul>
    <div class="hdr__tools">
      {% if pair %}
      <a class="pill" hreflang="{{ other_lang }}" href="{{ pair }}" lang="{{ other_lang }}" aria-label="{{ ui.lang.label }}: {{ ui.lang[other_lang] }}">{{ other_lang | upper }}</a>
      {% endif %}
      <button class="icon-btn" type="button" data-theme-toggle aria-label="{{ ui.theme.dark }}" data-label-light="{{ ui.theme.light }}" data-label-dark="{{ ui.theme.dark }}">
        <span class="icon-btn__glyph" aria-hidden="true"></span>
      </button>
    </div>
  </div>
  <div class="hdr__main wrap">
    <button class="icon-btn hdr__burger" type="button" data-menu-toggle aria-controls="site-menu" aria-expanded="false" aria-label="{{ ui.menu }}">
      <span class="burger" aria-hidden="true"></span>
    </button>
    <nav class="hdr__nav" aria-label="Main">
      <ul>
        {% for item in nav %}
        <li><a href="{{ item.href }}"{% if item.href == path %} aria-current="page"{% endif %}>{{ item.label }}</a></li>
        {% endfor %}
      </ul>
    </nav>
    <a class="brand" href="{{ url('home') }}" aria-label="{{ site.brand }}">
      <img src="/logo-mark.png" alt="" width="22" height="22">
      <span class="brand__word">{{ site.brand }}</span>
    </a>
    <div class="hdr__cta">
      <a class="btn btn--primary btn--small" href="{{ url('configurator') }}">{{ ui.nav.configurator }}</a>
      <a class="btn btn--secondary btn--small" href="{{ url('contact') }}">{{ ui.cta }}</a>
    </div>
  </div>
  <div class="hdr__menu wrap" id="site-menu" hidden>
    <ul>
      {% for item in nav %}
      <li><a href="{{ item.href }}">{{ item.label }}</a></li>
      {% endfor %}
    </ul>
    <a class="btn btn--primary btn--block" href="{{ url('configurator') }}">{{ ui.nav.configurator }}</a>
    <a class="btn btn--secondary btn--block" href="{{ url('contact') }}">{{ ui.cta }}</a>
  </div>
</header>
```

`templates/partials/footer.html`:

```html
<footer class="ftr">
  <div class="ftr__grid wrap">
    <div class="ftr__brand">
      <a class="brand brand--light" href="{{ url('home') }}"><img src="/logo-mark.png" alt="" width="22" height="22"><span class="brand__word">{{ site.brand }}</span></a>
      <p class="ftr__tag">{{ ui.footer.tag }}</p>
      <ul class="ftr__social" aria-label="Social">
        {% for s in site.socials %}
        <li><a href="{{ s.href }}" rel="me noopener" target="_blank" aria-label="{{ s.name }}"><img src="/assets/icons/{{ s.icon }}" alt="" width="18" height="18"></a></li>
        {% endfor %}
      </ul>
    </div>
    <nav class="ftr__col" aria-label="{{ ui.footer.site }}">
      <span class="ftr__head">{{ ui.footer.site }}</span>
      <ul>
        {% for item in nav %}<li><a href="{{ item.href }}">{{ item.label }}</a></li>{% endfor %}
        <li><a href="{{ url('configurator') }}">{{ ui.nav.configurator }}</a></li>
        <li><a href="{{ url('pricing') }}">{{ ui.nav.pricing }}</a></li>
      </ul>
    </nav>
    <div class="ftr__col">
      <span class="ftr__head">{{ ui.footer.elsewhere }}</span>
      <ul>
        {% for s in site.socials %}<li><a href="{{ s.href }}" rel="me noopener" target="_blank">{{ s.name }}</a></li>{% endfor %}
        <li><a href="mailto:{{ site.email }}">{{ site.email }}</a></li>
      </ul>
    </div>
  </div>
  <div class="ftr__legal wrap">
    <span>© {{ build_year }} {{ site.brand }} · {{ ui.footer.rights }}</span>
    <ul>
      {% for k in ['imprint', 'privacy', 'terms', 'cookies'] %}<li><a href="{{ url(k) }}">{{ ui.legal[k] }}</a></li>{% endfor %}
    </ul>
  </div>
</footer>
```

`templates/partials/cookie.html`:

```html
<div class="cookie" data-cookie hidden role="region" aria-label="{{ ui.cookie.title }}">
  <p class="cookie__title">{{ ui.cookie.title }}</p>
  <p class="cookie__text">{{ ui.cookie.text }} <a href="{{ url('cookies') }}">{{ ui.cookie.policy }}</a></p>
  <div class="cookie__actions">
    <button class="btn btn--secondary btn--small" type="button" data-cookie-essential>{{ ui.cookie.essential }}</button>
    <button class="btn btn--primary btn--small" type="button" data-cookie-accept>{{ ui.cookie.all }}</button>
  </div>
</div>
```

`templates/partials/auth-modal.html` (kept for `auth.js`; hidden until `auth.js` opens it; fields get stable ids):

```html
<div class="auth" id="ga-auth" hidden role="dialog" aria-modal="true" aria-labelledby="ga-auth-title">
  <div class="auth__card">
    <h2 id="ga-auth-title" class="auth__title">Sign in</h2>
    <form class="auth__form" id="ga-auth-form">
      <label for="ga-auth-name">Name</label>
      <input id="ga-auth-name" name="name" type="text" autocomplete="name">
      <label for="ga-auth-email">Email</label>
      <input id="ga-auth-email" name="email" type="email" autocomplete="email" required>
      <label for="ga-auth-password">Password</label>
      <input id="ga-auth-password" name="password" type="password" autocomplete="current-password" required>
      <button class="btn btn--primary btn--block" type="submit">Continue</button>
    </form>
  </div>
</div>
```

Do not change `backend/assets/auth.js` in this phase; it degrades gracefully. Phase 2 updates it to hook these ids.

- [ ] **Step 4: Write `assets/theme-boot.js` and `assets/site.js`**

`assets/theme-boot.js` (classic script, runs before first paint):

```js
(function () {
  try {
    var t = localStorage.getItem("ga_theme");
    if (t === "light" || t === "dark") document.documentElement.setAttribute("data-theme", t);
  } catch (e) {}
})();
```

`assets/site.js`:

```js
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
const store = {
  get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
};

function theme() {
  const btn = $("[data-theme-toggle]");
  if (!btn) return;
  const current = () => document.documentElement.getAttribute("data-theme")
    || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  const label = () => { btn.setAttribute("aria-label", current() === "dark" ? btn.dataset.labelLight : btn.dataset.labelDark); };
  label();
  btn.addEventListener("click", () => {
    const next = current() === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    store.set("ga_theme", next);
    label();
  });
}

function menu() {
  const btn = $("[data-menu-toggle]");
  const panel = $("#site-menu");
  if (!btn || !panel) return;
  const set = (open) => { panel.hidden = !open; btn.setAttribute("aria-expanded", String(open)); };
  btn.addEventListener("click", () => set(panel.hidden));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !panel.hidden) { set(false); btn.focus(); } });
  document.addEventListener("click", (e) => { if (!panel.hidden && !panel.contains(e.target) && !btn.contains(e.target)) set(false); });
}

function cookie() {
  const box = $("[data-cookie]");
  if (!box) return;
  const choice = store.get("ga_cookie");
  if (choice === "essential" || choice === "all") return;
  box.hidden = false;
  $("[data-cookie-essential]", box).addEventListener("click", () => { store.set("ga_cookie", "essential"); box.hidden = true; });
  $("[data-cookie-accept]", box).addEventListener("click", () => { store.set("ga_cookie", "all"); box.hidden = true; });
}

export { $, $$, store };
theme();
menu();
cookie();
```

Hero and booking modules are appended in Tasks 5 and 6 (`site.js` imports them as separate files: `assets/hero.js`, `assets/booking.js`).

- [ ] **Step 5: Add the shell styles to `assets/site.css`**

Append:

```css
/* header */
.hdr { position: sticky; top: 0; z-index: 30; background: var(--navBg); backdrop-filter: blur(8px); border-bottom: 1px solid var(--hairline); }
.hdr__util { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 6px 18px; padding-block: 8px; border-bottom: 1px solid var(--hairline); font-family: var(--mono); font-size: 12px; }
.hdr__contact { display: flex; align-items: center; gap: 12px; }
.hdr__contact a { color: var(--body); text-decoration: none; display: inline-flex; align-items: center; gap: 7px; }
.hdr__sep { color: var(--cardBorder); }
.dot { width: 6px; height: 6px; border-radius: 50%; background: #5db872; }
.hdr__social, .ftr__social { display: flex; gap: 12px; list-style: none; margin: 0; padding: 0; }
.hdr__social a, .ftr__social a { display: block; opacity: .8; }
.hdr__social a:hover, .ftr__social a:hover { opacity: 1; }
.hdr__tools { display: flex; align-items: center; gap: 10px; }
.pill { display: inline-flex; align-items: center; padding: 5px 12px; border-radius: var(--r-pill); background: var(--pillBg); border: 1px solid var(--cardBorder); color: var(--ink); text-decoration: none; font-family: var(--mono); font-size: 12px; letter-spacing: 1px; }
.icon-btn { width: 34px; height: 34px; border-radius: 50%; border: 1px solid var(--cardBorder); background: var(--card); display: inline-grid; place-items: center; cursor: pointer; padding: 0; }
.icon-btn__glyph { width: 14px; height: 14px; border-radius: 50%; background: linear-gradient(90deg, var(--ink) 50%, transparent 50%); border: 1.5px solid var(--ink); }
.hdr__main { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 18px; padding-block: 16px; }
.hdr__nav ul { display: flex; gap: 26px; list-style: none; margin: 0; padding: 0; font-size: 15px; font-weight: 500; }
.hdr__nav a { color: var(--ink); text-decoration: none; }
.hdr__nav a[aria-current="page"] { color: var(--accent); }
.brand { display: inline-flex; align-items: center; gap: 10px; text-decoration: none; justify-self: center; }
.brand__word { font-family: var(--display); font-size: 21px; letter-spacing: -.5px; color: var(--ink); }
.brand--light .brand__word { color: var(--footerHead); }
.hdr__cta { display: flex; gap: 10px; justify-self: end; }
.hdr__burger { display: none; justify-self: start; }
.burger { width: 16px; height: 2px; background: var(--ink); box-shadow: 0 -5px 0 var(--ink), 0 5px 0 var(--ink); }
.hdr__menu { padding-block: 6px 22px; border-top: 1px solid var(--hairline); display: grid; gap: 10px; }
.hdr__menu ul { list-style: none; margin: 0 0 6px; padding: 0; }
.hdr__menu li a { display: block; padding: 13px 0; font-size: 16px; color: var(--ink); text-decoration: none; border-bottom: 1px solid var(--hairline); }
@media (max-width: 859px) {
  .hdr__nav, .hdr__cta { display: none; }
  .hdr__burger { display: inline-grid; }
  .hdr__main { grid-template-columns: auto 1fr auto; }
  .hdr__contact { font-size: 11px; }
}

/* footer */
.ftr { background: var(--footerBg); color: var(--footerText); }
.ftr__grid { display: grid; grid-template-columns: 1.3fr 1fr 1fr; gap: 40px; padding-block: 72px 48px; }
.ftr__tag { max-width: 34ch; margin: 14px 0 18px; font-size: 14px; line-height: 1.6; }
.ftr__head { display: block; color: var(--footerHead); font-weight: 500; margin-bottom: 12px; }
.ftr__col ul { list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; font-size: 14px; }
.ftr a { color: inherit; text-decoration: none; }
.ftr a:hover { color: var(--footerHead); }
.ftr__legal { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 12px 24px; padding-block: 22px; border-top: 1px solid rgba(255,255,255,.08); font-size: 13px; }
.ftr__legal ul { display: flex; flex-wrap: wrap; gap: 18px; list-style: none; margin: 0; padding: 0; }
@media (max-width: 859px) { .ftr__grid { grid-template-columns: 1fr; gap: 32px; padding-block: 56px 32px; } }

/* cookie banner: fixed at the bottom, never over form controls */
.cookie { position: fixed; inset: auto 16px 16px 16px; z-index: 40; max-width: 560px; margin-inline: auto; background: var(--card); border: 1px solid var(--cardBorder); border-radius: var(--r-card); padding: 18px 20px; box-shadow: 0 12px 40px rgba(0,0,0,.18); }
.cookie__title { font-family: var(--display); font-size: 18px; color: var(--ink); margin-bottom: 6px; }
.cookie__text { font-size: 14px; line-height: 1.55; color: var(--body); }
.cookie__actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }

/* auth modal (opened by auth.js) */
.auth { position: fixed; inset: 0; z-index: 50; display: grid; place-items: center; background: rgba(24,23,21,.72); padding: 20px; }
.auth__card { width: min(420px, 100%); background: #181715; color: #faf9f5; border: 1px solid #2f2c28; border-radius: var(--r-card); padding: 28px; display: grid; gap: 10px; }
.auth__title { color: #faf9f5; font-size: 26px; margin-bottom: 8px; }
.auth__form { display: grid; gap: 8px; }
.auth__form label { font-family: var(--mono); font-size: 11px; letter-spacing: 1px; text-transform: uppercase; color: #a09d96; }
.auth__form input { padding: 12px 14px; border-radius: var(--r-btn); border: 1px solid #2f2c28; background: #1f1e1b; color: #faf9f5; font: inherit; }
```

- [ ] **Step 6: Add `jsonld_site` and `build_year` to the render context**

In `build.py`, add before `render_page`:

```python
def jsonld_site(site: dict, lang: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Organization", "@id": f"{DOMAIN}/#org", "name": site["brand"], "url": DOMAIN + "/",
             "logo": f"{DOMAIN}/logo-512.png", "email": site["email"], "telephone": site["phone"].replace(" ", ""),
             "sameAs": [s["href"] for s in site["socials"]],
             "address": {"@type": "PostalAddress", "addressLocality": "Hanstedt", "addressCountry": "DE"}},
            {"@type": "Person", "@id": f"{DOMAIN}/#person", "name": site["person"], "url": DOMAIN + "/",
             "worksFor": {"@id": f"{DOMAIN}/#org"}, "knowsLanguage": ["de", "en", "fr", "ro", "ar"]},
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=1)
```

and in `render_page`'s `tpl.render(...)` add `jsonld_site=jsonld_site(site, page.lang), build_year=date.today().year,`.

- [ ] **Step 7: Run the tests**

Run: `python3 -m pytest tests/test_build.py -v`
Expected: 11 passed (the forbidden-pattern test still passes: the shell has no inline styles)

- [ ] **Step 8: Build and look at it**

```bash
python3 build.py && (cd site && python3 -m http.server 8765 --bind 127.0.0.1 >/dev/null 2>&1 &) && sleep 1 && curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/en/
```
Open `http://127.0.0.1:8765/` in a browser: header with nav, brand centred, theme toggle switches and persists across reload, hamburger opens the menu below 860px, footer three columns. Then `pkill -f "http.server 8765"`.

- [ ] **Step 9: Commit**

```bash
git add build.py templates assets tests/test_build.py
git commit -m "Add the document shell: header, footer, cookie banner, auth modal, theme and menu scripts

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Home page (hero with panels, how it works, selected work, services, FAQ, CTA band)

**Files:**
- Modify: `content/de/home.json`, `content/en/home.json`
- Modify: `templates/pages/home.html`
- Create: `templates/partials/hero.html`, `templates/partials/cta-band.html`, `templates/partials/faq.html`
- Create: `assets/hero.js`
- Modify: `assets/site.js`, `assets/site.css`, `build.py` (REQUIRED keys), `tests/test_build.py`

**Interfaces:**
- Consumes: shell from Task 4.
- Produces: DOM hooks `[data-hero-panels]` with children `button.panel[aria-pressed]`; template partials `hero.html` (expects `c.hero`), `faq.html` (expects a `faq` dict with `eyebrow`, `title`, `items[{q,a}]`), `cta-band.html` (expects `cta` dict with `title`, `sub`, `btn`, `href`).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_build.py`:

```python
def test_home_sections_render(tmp_path):
    out, _ = _build(tmp_path)
    en = (out / "en" / "index.html").read_text(encoding="utf-8")
    assert en.count('class="panel"') == 5 and 'aria-pressed="true"' in en
    assert "How it works" in en and en.count('class="how__card"') == 4
    assert "Selected work" in en and en.count('class="work-card"') == 4
    assert en.count('class="svc-card') == 4
    assert "<details" in en and en.count("<details") == 6
    assert 'class="cta-band"' in en
    assert 'href="/en/contact/"' in en and 'href="/en/services/"' in en
    de = (out / "index.html").read_text(encoding="utf-8")
    assert "So funktioniert es" in de and 'href="/kontakt/"' in de
    assert '"@type": "FAQPage"' in de
```

Run: `python3 -m pytest tests/test_build.py::test_home_sections_render -v`
Expected: FAIL

- [ ] **Step 2: Extend the required keys in `build.py`**

Replace the `"home"` entry of `REQUIRED` with:

```python
    "home": ["meta.title", "meta.description", "hero.eyebrow", "hero.title", "hero.sub", "hero.cta1", "hero.cta2",
             "hero.panels", "how.eyebrow", "how.title", "how.sub", "how.cards", "work.title", "work.all", "work.items",
             "services.eyebrow", "services.title", "services.lead", "services.all", "services.items",
             "faq.eyebrow", "faq.title", "faq.items", "cta.title", "cta.sub", "cta.btn"],
```

Add a `jsonld_faq` helper next to `jsonld_site`:

```python
def jsonld_faq(items: list[dict]) -> str:
    data = {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": it["q"],
                            "acceptedAnswer": {"@type": "Answer", "text": it["a"]}} for it in items]}
    return json.dumps(data, ensure_ascii=False, indent=1)
```

and expose it in the render context: `jsonld_faq=jsonld_faq,`.

- [ ] **Step 3: Write the full home content**

`content/en/home.json`:

```json
{
  "meta": {"title": "GeorgeAI | AI voice agent and website assistant for trades, clinics and service firms", "description": "The enquiry you miss on a Saturday still ends up in your calendar. AI voice agent and website assistant for owner-run trades, clinics and service firms in Germany. Pilot live in about two weeks."},
  "hero": {
    "eyebrow": "For owner-run trades, clinics and service firms in Germany",
    "title": "The enquiry you miss on a Saturday still ends up in your calendar.",
    "sub": "An AI voice agent picks up the phone and an assistant answers on your website, day or night, in the caller's own language: every enquiry qualified and booked in. 8+ years, 40+ projects delivered, five languages. Your pilot goes live in about two weeks.",
    "cta1": "See the services", "cta2": "Ask about a pilot",
    "panelsTitle": "Selected projects, up close", "panelCta": "Read the case study",
    "panels": [
      {"name": "AI SEO Automation System", "cat": "Flagship project", "img": "SEO_AI.png", "slug": "ai-seo-automation-system", "desc": "An AI-driven SEO engine on OpenAI and n8n: keyword research, content generation and workflow automation that cut manual SEO work and scaled output."},
      {"name": "Medical AI Agent", "cat": "AI · RAG", "img": "medical_ai.png", "slug": "medical-ai-agent", "desc": "An OpenAI + Python + RAG assistant for medical data processing and query automation."},
      {"name": "Smart Facility Automation", "cat": "IoT · BMS", "img": "concept_smart_home.png", "slug": "smart-facility-automation", "desc": "n8n, OpenAI (RAG) and Python for smart-building monitoring and operational control."},
      {"name": "Containerized Infrastructure", "cat": "Infra · Cloud", "img": "clouddienste.jpg", "slug": "containerized-infrastructure", "desc": "Scalable infrastructure with Docker, PostgreSQL, Redis and Nginx, built for high availability."},
      {"name": "Full-stack Web Platform", "cat": "Django · AI", "img": "full_stack.png", "slug": "full-stack-web-platform", "desc": "A scalable Django platform with WordPress integration, AI services and API automations."}
    ]
  },
  "how": {
    "eyebrow": "How it works", "title": "From bottleneck to running system, in weeks, not months.",
    "sub": "A simple, proven path from your first call to a system that quietly does the work every day.",
    "cards": [
      {"tag": "01 · Discover", "title": "We map the bottleneck", "desc": "A short call to find the repetitive, costly work, and the fastest place to automate it."},
      {"tag": "02 · Build", "title": "I build and harden it", "desc": "Custom n8n + Python with error handling, tested against your real data until it is reliable."},
      {"tag": "03 · Connect", "title": "It plugs into your stack", "desc": "CRM, email, sheets, WhatsApp, phone: your tools, talking to each other automatically."},
      {"tag": "04 · Run", "title": "It runs, you watch it work", "desc": "Deployed, monitored and handed over, with dashboards so you always see what it is doing."}
    ]
  },
  "work": {
    "title": "Selected work", "all": "All projects",
    "items": [
      {"name": "Medical AI Agent", "tags": "AI · RAG", "slug": "medical-ai-agent", "desc": "An OpenAI + Python + RAG assistant for medical data processing and query automation."},
      {"name": "Smart Facility Automation", "tags": "IoT · BMS", "slug": "smart-facility-automation", "desc": "n8n, OpenAI (RAG) and Python for smart-building monitoring and operational control."},
      {"name": "Containerized Infrastructure", "tags": "Infra · Cloud", "slug": "containerized-infrastructure", "desc": "Scalable infrastructure with Docker, PostgreSQL, Redis and Nginx, built for high availability."},
      {"name": "Full-stack Web Platform", "tags": "Django · AI", "slug": "full-stack-web-platform", "desc": "A scalable Django platform with WordPress integration, AI services and API automations."}
    ]
  },
  "services": {
    "eyebrow": "Services", "title": "What I build for you", "lead": "Four areas, one goal: the enquiry gets answered, qualified and booked, whether you are on a job, in surgery or asleep.", "all": "All services",
    "priceLabel": "Price on request",
    "items": [
      {"tag": "Automation", "name": "n8n Workflows", "slug": "automation", "cta": "Get a quote", "desc": "Automated n8n workflows that connect your tools and remove manual, repetitive work, built with OpenAI and Python."},
      {"tag": "Optimization", "name": "SEO · AIO · GEO", "slug": "seo-aio-geo", "cta": "Get a quote", "desc": "SEO, AI Optimization (AIO) and Generative Engine Optimization (GEO) for your existing site, or a new one I build for you."},
      {"tag": "Data", "name": "Django Data Analytics", "slug": "django", "cta": "Get a quote", "desc": "Python backend and data-analytics dashboards in Django, turning your data into decisions."},
      {"tag": "Conversation", "name": "AI Chatbots & Phone AI", "slug": "ai-phone-calls", "cta": "Book a call", "featured": true, "desc": "Website chatbots and AI phone agents with a custom voice, plus social-media integration: conversations that convert."}
    ]
  },
  "faq": {
    "eyebrow": "FAQ", "title": "Questions & answers",
    "items": [
      {"q": "How long does a typical project take?", "a": "Most automations and AI agents ship in 2 to 6 weeks, depending on scope. A focused pilot can be live in about two weeks. You get a clear timeline after the first call."},
      {"q": "Do you work with my existing website and tools?", "a": "Yes. I connect to what you already use: WordPress, your CRM, email platform, sheets, WhatsApp and more. If you do not have a site yet, I can build that too."},
      {"q": "What does it cost?", "a": "Pricing depends on scope, so it is quoted per project. Use the configurator to outline what you need and I will send a tailored quote, usually within two days. No surprise fees."},
      {"q": "Will the automations keep running without you?", "a": "Yes. Everything is deployed, monitored and documented, and handed over to you. Optional ongoing support and maintenance are available if you would like me to keep an eye on it."},
      {"q": "Is my data safe?", "a": "Your data stays in your own tools and infrastructure wherever possible. I follow GDPR practices and can work within your security requirements."},
      {"q": "Which languages and regions do you serve?", "a": "I work remotely across Europe and the Middle East, in English, German, French, Romanian and Arabic."}
    ]
  },
  "cta": {"title": "Have a process worth automating?", "sub": "Taking on new projects now. Tell me what is slowing you down and I will reply within two days.", "btn": "Start a project"}
}
```

`content/de/home.json`:

```json
{
  "meta": {"title": "GeorgeAI | KI-Telefonagent und Website-Assistent für Handwerk, Praxen und Dienstleister", "description": "Der Anruf, den Sie samstags verpassen, steht montags in Ihrem Kalender. KI-Telefonagent und Website-Assistent für Handwerk, Praxen und Dienstleister in Deutschland. Pilot in rund zwei Wochen."},
  "hero": {
    "eyebrow": "Für Handwerk, Praxen und Dienstleister im Mittelstand",
    "title": "Der Anruf, den Sie samstags verpassen, steht montags in Ihrem Kalender.",
    "sub": "Ein KI-Assistent geht ans Telefon und antwortet auf Ihrer Website, Tag und Nacht, in der Sprache des Kunden: Anliegen notiert, Termin gebucht. 8+ Jahre Erfahrung, 40+ Projekte, fünf Sprachen. Nach rund zwei Wochen läuft Ihr Pilotprojekt.",
    "cta1": "Leistungen ansehen", "cta2": "Pilotprojekt anfragen",
    "panelsTitle": "Ausgewählte Projekte aus der Nähe", "panelCta": "Case Study lesen",
    "panels": [
      {"name": "AI SEO Automation System", "cat": "Leuchtturm-Projekt", "img": "SEO_AI.png", "slug": "ai-seo-automation-system", "desc": "Eine KI-gestützte SEO-Engine auf OpenAI und n8n: Keyword-Recherche, Content-Erstellung und Workflow-Automatisierung, die manuelle SEO-Arbeit reduziert und den Output skaliert."},
      {"name": "Medical AI Agent", "cat": "KI · RAG", "img": "medical_ai.png", "slug": "medical-ai-agent", "desc": "OpenAI- + Python- + RAG-Assistent für die Verarbeitung medizinischer Daten und Abfrage-Automatisierung."},
      {"name": "Smart Facility Automation", "cat": "IoT · GLT", "img": "concept_smart_home.png", "slug": "smart-facility-automation", "desc": "n8n, OpenAI (RAG) und Python für Smart-Building-Monitoring und Betriebssteuerung."},
      {"name": "Containerized Infrastructure", "cat": "Infra · Cloud", "img": "clouddienste.jpg", "slug": "containerized-infrastructure", "desc": "Skalierbare Infrastruktur mit Docker, PostgreSQL, Redis und Nginx, für hohe Verfügbarkeit gebaut."},
      {"name": "Full-stack Web Platform", "cat": "Django · KI", "img": "full_stack.png", "slug": "full-stack-web-platform", "desc": "Eine skalierbare Django-Plattform mit WordPress-Integration, KI-Diensten und API-Automatisierungen."}
    ]
  },
  "how": {
    "eyebrow": "So funktioniert es", "title": "Vom Engpass zum laufenden System, in Wochen, nicht Monaten.",
    "sub": "Ein einfacher, bewährter Weg vom ersten Gespräch bis zum System, das täglich leise die Arbeit erledigt.",
    "cards": [
      {"tag": "01 · Analyse", "title": "Wir kartieren den Engpass", "desc": "Ein kurzes Gespräch, um die repetitive, teure Arbeit zu finden, und den schnellsten Ansatzpunkt."},
      {"tag": "02 · Aufbau", "title": "Ich baue und härte es ab", "desc": "Individuelles n8n + Python mit Fehlerbehandlung, an Ihren echten Daten getestet, bis es zuverlässig läuft."},
      {"tag": "03 · Verbinden", "title": "Es klinkt sich in Ihren Stack ein", "desc": "CRM, E-Mail, Tabellen, WhatsApp, Telefon: Ihre Tools, die automatisch miteinander reden."},
      {"tag": "04 · Betrieb", "title": "Es läuft, Sie sehen ihm zu", "desc": "Deployt, überwacht und übergeben, mit Dashboards, damit Sie immer sehen, was es tut."}
    ]
  },
  "work": {
    "title": "Ausgewählte Arbeiten", "all": "Alle Projekte",
    "items": [
      {"name": "Medical AI Agent", "tags": "KI · RAG", "slug": "medical-ai-agent", "desc": "OpenAI- + Python- + RAG-Assistent für die Verarbeitung medizinischer Daten und Abfrage-Automatisierung."},
      {"name": "Smart Facility Automation", "tags": "IoT · GLT", "slug": "smart-facility-automation", "desc": "n8n, OpenAI (RAG) und Python für Smart-Building-Monitoring und Betriebssteuerung."},
      {"name": "Containerized Infrastructure", "tags": "Infra · Cloud", "slug": "containerized-infrastructure", "desc": "Skalierbare Infrastruktur mit Docker, PostgreSQL, Redis und Nginx, für hohe Verfügbarkeit gebaut."},
      {"name": "Full-stack Web Platform", "tags": "Django · KI", "slug": "full-stack-web-platform", "desc": "Eine skalierbare Django-Plattform mit WordPress-Integration, KI-Diensten und API-Automatisierungen."}
    ]
  },
  "services": {
    "eyebrow": "Leistungen", "title": "Was ich für Sie baue", "lead": "Vier Bereiche, ein Ziel: Die Anfrage wird beantwortet, qualifiziert und gebucht, ob Sie auf der Baustelle, in der Sprechstunde oder im Feierabend sind.", "all": "Alle Leistungen",
    "priceLabel": "Preis auf Anfrage",
    "items": [
      {"tag": "Automatisierung", "name": "n8n-Workflows", "slug": "automation", "cta": "Angebot anfragen", "desc": "Automatisierte n8n-Workflows, die Ihre Tools verbinden und manuelle, sich wiederholende Arbeit eliminieren, mit OpenAI und Python."},
      {"tag": "Optimierung", "name": "SEO · AIO · GEO", "slug": "seo-aio-geo", "cta": "Angebot anfragen", "desc": "SEO, AI Optimization (AIO) und Generative Engine Optimization (GEO) für Ihre bestehende Website, oder eine neue, die ich baue."},
      {"tag": "Daten", "name": "Django-Datenanalyse", "slug": "django", "cta": "Angebot anfragen", "desc": "Python-Backend und Datenanalyse-Dashboards in Django: aus Ihren Daten werden Entscheidungen."},
      {"tag": "Gespräch", "name": "KI-Chatbots & Phone AI", "slug": "ai-phone-calls", "cta": "Gespräch buchen", "featured": true, "desc": "Website-Chatbots und KI-Telefonagenten mit eigener Stimme, plus Social-Media-Integration: Gespräche, die konvertieren."}
    ]
  },
  "faq": {
    "eyebrow": "FAQ", "title": "Fragen & Antworten",
    "items": [
      {"q": "Wie lange dauert ein typisches Projekt?", "a": "Die meisten Automationen und KI-Agenten sind in 2 bis 6 Wochen einsatzbereit, je nach Umfang. Ein fokussierter Pilot läuft nach rund zwei Wochen. Nach dem ersten Gespräch erhalten Sie einen klaren Zeitplan."},
      {"q": "Arbeiten Sie mit meiner bestehenden Website und meinen Tools?", "a": "Ja. Ich verbinde mich mit dem, was Sie bereits nutzen: WordPress, Ihr CRM, E-Mail-Plattform, Tabellen, WhatsApp und mehr. Falls Sie noch keine Website haben, baue ich auch die."},
      {"q": "Was kostet es?", "a": "Der Preis hängt vom Umfang ab und wird pro Projekt kalkuliert. Nutzen Sie den Konfigurator, und ich sende ein individuelles Angebot, meist innerhalb von zwei Tagen. Keine versteckten Kosten."},
      {"q": "Laufen die Automationen ohne Sie weiter?", "a": "Ja. Alles wird deployt, überwacht, dokumentiert und übergeben. Optionaler laufender Support und Wartung sind verfügbar, wenn ich ein Auge darauf behalten soll."},
      {"q": "Sind meine Daten sicher?", "a": "Ihre Daten bleiben nach Möglichkeit in Ihren eigenen Tools und Ihrer Infrastruktur. Ich arbeite DSGVO-konform und innerhalb Ihrer Sicherheitsanforderungen."},
      {"q": "Welche Sprachen und Regionen bedienen Sie?", "a": "Ich arbeite remote in Europa und im Nahen Osten, auf Englisch, Deutsch, Französisch, Rumänisch und Arabisch."}
    ]
  },
  "cta": {"title": "Einen Prozess, der Automatisierung verdient?", "sub": "Ich nehme aktuell neue Projekte an. Sagen Sie mir, was Sie ausbremst, Antwort in zwei Tagen.", "btn": "Projekt starten"}
}
```

The FAQ "48 hours" claim from the export was replaced by "usually within two days" (allowed claim). `services.items[].slug` values are service slugs from `georgeai_services.json` (Phase 2 builds those pages; the links are valid after Phase 2 and the browser link check in Task 7 tolerates them via the allowlist until then).

- [ ] **Step 4: Write the partials and the home template**

`templates/partials/hero.html`:

```html
<section class="hero">
  <div class="hero__bg" aria-hidden="true">
    <span class="hero__aurora hero__aurora--a"></span>
    <span class="hero__aurora hero__aurora--b"></span>
    <span class="hero__glow"></span>
    <span class="hero__grid"></span>
    {% for i in range(7) %}<span class="hero__beam hero__beam--{{ i }}"></span>{% endfor %}
  </div>
  <div class="hero__inner wrap">
    <div class="hero__copy">
      <span class="eyebrow hero__eyebrow">{{ c.hero.eyebrow }}</span>
      <h1>{{ c.hero.title }}</h1>
      <p class="lead hero__sub">{{ c.hero.sub }}</p>
      <div class="hero__ctas">
        <a class="btn btn--primary" href="{{ url('services') }}">{{ c.hero.cta1 }}</a>
        <a class="btn btn--secondary" href="{{ url('contact') }}">{{ c.hero.cta2 }}</a>
      </div>
    </div>
    <div class="hero__panels" data-hero-panels aria-label="{{ c.hero.panelsTitle }}">
      {% for p in c.hero.panels %}
      <div class="panel" data-panel>
        <button class="panel__hit" type="button" aria-pressed="{{ 'true' if loop.first else 'false' }}" aria-label="{{ p.name }}">
          <img class="panel__img" src="/assets/img/{{ p.img }}" alt="" loading="{{ 'eager' if loop.first else 'lazy' }}">
          <span class="panel__scrim" aria-hidden="true"></span>
          <span class="panel__label" aria-hidden="true">{{ p.name }}</span>
        </button>
        <div class="panel__body">
          <span class="eyebrow">{{ '%02d' % loop.index }} · {{ p.cat }}</span>
          <h3 class="panel__title">{{ p.name }}</h3>
          <p class="panel__desc">{{ p.desc }}</p>
          <a class="btn btn--cream btn--small" href="{{ url('project', p.slug) }}">{{ c.hero.panelCta }}</a>
        </div>
      </div>
      {% endfor %}
    </div>
  </div>
</section>
```

`templates/partials/faq.html` (expects `faq`):

```html
<section class="section wrap faq">
  <div class="faq__grid">
    <div>
      <span class="eyebrow">{{ faq.eyebrow }}</span>
      <h2 class="faq__title">{{ faq.title }}</h2>
    </div>
    <div class="faq__list">
      {% for it in faq.items %}
      <details class="faq__item"{% if loop.first %} open{% endif %}>
        <summary>{{ it.q }}</summary>
        <p>{{ it.a }}</p>
      </details>
      {% endfor %}
    </div>
  </div>
</section>
```

`templates/partials/cta-band.html` (expects `cta` with `href`):

```html
<section class="section wrap">
  <div class="cta-band">
    <div>
      <h2 class="cta-band__title">{{ cta.title }}</h2>
      <p class="cta-band__sub">{{ cta.sub }}</p>
    </div>
    <a class="btn btn--cream" href="{{ cta.href }}">{{ cta.btn }}</a>
  </div>
</section>
```

`templates/pages/home.html`:

```html
{% extends "base.html" %}
{% block body_class %}page-home{% endblock %}
{% block jsonld %}<script type="application/ld+json">
{{ jsonld_faq(c.faq.items) | safe }}
</script>{% endblock %}
{% block content %}
{% include "partials/hero.html" %}

<section class="section wrap how">
  <div class="how__head">
    <span class="eyebrow">{{ c.how.eyebrow }}</span>
    <h2>{{ c.how.title }}</h2>
    <p class="lead">{{ c.how.sub }}</p>
  </div>
  <ol class="how__grid">
    {% for card in c.how.cards %}
    <li class="how__card">
      <span class="eyebrow eyebrow--muted">{{ card.tag }}</span>
      <h3>{{ card.title }}</h3>
      <p>{{ card.desc }}</p>
    </li>
    {% endfor %}
  </ol>
</section>

<section class="section wrap work">
  <div class="row-head">
    <h2>{{ c.work.title }}</h2>
    <a class="row-head__link" href="{{ url('work') }}">{{ c.work.all }} &rarr;</a>
  </div>
  <ul class="work__grid">
    {% for w in c.work.items %}
    <li><a class="work-card" href="{{ url('project', w.slug) }}">
      <span class="eyebrow eyebrow--muted">{{ w.tags }}</span>
      <h3>{{ w.name }}</h3>
      <p>{{ w.desc }}</p>
    </a></li>
    {% endfor %}
  </ul>
</section>

<section class="section section--band svcs">
  <div class="wrap">
    <div class="row-head">
      <div>
        <span class="eyebrow">{{ c.services.eyebrow }}</span>
        <h2>{{ c.services.title }}</h2>
        <p class="lead">{{ c.services.lead }}</p>
      </div>
      <a class="row-head__link" href="{{ url('services') }}">{{ c.services.all }} &rarr;</a>
    </div>
    <ul class="svcs__grid">
      {% for s in c.services.items %}
      <li class="svc-card{% if s.featured %} svc-card--featured{% endif %}">
        <span class="eyebrow">{{ s.tag }}</span>
        <h3>{{ s.name }}</h3>
        <p class="svc-card__desc">{{ s.desc }}</p>
        <div class="svc-card__foot">
          <span class="svc-card__price">{{ c.services.priceLabel }}</span>
          <a class="btn btn--small {{ 'btn--cream' if s.featured else 'btn--primary' }}" href="{{ url('service', s.slug) }}">{{ s.cta }}</a>
        </div>
      </li>
      {% endfor %}
    </ul>
  </div>
</section>

{% with faq = c.faq %}{% include "partials/faq.html" %}{% endwith %}
{% with cta = dict(c.cta, href=url('contact')) %}{% include "partials/cta-band.html" %}{% endwith %}
{% endblock %}
```

- [ ] **Step 5: Write `assets/hero.js` and import it**

`assets/hero.js`:

```js
export function hero() {
  const root = document.querySelector("[data-hero-panels]");
  if (!root) return;
  const panels = Array.from(root.querySelectorAll("[data-panel]"));
  const buttons = panels.map((p) => p.querySelector(".panel__hit"));
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let idx = 0, timer = null;
  const activate = (i) => {
    idx = i;
    panels.forEach((p, j) => { p.classList.toggle("is-active", j === i); buttons[j].setAttribute("aria-pressed", String(j === i)); });
  };
  const start = () => { if (reduced || timer) return; timer = setInterval(() => activate((idx + 1) % panels.length), 6000); };
  const stop = () => { clearInterval(timer); timer = null; };
  buttons.forEach((b, i) => b.addEventListener("click", () => { activate(i); stop(); }));
  root.addEventListener("pointerenter", stop);
  root.addEventListener("pointerleave", start);
  root.addEventListener("focusin", stop);
  root.addEventListener("focusout", (e) => { if (!root.contains(e.relatedTarget)) start(); });
  activate(0);
  start();
}
```

In `assets/site.js` add at the top `import { hero } from "./hero.js";` and at the bottom `hero();`.

- [ ] **Step 6: Add the home styles to `assets/site.css`**

Append:

```css
/* hero */
.hero { position: relative; overflow: hidden; padding-block: var(--heroY) var(--sectionY); background: var(--canvas); }
.hero__bg { position: absolute; inset: 0; pointer-events: none; }
.hero__grid { position: absolute; inset: 0; background-image: linear-gradient(var(--gridline) 1px, transparent 1px), linear-gradient(90deg, var(--gridline) 1px, transparent 1px); background-size: 48px 48px; mask-image: linear-gradient(180deg, #000 40%, transparent); }
.hero__aurora { position: absolute; width: 60vw; height: 60vw; max-width: 720px; max-height: 720px; border-radius: 50%; filter: blur(80px); opacity: .35; background: radial-gradient(circle, var(--coral), transparent 65%); }
.hero__aurora--a { top: -20%; right: -10%; animation: auroraA 18s ease-in-out infinite; }
.hero__aurora--b { bottom: -30%; left: -15%; animation: auroraB 22s ease-in-out infinite; opacity: .22; }
.hero__glow { position: absolute; left: 30%; top: 10%; width: 40vw; height: 40vw; max-width: 520px; max-height: 520px; border-radius: 50%; background: radial-gradient(circle, rgba(204,120,92,.35), transparent 60%); filter: blur(60px); animation: ggGlow 12s ease-in-out infinite; }
.hero__beam { position: absolute; bottom: 0; width: 2px; height: 230px; border-radius: 2px; background: linear-gradient(to top, transparent, #ff5c39 55%, #ff9e82); box-shadow: 0 0 8px rgba(255,92,57,.42); opacity: 0; will-change: transform, opacity; animation: beamRise 9s linear infinite, beamGlow 9s ease-in-out infinite; }
.hero__beam--0 { left: 8%; animation-delay: 0s; } .hero__beam--1 { left: 21%; animation-delay: -2s; animation-duration: 11s; }
.hero__beam--2 { left: 37%; animation-delay: -5s; } .hero__beam--3 { left: 52%; animation-delay: -1s; animation-duration: 13s; }
.hero__beam--4 { left: 66%; animation-delay: -7s; } .hero__beam--5 { left: 79%; animation-delay: -3s; animation-duration: 10s; }
.hero__beam--6 { left: 92%; animation-delay: -6s; }
@keyframes ggGlow { 0%, 100% { opacity: .5; transform: translate(0,0) scale(1); } 50% { opacity: .9; transform: translate(-5%,4%) scale(1.15); } }
@keyframes auroraA { 0%, 100% { transform: translate(0,0) scale(1); } 33% { transform: translate(7%,6%) scale(1.2); } 66% { transform: translate(-6%,-4%) scale(.95); } }
@keyframes auroraB { 0%, 100% { transform: translate(0,0) scale(1.05); } 50% { transform: translate(-9%,8%) scale(1.28); } }
@keyframes beamRise { from { transform: translateY(125%); } to { transform: translateY(-340%); } }
@keyframes beamGlow { 0% { opacity: 0; } 18% { opacity: .85; } 80% { opacity: .85; } 100% { opacity: 0; } }
.hero__inner { position: relative; z-index: 1; display: grid; grid-template-columns: .95fr 1.15fr; gap: 48px; align-items: center; }
.hero__eyebrow { display: inline-block; border: 1px solid var(--cardBorder); border-radius: var(--r-pill); padding: 6px 14px; font-size: 11px; letter-spacing: 1.5px; }
.hero__copy h1 { margin-top: 18px; max-width: 14ch; }
.hero__sub { margin-top: 16px; color: var(--muted); font-size: 17px; }
.hero__ctas { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 28px; }
.hero__panels { display: flex; gap: 10px; height: 460px; }
.panel { position: relative; flex: 1 1 0; min-width: 0; border-radius: 16px; overflow: hidden; border: 1px solid var(--cardBorder); background: #181715; transition: flex .6s cubic-bezier(.4,0,.2,1); }
.panel.is-active { flex: 5 1 0; }
.panel__hit { position: absolute; inset: 0; width: 100%; border: 0; padding: 0; background: none; cursor: pointer; }
.panel__img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; transform: scale(1.12); filter: grayscale(.4) brightness(.7); transition: transform .6s ease, filter .5s ease; }
.panel.is-active .panel__img { transform: scale(1.02); filter: none; }
.panel__scrim { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(24,23,21,.05) 30%, rgba(24,23,21,.5) 100%); transition: background .5s ease; }
.panel.is-active .panel__scrim { background: linear-gradient(180deg, rgba(24,23,21,.05) 30%, rgba(24,23,21,.82) 100%); }
.panel__label { position: absolute; bottom: 22px; left: 0; right: 0; display: flex; justify-content: center; writing-mode: vertical-rl; transform: rotate(180deg); font-family: var(--mono); font-size: 12px; letter-spacing: 1px; text-transform: uppercase; color: rgba(255,255,255,.82); white-space: nowrap; }
.panel.is-active .panel__label { display: none; }
.panel__body { position: absolute; left: 0; right: 0; bottom: 0; padding: 24px; color: #faf9f5; display: none; pointer-events: none; }
.panel__body .btn { pointer-events: auto; margin-top: 14px; }
.panel.is-active .panel__body { display: block; }
.panel__title { color: #faf9f5; margin-top: 6px; }
.panel__desc { color: rgba(250,249,245,.85); font-size: 14px; line-height: 1.55; margin-top: 6px; max-width: 48ch; }
@media (max-width: 859px) {
  .hero__inner { grid-template-columns: 1fr; gap: 32px; }
  .hero__panels { height: 340px; }
  .panel.is-active { flex: 6 1 0; }
}
@media (max-width: 559px) { .hero__panels { height: 300px; gap: 6px; } .panel__body { padding: 16px; } }

/* how it works */
.how__head { max-width: 62ch; }
.how__head h2 { margin-top: 12px; }
.how__head .lead { margin-top: 14px; }
.how__grid { list-style: none; margin: 40px 0 0; padding: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.how__card { background: var(--card); border: 1px solid var(--cardBorder); border-radius: 18px; padding: 28px; }
.how__card h3 { margin-top: 10px; }
.how__card p { margin-top: 8px; color: var(--muted); font-size: 15px; }
@media (max-width: 859px) { .how__grid { grid-template-columns: 1fr; } }

/* row heads, work, services */
.row-head { display: flex; justify-content: space-between; align-items: end; gap: 24px; flex-wrap: wrap; }
.row-head .lead { margin-top: 12px; }
.row-head h2 { margin-top: 12px; }
.row-head__link { color: var(--accent); text-decoration: none; font-weight: 500; white-space: nowrap; }
.work__grid { list-style: none; margin: 32px 0 0; padding: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.work-card { display: block; text-decoration: none; color: inherit; background: var(--card); border: 1px solid var(--cardBorder); border-radius: 14px; padding: 26px; transition: border-color .15s ease; }
.work-card:hover { border-color: var(--accent); }
.work-card h3 { margin-top: 8px; }
.work-card p { margin-top: 8px; color: var(--muted); font-size: 15px; }
.svcs__grid { list-style: none; margin: 36px 0 0; padding: 0; display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px; }
.svc-card { background: var(--card); border: 1px solid var(--cardBorder); border-radius: 14px; padding: 30px; display: flex; flex-direction: column; }
.svc-card h3 { margin-top: 10px; }
.svc-card__desc { margin-top: 10px; color: var(--muted); font-size: 15px; flex: 1; }
.svc-card__foot { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-top: 22px; padding-top: 18px; border-top: 1px solid var(--cardBorder); font-size: 14px; color: var(--muted); }
.svc-card--featured { background: var(--coral); border-color: var(--coral); color: #fff; }
.svc-card--featured .eyebrow, .svc-card--featured .svc-card__desc, .svc-card--featured .svc-card__foot { color: rgba(255,255,255,.85); }
.svc-card--featured h3 { color: #fff; }
.svc-card--featured .svc-card__foot { border-top-color: rgba(255,255,255,.25); }
@media (max-width: 859px) { .work__grid, .svcs__grid { grid-template-columns: 1fr; } }

/* faq */
.faq__grid { display: grid; grid-template-columns: .42fr .58fr; gap: 48px; }
.faq__title { margin-top: 12px; }
.faq__item { border-top: 1px solid var(--hairline); }
.faq__item:last-child { border-bottom: 1px solid var(--hairline); }
.faq__item summary { cursor: pointer; padding: 18px 0; font-size: 17px; font-weight: 500; color: var(--ink); list-style: none; display: flex; justify-content: space-between; gap: 16px; }
.faq__item summary::-webkit-details-marker { display: none; }
.faq__item summary::after { content: "+"; color: var(--accent); font-family: var(--mono); }
.faq__item[open] summary::after { content: "−"; }
.faq__item p { padding-bottom: 18px; color: var(--body); max-width: 65ch; }
@media (max-width: 859px) { .faq__grid { grid-template-columns: 1fr; gap: 24px; } }

/* cta band */
.cta-band { background: var(--coral); color: #faf9f5; border-radius: 20px; padding: 44px; display: flex; justify-content: space-between; align-items: center; gap: 24px; }
.cta-band__title { color: #faf9f5; }
.cta-band__sub { margin-top: 10px; color: rgba(250,249,245,.88); max-width: 52ch; }
@media (max-width: 859px) { .cta-band { flex-direction: column; align-items: flex-start; padding: 32px 24px; } }
```

- [ ] **Step 7: Run the tests**

Run: `python3 -m pytest tests/test_build.py -v`
Expected: 12 passed

- [ ] **Step 8: Build and check visually**

```bash
python3 build.py && (cd site && python3 -m http.server 8765 --bind 127.0.0.1 >/dev/null 2>&1 &) && sleep 1
```
Open `http://127.0.0.1:8765/` and `/en/`: hero with animated background and five panels (click and keyboard change the active one; auto-rotates), four how-cards, four work cards, four service cards with the coral featured one, FAQ accordion, CTA band. Both themes. Resize to 390px: single column, panels 300px high. Stop the server afterwards.

- [ ] **Step 9: Commit**

```bash
git add build.py content templates assets tests/test_build.py
git commit -m "Build the home page in German and English with the hero panels and sections

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Contact page with the booking form

**Files:**
- Create: `content/de/contact.json`, `content/en/contact.json`
- Create: `templates/pages/contact.html`
- Create: `assets/booking.js`
- Modify: `assets/site.js`, `assets/site.css`, `build.py` (REQUIRED, JSON-LD), `tests/test_build.py`

**Interfaces:**
- Consumes: shell, `.btn`, `.card`, `.eyebrow` classes.
- Produces: DOM hooks `form[data-booking]`, `[data-booking-days]`, `[data-booking-slots]`, `#ga-ct-service`, `#ga-ct-name`, `#ga-ct-email`, `#ga-ct-msg`, `[data-booking-error]`, `[data-booking-done]` (hidden section), `[data-booking-body]`, `[data-booking-copy]`, `[data-booking-mail]`, `[data-booking-wa]`, `[data-booking-edit]`, `[data-booking-summary]`; strings are passed to JS through `data-*` attributes on the form (`data-missing`, `data-field-day`, `data-field-time`, `data-field-name`, `data-field-email`, `data-copied`, `data-copy`, `data-mail-subject`, `data-mail-greeting`, `data-mail-slot`, `data-mail-service`, `data-mail-name`, `data-mail-email`, `data-mail-sign`, `data-locale`).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_build.py`:

```python
def test_contact_pages_render_with_form_and_steps(tmp_path):
    out, _ = _build(tmp_path)
    de = (out / "kontakt" / "index.html").read_text(encoding="utf-8")
    en = (out / "en" / "contact" / "index.html").read_text(encoding="utf-8")
    for html in (de, en):
        assert "<form" in html and "data-booking" in html
        assert 'for="ga-ct-name"' in html and 'id="ga-ct-name"' in html
        assert "<textarea" in html and 'id="ga-ct-msg"' in html
        assert 'data-booking-days' in html and 'data-booking-slots' in html
        assert html.count('class="step"') == 3
        assert '"@type": "ContactPage"' in html
    assert "Termin buchen" in de and "Book a call" in en
    assert 'href="/en/contact/"' in de and 'href="/kontakt/"' in en
```

Run: `python3 -m pytest tests/test_build.py::test_contact_pages_render_with_form_and_steps -v`
Expected: FAIL

- [ ] **Step 2: Extend `build.py`**

Replace the `"contact"` entry of `REQUIRED`:

```python
    "contact": ["meta.title", "meta.description", "eyebrow", "title", "lead", "infoTitle", "phoneL", "emailL",
                "locationL", "hoursL", "hours", "personal", "nextTitle", "steps", "form", "done", "mail"],
```

Add `jsonld_contact` next to the other JSON-LD helpers and expose it (`jsonld_contact=jsonld_contact,`):

```python
def jsonld_contact(page: Page) -> str:
    data = {"@context": "https://schema.org", "@type": "ContactPage", "url": DOMAIN + page.path,
            "name": _get(page.content, "meta.title"), "about": {"@id": f"{DOMAIN}/#person"}}
    return json.dumps(data, ensure_ascii=False, indent=1)
```

- [ ] **Step 3: Write the content**

`content/en/contact.json`:

```json
{
  "meta": {"title": "Contact | Book a free 30-minute call with George", "description": "Book a free 30-minute call or send a message. AI voice agent and website assistant pilots for trades, clinics and service firms in Germany. Reply usually within two days."},
  "eyebrow": "Contact", "title": "Let's talk about your project.",
  "lead": "Book a free 30-minute call or send a message. I usually reply within two days.",
  "infoTitle": "Direct", "phoneL": "Phone", "emailL": "Email", "locationL": "Location", "hoursL": "Hours", "hours": "Mon–Fri, 9:00–18:00 CET",
  "personal": "You reach me directly, not a sales team. Calls in German, English, French, Romanian or Arabic.",
  "nextTitle": "What happens next",
  "steps": [
    {"t": "A 30-minute call", "d": "We look at where enquiries slip through: evenings, Saturdays, the phone ringing while you're on a job."},
    {"t": "A short written proposal", "d": "Scope, price and what the pilot covers. Usually within two days."},
    {"t": "Pilot live in about two weeks", "d": "On your own number and website, answering in your callers' language."}
  ],
  "form": {
    "title": "Book a call", "serviceL": "What is it about?", "servicePh": "Select a service",
    "services": ["n8n Workflows", "SEO · AIO · GEO", "Django Data Analytics", "AI Chatbots & Phone AI", "Something else"],
    "dateL": "Pick a day", "timeL": "Pick a time (CET)", "slots": ["09:00", "10:30", "12:00", "14:00", "15:30", "17:00"],
    "nameL": "Your name", "emailL": "Your email", "msgL": "A line about your project", "optional": "optional",
    "submit": "Request this slot",
    "hint": "Opens your email app with the request prefilled. Nothing is sent until you press Send.",
    "missing": "Still needed:", "fieldDay": "a day", "fieldTime": "a time", "fieldName": "your name", "fieldEmail": "a valid email",
    "locale": "en-GB"
  },
  "done": {
    "title": "One more step: press Send.",
    "msg": "Your email app should have opened with the request below. If it didn't, copy the text and send it to contact@georgeai.dev, or send it on WhatsApp.",
    "copy": "Copy request", "copied": "Copied", "openMail": "Open email again", "edit": "Change something"
  },
  "mail": {"subject": "Booking request", "greeting": "Hi George,", "slot": "Requested slot:", "service": "Service:", "name": "Name:", "email": "Email:", "sign": "Thanks,"}
}
```

`content/de/contact.json`:

```json
{
  "meta": {"title": "Kontakt | Kostenloses 30-Minuten-Gespräch mit George buchen", "description": "Buchen Sie ein kostenloses 30-Minuten-Gespräch oder schreiben Sie mir. KI-Telefonagent und Website-Assistent als Pilotprojekt für Handwerk, Praxen und Dienstleister. Antwort meist innerhalb von zwei Tagen."},
  "eyebrow": "Kontakt", "title": "Sprechen wir über Ihr Projekt.",
  "lead": "Buchen Sie einen kostenlosen 30-Minuten-Call oder schreiben Sie mir. Ich antworte meist innerhalb von zwei Tagen.",
  "infoTitle": "Direkt", "phoneL": "Telefon", "emailL": "E-Mail", "locationL": "Standort", "hoursL": "Zeiten", "hours": "Mo–Fr, 9:00–18:00 Uhr",
  "personal": "Sie erreichen mich direkt, kein Vertriebsteam. Gespräche auf Deutsch, Englisch, Französisch, Rumänisch oder Arabisch.",
  "nextTitle": "So geht es weiter",
  "steps": [
    {"t": "Ein 30-Minuten-Gespräch", "d": "Wir schauen, wo Anfragen verloren gehen: abends, samstags, wenn das Telefon klingelt, während Sie auf der Baustelle sind."},
    {"t": "Ein kurzes schriftliches Angebot", "d": "Umfang, Preis und was der Pilot abdeckt. Meist innerhalb von zwei Tagen."},
    {"t": "Pilot in etwa zwei Wochen live", "d": "Auf Ihrer eigenen Nummer und Website, in der Sprache Ihrer Anrufer."}
  ],
  "form": {
    "title": "Termin buchen", "serviceL": "Worum geht es?", "servicePh": "Leistung wählen",
    "services": ["n8n-Workflows", "SEO · AIO · GEO", "Django-Datenanalyse", "KI-Chatbots & Phone AI", "Etwas anderes"],
    "dateL": "Tag wählen", "timeL": "Uhrzeit wählen (MEZ)", "slots": ["09:00", "10:30", "12:00", "14:00", "15:30", "17:00"],
    "nameL": "Ihr Name", "emailL": "Ihre E-Mail", "msgL": "Eine Zeile zu Ihrem Projekt", "optional": "optional",
    "submit": "Diesen Termin anfragen",
    "hint": "Öffnet Ihr E-Mail-Programm mit der fertigen Anfrage. Gesendet wird erst, wenn Sie auf Senden klicken.",
    "missing": "Es fehlt noch:", "fieldDay": "ein Tag", "fieldTime": "eine Uhrzeit", "fieldName": "Ihr Name", "fieldEmail": "eine gültige E-Mail-Adresse",
    "locale": "de-DE"
  },
  "done": {
    "title": "Noch ein Schritt: auf Senden klicken.",
    "msg": "Ihr E-Mail-Programm sollte sich mit der Anfrage unten geöffnet haben. Falls nicht: Text kopieren und an contact@georgeai.dev schicken, oder per WhatsApp senden.",
    "copy": "Anfrage kopieren", "copied": "Kopiert", "openMail": "E-Mail erneut öffnen", "edit": "Etwas ändern"
  },
  "mail": {"subject": "Terminanfrage", "greeting": "Hallo George,", "slot": "Gewünschter Termin:", "service": "Leistung:", "name": "Name:", "email": "E-Mail:", "sign": "Viele Grüße,"}
}
```

- [ ] **Step 4: Write `templates/pages/contact.html`**

```html
{% extends "base.html" %}
{% block body_class %}page-contact{% endblock %}
{% block jsonld %}<script type="application/ld+json">
{{ jsonld_contact(page) | safe }}
</script>{% endblock %}
{% block content %}
<section class="contact wrap">
  <span class="eyebrow">{{ c.eyebrow }}</span>
  <h1 class="contact__title">{{ c.title }}</h1>
  <p class="lead contact__lead">{{ c.lead }}</p>

  <div class="contact__grid">
    <div class="contact__info">
      <div class="direct">
        <span class="eyebrow eyebrow--muted">{{ c.infoTitle }}</span>
        <a class="direct__item" href="{{ site.phoneHref }}"><span class="direct__label">{{ c.phoneL }}</span><span class="direct__value">{{ site.phone }}</span></a>
        <a class="direct__item" href="mailto:{{ site.email }}"><span class="direct__label">{{ c.emailL }}</span><span class="direct__value">{{ site.email }}</span></a>
        <div class="direct__item"><span class="direct__label">{{ c.locationL }}</span><span class="direct__value">{{ site.location[lang] }}</span></div>
        <div class="direct__item"><span class="direct__label">{{ c.hoursL }}</span><span class="direct__value">{{ c.hours }}</span></div>
        <a class="direct__wa" href="{{ site.whatsapp }}" target="_blank" rel="noopener"><span class="mark" aria-hidden="true"></span>WhatsApp</a>
      </div>
      <div class="next">
        <span class="eyebrow eyebrow--muted">{{ c.nextTitle }}</span>
        <ol class="steps">
          {% for s in c.steps %}
          <li class="step">
            <span class="step__n">{{ '%02d' % loop.index }}</span>
            <span><span class="step__t">{{ s.t }}</span><span class="step__d">{{ s.d }}</span></span>
          </li>
          {% endfor %}
        </ol>
        <p class="next__personal">{{ c.personal }}</p>
      </div>
    </div>

    <div class="card contact__card">
      <form class="booking" data-booking novalidate
            data-locale="{{ c.form.locale }}" data-missing="{{ c.form.missing }}"
            data-field-day="{{ c.form.fieldDay }}" data-field-time="{{ c.form.fieldTime }}"
            data-field-name="{{ c.form.fieldName }}" data-field-email="{{ c.form.fieldEmail }}"
            data-copy="{{ c.done.copy }}" data-copied="{{ c.done.copied }}"
            data-mail-subject="{{ c.mail.subject }}" data-mail-greeting="{{ c.mail.greeting }}" data-mail-slot="{{ c.mail.slot }}"
            data-mail-service="{{ c.mail.service }}" data-mail-name="{{ c.mail.name }}" data-mail-email="{{ c.mail.email }}" data-mail-sign="{{ c.mail.sign }}"
            data-email="{{ site.email }}" data-whatsapp="{{ site.whatsapp }}">
        <h2 class="booking__title">{{ c.form.title }}</h2>

        <label class="label" for="ga-ct-service">{{ c.form.serviceL }}</label>
        <select class="field" id="ga-ct-service" name="service">
          <option value="">{{ c.form.servicePh }}</option>
          {% for s in c.form.services %}<option value="{{ s }}">{{ s }}</option>{% endfor %}
        </select>

        <div class="group" role="group" aria-labelledby="ga-ct-dayL">
          <span class="label" id="ga-ct-dayL">{{ c.form.dateL }}</span>
          <div class="chips" data-booking-days></div>
        </div>
        <div class="group" role="group" aria-labelledby="ga-ct-timeL">
          <span class="label" id="ga-ct-timeL">{{ c.form.timeL }}</span>
          <div class="chips" data-booking-slots>
            {% for t in c.form.slots %}<button class="chip chip--slot" type="button" aria-pressed="false" data-slot="{{ t }}">{{ t }}</button>{% endfor %}
          </div>
        </div>

        <div class="booking__fields">
          <div><label class="label" for="ga-ct-name">{{ c.form.nameL }}</label><input class="field" id="ga-ct-name" name="name" type="text" autocomplete="name"></div>
          <div><label class="label" for="ga-ct-email">{{ c.form.emailL }}</label><input class="field" id="ga-ct-email" name="email" type="email" autocomplete="email" inputmode="email"></div>
        </div>
        <label class="label" for="ga-ct-msg">{{ c.form.msgL }} <span class="label__opt">({{ c.form.optional }})</span></label>
        <textarea class="field field--area" id="ga-ct-msg" name="message" rows="3"></textarea>

        <button class="btn btn--primary btn--block" type="submit">{{ c.form.submit }}</button>
        <p class="booking__error" role="alert" data-booking-error hidden></p>
        <p class="booking__hint">{{ c.form.hint }}</p>
      </form>

      <div class="booking__done" data-booking-done hidden>
        <img src="/logo-mark.png" alt="" width="28" height="28">
        <h2 class="booking__title" tabindex="-1">{{ c.done.title }}</h2>
        <p class="booking__summary" data-booking-summary></p>
        <p class="booking__hint">{{ c.done.msg }}</p>
        <pre class="booking__body" data-booking-body></pre>
        <div class="booking__actions">
          <button class="btn btn--secondary btn--small" type="button" data-booking-copy>{{ c.done.copy }}</button>
          <a class="btn btn--secondary btn--small" href="mailto:{{ site.email }}" data-booking-mail>{{ c.done.openMail }}</a>
          <a class="btn btn--secondary btn--small" href="{{ site.whatsapp }}" target="_blank" rel="noopener" data-booking-wa><span class="mark" aria-hidden="true"></span>WhatsApp</a>
        </div>
        <button class="linklike" type="button" data-booking-edit>{{ c.done.edit }}</button>
      </div>
    </div>
  </div>
</section>
{% endblock %}
```

- [ ] **Step 5: Write `assets/booking.js` and import it**

```js
export function booking() {
  const form = document.querySelector("form[data-booking]");
  if (!form) return;
  const d = form.dataset;
  const days = form.querySelector("[data-booking-days]");
  const slots = form.querySelector("[data-booking-slots]");
  const err = form.querySelector("[data-booking-error]");
  const done = form.parentElement.querySelector("[data-booking-done]");
  const fields = { service: form.querySelector("#ga-ct-service"), name: form.querySelector("#ga-ct-name"), email: form.querySelector("#ga-ct-email"), msg: form.querySelector("#ga-ct-msg") };
  const longDay = new Intl.DateTimeFormat(d.locale, { weekday: "long", day: "numeric", month: "long" });
  const state = { date: null, time: null };

  const key = (dt) => dt.getFullYear() + "-" + String(dt.getMonth() + 1).padStart(2, "0") + "-" + String(dt.getDate()).padStart(2, "0");
  const fromKey = (k) => { const p = k.split("-"); return new Date(+p[0], +p[1] - 1, +p[2]); };

  // next 10 weekdays, keyed by local date (never toISOString: it shifts a day east of UTC)
  const dt = new Date(); dt.setHours(0, 0, 0, 0);
  let added = 0, guard = 0;
  while (added < 10 && guard < 40) {
    dt.setDate(dt.getDate() + 1); guard++;
    if (dt.getDay() === 0 || dt.getDay() === 6) continue;
    const k = key(dt), copy = new Date(dt);
    const b = document.createElement("button");
    b.type = "button"; b.className = "chip chip--day"; b.dataset.day = k;
    b.setAttribute("aria-pressed", "false"); b.setAttribute("aria-label", longDay.format(copy));
    b.innerHTML = `<span class="chip__dn">${new Intl.DateTimeFormat(d.locale, { weekday: "short" }).format(copy)}</span>` +
      `<span class="chip__num">${new Intl.DateTimeFormat(d.locale, { day: "numeric" }).format(copy)}</span>` +
      `<span class="chip__mon">${new Intl.DateTimeFormat(d.locale, { month: "short" }).format(copy)}</span>`;
    days.appendChild(b); added++;
  }
  const press = (group, attr, value) => group.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset[attr] === value)));
  days.addEventListener("click", (e) => { const b = e.target.closest("[data-day]"); if (!b) return; state.date = b.dataset.day; press(days, "day", state.date); clear(); });
  slots.addEventListener("click", (e) => { const b = e.target.closest("[data-slot]"); if (!b) return; state.time = b.dataset.slot; press(slots, "slot", state.time); clear(); });
  Object.values(fields).forEach((f) => f.addEventListener("input", clear));

  function clear() { err.hidden = true; err.textContent = ""; }
  const emailOk = () => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(fields.email.value.trim());
  const when = () => (state.date ? longDay.format(fromKey(state.date)) + ", " : "") + (state.time || "");
  const body = () => [d.mailGreeting, "", d.mailSlot + " " + when(), d.mailService + " " + (fields.service.value || "-"),
    d.mailName + " " + fields.name.value.trim(), d.mailEmail + " " + fields.email.value.trim(),
    ...(fields.msg.value.trim() ? ["", fields.msg.value.trim()] : []), "", d.mailSign, fields.name.value.trim()].join("\n");
  const mailto = () => "mailto:" + d.email + "?subject=" + encodeURIComponent(d.mailSubject + ": " + when()) + "&body=" + encodeURIComponent(body());

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const missing = [];
    if (!state.date) missing.push(d.fieldDay);
    if (!state.time) missing.push(d.fieldTime);
    if (!fields.name.value.trim()) missing.push(d.fieldName);
    if (!emailOk()) missing.push(d.fieldEmail);
    if (missing.length) { err.textContent = d.missing + " " + missing.join(", "); err.hidden = false; return; }
    done.querySelector("[data-booking-summary]").textContent = when();
    done.querySelector("[data-booking-body]").textContent = body();
    done.querySelector("[data-booking-mail]").href = mailto();
    done.querySelector("[data-booking-wa]").href = d.whatsapp + "?text=" + encodeURIComponent(body());
    form.hidden = true; done.hidden = false;
    done.querySelector("h2").focus?.();
    try { window.location.href = mailto(); } catch (x) {}
  });
  done.querySelector("[data-booking-edit]").addEventListener("click", () => { done.hidden = true; form.hidden = false; fields.name.focus(); });
  const copyBtn = done.querySelector("[data-booking-copy]");
  copyBtn.addEventListener("click", () => {
    navigator.clipboard?.writeText(body()).then(() => { copyBtn.textContent = d.copied; setTimeout(() => { copyBtn.textContent = d.copy; }, 2200); }, () => {});
  });
}
```

In `assets/site.js`: `import { booking } from "./booking.js";` and call `booking();`. The done-state `<h2>` carries `tabindex="-1"` so `focus()` moves the reader to the confirmation.

- [ ] **Step 6: Contact styles**

Append to `assets/site.css`:

```css
/* contact */
.contact { padding-block: var(--heroY) var(--sectionY); }
.contact__title { margin-top: 18px; max-width: 740px; }
.contact__lead { margin-top: 22px; max-width: 540px; }
.contact__grid { display: grid; grid-template-columns: .8fr 1.2fr; gap: 48px; margin-top: 48px; align-items: start; }
.direct { display: flex; flex-direction: column; gap: 22px; }
.direct__item { display: block; text-decoration: none; color: inherit; align-self: flex-start; }
.direct__label { display: block; font-family: var(--mono); font-size: 11px; letter-spacing: 1px; text-transform: uppercase; color: var(--muted); }
.direct__value { display: block; font-size: 17px; color: var(--ink); margin-top: 4px; }
.direct__wa { display: inline-flex; align-items: center; gap: 8px; color: var(--accent); font-weight: 500; font-size: 15px; text-decoration: none; align-self: flex-start; }
.mark { width: 7px; height: 7px; background: var(--coral); clip-path: polygon(50% 0,61% 39%,100% 50%,61% 61%,50% 100%,39% 61%,0 50%,39% 39%); }
.next { margin-top: 44px; padding-top: 32px; border-top: 1px solid var(--hairline); }
.steps { list-style: none; margin: 6px 0 0; padding: 0; }
.step { display: grid; grid-template-columns: 34px 1fr; gap: 14px; padding: 18px 0; border-bottom: 1px solid var(--hairline); }
.step__n { font-family: var(--mono); font-size: 12px; color: var(--accent); padding-top: 3px; }
.step__t { display: block; font-size: 16px; font-weight: 500; color: var(--ink); line-height: 1.35; }
.step__d { display: block; font-size: 14px; line-height: 1.55; color: var(--muted); margin-top: 4px; max-width: 46ch; }
.next__personal { margin-top: 20px; font-size: 14px; max-width: 46ch; }
.contact__card { padding: 32px; }
.booking__title { font-size: 26px; letter-spacing: -.4px; margin-bottom: 22px; }
.label { display: block; font-family: var(--mono); font-size: 11px; letter-spacing: 1px; text-transform: uppercase; color: var(--muted); margin-bottom: 8px; }
.label__opt { text-transform: none; letter-spacing: 0; font-family: var(--sans); opacity: .8; }
.field { width: 100%; padding: 13px 14px; border-radius: var(--r-btn); border: 1px solid var(--cardBorder); background: var(--surface); color: var(--ink); font: inherit; font-size: 15px; line-height: 1.4; margin-bottom: 22px; }
.field--area { resize: vertical; min-height: 84px; margin-bottom: 18px; }
.field::placeholder { color: var(--muted); }
.group { margin-bottom: 22px; }
.group .label { margin-bottom: 10px; }
.chips { display: flex; gap: 8px; flex-wrap: wrap; }
.chip { cursor: pointer; border: 1px solid var(--cardBorder); background: var(--surface); color: var(--body); transition: background-color .15s ease, border-color .15s ease; }
.chip[aria-pressed="true"] { background: var(--accentBtn); color: #fff; border-color: var(--accentBtn); }
.chip[aria-pressed="false"]:hover { border-color: var(--accent); }
.chip--day { display: flex; flex-direction: column; align-items: center; gap: 2px; min-width: 62px; padding: 10px; border-radius: 10px; line-height: 1; }
.chip__dn, .chip__mon { font-family: var(--mono); font-size: 10px; text-transform: uppercase; opacity: .8; }
.chip__num { font-family: var(--display); font-size: 20px; line-height: 1.1; }
.chip--slot { padding: 11px 16px; border-radius: var(--r-pill); font-family: var(--mono); font-size: 14px; line-height: 1; }
.booking__fields { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px; }
.booking__fields .field { margin-bottom: 0; }
.booking__error { margin-top: 12px; font-size: 14px; color: var(--accent); }
.booking__hint { margin-top: 14px; font-size: 13px; line-height: 1.5; color: var(--muted); }
.booking__done img { margin-bottom: 18px; }
.booking__done h2 { margin-bottom: 0; }
.booking__summary { margin-top: 10px; color: var(--body); }
.booking__body { white-space: pre-wrap; font: inherit; font-size: 14px; line-height: 1.6; background: var(--surface); border: 1px solid var(--cardBorder); border-radius: 10px; padding: 16px 18px; margin: 20px 0 0; }
.booking__actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 16px; }
.linklike { background: none; border: 0; padding: 0; margin-top: 22px; color: var(--accent); cursor: pointer; text-decoration: underline; text-underline-offset: 3px; font-size: 14px; }
@media (max-width: 859px) {
  .contact__grid { grid-template-columns: 1fr; }
  .contact__card { order: -1; }
}
@media (max-width: 559px) { .contact__card { padding: 22px 18px; } .booking__fields { grid-template-columns: 1fr; } }
```

- [ ] **Step 7: Run the tests**

Run: `python3 -m pytest tests/test_build.py -v`
Expected: 13 passed

- [ ] **Step 8: Build and try the flow**

Serve `site/` as in Task 5 and open `/en/contact/`: submitting empty shows "Still needed: a day, a time, your name, a valid email"; pick a day and time by keyboard (Tab + Space), fill name and email, submit: the done panel shows the local date matching the chip, the composed body, and three fallback buttons; "Change something" returns with values kept. `/kontakt/` shows the German copy. At 390px the form card comes first.

- [ ] **Step 9: Commit**

```bash
git add build.py content templates assets tests/test_build.py
git commit -m "Add the contact page with the accessible booking form and honest mail handoff

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Browser test suite (Playwright + axe)

**Files:**
- Create: `tests/browser/check_pages.mjs`
- Create: `tests/browser/package.json`
- Create: `tests/test_browser.py`

**Interfaces:**
- Consumes: the built `site/` directory, hooks from Tasks 4 to 6.
- Produces: `node tests/browser/check_pages.mjs <baseUrl>` exits non-zero on any failure and prints one line per check; `tests/test_browser.py::test_browser_suite` builds, serves and runs it.

- [ ] **Step 1: Set up the Node side**

`tests/browser/package.json`:

```json
{ "name": "georgeai-browser-tests", "private": true, "type": "module", "dependencies": { "playwright": "^1.63.0", "axe-core": "^4.10.0" } }
```

```bash
(cd tests/browser && npm install --no-audit --no-fund && npx playwright install chromium)
```
Expected: `node_modules` inside `tests/browser` (add `tests/browser/node_modules/` to `.gitignore`).

- [ ] **Step 2: Write `tests/browser/check_pages.mjs`**

```js
import { chromium } from "playwright";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const axeSource = require("axe-core").source;

const base = process.argv[2] || "http://127.0.0.1:8765";
const pages = ["/", "/en/", "/kontakt/", "/en/contact/"];
// links to pages that only exist after Phase 2 are tolerated for now
const allowMissing = [/^\/(en\/)?(leistungen|services|projekte|work|blog|preise|pricing|ueber-mich|about|konfigurator|configurator|impressum|datenschutz|agb|cookies|legal)\b/];
let failures = 0;
const check = (ok, msg) => { console.log((ok ? "ok   " : "FAIL ") + msg); if (!ok) failures++; };

const browser = await chromium.launch();
for (const theme of ["light", "dark"]) {
  for (const width of [1280, 390]) {
    const ctx = await browser.newContext({ viewport: { width, height: 900 }, timezoneId: "Europe/Berlin" });
    await ctx.addInitScript((t) => localStorage.setItem("ga_theme", t), theme);
    for (const path of pages) {
      const page = await ctx.newPage();
      const errors = [];
      page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
      page.on("pageerror", (e) => errors.push(e.message));
      const resp = await page.goto(base + path, { waitUntil: "networkidle" });
      const tag = `${path} ${theme} ${width}px`;
      check(resp.status() === 200, `${tag}: status 200`);
      check(errors.length === 0, `${tag}: no console errors ${errors.join(" | ")}`);
      check(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), `${tag}: no horizontal overflow`);
      check((await page.locator("h1").count()) === 1, `${tag}: one h1`);
      check(await page.evaluate(() => document.documentElement.getAttribute("data-theme") === localStorage.getItem("ga_theme")), `${tag}: theme applied`);
      const hrefs = await page.locator('a[href^="/"]').evaluateAll((as) => [...new Set(as.map((a) => a.getAttribute("href")))]);
      for (const h of hrefs) {
        const r = await ctx.request.get(base + h);
        const tolerated = allowMissing.some((re) => re.test(h));
        check(r.status() === 200 || tolerated, `${tag}: link ${h} -> ${r.status()}`);
      }
      const alt = await page.locator('link[rel="alternate"]').evaluateAll((ls) => ls.map((l) => l.getAttribute("hreflang")));
      check(alt.includes("de") && alt.includes("en") && alt.includes("x-default"), `${tag}: hreflang de/en/x-default`);
      await page.keyboard.press("Tab");
      check(await page.evaluate(() => { const el = document.activeElement; return el && el !== document.body && getComputedStyle(el).outlineStyle !== "none"; }), `${tag}: first Tab lands on a visibly focused element`);
      await page.addScriptTag({ content: axeSource });
      const axe = await page.evaluate(async () => (await window.axe.run(document, { runOnly: ["wcag2a", "wcag2aa"] })).violations.filter((v) => ["serious", "critical"].includes(v.impact)).map((v) => v.id + ":" + v.nodes.length));
      check(axe.length === 0, `${tag}: axe serious/critical ${axe.join(",")}`);
      await page.close();
    }
    await ctx.close();
  }
}

// flows (light, desktop)
const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, timezoneId: "Europe/Berlin" });
const page = await ctx.newPage();
await page.goto(base + "/en/", { waitUntil: "networkidle" });
await page.locator("[data-theme-toggle]").click();
await page.reload({ waitUntil: "networkidle" });
check(await page.evaluate(() => document.documentElement.getAttribute("data-theme") === "dark"), "theme toggle persists across reload");
const second = page.locator("[data-panel] .panel__hit").nth(1);
await second.focus(); await page.keyboard.press("Enter");
check((await second.getAttribute("aria-pressed")) === "true", "hero panel activates by keyboard");
await page.setViewportSize({ width: 390, height: 844 });
await page.locator("[data-menu-toggle]").click();
check(await page.locator("#site-menu").isVisible(), "mobile menu opens");
await page.keyboard.press("Escape");
check(!(await page.locator("#site-menu").isVisible()), "mobile menu closes on Escape");
await page.setViewportSize({ width: 1280, height: 900 });
await page.goto(base + "/en/contact/", { waitUntil: "networkidle" });
await page.locator('form[data-booking] button[type="submit"]').click();
check((await page.locator("[data-booking-error]").textContent()).startsWith("Still needed:"), "empty submit shows the alert");
const firstDay = page.locator("[data-booking-days] button").first();
await firstDay.focus(); await page.keyboard.press("Space");
await page.locator("[data-booking-slots] button").nth(2).click();
await page.fill("#ga-ct-name", "Max Mustermann"); await page.fill("#ga-ct-email", "max@example.de");
const label = await firstDay.getAttribute("aria-label");
await page.locator('form[data-booking] button[type="submit"]').click();
const summary = await page.locator("[data-booking-summary]").textContent();
check(summary.includes(label) && summary.includes("12:00"), `booking summary matches the chip (${summary})`);
check((await page.locator("[data-booking-body]").textContent()).includes("max@example.de"), "mail body carries the email");
check((await page.locator("[data-booking-mail]").getAttribute("href")).includes("subject="), "mailto link carries the subject");
await page.locator("[data-booking-edit]").click();
check((await page.inputValue("#ga-ct-name")) === "Max Mustermann", "edit keeps the values");
await browser.close();
console.log(failures ? `\n${failures} failure(s)` : "\nall checks passed");
process.exit(failures ? 1 : 0);
```

- [ ] **Step 3: Write `tests/test_browser.py`**

```python
import http.server
import socketserver
import subprocess
import threading
from pathlib import Path

import pytest

import build

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.browser
def test_browser_suite(tmp_path):
    out = tmp_path / "site"
    build.build(out)
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(out), **k)
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as srv:
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            proc = subprocess.run(["node", str(ROOT / "tests" / "browser" / "check_pages.mjs"), f"http://127.0.0.1:{port}"],
                                  capture_output=True, text=True, timeout=600)
        finally:
            srv.shutdown()
    print(proc.stdout)
    assert proc.returncode == 0, proc.stdout + proc.stderr
```

Register the marker in a new `pytest.ini` at the repo root:

```ini
[pytest]
markers =
    browser: needs node, Playwright and Chromium
testpaths = tests
```

- [ ] **Step 4: Run the suite**

Run: `python3 -m pytest tests/test_browser.py -v -s`
Expected: PASS with every line prefixed `ok`. If `axe` reports a violation, fix the template or CSS (typical: colour contrast of `--muted` on `--surface` in dark; raise the token only inside the offending component, never globally, and re-run).

- [ ] **Step 5: Commit**

```bash
git add tests pytest.ini .gitignore
git commit -m "Add the browser test suite: overflow, links, hreflang, focus, axe and the booking flow

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Impeccable pass on the two pages and a README section

**Files:**
- Modify: `assets/site.css`, templates, content (only what the review finds)
- Modify: `README.md` (new "Building the site" section)

- [ ] **Step 1: Run the Impeccable review on the built pages**

Serve `site/` and run, in this order, reading each command reference from `~/.claude/skills/impeccable/reference/`:

1. `$impeccable critique /en/ and /en/contact/` — UX review with heuristic scores; list findings.
2. `$impeccable audit /en/ and /en/contact/` — a11y, performance, responsive checks beyond the automated suite.
3. `$impeccable polish` — apply the fixes that the two reviews surfaced.

Every fix goes into `assets/site.css`, the templates or the JSON content, never into `site/`. Re-run `python3 -m pytest` (both files) after the changes.

- [ ] **Step 2: Document the build**

Append to `README.md`:

```markdown
## Building the site (new generator)

    python3 -m pip install -r requirements-site.txt
    python3 build.py              # content/ + templates/ -> site/
    python3 -m pytest             # everything; add -m 'not browser' to skip the Playwright suite

Content lives in `content/` (JSON per page and language, `site.json` for shared data). Templates in `templates/`, styles in `assets/site.css`, behaviour in `assets/site.js`. `site/` is generated and gitignored. German pages marked `"_status": "draft"` are counted at the end of every build.
```

- [ ] **Step 3: Commit**

```bash
git add -A assets templates content README.md
git commit -m "Polish the home and contact pages after the Impeccable review and document the build

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Self-review against the spec

- **Section 3 (layout):** Tasks 1 to 4 create `build.py`, `content/`, `templates/`, `assets/`, `tests/`. `frontend/template/` mirroring and retiring `seo/` are Phase 3.
- **Section 4 (URLs):** `SECTIONS`/`page_path` in Task 1 encode every slug in the spec table; `hreflang` and `x-default` in Task 2; language switch to the pair in Task 4. 301s are Phase 3.
- **Section 5 (pages):** home and contact here; the remaining page types and German drafts are Phase 2. Copy rules enforced by the forbidden-pattern test (em dash) and by the content itself (no "48 hours").
- **Section 6 (design):** tokens verbatim in Task 3 (tested), no inline styles (tested), components in Tasks 4 to 6, `prefers-reduced-motion` in Task 3, FAQ as `<details>`, cookie banner fixed at the bottom and only with an analytics id, newsletter absent.
- **Section 7 (JS):** `theme`, `menu`, `cookie` (Task 4), `hero` (Task 5), `booking` (Task 6). Configurator is Phase 2. Theme bootstrap is an external classic script, CSP-clean without a nonce (open item 1 resolved). `auth.js` untouched, stable ids provided.
- **Section 8 (tests):** determinism, validation, hreflang, sitemap/robots/llms, forbidden patterns (Task 2); browser checks and flows (Task 7). The URL-inventory test against the old sitemap belongs to Phase 3 with the 301s.
- **Placeholders:** none; every step has its content. **Names:** `page_path`, `inventory`, `render_page`, `build`, `BuildReport`, hooks `data-booking*`, `data-hero-panels`, `[data-theme-toggle]`, `#site-menu` are used consistently across tasks.
