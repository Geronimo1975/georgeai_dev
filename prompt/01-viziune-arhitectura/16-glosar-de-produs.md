# 01.16 — Glosar de produs

**Secțiune:** Viziune & arhitectură  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Creează `docs/console/GLOSSARY.md` cu termenii folosiți uniform în cod, UI și documentație (conversation vs chat, project, knowledge, artifact, style, turn, branch, regenerate, usage window). Include traducerile RO/DE/EN pentru UI.

**Acceptare:** fiecare termen are numele de model/variabilă corespunzător.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
