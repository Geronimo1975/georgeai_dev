# 10.16 — Experimente A/B

**Secțiune:** Produs, UX & creștere  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Infrastructură simplă de experimente (atribuire deterministă per user, expunere logată) pentru teste pe ecranul New chat și pe modalul de upgrade.

**Acceptare:** primul experiment configurat; analiză cu interval de încredere.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
