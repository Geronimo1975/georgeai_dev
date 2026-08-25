#!/usr/bin/env bash
#
# deploy.sh — georgeai.dev deployment pipeline
#
# Takes an HTML export (.zip) from the design tool, unpacks it into ./site,
# syncs the project to the VPS, brings up the nginx container behind Traefik,
# and verifies the site is live.
#
# Usage:
#   ./deploy.sh                       # use newest zip in ./exports (or current ./site if none)
#   ./deploy.sh exports/georgeai.zip  # use a specific zip
#   ./deploy.sh --no-content          # redeploy current ./site without unpacking a zip
#   ./deploy.sh --help
#
# Config via env (sensible defaults for this project):
#   GEORGEAI_SSH_HOST   ssh host/alias          (default: macbook-air)
#   GEORGEAI_REMOTE_DIR remote project dir       (default: /opt/georgeai)
#   GEORGEAI_HOMEPAGE   export file to serve as index.html (default: GeorgeAI.dc.html)
#   GEORGEAI_TEMPLATE_DIR  mirror each export here too (default: frontend/template; empty = skip)
#
set -euo pipefail

# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------
SSH_HOST="${GEORGEAI_SSH_HOST:-macbook-air}"
REMOTE_DIR="${GEORGEAI_REMOTE_DIR:-/opt/georgeai}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SITE_DIR="$PROJECT_DIR/site"
EXPORTS_DIR="$PROJECT_DIR/exports"
# SEO/GEO assets kept OUT of the design export (robots, sitemap, llms.txt, favicon,
# and the <head> meta block) so they survive every re-export. Injected into ./site below.
SEO_DIR="$PROJECT_DIR/seo"
# also mirror each unpacked export here so the Django frontend (backend/) can build
# against it. Set GEORGEAI_TEMPLATE_DIR= (empty) to skip the mirror.
TEMPLATE_DIR="${GEORGEAI_TEMPLATE_DIR-$PROJECT_DIR/frontend/template}"

# Only the apex serves content. www is deliberately a permanent redirect to it
# (deploy/docker-compose.yml, georgeai-www-redirect) — two hosts answering 200
# with identical bytes is a duplicate origin, so the check below expects the 301.
PROD_HOSTS=("georgeai.dev")
PROD_REDIRECT_HOSTS=("www.georgeai.dev")

# spaces in the remote path would break the remote shell commands and rsync below
case "$REMOTE_DIR" in *" "*) printf 'GEORGEAI_REMOTE_DIR must not contain spaces\n' >&2; exit 1 ;; esac

ASSETS_DIR="$PROJECT_DIR/backend/assets"
PAGES_DIR="$PROJECT_DIR/pages"
# brand accent layer — rewrites the export's hard-coded coral into theme-aware,
# WCAG-passing accents (see brand/apply_brand.py). Survives re-exports.
BRAND_DIR="$PROJECT_DIR/brand"
# image layer — the export leaves empty placeholder slots (About portrait, News
# cards, every service-detail view). images/apply_images.py swaps them for the
# committed on-brand SVG mockups. Survives re-exports.
IMAGES_DIR="$PROJECT_DIR/images"
HERO_DIR="$PROJECT_DIR/hero"

# ---------------------------------------------------------------------------
# frontend assets — JS kept out of the export (backend/assets/) so it survives
# re-exports. Copied into site/ so nginx can serve it (Django serves the same
# files from backend/assets/). Runs on every deploy, incl. --no-content.
# Idempotent.
# ---------------------------------------------------------------------------
apply_assets() {
  local f copied=""
  for f in auth.js audit.js; do
    [ -f "$ASSETS_DIR/$f" ] && { cp "$ASSETS_DIR/$f" "$SITE_DIR/$f"; copied="$copied $f"; }
  done
  [ -n "$copied" ] && ok "frontend assets:$copied"
}

# ---------------------------------------------------------------------------
# SEO layer — files in seo/ are kept out of the export so they survive
# re-exports (same rationale as backend/assets/auth.js). Runs on every deploy,
# including --no-content. Idempotent via the seo:head / seo:footer markers.
# ---------------------------------------------------------------------------
apply_seo() {
  [ -d "$SEO_DIR" ] || { warn "seo/ not found — skipping SEO layer"; return 0; }

  local f copied=""
  for f in robots.txt sitemap.xml llms.txt favicon.svg responsive.css; do
    [ -f "$SEO_DIR/$f" ] && { cp "$SEO_DIR/$f" "$SITE_DIR/$f"; copied="$copied $f"; }
  done
  [ -n "$copied" ] && ok "seo files:$copied"

  # Repo-owned static assets that must survive a re-export. Currently the OG /
  # social preview card: the export ships assets/SEO_AI.png at 1.79 MB, which is
  # over the size LinkedIn and WhatsApp will fetch, so shares rendered with no
  # image at all. seo/assets/og-cover.jpg is the same artwork cropped to the
  # 1200x630 the scrapers expect, at 137 KB. Copied (not rewritten in place)
  # because site/assets/ is repopulated from the export on every deploy.
  if [ -d "$SEO_DIR/assets" ]; then
    mkdir -p "$SITE_DIR/assets"
    cp -R "$SEO_DIR/assets"/. "$SITE_DIR/assets"/
    ok "seo assets: $(ls "$SEO_DIR/assets" | tr '\n' ' ')"
  fi

  if [ -f "$SITE_DIR/index.html" ] && [ -f "$SEO_DIR/head.html" ]; then
    if command -v python3 >/dev/null; then
      python3 - "$SITE_DIR/index.html" "$SEO_DIR/head.html" <<'PYEOF'
import re, sys
p, head_p = sys.argv[1], sys.argv[2]
html = open(p, encoding="utf-8").read()
head = open(head_p, encoding="utf-8").read().rstrip() + "\n"
# A previously injected block runs from the seo:head marker to </head> (it is
# always inserted immediately before it). Strip it so an edited seo/head.html
# actually reaches an already-deployed index.html — the marker comment promises
# "on every deploy", and skipping when the marker exists made that untrue.
# Bounded by the closing /seo:head marker: an unbounded strip to </head> also
# ate whatever a later layer had injected before </head> (apply_hero's
# stylesheet links), leaving the hero JS running with no CSS at all.
html, n = re.subn(r"<!--\s*seo:head\b.*?<!--\s*/seo:head\s*-->\s*", "",
                  html, count=1, flags=re.I | re.S)
if not n:  # legacy block predating the closing marker
    html = re.sub(r"<!--\s*seo:head\b.*?(?=</head>)", "", html, count=1, flags=re.I | re.S)
if re.search(r"</head>", html, re.I):
    html = re.sub(r"</head>", lambda m: head + m.group(0), html, count=1, flags=re.I)
else:  # no <head> in the export — prepend the block
    html = head + html
# add lang to <html> if it has none
html = re.sub(r"<html(?![^>]*\blang=)", '<html lang="en"', html, count=1, flags=re.I)
# crawlable internal links to the static pages (the SPA nav is JS-only)
footer = ('<div id="seo:footer" style="padding:16px 24px;text-align:center;'
          "font-family:'JetBrains Mono',monospace;font-size:12px\">"
          '<a href="/pricing/" style="color:#a9583e;text-decoration:none">'
          'Packages &amp; pricing &rarr;</a>'
          '&nbsp;&nbsp;·&nbsp;&nbsp;'
          '<a href="/services/" style="color:#8e8b82;text-decoration:none">'
          'Browse all services &rarr;</a>'
          '&nbsp;&nbsp;·&nbsp;&nbsp;'
          '<a href="/blog/" style="color:#8e8b82;text-decoration:none">'
          'Blog &rarr;</a></div>')
if "seo:footer" not in html and re.search(r"</body>", html, re.I):
    html = re.sub(r"</body>", lambda m: footer + m.group(0), html, count=1, flags=re.I)
open(p, "w", encoding="utf-8").write(html)
PYEOF
      ok "injected seo/head.html into index.html"
    else
      warn "python3 not found — skipped SEO head injection"
    fi
  fi

  # static <noscript> fallback for crawlers that do not execute JavaScript
  # (GPTBot, ClaudeBot, PerplexityBot). The SPA renders its hero client-side, so
  # without this the homepage arrives as unrendered {{ }} placeholders. Re-injected
  # on every deploy (stripped then re-added) so edits to seo/noscript.html ship.
  if [ -f "$SITE_DIR/index.html" ] && [ -f "$SEO_DIR/noscript.html" ]; then
    if command -v python3 >/dev/null; then
      python3 - "$SITE_DIR/index.html" "$SEO_DIR/noscript.html" <<'PYEOF'
import re, sys
p, ns_p = sys.argv[1], sys.argv[2]
html = open(p, encoding="utf-8").read()
ns = open(ns_p, encoding="utf-8").read().rstrip() + "\n"
# Strip a previously injected block so an edited seo/noscript.html reaches an
# already-deployed index.html. Without this the hero H1 that crawlers and AI
# engines actually read is frozen at whatever the first deploy injected.
html = re.sub(r'<noscript>\s*<div id="seo:noscript">.*?</noscript>\s*', "",
              html, count=1, flags=re.I | re.S)
m = re.search(r"<body[^>]*>", html, re.I)
if m:
    html = html[:m.end()] + "\n" + ns + html[m.end():]
    open(p, "w", encoding="utf-8").write(html)
else:
    sys.stderr.write("no <body> found — noscript fallback not injected\n")
    sys.exit(1)
PYEOF
      ok "injected seo/noscript.html into index.html"
    else
      warn "python3 not found — skipped noscript injection"
    fi
  fi

  # real, crawlable per-service pages + blog + sitemap (overwrites the static
  # seo/sitemap.xml copy with the full URL list). Failure must not block deploy.
  if [ -f "$SEO_DIR/generate_service_pages.py" ] && [ -f "$PROJECT_DIR/georgeai_services.json" ] \
     && command -v python3 >/dev/null; then
    if python3 "$SEO_DIR/generate_service_pages.py" "$PROJECT_DIR/georgeai_services.json" "$SITE_DIR" "$PROJECT_DIR/blog"; then
      ok "generated service pages + blog + sitemap"
    else
      warn "service page generation failed — deploy continues with static sitemap"
    fi
  fi
}

# ---------------------------------------------------------------------------
# content layer — the export hard-codes marketing copy inside the design-tool
# HTML (hero strings in the T() table, testimonials in services-data.js), so a
# re-export silently reverts any positioning or compliance work. seo/*.json is
# the source of truth and seo/apply_content.py re-applies it on every deploy,
# including --no-content. Idempotent: a full replace, never an append.
# Edit seo/hero.json and seo/testimonials.json — never site/.
# ---------------------------------------------------------------------------
apply_copy() {
  [ -d "$SEO_DIR" ] || return 0
  [ -f "$SEO_DIR/apply_content.py" ] || return 0
  command -v python3 >/dev/null || { warn "python3 not found — skipped content layer"; return 0; }

  if python3 "$SEO_DIR/apply_content.py" "$SITE_DIR" "$SEO_DIR" \
       index.html "${GEORGEAI_HOMEPAGE:-GeorgeAI.dc.html}"; then
    ok "content layer applied"
  else
    warn "content layer failed — deploy continues with the export's own copy"
  fi
  return 0
}

# ---------------------------------------------------------------------------
# brand accent layer — the export hard-codes coral #cc785c; apply_brand.py
# rewrites functional uses (buttons, links) into theme-aware accessible
# accents and mutes small decorative accents. Runs on every deploy,
# including --no-content. Idempotent (see brand/apply_brand.py).
# ---------------------------------------------------------------------------
apply_brand() {
  [ -f "$BRAND_DIR/apply_brand.py" ] || { warn "brand/ not found — skipping brand layer"; return 0; }
  command -v python3 >/dev/null || { warn "python3 not found — skipped brand layer"; return 0; }
  local targets=()
  local f
  for f in "$SITE_DIR/index.html" "$SITE_DIR/GeorgeAI.dc.html" \
           "$SITE_DIR/Portfolio.dc.html" "$SITE_DIR/Studio Site.dc.html"; do
    [ -f "$f" ] && targets+=("$f")
  done
  [ ${#targets[@]} -eq 0 ] && return 0
  if python3 "$BRAND_DIR/apply_brand.py" "${targets[@]}"; then
    ok "brand accent layer applied (${#targets[@]} files)"
  else
    warn "brand layer failed — deploy continues with export colors"
  fi
}

# ---------------------------------------------------------------------------
# prune layer — the export ships working files straight into the public web
# root, and nothing in the site links to any of them. Verified: zero references
# to uploads/ or screenshots/ from any served page, and robots.txt is Allow: /
# with no exceptions, so all of it is crawlable.
#
#   assets/hero.mp4          6.9 MB fetched on every homepage load for a <video>
#                            that can never be shown (the hero mode switch was
#                            never built); apply_content.py removes the markup,
#                            this removes the file
#   uploads/                 DESIGN-claude.md, Resume EN.pdf with a home address,
#                            a 17 MB unused video, pasted-*.png
#   screenshots/             62 design-tool QA captures
#   Portfolio.dc.html        an unrelated fictional persona ("Ilse Marlowe")
#   Studio Site.dc.html      a second one, rendering raw {{ }} placeholders
#   GeorgeAI - Portfolio.html  a 1.5 MB stale snapshot of an older build
#   .thumbnail               design-tool metadata
#
# Deliberately a denylist, not an allowlist: an allowlist that is wrong takes
# the site down, while a denylist that is incomplete only leaves junk. The
# unexpected-entry warning below covers the drift an allowlist would have.
# ---------------------------------------------------------------------------
apply_prune() {
  local removed="" p
  for p in "assets/hero.mp4" "uploads" "screenshots" ".thumbnail" \
           "Portfolio.dc.html" "Studio Site.dc.html" "GeorgeAI - Portfolio.html"; do
    if [ -e "$SITE_DIR/$p" ]; then
      rm -rf "$SITE_DIR/$p"
      removed="$removed $p"
    fi
  done
  [ -n "$removed" ] && ok "pruned from web root:$removed"

  # surface anything new the next export drops in, without deleting it
  local known=" index.html GeorgeAI.dc.html assets services blog pricing about \
auth.js audit.js support.js services-data.js legal-data.js responsive.css \
robots.txt sitemap.xml llms.txt favicon.svg "
  local entry unexpected=""
  for entry in "$SITE_DIR"/* "$SITE_DIR"/.[!.]*; do
    [ -e "$entry" ] || continue
    case "$known" in *" ${entry##*/} "*) ;; *) unexpected="$unexpected ${entry##*/}" ;; esac
  done
  [ -n "$unexpected" ] && warn "unexpected files in web root (not pruned, check them):$unexpected"
  return 0
}

# ---------------------------------------------------------------------------
# media layer — the design tool exports mp4s with the moov atom AFTER mdat,
# so browsers must download the whole file before playback starts (the hero
# video stutters on first load). Remux those files with +faststart (stream
# copy, lossless). Runs on every deploy, including --no-content. Idempotent:
# already-faststarted files are detected and skipped.
# ---------------------------------------------------------------------------
apply_media() {
  command -v ffmpeg  >/dev/null || { warn "ffmpeg not found — skipped video faststart"; return 0; }
  command -v python3 >/dev/null || { warn "python3 not found — skipped video faststart"; return 0; }
  local f fixed=""
  while IFS= read -r -d '' f; do
    # exit 0 = mdat precedes moov → needs the remux
    if python3 - "$f" <<'PY'
import struct, sys
order = []
with open(sys.argv[1], "rb") as fh:
    while True:
        hdr = fh.read(8)
        if len(hdr) < 8:
            break
        size, name = struct.unpack(">I", hdr[:4])[0], hdr[4:8]
        if name in (b"moov", b"mdat"):
            order.append(name)
        if size == 1:  # 64-bit extended size
            size = struct.unpack(">Q", fh.read(8))[0]
            fh.seek(size - 16, 1)
        elif size == 0:  # atom runs to EOF
            break
        else:
            fh.seek(size - 8, 1)
sys.exit(0 if order[:1] == [b"mdat"] else 1)
PY
    then
      if ffmpeg -v error -y -i "$f" -c copy -movflags +faststart "$f.tmp.mp4" 2>/dev/null; then
        mv "$f.tmp.mp4" "$f"
        fixed="$fixed ${f#$SITE_DIR/}"
      else
        rm -f "$f.tmp.mp4"
        warn "faststart remux failed: ${f#$SITE_DIR/}"
      fi
    fi
  done < <(find "$SITE_DIR" -name '*.mp4' -print0)
  [ -n "$fixed" ] && ok "video faststart:$fixed"
  return 0
}

# ---------------------------------------------------------------------------
# image layer — the export ships empty placeholder slots (diagonal-hatch divs
# with a `[ label ]`) on the About page, the News cards and every service-detail
# view. Copy the committed on-brand SVG mockups into site/assets/mock/ and let
# images/apply_images.py rewrite those placeholders to <img> elements. Kept out
# of the export so it survives re-exports. Runs on every deploy, incl.
# --no-content. Idempotent (see images/apply_images.py). Failure must not block
# the deploy — the placeholders simply stay.
# ---------------------------------------------------------------------------
apply_images() {
  [ -f "$IMAGES_DIR/apply_images.py" ] || { warn "images/ not found — skipping image layer"; return 0; }
  command -v python3 >/dev/null || { warn "python3 not found — skipped image layer"; return 0; }
  # ship the mockups next to the other site assets
  if [ -d "$IMAGES_DIR/mock" ]; then
    mkdir -p "$SITE_DIR/assets/mock"
    cp "$IMAGES_DIR"/mock/*.svg "$SITE_DIR/assets/mock/" 2>/dev/null || true
  fi
  local targets=() f
  for f in "$SITE_DIR/index.html" "$SITE_DIR/GeorgeAI.dc.html"; do
    [ -f "$f" ] && targets+=("$f")
  done
  [ ${#targets[@]} -eq 0 ] && return 0
  if python3 "$IMAGES_DIR/apply_images.py" "${targets[@]}"; then
    ok "image layer applied (${#targets[@]} files)"
  else
    warn "image layer failed — deploy continues with placeholder slots"
  fi
}

# ---------------------------------------------------------------------------
# repo-owned pages (e.g. pages/pricing/) — kept out of the export so they
# survive re-exports. Copied verbatim into site/. Runs on every deploy,
# including --no-content. Idempotent.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# lead-capture widget — the free-visibility-check button is the only thing on
# the site that turns an anonymous visitor into a name. It used to be injected
# into the homepage only, which meant a warm visitor who reached /pricing/ or a
# service page and decided not to buy today left no trace. Runs last, so it
# also covers the service and blog pages generated by apply_seo and the static
# pages copied by apply_pages. Idempotent: skips a page that already has it.
# ---------------------------------------------------------------------------
apply_widget() {
  [ -f "$SITE_DIR/audit.js" ] || return 0
  command -v python3 >/dev/null || { warn "python3 not found — skipped widget injection"; return 0; }

  local n
  if n=$(python3 "$SEO_DIR/inject_widget.py" "$SITE_DIR"); then
    ok "lead widget on $n page(s)"
  else
    warn "widget injection failed — deploy continues"
  fi
  return 0
}

apply_pages() {
  [ -d "$PAGES_DIR" ] || return 0
  cp -R "$PAGES_DIR"/. "$SITE_DIR"/
  ok "pages: $(find "$PAGES_DIR" -name index.html | sed "s|$PAGES_DIR/||;s|/index.html||" | tr '\n' ' ')"
}


# ---------------------------------------------------------------------------
# hero motion layer — hero/hero-motion.{css,js} add autoplay, entrance
# choreography, pointer parallax and the video backdrop to the homepage hero.
# Kept out of the export (the export has no classes and re-renders the hero
# subtree, so the JS hooks it by structure) and re-applied on every deploy,
# including --no-content. Idempotent per asset (hero:motion / hero-cinema markers).
# ---------------------------------------------------------------------------
apply_hero() {
  [ -d "$HERO_DIR" ] || { warn "hero/ not found — skipping hero motion layer"; return 0; }

  local f copied=""
  for f in hero-motion.css hero-motion.js hero-cinema.css hero-cinema.js; do
    [ -f "$HERO_DIR/$f" ] && { cp "$HERO_DIR/$f" "$SITE_DIR/$f"; copied="$copied $f"; }
  done
  [ -n "$copied" ] && ok "hero motion:$copied"

  # The export ships the hero backdrop at 1920p/3.8Mbps — 7.2MB for a video
  # that plays dimmed behind the hero. hero/assets/ holds a 1280p re-encode at
  # a quarter the weight and no visible difference in context. Copied after
  # apply_media so it wins, and it is already +faststart.
  if [ -f "$HERO_DIR/assets/hero.mp4" ] && [ -d "$SITE_DIR/assets" ]; then
    cp "$HERO_DIR/assets/hero.mp4" "$SITE_DIR/assets/hero.mp4"
    ok "hero video: $(du -h "$HERO_DIR/assets/hero.mp4" | cut -f1) (repo-owned re-encode)"
  fi

  # No outer marker gate: the per-asset guards inside are already idempotent, and
  # gating the whole block on hero-cinema.js meant a head rewritten by a later
  # layer could never get its stylesheet links back while the scripts survived.
  if [ -f "$SITE_DIR/index.html" ]; then
    if command -v python3 >/dev/null; then
      python3 - "$SITE_DIR/index.html" <<'PY'
import re, sys
p = sys.argv[1]
html = open(p, encoding="utf-8").read()

# Idempotent per asset, not per layer: a site/ that survived an earlier deploy
# already carries the motion layer, and a single hero:motion guard would then
# skip the cinema layer forever.
def in_head(markup):
    global html
    if re.search(r"</head>", html, re.I):
        html = re.sub(r"</head>", lambda m: markup + m.group(0), html, count=1, flags=re.I)
    else:
        html = markup + html

def at_body_end(markup):
    # the LAST closing body tag: an injected block may mention one inside its own
    # comment, and matching that buries the tag inside a comment.
    global html
    hits = list(re.finditer(r"</body>", html, re.I))
    if hits:
        at = hits[-1].start()
        html = html[:at] + markup + html[at:]
    else:
        html = html + "\n" + markup + "\n"

def script_once(src):
    """Ensure exactly one <script src=SRC defer> at the end of the body.

    Guarding on a marker in the <head> was wrong twice over. The head marker and
    the body script are injected together but live in different places, so a
    later layer that rewrites the head drops the marker while the script
    survives — and the next deploy, seeing no marker, appends a SECOND copy.
    That is how /hero-motion.js ended up loading twice in production, running
    its whole discovery-and-observer pass a second time over the same DOM.

    Guarding on the bare filename is wrong too: hero-lede.html and
    hero-cinema.html both NAME these files in their comments, so once either
    block is injected the guard sees the name in prose and skips the real tag
    forever. Match the exact tag, and keep the FIRST copy rather than the last
    so that hero-motion.js stays ahead of hero-cinema.js — both are deferred,
    so document order is execution order, and the cinema mount expects the
    motion layer's hooks to already exist.
    """
    global html
    tag = "<script src=\"%s\" defer></script>" % src
    first = html.find(tag)
    if first < 0:
        at_body_end(tag)
        return
    # self-healing: drop any extra copies a previous deploy already appended
    head, tail = html[:first + len(tag)], html[first + len(tag):]
    html = head + tail.replace(tag, "")

if "hero:motion" not in html:
    in_head("<!-- hero:motion — see hero/hero-motion.css, never edit site/ -->"
            "<link rel=\"stylesheet\" href=\"/hero-motion.css\">")
if "hero-cinema.css" not in html:
    in_head("<link rel=\"stylesheet\" href=\"/hero-cinema.css\">")

script_once("/hero-motion.js")
script_once("/hero-cinema.js")

open(p, "w", encoding="utf-8").write(html)
PY
      ok "injected hero motion + cinema layers into index.html"
    else
      warn "python3 not found — skipped hero motion injection"
    fi
  fi

  # hero lede — the export's home view renders no <h1> and no value proposition
  # (its 7 <h1>s all belong to sub-page views). The block goes into the raw HTML
  # between hero:lede markers so crawlers get the heading without executing JS;
  # hero-motion.js relocates it into the hero above the panel row at runtime.
  # Re-injected (not skipped) when already present, so edits to hero-lede.html
  # actually reach a site/ that survived from an earlier deploy.
  if [ -f "$HERO_DIR/hero-lede.html" ] && [ -f "$SITE_DIR/index.html" ]; then
    if command -v python3 >/dev/null; then
      python3 - "$SITE_DIR/index.html" "$HERO_DIR/hero-lede.html" <<'LEDE'
import re, sys
page, block = sys.argv[1], sys.argv[2]
html = open(page, encoding="utf-8").read()
lede = ("<!-- hero:lede:start -->\n"
        + open(block, encoding="utf-8").read().strip()
        + "\n<!-- hero:lede:end -->")
existing = re.search(r"<!-- hero:lede:start -->.*?<!-- hero:lede:end -->", html, re.S)
if existing:
    html = html[:existing.start()] + lede + html[existing.end():]
else:
    # first run on this file, or an older marker-less block from a previous
    # deploy — drop that too so the two never coexist
    html = re.sub(r"<!-- hero:lede\b.*?</div>\s*(?=</body>)", "", html, count=1, flags=re.S | re.I)
    # the LAST closing body tag, never the first — see the same note in the
    # cinema injection below.
    hits = list(re.finditer(r"</body>", html, re.I))
    if hits:
        at = hits[-1].start()
        html = html[:at] + lede + "\n" + html[at:]
    else:
        html = html + "\n" + lede + "\n"
open(page, "w", encoding="utf-8").write(html)
LEDE
      ok "injected hero lede (h1) into index.html"
    else
      warn "python3 not found — skipped hero lede injection"
    fi
  fi

  # hero cinema — the scroll-driven stage that opens the home view. Static in
  # the raw HTML so both headings, both paragraphs and both calls to action are
  # crawlable without JS; hero-cinema.js moves it to the top of the home view at
  # runtime and takes the <h1> block into its first caption band.
  # Re-injected (not skipped) so copy edits reach a surviving site/.
  if [ -f "$HERO_DIR/hero-cinema.html" ] && [ -f "$SITE_DIR/index.html" ]; then
    if command -v python3 >/dev/null; then
      python3 - "$SITE_DIR/index.html" "$HERO_DIR/hero-cinema.html" <<'CINEMA'
import re, sys
page, block = sys.argv[1], sys.argv[2]
html = open(page, encoding="utf-8").read()
cinema = ("<!-- hero:cinema:start -->\n"
          + open(block, encoding="utf-8").read().strip()
          + "\n<!-- hero:cinema:end -->")
existing = re.search(r"<!-- hero:cinema:start -->.*?<!-- hero:cinema:end -->", html, re.S)
if existing:
    html = html[:existing.start()] + cinema + html[existing.end():]
else:
    # the LAST closing body tag, never the first: an earlier injected block may
    # mention one inside its own comment, and matching that buries this block
    # inside a comment where the parser silently swallows it.
    hits = list(re.finditer(r"</body>", html, re.I))
    if hits:
        at = hits[-1].start()
        html = html[:at] + cinema + "\n" + html[at:]
    else:
        html = html + "\n" + cinema + "\n"
open(page, "w", encoding="utf-8").write(html)
CINEMA
      ok "injected hero cinema stage into index.html"
    else
      warn "python3 not found — skipped hero cinema injection"
    fi
  fi
}

# ---------------------------------------------------------------------------
# pretty output
# ---------------------------------------------------------------------------
if [ -t 1 ]; then
  C_RST=$'\033[0m'; C_BOLD=$'\033[1m'; C_GRN=$'\033[32m'; C_YEL=$'\033[33m'
  C_RED=$'\033[31m'; C_CRL=$'\033[38;5;173m'; C_DIM=$'\033[2m'
else
  C_RST=""; C_BOLD=""; C_GRN=""; C_YEL=""; C_RED=""; C_CRL=""; C_DIM=""
fi
step() { printf "\n%s==>%s %s%s\n" "$C_CRL$C_BOLD" "$C_RST$C_BOLD" "$1" "$C_RST"; }
ok()   { printf "  %s✓%s %s\n" "$C_GRN" "$C_RST" "$1"; }
info() { printf "  %s·%s %s\n" "$C_DIM" "$C_RST" "$1"; }
warn() { printf "  %s!%s %s\n" "$C_YEL" "$C_RST" "$1"; }
die()  { printf "\n%s✗ %s%s\n" "$C_RED$C_BOLD" "$1" "$C_RST" >&2; exit 1; }

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  sed -n '9,19p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

# ---------------------------------------------------------------------------
# 1. resolve the zip to unpack
# ---------------------------------------------------------------------------
ZIP=""
NO_CONTENT=0
case "${1:-}" in
  --no-content) NO_CONTENT=1 ;;
  "" ) ZIP="$(ls -t "$EXPORTS_DIR"/*.zip 2>/dev/null | head -1 || true)" ;;
  * )  ZIP="$1" ;;
esac

step "georgeai.dev deployment"
info "project : $PROJECT_DIR"
info "target  : $SSH_HOST:$REMOTE_DIR"

# ---------------------------------------------------------------------------
# 2. unpack export into ./site (handles a single wrapping folder)
# ---------------------------------------------------------------------------
if [ "$NO_CONTENT" -eq 0 ] && [ -n "$ZIP" ]; then
  [ -f "$ZIP" ] || die "zip not found: $ZIP"
  command -v unzip >/dev/null || die "unzip not installed (brew install unzip)"
  step "Unpacking export"
  info "source: $ZIP"

  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  unzip -q -o "$ZIP" -d "$TMP"

  # if the archive wraps everything in a single top-level folder, descend into it
  SRC="$TMP"
  entries=("$TMP"/*)
  if [ "${#entries[@]}" -eq 1 ] && [ -d "${entries[0]}" ] && [ ! -f "$TMP/index.html" ]; then
    SRC="${entries[0]}"
    info "flattened wrapper folder: $(basename "$SRC")"
  fi

  # validate the export is non-empty BEFORE wiping ./site, so a broken/empty
  # archive can't destroy the currently-deployed content.
  [ -n "$(ls -A "$SRC" 2>/dev/null)" ] || die "export is empty — ./site left untouched"

  # remove the whole dir (not just *) so stale dotfiles from a prior export
  # don't survive and get re-synced; then repopulate.
  rm -rf "$SITE_DIR"
  mkdir -p "$SITE_DIR"
  cp -R "$SRC"/. "$SITE_DIR"/
  ok "unpacked $(find "$SITE_DIR" -type f | wc -l | tr -d ' ') files into ./site"

  # The export contains no index.html. It also ships a "Bundled Page"
  # (GeorgeAI - Portfolio.html), but that is a STALE one-off snapshot that is NOT
  # regenerated on re-export. The real homepage is GeorgeAI.dc.html, which renders
  # client-side from ./support.js + ./services-data.js (both refreshed every export).
  # Serve that as index.html so nginx (index index.html;) picks it up.
  if [ ! -f "$SITE_DIR/index.html" ]; then
    HOMEPAGE="${GEORGEAI_HOMEPAGE:-GeorgeAI.dc.html}"
    if [ -f "$SITE_DIR/$HOMEPAGE" ]; then
      cp "$SITE_DIR/$HOMEPAGE" "$SITE_DIR/index.html"
      info "using $HOMEPAGE as index.html"
    elif home="$(ls -S "$SITE_DIR"/*.html 2>/dev/null | head -1)" && [ -n "$home" ]; then
      cp "$home" "$SITE_DIR/index.html"
      warn "$HOMEPAGE not found — falling back to largest html: $(basename "$home")"
    else
      warn "no .html to use as index.html — check the export structure"
    fi
  fi

  # inject the auth bridge so the static signin form talks to the Django auth API.
  # kept out of the export (added here) so it survives re-exports. Idempotent.
  if [ -f "$SITE_DIR/index.html" ] && ! grep -q '/auth.js' "$SITE_DIR/index.html"; then
    if command -v python3 >/dev/null; then
      python3 - "$SITE_DIR/index.html" <<'PY'
import re, sys
p = sys.argv[1]
html = open(p, encoding="utf-8").read()
tag = '<script src="/auth.js" defer></script>'
html = re.sub(r"</body>", tag + "</body>", html, count=1, flags=re.I) \
    if re.search(r"</body>", html, re.I) else html + "\n" + tag + "\n"
open(p, "w", encoding="utf-8").write(html)
PY
      ok "injected auth.js into index.html"
    else
      warn "python3 not found — skipped auth.js injection"
    fi
  fi

  # frontend assets + SEO layer BEFORE the mirror, so frontend/template gets
  # the same asset- and SEO-complete content.
  apply_assets
  apply_seo
  apply_copy
  apply_brand
  apply_images
  apply_pages
  apply_prune
  apply_media
  apply_hero
  apply_widget
  # mirror the unpacked content (incl. the derived index.html) into the frontend
  # template dir so the Django backend in backend/ can build against the same export.
  if [ -n "$TEMPLATE_DIR" ]; then
    rm -rf "${TEMPLATE_DIR:?}"
    mkdir -p "$TEMPLATE_DIR"
    cp -R "$SITE_DIR"/. "$TEMPLATE_DIR"/
    ok "mirrored into ${TEMPLATE_DIR#$PROJECT_DIR/}"
  fi
else
  step "Using existing ./site (no zip)"
  # keep assets + SEO layer current even on content-less redeploys
  apply_assets
  apply_seo
  apply_copy
  apply_brand
  apply_images
  apply_pages
  apply_prune
  apply_media
  apply_hero
  apply_widget
fi

[ -f "$SITE_DIR/index.html" ] || die "./site has no index.html — nothing to deploy"
ok "content ready: ./site ($(du -sh "$SITE_DIR" | cut -f1))"

# ---------------------------------------------------------------------------
# 3. sync project to the VPS
# ---------------------------------------------------------------------------
step "Syncing to VPS"
ssh -o BatchMode=yes -o ConnectTimeout=10 "$SSH_HOST" "mkdir -p \"$REMOTE_DIR/site\" \"$REMOTE_DIR/deploy\"" \
  || die "cannot reach $SSH_HOST over ssh"

rsync -az --delete -e ssh "$SITE_DIR"/ "$SSH_HOST:$REMOTE_DIR/site/"
ok "site/ synced"
# nginx.conf is bind-mounted into the container as a single file. rsync replaces
# it with a new inode, but the running container stays bound to the old one — so
# neither `nginx -s reload` nor plain `up -d` can ever pick up the change.
# Compare the local file against what the RUNNING CONTAINER actually serves (not
# the remote disk copy, which rsync may already have updated under a stale mount)
# and force-recreate in step 4 so the mount rebinds when they differ.
# `|| true`: container missing/stopped (e.g. first deploy) → treat as changed.
NGINX_CHANGED=0
CONTAINER_NGINX_SUM=$(ssh "$SSH_HOST" "docker exec georgeai-web cksum /etc/nginx/conf.d/default.conf 2>/dev/null" | awk '{print $1, $2}' || true)
LOCAL_NGINX_SUM=$(cksum "$PROJECT_DIR/deploy/nginx.conf" | awk '{print $1, $2}')
[ "$CONTAINER_NGINX_SUM" = "$LOCAL_NGINX_SUM" ] || NGINX_CHANGED=1

# compose runs from $REMOTE_DIR and references ./deploy/nginx.conf — sync only what
# it needs (avoids shipping a second, unused copy of docker-compose.yml under deploy/).
rsync -az -e ssh "$PROJECT_DIR/deploy/nginx.conf"         "$SSH_HOST:$REMOTE_DIR/deploy/nginx.conf"
rsync -az -e ssh "$PROJECT_DIR/deploy/docker-compose.yml" "$SSH_HOST:$REMOTE_DIR/docker-compose.yml"
ok "deploy config synced"

# The Django API is built on the VPS from this source. Excludes keep the local
# venv, caches and — critically — the dev backend/.env off the server; the
# production env lives at deploy/backend.env and is never in this repo.
rsync -az --delete -e ssh \
  --exclude '.venv/' --exclude '__pycache__/' --exclude '*.pyc' \
  --exclude '.env' --exclude 'logs/' --exclude 'staticfiles/' \
  "$PROJECT_DIR/backend/" "$SSH_HOST:$REMOTE_DIR/backend/"
ok "backend source synced"

# ---------------------------------------------------------------------------
# 4. bring up the container behind Traefik
# ---------------------------------------------------------------------------
step "Bringing up container"
# `up -d` recreates on any compose/label change and is a no-op otherwise; the
# bind-mounted ./site directory is live the instant rsync finishes. The one
# blind spot is the single-file nginx.conf mount (see step 3): when that file
# changed we must force-recreate so the container rebinds to the new inode.
COMPOSE_FLAGS="--remove-orphans"
if [ "$NGINX_CHANGED" = 1 ]; then
  warn "nginx.conf changed — force-recreating container so the file mount rebinds"
  COMPOSE_FLAGS="$COMPOSE_FLAGS --force-recreate"
fi
ssh "$SSH_HOST" "cd \"$REMOTE_DIR\" && docker compose up -d --build $COMPOSE_FLAGS" \
  || die "docker compose failed on VPS"
ok "georgeai-web is up"

# Migrations run after the container is up but before the health checks gate
# the deploy, so a bad migration fails the run rather than surfacing later as
# 500s on /api/auth/*.
if ssh "$SSH_HOST" "cd \"$REMOTE_DIR\" && docker compose exec -T georgeai-app python manage.py migrate --noinput" >/dev/null 2>&1; then
  ok "migrations applied"
else
  die "migrate failed — inspect: ssh $SSH_HOST 'docker logs georgeai-app'"
fi

# ---------------------------------------------------------------------------
# 5. health checks
# ---------------------------------------------------------------------------
step "Verifying"
sleep 3
# internal check (container reachable on the docker network, independent of DNS).
# This is the real gate — fail the deploy if the container isn't serving.
if ssh "$SSH_HOST" "docker exec georgeai-web wget -qO- http://localhost/healthz 2>/dev/null" | grep -q ok; then
  ok "container healthy (internal /healthz)"
else
  die "internal health check failed — inspect: ssh $SSH_HOST 'docker logs georgeai-web'"
fi

# The API is the whole point of shipping Django — a 404 here means nginx is
# still answering /api/ with an HTML error page, which is the bug this
# replaced. Check the JSON shape, not just the status code.
if ssh "$SSH_HOST" "docker exec georgeai-web wget -qO- http://localhost/api/auth/me 2>/dev/null" | grep -q 'authenticated'; then
  ok "API healthy (/api/auth/me returns JSON)"
else
  die "API check failed — inspect: ssh $SSH_HOST 'docker logs georgeai-app'"
fi

DEPLOY_FAIL=0
check_url() {
  local url="$1" code
  # curl prints "000" on connect failure; capture it without a spurious extra echo
  code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 12 "$url")" || code="000"
  if [ "$code" = "200" ]; then
    ok "$url → 200"
  elif [ "$code" = "000" ]; then
    warn "$url → no response yet (DNS not pointing to this VPS?)"
  else
    warn "$url → $code (reachable but not serving 200)"
    DEPLOY_FAIL=1
  fi
}
# www must permanently redirect to the apex, not serve 200 — a 200 here means the
# Traefik www router lost its redirect middleware and the duplicate origin is back.
check_redirect_to_apex() {
  local url="$1" code loc
  code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 12 "$url")" || code="000"
  loc="$(curl -s -o /dev/null -w '%{redirect_url}' --max-time 12 "$url")" || loc=""
  case "$code" in
    301|308)
      case "$loc" in
        https://georgeai.dev/*|https://georgeai.dev) ok "$url → $code → $loc" ;;
        *) warn "$url → $code but to '$loc', expected the apex"; DEPLOY_FAIL=1 ;;
      esac
      ;;
    000) warn "$url → no response yet (DNS not pointing to this VPS?)" ;;
    200) warn "$url → 200 (expected a redirect to the apex — duplicate origin is back)"; DEPLOY_FAIL=1 ;;
    *)   warn "$url → $code (expected 301/308 to the apex)"; DEPLOY_FAIL=1 ;;
  esac
}

for h in "${PROD_HOSTS[@]}"; do check_url "https://$h"; done
for h in "${PROD_REDIRECT_HOSTS[@]}"; do check_redirect_to_apex "https://$h"; done

# ---------------------------------------------------------------------------
# done
# ---------------------------------------------------------------------------
step "Done"
[ "$DEPLOY_FAIL" -eq 0 ] || die "a host is reachable but returned a non-200 status — see above"
ok "Live:  https://georgeai.dev"
printf "\n%sTip:%s drop a new export in ./exports and re-run ./deploy.sh to publish.\n" "$C_BOLD" "$C_RST"
