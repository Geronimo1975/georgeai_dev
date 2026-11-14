# 01.01 — Audit de paritate claude.ai

**Secțiune:** Viziune & arhitectură  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Analizează claude.ai (din cunoștințele tale și din documentația publică Anthropic) și produ `docs/console/PARITY.md`: un tabel cu toate funcțiile vizibile ale consolei claude.ai (sidebar, new chat, projects, artifacts, styles, model picker, extended thinking, attachments, search, share, settings, usage limits, keyboard shortcuts, mobile). Pentru fiecare: descriere, prioritate (P0/P1/P2), complexitate (S/M/L), dependențe și starea curentă în acest repo.

**Acceptare:** minim 40 de rânduri; P0 = MVP care se simte ca claude.ai în primele 10 secunde de folosire.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
