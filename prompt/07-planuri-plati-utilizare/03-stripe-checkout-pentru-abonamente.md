# 07.03 — Stripe Checkout pentru abonamente

**Secțiune:** Planuri, plăți & limite de utilizare  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Integrează Stripe Checkout (mode=subscription) din pagina de billing a consolei, în modul test (`acct_1TIuuYEffkWmXH1r`), cu `client_reference_id` = user id.

**Acceptare:** consultă skill-ul `stripe:stripe-best-practices`; flux complet testat cu carduri de test.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
