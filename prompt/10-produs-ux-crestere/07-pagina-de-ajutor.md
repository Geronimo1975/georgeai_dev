# 10.07 — Pagina de ajutor

**Secțiune:** Produs, UX & creștere  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Centru de ajutor (`/help/`) cu articole: ce sunt proiectele, cum funcționează artifacts, limitele de utilizare, confidențialitatea datelor, scurtături.

**Acceptare:** căutabil, legat din consolă (meniul „?”), în DE/EN/RO.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
