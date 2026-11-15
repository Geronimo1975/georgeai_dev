# 06.01 — Extinderea auth-ului existent

**Secțiune:** Autentificare, securitate & GDPR  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Pornind de la `backend/accounts` (user pe email, DRF session auth, `auth.js`), adaugă verificare email, resetare parolă și pagini de login/signup dedicate consolei în stilul claude.ai (centrate, minimaliste).

**Acceptare:** fluxurile existente `/api/auth/*` nu se rup; testele `accounts` trec.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
