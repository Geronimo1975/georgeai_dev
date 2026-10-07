#!/usr/bin/env python3
"""Inject the repo-owned Impressum identity block into the design-tool export.

site/legal-data.js ships from the export with [bracketed] placeholders for the
street, ZIP and VAT number, and site/ is wiped and regenerated on every deploy —
so filling them in inside site/ is lost at the next re-export. seo/legal.json is
the source of truth and this script re-applies it on every deploy.

Per language it replaces, inside the `imprint` object:
  sub          -> the statutory-basis subtitle (the export still says § 5 TMG,
                  repealed and replaced by the DDG in May 2024)
  sections[0]  -> the provider block (name / street / ZIP + city / country)
  sections[2]  -> the VAT line (a real USt-IdNr., or the § 19 UStG note)

Exit codes: 0 patched, 2 not configured yet (nothing written — the placeholders
stay, which is honest), 1 the export changed shape and the patch was refused.
Nothing is written unless every edit succeeds, so a bad patch cannot ship a
half-modified Impressum.

Usage: apply_legal.py SITE_DIR SEO_DIR
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

LANGS = ("en", "de", "fr", "ro", "ar")
PROVIDER_INDEX = 0
VAT_INDEX = 2


class PatchError(Exception):
    pass


def js_string(value: str) -> str:
    """Encode a Python string as a JS double-quoted literal (\\n stays escaped)."""
    return json.dumps(value, ensure_ascii=False)


def imprint_block(js: str, lang: str) -> tuple[int, int]:
    """Byte range of one language's `imprint: { ... }` object inside docs."""
    anchor = re.search(r"\n    %s: \{\n      imprint: \{" % re.escape(lang), js)
    if not anchor:
        raise PatchError(f"{lang}: imprint block not found")
    start = anchor.end() - len("imprint: {")
    depth, i = 0, js.index("{", start)
    for j in range(i, len(js)):
        if js[j] == "{":
            depth += 1
        elif js[j] == "}":
            depth -= 1
            if depth == 0:
                return start, j + 1
    raise PatchError(f"{lang}: imprint block is unbalanced")


def replace_sub(block: str, lang: str, sub: str) -> str:
    out, n = re.subn(r'(\bsub: )"(?:[^"\\]|\\.)*"', lambda m: m.group(1) + js_string(sub),
                     block, count=1)
    if n != 1:
        raise PatchError(f"{lang}: imprint `sub` not found")
    return out


def replace_section_p(block: str, lang: str, index: int, text: str) -> str:
    """Replace the `p:` value of the index-th `{ h: ..., p: ... }` section."""
    sections = list(re.finditer(r'\{ h: "(?:[^"\\]|\\.)*", p: ("(?:[^"\\]|\\.)*")', block))
    if len(sections) <= index:
        raise PatchError(f"{lang}: imprint has {len(sections)} sections, needed index {index}")
    span = sections[index].span(1)
    return block[:span[0]] + js_string(text) + block[span[1]:]


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 1
    site_dir, seo_dir = Path(sys.argv[1]), Path(sys.argv[2])
    target = site_dir / "legal-data.js"
    config_file = seo_dir / "legal.json"

    if not target.exists() or not config_file.exists():
        print(f"legal layer: {target if not target.exists() else config_file} missing — skipped")
        return 2

    cfg = json.loads(config_file.read_text(encoding="utf-8"))
    identity = cfg.get("identity", {})
    vat = cfg.get("vat", {})
    street, zip_code = identity.get("street", "").strip(), identity.get("zip", "").strip()
    mode = vat.get("mode", "").strip()
    vat_id = vat.get("id", "").strip()

    missing = [n for n, v in (("identity.street", street), ("identity.zip", zip_code),
                              ("vat.mode", mode)) if not v]
    if mode == "vat_id" and not vat_id:
        missing.append("vat.id")
    if missing:
        print("legal layer: NOT APPLIED — seo/legal.json is missing " + ", ".join(missing) + ".\n"
              "             The export's [bracketed] Impressum placeholders stay live.\n"
              "             A placeholder Impressum is a § 5 DDG defect: fix this before\n"
              "             the site takes real money.", file=sys.stderr)
        return 2
    if mode not in ("vat_id", "kleinunternehmer"):
        print(f"legal layer: vat.mode {mode!r} is not 'vat_id' or 'kleinunternehmer'", file=sys.stderr)
        return 1

    js = original = target.read_text(encoding="utf-8")
    try:
        for lang in LANGS:
            copy = cfg["langs"][lang]
            fields = {"street": street, "zip": zip_code,
                      "city": copy.get("city", identity.get("city", "")), "vat_id": vat_id,
                      "steuernummer": identity.get("steuernummer", "").strip()}
            start, end = imprint_block(js, lang)
            block = js[start:end]
            block = replace_sub(block, lang, copy["sub"])
            block = replace_section_p(block, lang, PROVIDER_INDEX, copy["provider"].format(**fields))
            vat_text = copy[mode].format(**fields)
            if fields["steuernummer"]:
                # § 5 DDG asks for the USt-IdNr., not the Steuernummer — this line is
                # optional, and clearing identity.steuernummer drops it everywhere.
                vat_text += "\n" + copy["steuernummer"].format(**fields)
            block = replace_section_p(block, lang, VAT_INDEX, vat_text)
            # every [bracketed] placeholder in this imprint must now be gone
            leftovers = re.findall(r"\[[^\]\"]{3,}\]", block)
            if leftovers:
                raise PatchError(f"{lang}: placeholders remain in the Impressum: {leftovers}")
            js = js[:start] + block + js[end:]
    except (PatchError, KeyError) as exc:
        print(f"legal layer: refused to patch — {exc} (nothing written)", file=sys.stderr)
        return 1

    if js != original:
        target.write_text(js, encoding="utf-8")
    print(f"legal layer: Impressum identity applied in {len(LANGS)} languages ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
