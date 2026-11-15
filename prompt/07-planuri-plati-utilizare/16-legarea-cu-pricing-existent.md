# 07.16 — Legarea cu /pricing/ existent

**Secțiune:** Planuri, plăți & limite de utilizare  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Actualizează `pages/pricing/index.html` (repo-owned) ca să includă planurile consolei lângă serviciile existente, fără a strica cele 7 Payment Links și testul `tests/test_payments_pipeline.py`.

**Acceptare:** `CATALOG` din test actualizat dacă se schimbă prețuri; suita trece.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
