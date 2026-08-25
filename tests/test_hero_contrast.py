#!/usr/bin/env python3
"""Contrast floors for the hero canvas.

The hero field draws its text with globalAlpha over the page ground, so the
effective contrast is not visible in any colour token — it only exists once
the alpha is composited. This suite recomputes that composite from the alpha
expressions in hero-cinema.js and asserts the result clears WCAG AA.

Stdlib only, exit 0/1, same contract as tests/test_payments_pipeline.py.
"""
import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "hero" / "hero-cinema.js"

GROUND = "#141413"
INK = "#f5f2ec"
BODY = "#a8a29a"  # kept for reference; the sub-line moved to ink

# The near-plane depth. Nodes sit between z=0.66 and z=1.0; the floor has to
# hold at the dimmest of them, which is the 0.66 plane.
NEAR_Z = 0.66

FLOOR = 4.5


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


def alpha_at(base, slope, z):
    return base + slope * z


def find_alpha(label, pattern):
    """Pull (base, slope) out of a `k * (BASE + SLOPE * n.z)` expression."""
    src = SRC.read_text(encoding="utf-8")
    m = re.search(pattern, src)
    if not m:
        raise AssertionError(
            "%s: could not find the alpha expression in %s. If the line was "
            "reworded, update the pattern here rather than deleting the check."
            % (label, SRC.name)
        )
    return float(m.group(1)), float(m.group(2))


def check(label, fg, base, slope):
    a = alpha_at(base, slope, NEAR_Z)
    ratio = contrast(composite(fg, a, GROUND), GROUND)
    ok = ratio >= FLOOR
    print("%-14s alpha=%.3f contrast=%.2f:1 %s" % (label, a, ratio, "OK" if ok else "FAIL"))
    return ok


def main():
    results = []

    # The sub-line is the only draw inside `if (n.sub)`, which is what anchors
    # it. It is drawn in ink, same as the label, so a colour-based anchor would
    # be ambiguous.
    base, slope = find_alpha(
        "sub-label",
        r"if \(n\.sub\) \{\s*\n\s*ctx\.globalAlpha = k \* \(([\d.]+) \+ ([\d.]+) \* n\.z\);")
    results.append(check("sub-label", INK, base, slope))

    # Anchored on the `'600 '` font weight, which only the label sets. Two other
    # draws combine a `k * (base + slope * n.z)` alpha with colors.ink, and a
    # bare search would silently measure one of those instead.
    base, slope = find_alpha(
        "label",
        r"ctx\.globalAlpha = k \* \(([\d.]+) \+ ([\d.]+) \* n\.z\);\s*\n\s*ctx\.fillStyle = colors\.ink;\s*\n\s*ctx\.font = '600 '")
    results.append(check("label", INK, base, slope))

    if all(results):
        print("\nhero contrast: all floors clear")
        return 0
    print("\nhero contrast: below the %.1f:1 floor" % FLOOR)
    return 1


if __name__ == "__main__":
    sys.exit(main())
