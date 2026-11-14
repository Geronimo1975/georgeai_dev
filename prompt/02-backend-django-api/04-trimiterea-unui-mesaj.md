# 02.04 — Trimiterea unui mesaj

**Secțiune:** Backend Django & API  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

`POST /api/console/v1/conversations/{id}/messages` acceptă text + atașamente + `parent_id`, salvează mesajul user, pornește generarea și returnează imediat ID-urile (mesaj user + mesaj asistent placeholder). Idempotency-Key obligatoriu.

**Acceptare:** dublu-submit cu aceeași cheie nu creează mesaje duplicate.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
