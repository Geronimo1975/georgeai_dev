# 04.01 — Scaffold SPA

**Secțiune:** Frontend — UI-ul consolei  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Creează `console/frontend/` (React + Vite + TypeScript conform ADR-ului) cu build în `backend/console/static/console/`, servit de Django la `/console/` cu `ensure_csrf_cookie`. Router client (`/console/new`, `/console/chat/:id`, `/console/project/:id`).
**Acceptare:** `npm run dev` cu proxy spre Django; build reproducibil; zero dependențe de UI kit greu.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
