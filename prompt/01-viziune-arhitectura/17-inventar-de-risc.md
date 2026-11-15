# 01.17 — Inventar de risc

**Secțiune:** Viziune & arhitectură  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Listează riscurile proiectului: costuri API scăpate de sub control, prompt injection prin fișiere, abuz al planului gratuit, GDPR (conversații = date personale), dependență de un singur furnizor, downtime VPS.

**Acceptare:** `docs/console/RISKS.md` cu probabilitate × impact și mitigare concretă pentru fiecare.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
