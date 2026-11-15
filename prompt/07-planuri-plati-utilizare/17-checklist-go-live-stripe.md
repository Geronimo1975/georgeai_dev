# 07.17 — Checklist go-live Stripe

**Secțiune:** Planuri, plăți & limite de utilizare  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Extinde checklist-ul de go-live existent (test → live) cu abonamentele consolei: produse/prețuri live, webhook live, chei în `.env`, `GEORGEAI_STRIPE_MODE=live`, Impressum completat (`seo/legal.json`).

**Acceptare:** `docs/console/STRIPE-GO-LIVE.md`; blocant dacă Impressum e placeholder.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
