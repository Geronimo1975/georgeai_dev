# 02.05 — Endpoint de streaming SSE

**Secțiune:** Backend Django & API  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

`GET /api/console/v1/messages/{id}/stream` emite evenimente SSE normalizate: `message_start`, `content_block_start`, `delta` (text/thinking), `content_block_stop`, `message_stop`, `error`, `ping`. Acceptă `Last-Event-ID` pentru reluare.

**Acceptare:** funcționează prin Traefik fără buffering (`X-Accel-Buffering: no`), test cu un provider fake.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
