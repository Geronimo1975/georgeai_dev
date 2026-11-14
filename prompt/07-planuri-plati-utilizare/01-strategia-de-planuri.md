# 07.01 — Strategia de planuri

**Secțiune:** Planuri, plăți & limite de utilizare  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Definește planurile Free / Pro / Team (și opțional Max) cu prețuri în EUR, modele incluse, limite de utilizare, mărime fișiere, proiecte, funcții (artifacts, thinking, web search). Calculează marja pe baza costului API per utilizator tipic.

**Acceptare:** `docs/console/PLANS.md` cu tabel și model de cost; aprobare umană înainte de implementare.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
