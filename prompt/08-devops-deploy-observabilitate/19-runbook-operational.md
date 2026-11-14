# 08.19 — Runbook operațional

**Secțiune:** DevOps, deploy & observabilitate  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Scrie `docs/console/RUNBOOK.md`: restart servicii, rotire chei, golire cozi, restore DB, investigarea unui stream blocat, creșterea limitelor pentru un client.

**Acceptare:** fiecare procedură cu comenzi exacte, testate pe staging.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
