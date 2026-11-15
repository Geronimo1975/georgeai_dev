# 08.02 — Serviciul georgeai-app în compose

**Secțiune:** DevOps, deploy & observabilitate  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Adaugă în `deploy/docker-compose.yml` serviciile `georgeai-app` (Django ASGI), `georgeai-worker` (joburi) și Redis, pe rețeaua `gethub_gethub-network`, cu labels Traefik pentru `/console` și `/api`.

**Acceptare:** `georgeai-web` (nginx) neschimbat funcțional; rollback documentat.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
