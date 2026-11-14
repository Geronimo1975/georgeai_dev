# 01.15 — Plan de lansare în faze

**Secțiune:** Viziune & arhitectură  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Scrie `docs/console/ROADMAP.md` cu 5 faze: (0) fundație + auth, (1) chat cu streaming ca claude.ai, (2) proiecte + fișiere, (3) artifacts, (4) monetizare + limite, (5) polish/mobile. Fiecare fază: livrabile, criterii de ieșire, riscuri.

**Acceptare:** fiecare fază e demo-abilă independent; referințe la prompturile din `prompt/`.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
