# 07.04 — Webhook-uri Stripe

**Secțiune:** Planuri, plăți & limite de utilizare  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Endpoint de webhook cu verificare de semnătură, idempotent pe `event.id`, pentru `checkout.session.completed`, `customer.subscription.*`, `invoice.paid`, `invoice.payment_failed`.

**Acceptare:** test cu `stripe trigger`; relația cu workflow-ul n8n `stripe-orders` documentată (cine procesează ce).

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
