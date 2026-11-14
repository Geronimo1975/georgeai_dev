# 02.19 — Performanța query-urilor

**Secțiune:** Backend Django & API  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Profilează endpoint-urile listare conversații, încărcare conversație (500 mesaje) și bootstrap cu `django-debug-toolbar`/`assertNumQueries`. Elimină N+1 cu `select_related`/`prefetch_related` și indexuri.

**Acceptare:** număr fix de query-uri indiferent de mărimea datelor, fixat prin teste.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
