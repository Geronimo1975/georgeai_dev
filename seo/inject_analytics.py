#!/usr/bin/env python3
"""Put the consent-gated GA4 loader on every generated page.

analytics.js self-gates on localStorage.ga_cookie === "all" (see
backend/assets/analytics.js), so loading it everywhere is safe: a page only
starts talking to Google after the visitor clicks "Accept all" on the export's
cookie banner. It belongs on every page, not just the homepage, because a
visitor can land on /pricing/ or a service page straight from search.

Runs late in deploy.sh (apply_analytics), after apply_seo has generated the
service and blog pages and apply_pages has copied the static ones. Idempotent:
a page that already references analytics.js is skipped.

Usage: inject_analytics.py SITE_DIR   ->  prints the number of pages changed
"""

from __future__ import annotations

import pathlib
import re
import sys

TAG = '<script src="/analytics.js" defer></script>'


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
        if "/analytics.js" in html:
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
