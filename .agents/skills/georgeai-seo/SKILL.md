---
name: georgeai-seo
description: Edit SEO for georgeai.dev — meta tags, OG, JSON-LD, robots.txt, sitemap, llms.txt. Use for any SEO/metadata change to the site.
---

# SEO layer for georgeai.dev

All SEO lives in `seo/` and is applied by `deploy.sh` on every deploy
(idempotent, runs even with `--no-content`). **Never edit SEO in `site/`** —
it is wiped and regenerated.

| File | What it is |
|------|------------|
| `seo/head.html` | title / meta / OG / JSON-LD block, injected before `</head>` (marker `seo:head`); deploy also sets `lang="en"` on `<html>` |
| `seo/robots.txt` | copied into site/ |
| `seo/sitemap.xml` | copied into site/ |
| `seo/llms.txt` | AI-crawler guidance, copied into site/ |
| `seo/favicon.svg` | copied into site/ |
| `seo/generate_service_pages.py` | service-page generator (data: `georgeai_services.json`) |

## Workflow

1. Edit files in `seo/`.
2. Apply with `./deploy.sh --no-content` (re-injects SEO without unpacking a new export).
3. Verify: `curl -s https://georgeai.dev | grep -A2 'seo:head'` and check
   `https://georgeai.dev/robots.txt`, `/sitemap.xml`, `/llms.txt`.

Design/branding context for OG images etc.: `DESIGN-AGENTS.md`
(warm cream/coral palette, `#cc785c` primary).
