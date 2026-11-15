# 01.10 — Hartă de feature flags

**Secțiune:** Viziune & arhitectură  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Introdu un mecanism simplu de feature flags (model `Flag` sau `django-waffle`) pentru lansarea treptată a funcțiilor consolei: artifacts, projects, extended thinking, web search, share links.

**Acceptare:** flag-urile se pot activa per user din admin; frontend-ul primește lista în `/api/console/bootstrap`.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
