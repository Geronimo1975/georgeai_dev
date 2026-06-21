#!/usr/bin/env bash
#
# deploy.sh — georgeai.dev deployment pipeline
#
# Takes an HTML export (.zip) from the design tool, unpacks it into ./site,
# syncs the project to the VPS, (re)starts the nginx container behind Traefik,
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
# also mirror each unpacked export here so the Django frontend (backend/) can build
# against it. Set GEORGEAI_TEMPLATE_DIR= (empty) to skip the mirror.
TEMPLATE_DIR="${GEORGEAI_TEMPLATE_DIR-$PROJECT_DIR/frontend/template}"

PROD_HOSTS=("georgeai.dev" "www.georgeai.dev")

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

[ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ] && { sed -n '2,30p' "$0" | sed 's/^#//'; exit 0; }

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

  rm -rf "${SITE_DIR:?}"/*
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

  # mirror the unpacked content (incl. the derived index.html) into the frontend
  # template dir so the Django backend in backend/ can build against the same export.
  if [ -n "$TEMPLATE_DIR" ]; then
    rm -rf "${TEMPLATE_DIR:?}"/*
    mkdir -p "$TEMPLATE_DIR"
    cp -R "$SITE_DIR"/. "$TEMPLATE_DIR"/
    ok "mirrored into ${TEMPLATE_DIR#$PROJECT_DIR/}"
  fi
else
  step "Using existing ./site (no zip)"
fi

[ -f "$SITE_DIR/index.html" ] || die "./site has no index.html — nothing to deploy"
ok "content ready: ./site ($(du -sh "$SITE_DIR" | cut -f1))"

# ---------------------------------------------------------------------------
# 3. sync project to the VPS
# ---------------------------------------------------------------------------
step "Syncing to VPS"
ssh -o BatchMode=yes -o ConnectTimeout=10 "$SSH_HOST" "mkdir -p $REMOTE_DIR/site $REMOTE_DIR/deploy" \
  || die "cannot reach $SSH_HOST over ssh"

rsync -az --delete -e ssh "$SITE_DIR"/ "$SSH_HOST:$REMOTE_DIR/site/"
ok "site/ synced"
rsync -az -e ssh "$PROJECT_DIR/deploy/" "$SSH_HOST:$REMOTE_DIR/deploy/"
rsync -az -e ssh "$PROJECT_DIR/deploy/docker-compose.yml" "$SSH_HOST:$REMOTE_DIR/docker-compose.yml"
ok "deploy config synced"

# ---------------------------------------------------------------------------
# 4. (re)start the container behind Traefik
# ---------------------------------------------------------------------------
step "Restarting container"
ssh "$SSH_HOST" "cd $REMOTE_DIR && docker compose up -d --remove-orphans && docker compose restart georgeai-web" \
  || die "docker compose failed on VPS"
ok "georgeai-web is up"

# ---------------------------------------------------------------------------
# 5. health checks
# ---------------------------------------------------------------------------
step "Verifying"
sleep 3
# internal check (container reachable on the docker network, independent of DNS)
if ssh "$SSH_HOST" "docker exec georgeai-web wget -qO- http://localhost/healthz 2>/dev/null" | grep -q ok; then
  ok "container healthy (internal /healthz)"
else
  warn "internal health check did not return ok — check: ssh $SSH_HOST 'docker logs georgeai-web'"
fi

check_url() {
  local url="$1"
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 12 "$url" 2>/dev/null || echo 000)"
  if [ "$code" = "200" ]; then ok "$url → $code"
  elif [ "$code" = "000" ]; then warn "$url → no response (DNS not pointing here yet?)"
  else warn "$url → $code"; fi
}
for h in "${PROD_HOSTS[@]}"; do check_url "https://$h"; done

# ---------------------------------------------------------------------------
# done
# ---------------------------------------------------------------------------
step "Done"
ok "Live:  https://georgeai.dev"
printf "\n%sTip:%s drop a new export in ./exports and re-run ./deploy.sh to publish.\n" "$C_BOLD" "$C_RST"
