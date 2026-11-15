# 05.02 — Protocol de creare artifacts

**Secțiune:** Artifacts, proiecte & fișiere  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Definește în system prompt și parser cum creează modelul un artifact (tool `create_artifact`/`update_artifact` cu schemă JSON — preferat față de taguri XML), cu update incremental (find/replace) pentru fișiere mari.
**Acceptare:** parserul funcționează pe stream parțial; teste pe toate tipurile.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
