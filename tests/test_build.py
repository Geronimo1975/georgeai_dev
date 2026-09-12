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
