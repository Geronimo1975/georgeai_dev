---
name: georgeai-deploy
description: Deploy georgeai.dev to the VPS. Use when the user asks to deploy, redeploy, ship the site, publish a new export, or when a new .zip lands in exports/.
---

# Deploying georgeai.dev

Everything goes through `deploy.sh` — never rsync or edit `site/` by hand.

```bash
./deploy.sh                        # newest zip in exports/ → site/ → VPS → restart → health checks
./deploy.sh exports/georgeai.zip   # specific archive
./deploy.sh --no-content           # redeploy current site/ without unpacking a new export
```

Config env vars (defaults in parentheses): `GEORGEAI_SSH_HOST` (`macbook-air`),
`GEORGEAI_REMOTE_DIR` (`/opt/georgeai`), `GEORGEAI_HOMEPAGE` (`GeorgeAI.dc.html`),
`GEORGEAI_TEMPLATE_DIR` (`frontend/template`, empty = skip mirroring).

## The layers

The export is only the starting point. Everything the design tool does *not*
ship is layered back on at deploy time from repo-owned source dirs, so it
survives every re-export. **All layers are idempotent and all of them run even
with `--no-content`** — that flag skips unpacking, not the layers.

| Layer | Source | Adds |
|---|---|---|
| `apply_assets` | `backend/assets/` | `auth.js` + `audit.js` and their script tags |
| `apply_seo` | `seo/` | head block, footer links, robots/sitemap/llms/favicon, `seo/assets/` (OG card), service + blog pages |
| `apply_copy` | `seo/hero.json`, `seo/testimonials.json` | marketing copy the export hard-codes and would revert |
| `apply_brand` | `brand/apply_brand.py` | rewrites the export's coral into WCAG-AA accents |
| `apply_images` | `images/` | swaps placeholder slots for the committed SVG mockups |
| `apply_pages` | `pages/` | repo-owned static pages (`/pricing/`) |
| `apply_prune` | — | deletes junk the export ships (a résumé with a home address, QA screenshots, fictional-persona pages). Deliberately a **denylist** |
| `apply_media` | — | `ffmpeg` faststart remux (the export writes `moov` after `mdat`) |
| `apply_hero` | `hero/` | hero motion + cinema stage, and a lighter `hero.mp4` re-encode |
| `apply_widget` | `seo/inject_widget.py` | the lead-capture widget — runs **last**, so it also covers generated pages |

Full detail lives in `CLAUDE.md`. If a change must survive the next export, it
belongs in one of those source dirs — never in `site/`.

## Hard rules

- **Never** use `GeorgeAI - Portfolio.html` as homepage — it is a stale one-off
  snapshot. The real homepage is `GeorgeAI.dc.html` (renders client-side from
  `support.js` + `services-data.js`).
- `site/` and `frontend/template/` are **wiped every deploy** *and are
  gitignored* — the working tree can be the only copy, so `git clean -xfd` is
  destructive here. Recovery procedure: `CLAUDE.md` → "Recovering `site/`".
- **Do not seed `exports/` from `~/Downloads`.** Those zips predate what is
  live; `deploy.sh` picks the newest by mtime and would silently roll
  production back. Verify a candidate by diffing its `support.js` and
  `services-data.js` against `site/` first — no layer touches those two, so a
  size gap is export age.
- SEO edits go in `seo/` (see the georgeai-seo skill), never in `site/`.

## Verify after deploy

deploy.sh runs its own checks: container health, `/api/auth/me`, apex → 200,
and **www → 301 to the apex** (a 200 on www means the redirect middleware was
lost and the duplicate origin is back). To double-check by hand:

```bash
curl -sI https://georgeai.dev | head -5
curl -sI https://www.georgeai.dev/ | grep -i '^HTTP\|^location'   # expect 308 → apex
curl -sI https://georgeai.dev/services/crm | grep -i location     # expect a RELATIVE /services/crm/
ssh macbook-air "docker logs --tail 20 georgeai-web"
```
