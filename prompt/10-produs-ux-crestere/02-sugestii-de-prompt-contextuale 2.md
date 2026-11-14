# 10.02 — Sugestii de prompt contextuale

**Secțiune:** Produs, UX & creștere  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Sugestii pe ecranul New chat bazate pe interesele declarate și pe serviciile georgeai.dev (Django, n8n, SEO, CRM, AI) — rotite, clicabile.
**Acceptare:** configurabile din admin fără deploy.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
