# 05.17 — Memorie între conversații

**Secțiune:** Artifacts, proiecte & fișiere  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Implementează opțional „memory” ca în claude.ai: rezumate ale conversațiilor anterioare pe care userul le poate vedea, edita și dezactiva, folosite ca context.

**Acceptare:** control complet din setări; nimic salvat fără opt-in; ADR despre confidențialitate.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
