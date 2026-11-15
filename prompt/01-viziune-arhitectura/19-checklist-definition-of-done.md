# 01.19 — Checklist Definition of Done

**Secțiune:** Viziune & arhitectură  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Scrie `docs/console/DOD.md` aplicabil fiecărui PR al consolei: teste, migrații reversibile, accesibilitate, dark/light, mobile 375px, i18n, log-uri fără date personale, actualizare PARITY.md.

**Acceptare:** adaugă checklist-ul în `.github/pull_request_template.md`.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
