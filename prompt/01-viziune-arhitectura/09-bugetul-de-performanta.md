# 01.09 — Bugetul de performanță

**Secțiune:** Viziune & arhitectură  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Definește bugete măsurabile, aliniate cu senzația claude.ai: time-to-first-token < 1,2 s (p75), primul paint al consolei < 1,5 s, input latency < 50 ms în composer, schimbarea conversației < 200 ms din cache, bundle JS inițial < 250 KB gzip.

**Acceptare:** `docs/console/PERF-BUDGET.md` + cum se măsoară fiecare (script, Lighthouse CI, log server).

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
