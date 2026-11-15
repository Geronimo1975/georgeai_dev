# 01.06 — Structura de aplicații Django

**Secțiune:** Viziune & arhitectură  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Propune și creează scheletul de aplicații Django sub `backend/`: `console` (conversații/mesaje), `llm` (client Anthropic, abstracție provider), `projects`, `artifacts`, `files`, `billing`, `usage`. Fiecare cu `apps.py`, `urls.py`, `models.py` gol, înregistrate în settings.

**Acceptare:** `python manage.py check` trece; testele `accounts` trec în continuare; nicio migrare cu modele încă.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
