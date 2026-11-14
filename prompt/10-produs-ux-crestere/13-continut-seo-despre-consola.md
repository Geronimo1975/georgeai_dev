# 10.13 — Conținut SEO despre consolă

**Secțiune:** Produs, UX & creștere  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

3 articole de blog (format `blog/` cu header `<!--meta {json} -->`) despre GeorgeAI Console: comparație cu claude.ai pentru companii germane (GDPR), cazuri de utilizare, ghid de proiecte.

**Acceptare:** generate prin `generate_service_pages.py`; în sitemap; `llms.txt` actualizat.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
