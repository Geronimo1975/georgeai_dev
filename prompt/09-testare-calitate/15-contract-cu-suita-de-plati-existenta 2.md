# 09.15 — Contract cu suita de plăți existentă

**Secțiune:** Testare & calitate  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Asigură-te că `tests/test_payments_pipeline.py` și cron-ul `cron/check_payments.sh` continuă să treacă după adăugarea abonamentelor consolei; adaugă o suită soră `tests/test_console_health.py` în același stil stdlib-only.
**Acceptare:** ambele rulate de GitHub Actions la 6h.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
