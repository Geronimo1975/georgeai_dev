#!/usr/bin/env python3
"""
apply_services.py — re-order (and extend) the service catalogue in the export.

The homepage groups its service cards by category and numbers them by array
position, and both the `svcMeta` array (site/index.html, site/GeorgeAI.dc.html)
and the translated prose (`cats` / `items` in site/services-data.js) are
hard-coded by the design tool in *its* order. seo/services.json is the source
of truth for the commercial order; this script rewrites those three blocks
from it on every deploy, so a re-export cannot silently revert the positioning.

Prose is moved by service *name*, never by position: the export's own svcMeta
tells us which line of `items` belongs to which service, then the lines are
re-emitted in the JSON order. Cards the export does not ship (`new`) get their
prose from the JSON. Fully idempotent — a second run is a byte-for-byte no-op.
All-or-nothing: any shape mismatch raises and nothing is written.

Usage:  python3 seo/apply_services.py <site_dir> <seo_dir> <page.html> [more.html ...]
"""
import json
import re
import sys
from pathlib import Path

LANGS = ("en", "de", "fr", "ro", "ar")
PROSE = ("tagline", "intro", "includes", "steps", "outcome")
MOCK = "/assets/mock"


class PatchError(Exception):
    pass


def slugify(name: str) -> str:
    """Mirror of seo/generate_service_pages.py:slugify / images/gen_mockups.py slugs."""
    s = name.lower().replace("&", " ").replace("/", " ")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def js(v) -> str:
    return json.dumps(v, ensure_ascii=False)


# ---------------------------------------------------------------------------
# svcMeta — one object literal per line inside `const svcMeta = [ ... ];`
# ---------------------------------------------------------------------------
META_RE = re.compile(
    r'^\s*\{\s*name:\s*"(?P<name>[^"]+)",\s*cat:\s*(?P<cat>\d+),'
    r'\s*stack:\s*\[(?P<stack>[^\]]*)\],\s*label:\s*"(?P<label>[^"]*)"'
    r'(?:,\s*img:\s*"[^"]*")?\s*\},?\s*$'
)


def _svcmeta_span(html: str):
    m = re.search(r"^(?P<indent>\s*)const svcMeta = \[\n", html, re.M)
    if not m:
        raise PatchError("no 'const svcMeta = [' in page")
    end = html.find("\n" + m.group("indent") + "];", m.end())
    if end < 0:
        raise PatchError("svcMeta array is not closed")
    return m, m.end(), end + 1  # body is html[m.end():end+1]


def read_export_names(html: str) -> list:
    """Service names in the order the export (or a previous run) lists them."""
    _m, start, end = _svcmeta_span(html)
    names = []
    for line in html[start:end].splitlines():
        if not line.strip():
            continue
        mm = META_RE.match(line)
        if not mm:
            raise PatchError(f"unrecognised svcMeta entry: {line.strip()[:80]}")
        names.append(mm.group("name"))
    return names


def render_svcmeta(order: list, indent: str) -> str:
    lines = []
    for e in order:
        lines.append(
            f'{indent}  {{ name: {js(e["name"])}, cat: {e["cat"]}, stack: {js(e["stack"])}, '
            f'label: {js(e["label"])}, img: "{MOCK}/svc-{slugify(e["name"])}.svg" }},'
        )
    return "\n".join(lines) + "\n"


def patch_svcmeta(html: str, order: list) -> str:
    m, start, end = _svcmeta_span(html)
    return html[:start] + render_svcmeta(order, m.group("indent")) + html[end:]


# ---------------------------------------------------------------------------
# services section headline — servicesTitle / servicesSub in the T() table
# ---------------------------------------------------------------------------
def patch_section(html: str, section: dict) -> str:
    for lang, copy in section.items():
        block = re.search(r"^ {6}%s: \{" % re.escape(lang), html, re.M)
        if not block:
            raise PatchError(f"no '{lang}: {{' language block found")
        pat = re.compile(r'servicesTitle: "[^"]*", servicesSub: "[^"]*"')
        mm = pat.search(html, block.end())
        if not mm:
            raise PatchError(f"no servicesTitle/servicesSub in the {lang} block")
        repl = f"servicesTitle: {js(copy['title'])}, servicesSub: {js(copy['sub'])}"
        html = html[: mm.start()] + repl + html[mm.end():]
    return html


# ---------------------------------------------------------------------------
# services-data.js — `cats` labels and per-language `items` lines
# ---------------------------------------------------------------------------
def _block(js_src: str, key: str):
    """(start, end) of the top-level `  key: {` ... `  },` block."""
    m = re.search(r"^  %s: \{\n" % re.escape(key), js_src, re.M)
    if not m:
        raise PatchError(f"no '{key}:' block in services-data.js")
    end = js_src.find("\n  },", m.end())
    if end < 0:
        raise PatchError(f"'{key}:' block is not closed")
    return m.end(), end + 1


def patch_cats(js_src: str, cats: dict) -> str:
    start, end = _block(js_src, "cats")
    body = "".join(f"    {lang}: {js(cats[lang])},\n" for lang in LANGS)
    return js_src[:start] + body + js_src[end:]


def read_items(js_src: str) -> dict:
    """{lang: [raw entry line, ...]} in export order."""
    start, end = _block(js_src, "items")
    out = {}
    cur = None
    for line in js_src[start:end].splitlines():
        lm = re.match(r"^    (\w\w): \[$", line)
        if lm:
            cur = lm.group(1)
            out[cur] = []
        elif line == "    ],":
            cur = None
        elif cur and line.strip():
            out[cur].append(line.rstrip())
    missing = [l for l in LANGS if l not in out]
    if missing:
        raise PatchError(f"items block lacks languages: {missing}")
    return out


def render_entry(p: dict) -> str:
    return (
        f'      {{ tagline: {js(p["tagline"])}, intro: {js(p["intro"])}, '
        f'includes: {js(p["includes"])}, steps: {js(p["steps"])}, outcome: {js(p["outcome"])} }},'
    )


def patch_items(js_src: str, export_names: list, order: list, new: dict) -> str:
    items = read_items(js_src)
    langs = []
    for lang in LANGS:
        lines = items[lang]
        if len(lines) != len(export_names):
            raise PatchError(
                f"items[{lang}] has {len(lines)} entries but svcMeta has {len(export_names)}")
        by_name = dict(zip(export_names, lines))
        rendered = []
        for e in order:
            name = e["name"]
            if name in by_name:
                rendered.append(by_name[name])
            elif name in new:
                prose = new[name].get(lang)
                if not prose or any(k not in prose for k in PROSE):
                    raise PatchError(f"services.json new[{name}][{lang}] incomplete")
                rendered.append(render_entry(prose))
            else:
                raise PatchError(f"'{name}' is neither in the export nor in services.json new")
        langs.append(f"    {lang}: [\n" + "\n".join(rendered) + "\n    ],")
    start, end = _block(js_src, "items")
    return js_src[:start] + "\n".join(langs) + "\n" + js_src[end:]


def main(argv):
    if len(argv) < 4:
        sys.stderr.write(__doc__)
        return 2
    site, seo = Path(argv[1]), Path(argv[2])
    cfg = json.loads((seo / "services.json").read_text(encoding="utf-8"))
    order, cats, new, section = cfg["order"], cfg["cats"], cfg.get("new", {}), cfg.get("section", {})
    ncat = max(e["cat"] for e in order) + 1
    for lang in LANGS:
        if len(cats.get(lang, [])) != ncat:
            raise SystemExit(f"services layer: cats[{lang}] must have {ncat} labels")

    data = site / "services-data.js"
    if not data.exists():
        sys.stderr.write("services layer: services-data.js missing — skipped\n")
        return 0
    js_src = data.read_text(encoding="utf-8")

    writes = []
    export_names = None
    try:
        for name in argv[3:]:
            page = site / name
            if not page.exists():
                continue
            html = page.read_text(encoding="utf-8")
            names = read_export_names(html)
            if export_names is None:
                export_names = names
            elif names != export_names:
                raise PatchError(f"{name}: svcMeta order differs from the first page")
            html = patch_svcmeta(html, order)
            if section:
                html = patch_section(html, section)
            writes.append((page, html))
        if export_names is None:
            sys.stderr.write("services layer: no page with svcMeta — skipped\n")
            return 0
        js_src = patch_cats(js_src, cats)
        js_src = patch_items(js_src, export_names, order, new)
        writes.append((data, js_src))
    except PatchError as exc:
        sys.stderr.write(f"services layer: {exc}\n")
        return 1

    for path, text in writes:
        path.write_text(text, encoding="utf-8")
    sys.stderr.write(
        f"services layer: {len(order)} services in {ncat} categories, "
        f"{len(writes) - 1} page(s) + services-data.js\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
