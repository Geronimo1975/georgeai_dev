# 01.07 — Rutare consolă vs site static

**Secțiune:** Viziune & arhitectură  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Definește cum ajunge `https://georgeai.dev/console/` (sau `app.georgeai.dev`) la Django, în timp ce homepage-ul rămâne pe nginx. Compară subpath vs subdomeniu (cookies, CSRF, CSP, SEO). Scrie labels Traefik în `deploy/docker-compose.yml` pentru un serviciu nou `georgeai-app` fără a atinge `georgeai-web`.

**Acceptare:** diff de config + plan de rollback într-un singur pas.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
