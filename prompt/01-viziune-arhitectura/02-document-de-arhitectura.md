# 01.02 — Document de arhitectură

**Secțiune:** Viziune & arhitectură  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Scrie `docs/console/ARCHITECTURE.md` pentru GeorgeAI Console: componente (Django API, worker de streaming, frontend SPA, PostgreSQL, Redis, storage fișiere, Anthropic API), fluxul unui mesaj de la tastă până la ultimul token, și cum coexistă cu nginx-ul static actual (`/console/` rutat spre Django, restul rămâne static).

**Acceptare:** diagramă Mermaid, secțiune „decizii respinse și de ce”, fără nicio modificare de cod.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
