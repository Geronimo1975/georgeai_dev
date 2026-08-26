#!/usr/bin/env python3
"""Contrast floors for the hero canvas.

The hero field draws its text with globalAlpha over the page ground, so the
effective contrast is not visible in any colour token — it only exists once
the alpha is composited. This suite recomputes that composite from the alpha
expressions in hero-cinema.js (the designed base/slope coefficients, plus the
runtime WCAG lift rule) and asserts the result clears WCAG AA.

This is NOT a test of the shipped JS: it does not execute parseColor,
relLum, contrastAt or minAlphaFor from hero-cinema.js. It reimplements the
same maths in Python and recomputes the design (designed alpha + lift rule)
against the real palettes, so it proves the RULE clears the floor for the
colours that are actually deployed — it does not prove the JS implementation
of that rule is bug-free. node --check plus manual/visual verification cover
that side.

Stdlib only, exit 0/1, same contract as tests/test_payments_pipeline.py.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "hero" / "hero-cinema.js"
PALETTE_PATH = ROOT / "brand" / "palette.json"

# These mirror the `colors` fallback object in hero/hero-cinema.js, which are
# the export's own cream palette. readColors() normally overrides them, but they
# matter for the first frame before the export has painted. They must stay in
# step with hero-cinema.js; if they drift, the test will silently measure
# contrast for a color nothing paints — worse than failing.
FALLBACK_GROUND = "#141413"
FALLBACK_INK = "#f5f2ec"
FALLBACK_BODY = "#a8a29a"

FALLBACK_PALETTE = {"ink": FALLBACK_INK, "body": FALLBACK_BODY}


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def composite(fg_hex, alpha, bg_hex):
    """Flatten fg at `alpha` over bg, the way canvas globalAlpha does."""
    fg, bg = _rgb(fg_hex), _rgb(bg_hex)
    out = tuple(round(alpha * f + (1 - alpha) * b) for f, b in zip(fg, bg))
    return "#%02x%02x%02x" % out


def _lum(h):
    def chan(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(c) for c in _rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def contrast_at_alpha(fg_hex, alpha, bg_hex):
    return contrast(composite(fg_hex, alpha, bg_hex), bg_hex)


def min_alpha_for(fg_hex, bg_hex, target):
    """Mirrors minAlphaFor() in hero-cinema.js: binary search the smallest
    alpha that clears `target`, or 1 if even opaque cannot reach it."""
    if contrast_at_alpha(fg_hex, 1.0, bg_hex) < target:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(24):
        mid = (lo + hi) / 2
        if contrast_at_alpha(fg_hex, mid, bg_hex) >= target:
            hi = mid
        else:
            lo = mid
    return hi


def alpha_at(base, slope, z):
    return base + slope * z


SRC_TEXT = SRC.read_text(encoding="utf-8")


def find_alpha(label, pattern, palette_tokens):
    """Pull (base, slope, color_token) out of a
    `Math.min(1, k * (BASE + SLOPE * n.z) + xLift * k)` expression."""
    m = re.search(pattern, SRC_TEXT)
    if not m:
        raise AssertionError(
            "%s: could not find the alpha expression in %s. If the line was "
            "reworded, update the pattern here rather than deleting the check."
            % (label, SRC.name)
        )
    base = float(m.group(1))
    slope = float(m.group(2))
    token = m.group(3)

    if token not in palette_tokens:
        raise AssertionError(
            "%s: unknown color token 'colors.%s' in %s. Update the palette or "
            "the pattern if the source changed."
            % (label, token, SRC.name)
        )

    return base, slope, token


def find_float_const(name):
    m = re.search(r"var %s = ([\d.]+);" % re.escape(name), SRC_TEXT)
    if not m:
        raise AssertionError(
            "could not find `var %s = ...;` in %s — the test parses this "
            "rather than hardcoding it, so it fails loudly if the target "
            "changes instead of silently passing against a stale value."
            % (name, SRC.name)
        )
    return float(m.group(1))


def find_min_z():
    """MIN_Z is derived in the source from NODES' own z values
    (`NODES.reduce(...Math.min...)`), not hardcoded — pull every node's z out
    of the NODES literal and take the min, the same derivation the source
    performs, so the test tracks a changed node depth instead of a stale
    constant."""
    if not re.search(r"var MIN_Z = NODES\.reduce\(", SRC_TEXT):
        raise AssertionError(
            "MIN_Z is no longer derived from NODES via .reduce(...) in %s — "
            "update find_min_z() to match the new derivation." % SRC.name
        )
    zs = [float(z) for z in re.findall(r"z:\s*([\d.]+)", SRC_TEXT)]
    if not zs:
        raise AssertionError("found no `z: <num>` node entries in %s" % SRC.name)
    return min(zs)


AA_RATIO = find_float_const("AA_RATIO")
MIN_Z = find_min_z()

# sub-label: the only draw inside `if (n.sub)`. Anchored there so a bare
# search cannot pick up the label's own alpha expression instead.
SUB_BASE, SUB_SLOPE, SUB_TOKEN = find_alpha(
    "sub-label",
    r"if \(n\.sub\) \{\s*\n\s*"
    r"ctx\.globalAlpha = Math\.min\(1, k \* \(([\d.]+) \+ ([\d.]+) \* n\.z\) \+ subLift \* k\);\s*\n\s*"
    r"ctx\.fillStyle = colors\.(\w+);",
    {"ink", "body"},
)

# label: anchored on the `'600 '` font weight, which only the label sets.
LABEL_BASE, LABEL_SLOPE, LABEL_TOKEN = find_alpha(
    "label",
    r"ctx\.globalAlpha = Math\.min\(1, k \* \(([\d.]+) \+ ([\d.]+) \* n\.z\) \+ labelLift \* k\);\s*\n\s*"
    r"ctx\.fillStyle = colors\.(\w+);\s*\n\s*ctx\.font = '600 '",
    {"ink", "body"},
)


def check(label, fg_hex, bg_hex, base, slope):
    """Recompute lift = max(0, requiredAlpha - designedAlphaAtMIN_Z), then
    the composited contrast at MIN_Z (the dimmest, and therefore tightest,
    depth plane) with that lift applied — mirroring readColors()'s lift
    computation and drawGraph's `Math.min(1, k * designed + lift * k)` at
    k=1."""
    designed_at_min_z = alpha_at(base, slope, MIN_Z)
    required = min_alpha_for(fg_hex, bg_hex, AA_RATIO)
    lift = max(0.0, required - designed_at_min_z)
    alpha = min(1.0, designed_at_min_z + lift)
    ratio = contrast_at_alpha(fg_hex, alpha, bg_hex)
    ok = ratio >= AA_RATIO
    print(
        "%-24s alpha=%.3f (lift=%.3f) contrast=%.2f:1 %s"
        % (label, alpha, lift, ratio, "OK" if ok else "FAIL")
    )
    return ok


def check_theme(theme_label, ground, ink, body):
    tokens = {"ink": ink, "body": body}
    results = []
    results.append(check("%s sub-label" % theme_label, tokens[SUB_TOKEN], ground, SUB_BASE, SUB_SLOPE))
    results.append(check("%s label" % theme_label, tokens[LABEL_TOKEN], ground, LABEL_BASE, LABEL_SLOPE))
    return results


def main():
    results = []

    # The export's own fallback palette — what paints before readColors() has
    # sampled anything real, and what the original version of this suite
    # checked exclusively.
    results += check_theme("export-fallback", FALLBACK_GROUND, FALLBACK_INK, FALLBACK_BODY)

    # The real deployed palettes. The lift exists precisely because the export
    # fallback alone does not prove the floor holds once the canvas is
    # sampling brand/palette.json's light theme.
    palette = json.loads(PALETTE_PATH.read_text(encoding="utf-8"))
    for theme in ("dark", "light"):
        p = palette[theme]
        results += check_theme(theme, p["canvas"], p["ink"], p["body"])

    if all(results):
        print("\nhero contrast: all floors clear")
        return 0
    print("\nhero contrast: below the %.1f:1 floor" % AA_RATIO)
    return 1


if __name__ == "__main__":
    sys.exit(main())
