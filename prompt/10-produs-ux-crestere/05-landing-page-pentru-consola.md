# 10.05 — Landing page pentru consolă

**Secțiune:** Produs, UX & creștere  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Pagină de prezentare `/console-landing/` (repo-owned în `pages/`) care explică GeorgeAI Console, cu demo vizual, planuri și CTA spre signup — consecventă cu brandul și `ui-ux-pro-max`.

**Acceptare:** trece prin `apply_pages`; SEO meta; fără a copia branding Anthropic.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
