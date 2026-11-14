# 08.01 — Dockerfile de producție

**Secțiune:** DevOps, deploy & observabilitate  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Rescrie `backend/Dockerfile` multi-stage: build frontend (Node) → Python slim, user non-root, `collectstatic`, uvicorn/gunicorn cu workers ASGI pentru SSE.

**Acceptare:** imagine < 300 MB; pornește cu `docker run` și `.env`; healthcheck.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
