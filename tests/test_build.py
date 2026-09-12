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
