#!/usr/bin/env python3
r"""Inject the repo-owned homepage sections into the design-tool export.

Run by deploy.sh:apply_idn(). Usage: sections.py SITE_INDEX_HTML IDN_DIR

WHY SURGERY ON THE EXPORT, and not a runtime layer like hero/hero-cinema.js
    Every homepage section lives inside the subtree support.js re-renders on
    every setState — the language pill, the theme toggle, the mobile menu. The
    hero layer pays for that with a data-dc-tpl readiness gate, a dedupe() pass
    and a MutationObserver, because it mounts a node from the outside.

    Sections injected into the <x-dc> template instead ARE the template. They
    get {{ }} interpolation, <sc-for>, <sc-if>, the theme variables and the
    export's own i18n for free, with no observer and no layout shift. The cost
    is that they must be re-injected after every export — which is what this
    script, and the whole deploy-layer pattern around it, exists to do.

HOW IT FINDS ITS PLACE
    The design tool emits stable section comments (<!-- LOGO CAROUSEL -->,
    <!-- HOW IT WORKS -->, ...) and they survive into the built index.html. Those
    are the anchors. They are the one thing here that a redesign in the design
    tool could take away, so a missing anchor is a HARD FAILURE (exit 1) rather
    than a warning: deploy.sh must stop before rsync. Injecting a section into
    the wrong place, or silently dropping it, is worse than not deploying.

IDEMPOTENCY
    Each block is wrapped in <!-- idn:NAME:start --> ... <!-- idn:NAME:end -->.
    When those markers exist the block is REPLACED IN PLACE, never skipped —
    site/ survives a --no-content deploy, so skipping would mean copy edits in
    idn/sections/*.html never reach the built page. When they do not exist the
    block is inserted relative to its anchor.

I18N
    New copy goes into the export's own per-language `t` tables rather than into
    a JS shim, so it switches language through the export's existing machinery
    with no extra script. Insertion is likewise self-healing: an existing key is
    rewritten, so editing a translation here lands on the next deploy.

EXIT CODES
    0  applied, or already current
    1  the export changed shape — anchor or i18n target missing. Deploy must stop.
"""
import re
import sys
from pathlib import Path

# name -> (fragment file, anchor comment, placement)
SECTIONS = [
    ("glance", "glance.html", "<!-- LOGO CAROUSEL -->", "before"),
]

# Copy that lives in the export's own language tables.
# obj literal -> key -> {lang: translation}
#
# Translations are unreviewed by a native speaker except en/de/ro. They are
# short, standard section labels; anything longer or more load-bearing than an
# eyebrow should be reviewed before it ships.
I18N = {
    "about": {
        "glance": {
            "en": "At a glance",
            "de": "Auf einen Blick",
            "fr": "En un coup d'œil",
            "ro": "Pe scurt",
            "ar": "لمحة سريعة",
        },
    },
}

LANGS = ("en", "de", "fr", "ro", "ar")
LANG_RE = re.compile(r'^      (%s): \{$' % "|".join(LANGS), re.M)


def fail(msg):
    sys.stderr.write("idn/sections.py: %s\n" % msg)
    sys.exit(1)


def block(name, markup):
    return ("<!-- idn:%s:start -->\n%s\n<!-- idn:%s:end -->"
            % (name, markup.strip(), name))


def place_section(html, name, markup, anchor, where):
    """Insert or replace one section. Returns the new html."""
    wrapped = block(name, markup)

    existing = re.search(r"<!-- idn:%s:start -->.*?<!-- idn:%s:end -->" % (name, name),
                         html, re.S)
    if existing:
        # Re-inject, never skip: a site/ carried over from an earlier deploy
        # already has the markers, and skipping would strand every copy edit.
        return html[:existing.start()] + wrapped + html[existing.end():]

    at = html.find(anchor)
    if at < 0:
        fail("anchor %r for section %r not found in the export.\n"
             "       The design tool renamed or dropped its section comment.\n"
             "       Fix the anchor in SECTIONS rather than deploying a homepage\n"
             "       that is silently missing this block." % (anchor, name))

    if where == "before":
        return html[:at] + wrapped + "\n\n  " + html[at:]
    end = at + len(anchor)
    return html[:end] + "\n\n  " + wrapped + html[end:]


def put_i18n(html, obj, key, translations):
    """Insert or rewrite `key` inside each language's `obj: { ... }` literal.

    Operates per language block and in reverse document order so earlier match
    offsets stay valid as later ones are rewritten.
    """
    starts = list(LANG_RE.finditer(html))
    if len(starts) != len(LANGS):
        fail("expected %d language blocks in the t table, found %d — the export's "
             "i18n changed shape." % (len(LANGS), len(starts)))

    key_re = re.compile(r'(%s: \{ )(?:%s: "[^"]*", )?' % (re.escape(obj), re.escape(key)))

    for i in range(len(starts) - 1, -1, -1):
        m = starts[i]
        lang = m.group(1)
        seg_start = m.end()
        seg_end = starts[i + 1].start() if i + 1 < len(starts) else len(html)
        segment = html[seg_start:seg_end]

        text = translations.get(lang) or translations["en"]
        if '"' in text:
            fail("translation for %s.%s [%s] contains a double quote, which would "
                 "terminate the JS string it is written into." % (obj, key, lang))

        new_segment, n = key_re.subn(
            lambda mm: '%s%s: "%s", ' % (mm.group(1), key, text), segment, count=1)
        if n != 1:
            fail("could not find the %r object literal inside the %r language "
                 "block — the export's t table changed shape." % (obj, lang))

        html = html[:seg_start] + new_segment + html[seg_end:]

    return html


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: sections.py SITE_INDEX_HTML IDN_DIR")

    page = Path(sys.argv[1])
    idn = Path(sys.argv[2])

    if not page.is_file():
        fail("%s does not exist" % page)

    html = page.read_text(encoding="utf-8")
    orig = html

    for obj, keys in I18N.items():
        for key, translations in keys.items():
            html = put_i18n(html, obj, key, translations)

    applied = []
    for name, fname, anchor, where in SECTIONS:
        src = idn / "sections" / fname
        if not src.is_file():
            fail("fragment %s is missing" % src)
        html = place_section(html, name, src.read_text(encoding="utf-8"), anchor, where)
        applied.append(name)

    if html != orig:
        page.write_text(html, encoding="utf-8")
        print("idn sections: %s" % " ".join(applied))
    else:
        print("idn sections: already current (%s)" % " ".join(applied))
    return 0


if __name__ == "__main__":
    sys.exit(main())
