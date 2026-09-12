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
