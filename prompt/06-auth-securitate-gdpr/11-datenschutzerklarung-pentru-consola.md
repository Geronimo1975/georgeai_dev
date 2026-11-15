# 06.11 — Datenschutzerklärung pentru consolă

**Secțiune:** Autentificare, securitate & GDPR  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Redactează secțiunile de declarație de confidențialitate pentru consolă (DE + EN): Anthropic ca procesator (SCC/DPF), Stripe, hosting, retenție, drepturile persoanei vizate, temei legal art. 6.

**Acceptare:** draft în `docs/legal/`, marcat clar pentru verificare de un jurist; nu publica automat.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
