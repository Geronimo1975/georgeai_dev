#!/usr/bin/env python3
"""Build georgeai.dev: content/ + templates/ -> site/.

Usage: python3 build.py [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from jinja2.exceptions import UndefinedError

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
    "home": ["meta.title", "meta.description", "hero.eyebrow", "hero.title", "hero.sub", "hero.cta1", "hero.cta2",
             "hero.panels", "how.eyebrow", "how.title", "how.sub", "how.cards", "work.title", "work.all", "work.items",
             "services.eyebrow", "services.title", "services.lead", "services.all", "services.items",
             "faq.eyebrow", "faq.title", "faq.items", "cta.title", "cta.sub", "cta.btn"],
    "contact": ["meta.title", "meta.description", "eyebrow", "title", "lead", "infoTitle", "phoneL", "emailL",
                "locationL", "hoursL", "hours", "personal", "nextTitle", "steps", "form", "done", "mail"],
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


@dataclass
class BuildReport:
    pages: dict[str, int]
    drafts: dict[str, int]


def _env(root: Path) -> Environment:
    env = Environment(loader=FileSystemLoader(str(root / "templates")), undefined=StrictUndefined,
                      autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)
    return env


def _nav(site: dict, lang: str) -> list[dict]:
    labels = site["ui"][lang]["nav"]
    order = ("services", "work", "about", "blog", "contact")
    return [{"key": k, "label": labels[k], "href": page_path(lang, k)} for k in order]


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


def jsonld_faq(items: list[dict]) -> str:
    data = {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": it["q"],
                            "acceptedAnswer": {"@type": "Answer", "text": it["a"]}} for it in items]}
    return json.dumps(data, ensure_ascii=False, indent=1)


def jsonld_contact(page: Page) -> str:
    data = {"@context": "https://schema.org", "@type": "ContactPage", "url": DOMAIN + page.path,
            "name": _get(page.content, "meta.title"), "about": {"@id": f"{DOMAIN}/#person"}}
    return json.dumps(data, ensure_ascii=False, indent=1)


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
        jsonld_site=jsonld_site(site, page.lang), build_year=date.today().year,
        jsonld_faq=jsonld_faq, jsonld_contact=jsonld_contact,
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
    for name in ("favicon.svg", "favicon.ico", "favicon-32.png", "apple-touch-icon.png", "logo-mark.png", "logo-mark-ink.png",
                 "logo-512.png"):
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
        try:
            html = render_page(env, p, pages)
        except UndefinedError as exc:
            raise ContentError(f"{p.lang}/{p.key}: {exc}") from exc
        target.write_text(html, encoding="utf-8")
    copy_assets(ROOT, out)
    write_sitemap(pages, out)
    write_robots(out)
    write_llms(pages, out)
    return BuildReport(
        pages={lang: sum(1 for p in pages if p.lang == lang) for lang in LANGS},
        drafts={lang: sum(1 for p in pages if p.lang == lang and p.draft) for lang in LANGS},
    )


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
        report = build(Path(args.out))
    except ContentError as exc:
        sys.stderr.write(f"build: {exc}\n")
        return 1
    for lang in LANGS:
        sys.stderr.write(f"build: {lang}: {report.pages[lang]} pages, {report.drafts[lang]} draft\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
