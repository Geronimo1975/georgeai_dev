# 08.08 — Migrații fără downtime

**Secțiune:** DevOps, deploy & observabilitate  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Ghid și verificare pentru migrații sigure (expand/contract, fără lock-uri lungi pe `Message`), cu `django-migration-linter` în CI.

**Acceptare:** documentat; CI prinde o migrare periculoasă de test.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
