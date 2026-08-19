#!/usr/bin/env python3
"""Brand accent layer for the exported SPA pages.

The design-tool export hard-codes the Anthropic coral #cc785c everywhere.
That shade is fine as a brand surface, but fails WCAG AA where it carries
meaning: white button labels on it hit 3.28:1 and coral text on the cream
(light) canvas hits 3.11:1 (AA needs 4.5:1). This script rewrites the
export so functional coral becomes theme-aware while decorative coral
(spike glyphs, CTA bands, hero streaks) keeps the brand shade:

  - adds `accent` / `accentBtn` keys to the page's theme palettes
    (they are emitted as CSS variables by the export's own renderer):
      dark  accent #ff6b1a (6.29:1 on dark canvas)
      light accent #c2410c (4.92:1 on cream)
      accentBtn    #ff6b1a in both themes, with an INK label (6.47:1).
      A white label on this orange is 2.85:1 and fails; dark-on-bright is
      also what makes it read as neon rather than as a muted coral.
  - buttons  background:#cc785c;color:#fff  ->  var(--accentBtn) + ink label
  - text/links/borders  #cc785c             ->  var(--accent)
  - social icons (simpleicons CDN + inline data-URI) -> neutral #8e8b82,
    so the coral stays scarce and CTAs keep the voltage
  - hero glow streaks: strongest alphas reduced (.55/.4/.35 -> .4/.3/.25)

Idempotent: every replacement's output no longer matches its input pattern.
Files without the theme-palette anchor get only the non-var-based, safe
replacements (icons, glow).

Usage: apply_brand.py FILE [FILE...]
"""
import re
import sys

PALETTE_ANCHOR_LIGHT = 'ink: "#141413",'
PALETTE_ANCHOR_DARK = 'ink: "#faf9f5",'

# order matters: buttons first (they also contain `color:#fff`, not coral text),
# then remaining coral text/border occurrences.
VAR_REPLACEMENTS = [
    ('background:#cc785c;color:#fff', 'background:var(--accentBtn);color:#141413'),
    # A site/ carried over from an earlier deploy is already half-rewritten:
    # the fill became a var but the label is still white from when the button
    # was a darker orange. Catch that form too, or the label never updates.
    ('background:var(--accentBtn);color:#fff', 'background:var(--accentBtn);color:#141413'),
    ('color:#cc785c', 'color:var(--accent)'),
    ('solid #cc785c', 'solid var(--accent)'),
]

SAFE_REPLACEMENTS = [
    # the seo:footer block sits OUTSIDE the app root, so var(--accent) does not
    # resolve there — pin its pricing link to the fixed accessible accent.
    # (first form: fresh injection; second: repairs an over-eager var rewrite)
    ('<a href="/pricing/" style="color:#cc785c', '<a href="/pricing/" style="color:#ff6b1a'),
    ('<a href="/pricing/" style="color:var(--accent)', '<a href="/pricing/" style="color:#ff6b1a'),
    ('+ s + "/cc785c"', '+ s + "/8e8b82"'),          # simpleicons CDN color
    ("fill='%23cc785c", "fill='%238e8b82"),           # inline LinkedIn data-URI
    # hero glow: target alphas deliberately outside the source set so no
    # replacement's output ever matches another pattern (keeps this idempotent)
    ('rgba(204,120,92,.35)', 'rgba(204,120,92,.26)'),
    ('rgba(204,120,92,.4)', 'rgba(204,120,92,.31)'),
    ('rgba(204,120,92,.55)', 'rgba(204,120,92,.42)'),
]


def apply(path: str) -> None:
    with open(path, encoding="utf-8") as f:
        html = f.read()
    orig = html

    has_palette = PALETTE_ANCHOR_LIGHT in html and PALETTE_ANCHOR_DARK in html
    if has_palette:
        # Insert on a fresh export, REWRITE when the keys are already there.
        # This used to be `if 'accent:' not in html`, which made the layer a
        # one-shot: site/ survives a --no-content deploy, so changing the
        # accent values here silently never reached the built homepage while
        # the generated pages picked them up, leaving the two out of step.
        if 'accent:' not in html:
            html = html.replace(
                PALETTE_ANCHOR_LIGHT,
                PALETTE_ANCHOR_LIGHT + ' accent: "", accentBtn: "",', 1)
            html = html.replace(
                PALETTE_ANCHOR_DARK,
                PALETTE_ANCHOR_DARK + ' accent: "", accentBtn: "",', 1)
        html = re.sub(
            re.escape(PALETTE_ANCHOR_LIGHT) + r' accent: "[^"]*", accentBtn: "[^"]*",',
            PALETTE_ANCHOR_LIGHT + ' accent: "#c2410c", accentBtn: "#ff6b1a",', html, count=1)
        html = re.sub(
            re.escape(PALETTE_ANCHOR_DARK) + r' accent: "[^"]*", accentBtn: "[^"]*",',
            PALETTE_ANCHOR_DARK + ' accent: "#ff6b1a", accentBtn: "#ff6b1a",', html, count=1)
    if has_palette:
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
