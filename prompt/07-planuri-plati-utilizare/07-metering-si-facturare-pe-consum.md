# 07.07 — Metering și facturare pe consum

**Secțiune:** Planuri, plăți & limite de utilizare  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Opțional pentru Team/API: raportare usage spre Stripe Billing Meters pentru depășiri plătite.

**Acceptare:** ADR dacă merită; prototip în test mode.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
