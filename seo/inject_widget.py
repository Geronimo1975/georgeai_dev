#!/usr/bin/env python3
"""Put the lead-capture widget on every generated page.

The free-visibility-check button is the only thing on the site that turns an
anonymous visitor into a name. It used to be injected into the homepage only,
so a warm visitor who reached /pricing/ or a service page and decided not to
buy today left no trace at all.

Runs last in deploy.sh, after apply_seo has generated the service and blog
pages and apply_pages has copied the static ones. Idempotent: a page that
already references audit.js is skipped.

Usage: inject_widget.py SITE_DIR   ->  prints the number of pages changed
"""

from __future__ import annotations

import pathlib
import re
import sys

TAG = '<script src="/audit.js" defer></script>'


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        sys.stderr.write(__doc__)
        return 2
    root = pathlib.Path(argv[1])
    if not root.is_dir():
        sys.stderr.write(f"not a directory: {root}\n")
        return 1

    changed = 0
    for page in sorted(root.rglob("index.html")):
        html = page.read_text(encoding="utf-8")
        if "/audit.js" in html:
            continue
        if re.search(r"</body>", html, re.I):
            html = re.sub(r"</body>", TAG + "</body>", html, count=1, flags=re.I)
        else:
            html = html + "\n" + TAG + "\n"
        page.write_text(html, encoding="utf-8")
        changed += 1

    print(changed)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
