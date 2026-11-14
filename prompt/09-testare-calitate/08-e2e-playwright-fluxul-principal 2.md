# 09.08 — E2E Playwright — fluxul principal

**Secțiune:** Testare & calitate  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Test E2E: signup → new chat → trimite mesaj → stream → regenerate → edit → redenumește → caută → șterge. Rulat cu provider fake.
**Acceptare:** stabil 20/20 rulări; rulează în CI headless.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
