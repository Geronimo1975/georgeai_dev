# 01.14 — Background jobs

**Secțiune:** Viziune & arhitectură  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Alege și configurează un runner de joburi (Celery, `django-tasks`/Django 6 Tasks, sau RQ) pentru: generarea titlurilor de conversație, procesarea fișierelor încărcate, rezumate pentru proiecte, export de date.

**Acceptare:** un job demo `generate_conversation_title` rulează local și în compose; retry cu backoff.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
