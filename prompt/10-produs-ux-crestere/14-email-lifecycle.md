# 10.14 — Email lifecycle

**Secțiune:** Produs, UX & creștere  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Secvență de emailuri: ziua 0 bun venit, ziua 2 „încearcă proiectele”, ziua 5 artifacts, ziua 10 ofertă Pro, reactivare după 14 zile de inactivitate (prin n8n).

**Acceptare:** dezabonare cu un click; conținut DE/EN/RO.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
