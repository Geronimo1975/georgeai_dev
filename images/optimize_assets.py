#!/usr/bin/env python3
"""
optimize_assets.py — recompress the export's raster assets to WebP.

The design-tool export ships its photography as full-size PNG: at the last
audit three files alone (concept_smart_home.png 2.3 MB, SEO_AI.png 1.7 MB,
medical_ai.png 1.7 MB) accounted for 5.7 MB of a 7.8 MB homepage. Re-encoding
them to WebP at display width costs nothing visually and removes ~95 % of the
bytes.

Same rationale as apply_images.py and brand/apply_brand.py: the export is
regenerated every time, so this runs at deploy time rather than being baked
into the export. Two steps:

  1. every raster in site/assets/ over MIN_BYTES gets a .webp sibling
     (skipped when the .webp is already newer than its source)
  2. every reference to the original filename in the site's HTML/JS is
     rewritten to the .webp

The originals are deliberately **left in place**. They cost only deploy-time
rsync (which transfers changed files only), and keeping them means a reference
this script failed to rewrite still resolves instead of 404ing.

Requires `cwebp` (libwebp). Without it the script prints a note and exits 0 —
a missing encoder must never block a deploy.

Usage:  python3 images/optimize_assets.py site/
"""
import os
import re
import shutil
import subprocess
import sys

# Anything smaller than this is not worth a second file.
MIN_BYTES = 100 * 1024
# Cap the long edge: these are decorative card/slider images, never full-bleed.
MAX_WIDTH = 1280
QUALITY = 80

SOURCE_EXT = (".png", ".jpg", ".jpeg")

# og-cover.jpg is fetched by social/link-preview scrapers, several of which
# still do not accept WebP — it stays JPEG. Mockups are already vector.
SKIP_NAMES = {"og-cover.jpg"}
SKIP_DIRS = {"mock"}

# Files whose bodies carry the asset references (the SPA homepage and the
# design-tool data modules).
REWRITE_EXT = (".html", ".js", ".css")


def encoder():
    return shutil.which("cwebp")


def find_sources(assets_dir):
    """Raster files worth converting, largest first."""
    out = []
    for root, dirs, files in os.walk(assets_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if not fn.lower().endswith(SOURCE_EXT) or fn in SKIP_NAMES:
                continue
            p = os.path.join(root, fn)
            if os.path.getsize(p) >= MIN_BYTES:
                out.append(p)
    return sorted(out, key=os.path.getsize, reverse=True)


def convert(src, cwebp):
    """Encode `src` to a .webp sibling. Returns (dst, before, after) or None."""
    dst = os.path.splitext(src)[0] + ".webp"
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
        return dst, os.path.getsize(src), os.path.getsize(dst)  # already done
    cmd = [cwebp, "-quiet", "-q", str(QUALITY), "-metadata", "none",
           "-resize", str(MAX_WIDTH), "0", src, "-o", dst]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except (subprocess.CalledProcessError, OSError):
        return None
    if not os.path.exists(dst) or os.path.getsize(dst) == 0:
        return None
    # A conversion that grew the file is not an optimisation.
    if os.path.getsize(dst) >= os.path.getsize(src):
        os.remove(dst)
        return None
    return dst, os.path.getsize(src), os.path.getsize(dst)


def rewrite_refs(site_dir, mapping):
    """Point every reference at the .webp. Idempotent — the .webp name has no
    match left to rewrite on a second run."""
    if not mapping:
        return 0
    # Longest first so `full_stack.png` cannot be shadowed by a shorter stem.
    pat = re.compile("|".join(re.escape(k) for k in
                     sorted(mapping, key=len, reverse=True)))
    touched = 0
    for root, dirs, files in os.walk(site_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in files:
            if not fn.lower().endswith(REWRITE_EXT):
                continue
            p = os.path.join(root, fn)
            try:
                with open(p, encoding="utf-8") as fh:
                    body = fh.read()
            except (UnicodeDecodeError, OSError):
                continue
            new = pat.sub(lambda m: mapping[m.group(0)], body)
            if new != body:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(new)
                touched += 1
    return touched


def main(argv):
    if len(argv) < 2:
        print("usage: optimize_assets.py <site-dir>", file=sys.stderr)
        return 2
    site_dir = argv[1].rstrip("/")
    assets_dir = os.path.join(site_dir, "assets")
    if not os.path.isdir(assets_dir):
        print("optimize_assets: no assets/ dir — nothing to do")
        return 0

    cwebp = encoder()
    if not cwebp:
        print("optimize_assets: cwebp not found — assets left as-is")
        return 0

    mapping, before, after, made = {}, 0, 0, 0
    for src in find_sources(assets_dir):
        res = convert(src, cwebp)
        if res is None:
            print(f"optimize_assets: could not encode {os.path.basename(src)}")
            continue
        dst, b, a = res
        mapping[os.path.basename(src)] = os.path.basename(dst)
        before += b
        after += a
        made += 1

    touched = rewrite_refs(site_dir, mapping)
    if made:
        saved = (before - after) / 1024
        print(f"optimize_assets: {made} image(s) → webp, "
              f"{before/1024:.0f}KB → {after/1024:.0f}KB "
              f"(−{saved:.0f}KB), {touched} file(s) rewritten")
    else:
        print("optimize_assets: nothing above the size threshold")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
