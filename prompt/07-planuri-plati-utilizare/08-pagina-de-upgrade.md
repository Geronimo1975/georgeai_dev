# 07.08 — Pagina de upgrade

**Secțiune:** Planuri, plăți & limite de utilizare  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Modal/pagină de upgrade în consolă cu comparația planurilor, accentul pe planul recomandat, apărând contextual când userul atinge o limită.

**Acceptare:** respectă `ui-ux-pro-max`; urmărit în analytics intern (fără GA în consolă).

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
