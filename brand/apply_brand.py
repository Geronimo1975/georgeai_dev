#!/usr/bin/env python3
r"""Brand + palette layer for the exported SPA pages.

The design-tool export ships a warm cream/coral personal-portfolio palette and
hard-codes the coral #cc785c throughout. This layer rewrites the export into
the site's actual brand: a corporate B2B system with a deep navy canvas and a
teal accent, defined once in brand/palette.json.

Two jobs, in order:

  1. PALETTE — rewrite the `light:` / `dark:` literals inside `const themes = {`
     from brand/palette.json. The export's own renderer turns every key into a
     CSS custom property on its root div (--canvas, --ink, --accent, ...), so
     this one edit repaints everything that uses the variables.

  2. LITERALS — the export also paints coral directly in inline styles, in JS
     ternaries and in data-URIs, where no variable can reach. Those are
     rewritten to var(--accent) / var(--accentBtn) where a variable resolves,
     and to a fixed hex where it does not (the seo:footer strip is painted
     outside the app root, so var(--accent) is undefined there).

  Social icons are muted to grey so the accent stays scarce and CTAs keep the
  voltage. Hero glow streaks keep their alphas but move to the teal RGB.

WHY A WHOLESALE PALETTE REWRITE, not the key-by-key patching this file used to
do: the old version anchored on `ink: "#141413",` and injected only accent and
accentBtn after it. That made `ink` simultaneously the anchor and a value —
so `ink` itself could never change. Matching the whole literal removes that
knot and makes a 19-key swap a one-line edit in JSON.

The match is `(light|dark): \{[^}]*\},` — deliberately NOT non-greedy `.*?`.
The literal contains no nested braces, so a negated character class physically
cannot run past the closing brace. A `.*?` match that overshoots would corrupt
the export's script and render a blank #dc-root, which is the single worst
failure this layer could cause.

Idempotent throughout: the palette rewrite reproduces its own anchor, and
every literal replacement's output no longer matches its input pattern.
Files without the theme-palette anchor (generated service/blog pages) get only
the non-var-based safe replacements.

Usage: apply_brand.py FILE [FILE...]
"""
import json
import re
import sys
from pathlib import Path

PALETTE_FILE = Path(__file__).resolve().parent / "palette.json"

# The key set this layer knows how to write. If a re-export introduces a key
# that is not here, a wholesale rewrite would SILENTLY DROP it and the page
# would lose a CSS variable with no error anywhere. So: refuse instead.
KNOWN_KEYS = {
    "canvas", "surface", "card", "cardBorder", "ink", "accent", "accentBtn",
    "body", "muted", "hairline", "navBg", "pillBg", "phA", "phB", "phText",
    "footerBg", "footerText", "footerHead", "gridline",
}

THEME_RE = re.compile(r'^(\s*)(light|dark): \{([^}]*)\},$', re.M)


def load_palette():
    with open(PALETTE_FILE, encoding="utf-8") as f:
        pal = json.load(f)
    for theme in ("light", "dark"):
        missing = KNOWN_KEYS - set(pal[theme])
        if missing:
            sys.exit("brand: palette.json %s is missing keys: %s"
                     % (theme, ", ".join(sorted(missing))))
    return pal


PALETTE = load_palette()
BTN_LABEL = PALETTE["buttonLabel"]
ACCENT_DARK = PALETTE["dark"]["accent"]      # the footer strip sits on navy
ACCENT_RGB = "47,212,193"                    # teal, for the rgba() glow streaks
INV_BG = PALETTE["inverseBtnBg"]             # the secondary CTA that sits ON the
INV_LABEL = PALETTE["inverseBtnLabel"]       # accent band, so it cannot be accent
FONT_DISPLAY = PALETTE["fontDisplayLatin"]
FONT_BODY = PALETTE["fontBodyLatin"]
SOCIAL_GREY = PALETTE["socialGrey"].lstrip("#")
NEUTRALS = PALETTE["hardcodedNeutrals"]

# Sanity: the neutral map must not translate one of its own outputs, or the
# sweep would keep moving on every run and never reach a fixed point.
_collide = set(NEUTRALS) & set(NEUTRALS.values())
if _collide:
    sys.exit("brand: hardcodedNeutrals maps onto its own keys (%s) — the sweep "
             "would never converge." % ", ".join(sorted(_collide)))
if PALETTE["socialGrey"] != NEUTRALS.get("#8e8b82"):
    sys.exit("brand: socialGrey must equal hardcodedNeutrals['#8e8b82'], or the "
             "simpleicons rewrite and the neutral sweep will fight each other.")

# The export funnels every face through two one-line ternaries in its own
# script. Rewriting only the LATIN arm of each leaves the arabic arm — and the
# 52 inline 'JetBrains Mono' declarations — untouched, which is why this beats
# a `#dc-root *` font override with !important and carve-outs.
#
# Each pattern keeps the whole `... ar ? "<arabic>" : ` prefix as group 1 and
# replaces only the string after the colon, so re-running reproduces byte-identical
# output. `[^"]*` cannot escape its own quoted string, the same reasoning that
# makes the palette rewrite safe.
FONT_RES = [
    (re.compile(r'(fontDisplay: ar \? "[^"]*" : )"[^"]*"'), FONT_DISPLAY),
    (re.compile(r'(const fontBody = ar \? "[^"]*" : )"[^"]*"'), FONT_BODY),
]


def render_theme(name):
    """Rebuild one theme literal, keys in the palette file's own order."""
    pairs = ", ".join('%s: "%s"' % (k, v)
                      for k, v in PALETTE[name].items())
    return "{ %s }" % pairs


def rewrite_palette(html):
    """Replace both theme literals wholesale. Returns (html, did_match)."""
    seen = set()

    def sub(m):
        indent, name, inner = m.group(1), m.group(2), m.group(3)
        # Guard: never drop a key the export added and this layer doesn't know.
        found = set(re.findall(r'(\w+):\s*"', inner))
        unknown = found - KNOWN_KEYS
        if unknown:
            sys.exit(
                "brand: the export's `%s` palette carries unknown key(s): %s\n"
                "       A wholesale rewrite would drop them silently. Add them to\n"
                "       brand/palette.json and to KNOWN_KEYS, then re-run."
                % (name, ", ".join(sorted(unknown))))
        seen.add(name)
        return "%s%s: %s," % (indent, name, render_theme(name))

    out = THEME_RE.sub(sub, html)
    if not seen:
        return html, False
    if seen != {"light", "dark"}:
        sys.exit("brand: found only the %s palette — the export's themes object "
                 "changed shape." % ", ".join(sorted(seen)))
    # The rewrite must reproduce its own anchor, or the next run would not be a
    # no-op and every deploy would rewrite the file forever.
    if len(THEME_RE.findall(out)) != 2:
        sys.exit("brand: palette rewrite did not reproduce its own anchor — "
                 "refusing to write a file this layer can no longer re-read.")
    return out, True


# order matters: buttons first (they also contain `color:#fff`, not coral text),
# then remaining coral text/border occurrences.
VAR_REPLACEMENTS = [
    ('background:#cc785c;color:#fff', 'background:var(--accentBtn);color:' + BTN_LABEL),
    ('color:#cc785c', 'color:var(--accent)'),
    # Everything below is coral the export paints as a SURFACE rather than as
    # text: the CTA band before the footer, the spark bullets, the chart bars,
    # the active FAQ / testimonial borders. Left alone, these kept the old
    # coral next to the new teal and read as two brands on one page.
    ('background:#cc785c', 'background:var(--accentBtn)'),
    # JS ternaries build their own strings, so the hex arrives quoted and the
    # plain `solid #cc785c` pattern never sees it.
    ('"#cc785c"', '"var(--accent)"'),
    # bar-chart gradient: coral into a pale coral tip -> teal into a pale teal
    ('#cc785c 55%,#f0a98a', 'var(--accentBtn) 55%,#7fe8db'),
    ('solid #cc785c', 'solid var(--accent)'),
    # the active row in the language dropdown, the one coral rgba() that is a
    # surface tint rather than a glow
    ('rgba(204,120,92,.12)', 'rgba(%s,.14)' % ACCENT_RGB),
    # Six headings pin the serif display face literally instead of going through
    # {{ fontDisplay }} — the wordmark (header, mobile panel, footer), the work
    # card titles, a stat number, a marquee item. Pointing them at the template
    # variable rather than at a hardcoded sans is deliberate: fontDisplay still
    # carries the `ar ? Amiri : ...` ternary, and Plus Jakarta Sans ships no
    # arabic subset, so a literal swap would leave the ar locale with a face
    # that cannot render its own script.
    ('font-family:Newsreader,serif', 'font-family:{{ fontDisplay }}'),
]

SAFE_REPLACEMENTS = [
    # The export sets JetBrains Mono inline on ~52 nodes: the utility row, the
    # nav labels, tag chips, stat numbers. Mono reads "developer tool"; the
    # corporate B2B target is one geometric sans everywhere, so these move too.
    # The arabic-aware form keeps its arabic fallback — Plus Jakarta Sans has no
    # arabic subset, and dropping Noto here would break the ar locale.
    ("font-family:'JetBrains Mono','Noto Sans Arabic',monospace",
     "font-family:%s,'Noto Sans Arabic',sans-serif" % FONT_BODY.rsplit(",", 1)[0]),
    ("font-family:'JetBrains Mono',monospace", "font-family:%s" % FONT_BODY),
    # Two more live as JS strings rather than as inline CSS — a `const mono` and
    # a React.createElement style object — so they carry no `font-family:`
    # prefix for the pair above to anchor on. Matching with the surrounding
    # double quotes keeps this from also firing inside a style="..." attribute,
    # where the quote character never immediately precedes the family.
    ('"\'JetBrains Mono\',monospace"', '"%s"' % FONT_BODY),
    # The secondary "cream" CTA: warm cream fill + warm ink label, both stranded
    # from the old palette. It appears twice inline (the closing CTA band, the
    # About page) and once as the `creamBtn` JS const, so one literal pair on the
    # fill+label together catches all three without touching a bare #faf9f5
    # anywhere else. Not var()-based, so generated pages get it too.
    ('background:#faf9f5;color:#141413',
     'background:%s;color:%s' % (INV_BG, INV_LABEL)),
    ('+ s + "/cc785c"', '+ s + "/%s"' % SOCIAL_GREY),   # simpleicons CDN color
    ("fill='%23cc785c", "fill='%%23%s" % SOCIAL_GREY),  # inline LinkedIn data-URI
    # Hero glow streaks. The alphas were already tuned down by an earlier pass
    # of this layer, so BOTH the original and the tuned forms have to map onto
    # the teal RGB — a site/ that survived a deploy only carries the tuned one.
    # Target alphas stay outside the source set so no replacement's output ever
    # matches another pattern, which is what keeps this idempotent.
    ('rgba(204,120,92,.35)', 'rgba(%s,.26)' % ACCENT_RGB),
    ('rgba(204,120,92,.4)', 'rgba(%s,.31)' % ACCENT_RGB),
    ('rgba(204,120,92,.55)', 'rgba(%s,.42)' % ACCENT_RGB),
    ('rgba(204,120,92,.26)', 'rgba(%s,.26)' % ACCENT_RGB),
    ('rgba(204,120,92,.31)', 'rgba(%s,.31)' % ACCENT_RGB),
    ('rgba(204,120,92,.42)', 'rgba(%s,.42)' % ACCENT_RGB),
]

# Everything else the export paints as a translucent coral SURFACE: the hero's
# radial glow, the blurred halo behind it, the 54px icon discs, the card
# box-shadow ring, the active row in the legal-doc list. Nine of them, at nine
# different alphas — and enumerating them is how the previous version of this
# layer fell behind the export. It knew only the three hero streaks, so on a
# navy canvas every other coral wash would have stayed brown.
#
# Blanket-swapping the RGB while PRESERVING each alpha is both complete and
# idempotent: the output carries the teal RGB, so it can never match the coral
# pattern a second time. Runs after the tuned pairs above, which have already
# consumed the three streak alphas they deliberately reduce.
CORAL_RGBA_RE = re.compile(r'rgba\(204,\s*120,\s*92,')


def apply(path: str) -> None:
    with open(path, encoding="utf-8") as f:
        html = f.read()
    orig = html

    html, has_palette = rewrite_palette(html)

    if has_palette:
        for old, new in VAR_REPLACEMENTS:
            html = html.replace(old, new)

        for rx, face in FONT_RES:
            html = rx.sub(lambda m, f=face: m.group(1) + '"%s"' % f, html)

        # The closing CTA band sets a label colour on its wrapper that both its
        # heading and its body inherit. Matching ANY hex rather than the one the
        # previous palette happened to use keeps this from going stale in a
        # site/ that survived an earlier deploy — which is how the label trailed
        # a palette change once already.
        html = re.sub(r'(color:)#[0-9a-fA-F]{6}(;display:flex;flex-direction:\{\{ ctaDir \}\})',
                      r'\g<1>' + BTN_LABEL + r'\g<2>', html)

        # Same reasoning for the button label sitting on the accent fill.
        html = re.sub(r'(background:var\(--accentBtn\);color:)#[0-9a-fA-F]{6}',
                      r'\g<1>' + BTN_LABEL, html)

    for old, new in SAFE_REPLACEMENTS:
        html = html.replace(old, new)

    html = CORAL_RGBA_RE.sub('rgba(%s,' % ACCENT_RGB, html)

    # Hardcoded warm chrome the theme variables never reach — the auth modal,
    # the mobile panel wordmark, the seo:footer strip. Runs AFTER the palette
    # rewrite, which has already emitted the navy literals, so nothing here can
    # walk back over a value this layer just wrote. Idempotent because no output
    # of the map is also a key (asserted at import).
    for old, new in NEUTRALS.items():
        html = html.replace(old, new)
        html = html.replace(old.upper(), new)

    # Social icons are muted to grey so the accent stays scarce. The literal
    # pair above only catches the URL built by string concatenation; some are
    # written out in full, which left one GitHub mark in the old coral.
    html = re.sub(r'(cdn\.simpleicons\.org/[a-z0-9.+-]+/)(?!%s)[0-9a-fA-F]{6}' % SOCIAL_GREY,
                  r'\g<1>' + SOCIAL_GREY, html)

    # The seo:footer strip sits outside the app root when it is first painted,
    # so var(--accent) cannot resolve there and the colour has to be a literal.
    # Matching any hex rather than a specific previous one keeps it current
    # across palette changes, and also repairs an over-eager var() rewrite.
    html = html.replace('<a href="/pricing/" style="color:var(--accent)',
                        '<a href="/pricing/" style="color:' + ACCENT_DARK)
    html = re.sub(r'(<a href="/pricing/" style="color:)#[0-9a-fA-F]{6}',
                  r'\g<1>' + ACCENT_DARK, html)

    if html != orig:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print("brand: rewrote %s%s"
              % (path, "" if has_palette else " (safe subset — no theme palette)"))
    else:
        print("brand: %s already current" % path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: apply_brand.py FILE [FILE...]")
    for p in sys.argv[1:]:
        apply(p)
