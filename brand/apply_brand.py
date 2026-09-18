#!/usr/bin/env python3
"""Brand accent layer for the exported SPA pages.

The design-tool export hard-codes the Anthropic coral #cc785c everywhere.
That shade is a muted, dusty coral with little voltage, and it fails WCAG AA
where it carries meaning. This script rewrites the export to a hotter,
neon coral-orange while keeping every text/label pairing accessible:

  ACCENT_NEON  #ff5c39  the brand voltage. Large surfaces and dark-theme text.
                        5.84:1 on the dark canvas; 6.01:1 against ink labels.
                        NOT usable for small text on cream (2.91:1) or under
                        white labels (3.07:1) — that is what ACCENT_TEXT is for.
  ACCENT_TEXT  #df2700  the darkened companion. Small text on the cream canvas
                        (4.50:1) and button fills under white labels (4.74:1).

Applied as:
  - `accent` / `accentBtn` keys on the page's theme palettes (the export's own
    renderer emits them as CSS variables):
      dark  accent #ff5c39   light accent #df2700   accentBtn #df2700 (both)
  - buttons  background:#cc785c;color:#fff  ->  var(--accentBtn)
  - text/links/borders  #cc785c             ->  var(--accent)
  - the full-bleed CTA band goes neon and flips its label to ink, which also
    repairs a pre-existing failure (white on the old coral was 3.28:1)
  - the coral pricing card keeps white text, so it takes ACCENT_TEXT, not neon
  - decorative coral (glyphs, glow streaks, tints) becomes neon
  - social icons (simpleicons CDN + inline data-URI) -> neutral #8e8b82,
    so the accent stays scarce and CTAs keep the voltage

Idempotent: every replacement's output no longer matches its input pattern,
and the palette keys are updated in place when they already exist.

Usage: apply_brand.py FILE [FILE...]
"""
import re
import sys

ACCENT_NEON = "#ff5c39"
ACCENT_TEXT = "#df2700"

PALETTE_ANCHOR_LIGHT = 'ink: "#141413",'
PALETTE_ANCHOR_DARK = 'ink: "#faf9f5",'
PALETTE_LIGHT = f' accent: "{ACCENT_TEXT}", accentBtn: "{ACCENT_TEXT}",'
PALETTE_DARK = f' accent: "{ACCENT_NEON}", accentBtn: "{ACCENT_TEXT}",'

# an already-injected pair, whatever shades it currently carries
_ACCENT_DECL = re.compile(r' accent: "#[0-9a-fA-F]{6}", accentBtn: "#[0-9a-fA-F]{6}",')

# order matters: buttons first (they also contain `color:#fff`, not coral text),
# then remaining coral text/border occurrences.
VAR_REPLACEMENTS = [
    ('background:#cc785c;color:#fff', 'background:var(--accentBtn);color:#fff'),
    ('color:#cc785c', 'color:var(--accent)'),
    ('solid #cc785c', 'solid var(--accent)'),
]

SAFE_REPLACEMENTS = [
    # The coral pricing card renders white body text on the fill, so it cannot
    # take the neon shade (3.07:1). Pin it to the companion BEFORE the generic
    # decorative rule below turns every remaining coral fill neon.
    ('background:#cc785c;border:1px solid var(--accent)',
     f'background:{ACCENT_TEXT};border:1px solid var(--accent)'),

    # the seo:footer block sits OUTSIDE the app root, so var(--accent) does not
    # resolve there — pin its pricing link to the fixed accessible accent.
    # (first form: fresh injection; second: repairs an over-eager var rewrite;
    #  third: lifts the previous, duller pin)
    ('<a href="/pricing/" style="color:#cc785c', f'<a href="/pricing/" style="color:{ACCENT_TEXT}'),
    ('<a href="/pricing/" style="color:var(--accent)', f'<a href="/pricing/" style="color:{ACCENT_TEXT}'),
    ('<a href="/pricing/" style="color:#a9583e', f'<a href="/pricing/" style="color:{ACCENT_TEXT}'),

    ('+ s + "/cc785c"', '+ s + "/8e8b82"'),          # simpleicons CDN color
    ("fill='%23cc785c", "fill='%238e8b82"),           # inline LinkedIn data-URI

    # decorative coral fills (spike glyphs, timeline dot, CTA band) go neon
    ('background:#cc785c', f'background:{ACCENT_NEON}'),

    # ...and the CTA band, now neon, flips its label to ink: white on neon is
    # 3.07:1, ink is 6.01:1. Runs after the fill swap above, so it matches.
    (f'background:{ACCENT_NEON};border-radius:16px;padding:{{{{ ctaPad }}}};color:#fff',
     f'background:{ACCENT_NEON};border-radius:16px;padding:{{{{ ctaPad }}}};color:#141413'),

    # glow streaks and tints: same alphas, hotter hue (204,120,92 -> 255,92,57)
    ('rgba(204,120,92,', 'rgba(255,92,57,'),

    # The renderer also carries the accent inside JS string literals — selected
    # states, active dots, open-row borders, mock diagram nodes. Those are not
    # CSS text, so the rules above miss them.
    # The light pricing card's tag is small text on cream, so it takes the
    # companion; pin it before the generic literal rule below.
    ('tagColor: "#cc785c"', f'tagColor: "{ACCENT_TEXT}"'),
    # everything else in that form is a border, dot or fill -> neon.
    # (the GitHub icon path "/assets/icons/github-cc785c.svg" has no '#', so it
    #  is not touched by this)
    ('"#cc785c"', f'"{ACCENT_NEON}"'),

    # the animated hero light beams: a gradient literal inside a template
    # string, with its own lighter coral tip. Purely decorative (no text), so
    # both stops go to the neon family.
    ('transparent,#cc785c 55%,#f0a98a', f'transparent,{ACCENT_NEON} 55%,#ff9e82'),
]


def _set_palette(html: str, anchor: str, decl: str) -> str:
    """Insert the accent pair after `anchor`, or update one already there."""
    i = html.find(anchor)
    if i < 0:
        return html
    j = i + len(anchor)
    existing = _ACCENT_DECL.match(html, j)
    if existing:
        return html[:j] + decl + html[existing.end():]
    return html[:j] + decl + html[j:]


def apply(path: str) -> None:
    with open(path, encoding="utf-8") as f:
        html = f.read()
    orig = html

    has_palette = PALETTE_ANCHOR_LIGHT in html and PALETTE_ANCHOR_DARK in html
    if has_palette:
        html = _set_palette(html, PALETTE_ANCHOR_LIGHT, PALETTE_LIGHT)
        html = _set_palette(html, PALETTE_ANCHOR_DARK, PALETTE_DARK)
        for old, new in VAR_REPLACEMENTS:
            html = html.replace(old, new)
    for old, new in SAFE_REPLACEMENTS:
        html = html.replace(old, new)

    if html != orig:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"brand: rewrote {path}" + ("" if has_palette else " (safe subset — no theme palette)"))
    else:
        print(f"brand: {path} already current")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: apply_brand.py FILE [FILE...]")
    for p in sys.argv[1:]:
        apply(p)
