# 01.11 — Endpoint de bootstrap

**Secțiune:** Viziune & arhitectură  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Creează `GET /api/console/bootstrap` care returnează într-un singur request tot ce are nevoie UI-ul la încărcare: user, preferințe, modele disponibile, flags, limite de utilizare rămase, ultimele 30 de conversații (doar titlu/id/updated_at), proiecte.

**Acceptare:** un singur round-trip, < 80 ms server-side cu 1000 de conversații, testat.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
