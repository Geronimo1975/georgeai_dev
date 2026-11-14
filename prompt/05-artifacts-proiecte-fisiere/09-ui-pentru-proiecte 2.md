# 05.09 — UI pentru proiecte

**Secțiune:** Artifacts, proiecte & fișiere  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Pagina de proiect ca pe claude.ai: titlu și descriere, lista conversațiilor din proiect, composer pentru conversație nouă în proiect, panou dreapta „Project knowledge” + „Instructions”.
**Acceptare:** indicator de capacitate (% din context ocupat de knowledge).

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
