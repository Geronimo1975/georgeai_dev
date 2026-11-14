# 06.07 — CSP pentru consolă

**Secțiune:** Autentificare, securitate & GDPR  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

CSP strict pentru `/console/` (fără `unsafe-eval`, spre deosebire de homepage), cu nonce pentru scripturi, `connect-src` doar spre API, `frame-src` doar sandbox-ul de artifacts. Mai întâi Report-Only.

**Acceptare:** zero violări în fluxurile principale; plan de trecere la enforced.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
