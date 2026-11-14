# 07.02 — Modelul Subscription

**Secțiune:** Planuri, plăți & limite de utilizare  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Modele `Plan`, `Subscription` (user/org, stripe ids, status, current_period_end, cancel_at), cu planul derivat într-un singur loc (`user.entitlements`).

**Acceptare:** teste pentru toate stările Stripe (trialing, active, past_due, canceled).

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
