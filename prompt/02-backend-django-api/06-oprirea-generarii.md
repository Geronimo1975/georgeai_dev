# 02.06 — Oprirea generării

**Secțiune:** Backend Django & API  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Implementează butonul „Stop” ca pe claude.ai: `POST /messages/{id}/stop` setează un flag în Redis; workerul închide streamul spre Anthropic, salvează textul parțial cu `stop_reason='user_cancelled'`.

**Acceptare:** mesajul parțial rămâne vizibil și poate fi continuat sau regenerat.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
