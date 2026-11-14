# 01.20 — Revizuire de arhitectură adversarială

**Secțiune:** Viziune & arhitectură  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Joacă rolul unui staff engineer sceptic: citește `docs/console/ARCHITECTURE.md`, `DATA-MODEL.md` și ADR-urile și găsește cele mai slabe 10 puncte (scalare, cost, complexitate inutilă, puncte unice de eșec).

**Acceptare:** raport cu severitate și propunere de corecție pentru fiecare; nu modifica fișierele, doar raportează.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
