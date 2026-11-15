# 01.04 — ADR: transport pentru streaming

**Secțiune:** Viziune & arhitectură  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Decide între Server-Sent Events, WebSocket (Django Channels) și fetch + ReadableStream pentru streamingul răspunsurilor. Ia în calcul Traefik v2.11 (buffering, timeouts), gunicorn vs uvicorn, reconectare după pierderea rețelei și oprirea generării („Stop”) ca pe claude.ai.

**Acceptare:** `docs/console/adr/0002-streaming.md` + config Traefik/nginx necesar listat explicit.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
