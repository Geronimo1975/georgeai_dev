# 04.11 — Paleta de comenzi și căutarea

**Secțiune:** Frontend — UI-ul consolei  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Căutare globală (Ctrl/Cmd+K) cu rezultate în conversații și proiecte, navigare din tastatură, fragmente evidențiate.

**Acceptare:** debounce 150 ms; rezultatele recente când query-ul e gol.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
