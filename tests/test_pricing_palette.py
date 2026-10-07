#!/usr/bin/env python3
"""Palette + contrast floors for pages/pricing/index.html.

WHY THIS FILE EXISTS. deploy.sh runs apply_pages (which copies pages/pricing/
verbatim) AFTER apply_brand, so the brand layer never reaches the pricing page
— its :root is maintained by hand. That makes it the one page on the site that
can silently drift back to a palette nothing else uses, on the page where money
changes hands. This suite is the guard: it re-reads brand/palette.json and
fails if the hand-maintained copy no longer matches it.

It also recomputes WCAG contrast for every pair the page actually paints,
including the two traps recorded in palette.json:
  * a white label on the accent fill is 3.11:1 and fails,
  * light-theme #c2410c passes on white and fails on --surface.

Stdlib only, exit 0/1 — same contract as tests/test_payments_pipeline.py.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "pages" / "pricing" / "index.html"
PALETTE = ROOT / "brand" / "palette.json"

AA = 4.5


def rel_lum(hex_colour):
    h = hex_colour.lstrip("#")
    parts = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    parts = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in parts]
    return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]


def contrast(a, b):
    hi, lo = sorted((rel_lum(a), rel_lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def read_root_vars(html):
    """The :root block only — not the whole file, which also carries the dark
    .after band's literals."""
    block = re.search(r":root\{(.*?)\}", html, re.S)
    if not block:
        return {}
    return dict(re.findall(r"--([a-z-]+)\s*:\s*([^;]+?)\s*(?:;|$)", block.group(1)))


def main():
    for path in (PAGE, PALETTE):
        if not path.is_file():
            print(f"FAIL  missing {path.relative_to(ROOT)}")
            return 1

    html = PAGE.read_text(encoding="utf-8")
    light = json.loads(PALETTE.read_text(encoding="utf-8"))["light"]
    css = read_root_vars(html)
    failures = []

    # 1. The hand-maintained :root must still agree with palette.json. Only the
    #    roles the page actually uses are mapped; --faint is deliberately NOT
    #    palette.json's muted-equivalent for dark, it is a second reference to
    #    light's muted because the old #8e8b82 was failing body text at 3.4:1.
    expected = {
        "cream": light["canvas"],
        "card": light["card"],
        "ink": light["ink"],
        "body": light["body"],
        "muted": light["muted"],
        "faint": light["muted"],
        "line": light["cardBorder"],
        "line-soft": light["hairline"],
        "accent": light["accentBtn"],
        "accent-ink": light["accent"],
        "dark": light["ink"],
    }
    for name, want in expected.items():
        got = css.get(name, "").lower()
        if got != want.lower():
            failures.append(f"--{name} is {got or '<missing>'}, palette.json says {want}")

    # 2. Every pair the page paints, against the AA floor.
    canvas, card = light["canvas"], light["card"]
    pairs = [
        ("ink on canvas", light["ink"], canvas),
        ("body on canvas", light["body"], canvas),
        ("muted on canvas", light["muted"], canvas),
        ("accent text on canvas", light["accent"], canvas),
        ("accent text on card", light["accent"], card),
        ("button label on accent fill", light["ink"], light["accentBtn"]),
    ]
    for label, fg, bg in pairs:
        ratio = contrast(fg, bg)
        mark = "ok  " if ratio >= AA else "FAIL"
        print(f"{mark}  {label:30} {ratio:5.2f}:1")
        if ratio < AA:
            failures.append(f"{label} is {ratio:.2f}:1, below {AA}")

    # 3. The two recorded traps must stay traps — if either starts passing, the
    #    palette moved and the reasoning in palette.json needs rereading.
    white_on_fill = contrast("#ffffff", light["accentBtn"])
    if white_on_fill >= AA:
        failures.append(
            f"white on accent fill is now {white_on_fill:.2f}:1 — palette.json "
            "records it as failing at 3.11:1; re-check before trusting it")
    c2410c_on_surface = contrast("#c2410c", light["surface"])
    if c2410c_on_surface >= AA:
        failures.append(
            f"#c2410c on --surface is now {c2410c_on_surface:.2f}:1 — palette.json "
            "records it as failing at 4.23:1; re-check before trusting it")

    # 4. No remote font request: the same faces are vendored in seo/vendor/.
    if "fonts.googleapis.com" in html:
        failures.append("pricing page still requests fonts from Google")
    for var in ("mono", "sans", "serif"):
        if "Plus Jakarta Sans" not in css.get(var, ""):
            failures.append(f"--{var} does not resolve to Plus Jakarta Sans")

    if failures:
        print("\n" + "\n".join("FAIL  " + f for f in failures))
        return 1
    print("\nOK    pricing palette matches brand/palette.json and clears WCAG AA")
    return 0


if __name__ == "__main__":
    sys.exit(main())
