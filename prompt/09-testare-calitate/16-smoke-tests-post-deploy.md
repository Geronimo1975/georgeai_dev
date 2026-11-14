# 09.16 — Smoke tests post-deploy

**Secțiune:** Testare & calitate  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Script rulat automat după fiecare deploy: login cu user de test, trimite un mesaj cu modelul cel mai ieftin, verifică stream complet și ștergere.

**Acceptare:** eșecul declanșează alertă și blochează promovarea staging → producție.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
