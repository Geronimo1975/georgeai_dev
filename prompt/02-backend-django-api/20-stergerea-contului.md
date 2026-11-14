# 02.20 — Ștergerea contului

**Secțiune:** Backend Django & API  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Flux complet „Delete account”: confirmare prin parolă, anulare abonament Stripe, ștergere conversații/fișiere/artifacts, anonimizare usage events, email de confirmare.

**Acceptare:** job idempotent, teste, document al datelor păstrate legal (facturi).

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
