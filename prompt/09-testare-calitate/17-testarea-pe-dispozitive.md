# 09.17 — Testarea pe dispozitive

**Secțiune:** Testare & calitate  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Plan de testare manuală pe dispozitive reale (iPhone Safari, Android Chrome, iPad, Firefox desktop) cu checklist pentru composer, tastatură virtuală, artifacts.

**Acceptare:** checklist în `docs/console/QA-DEVICES.md`, rulat la fiecare release.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
