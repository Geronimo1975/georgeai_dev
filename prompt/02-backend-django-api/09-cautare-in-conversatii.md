# 02.09 — Căutare în conversații

**Secțiune:** Backend Django & API  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Căutare full-text în titluri și conținutul mesajelor cu PostgreSQL `tsvector` (configurații `simple` + `english`/`german`/`romanian` unde există), cu highlight de fragmente.

**Acceptare:** `GET /search?q=` < 150 ms pe 50k mesaje; index GIN; respectă ownership.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
