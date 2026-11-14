# 04.18 — Accesibilitate

**Secțiune:** Frontend — UI-ul consolei  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Audit și corectare: landmark-uri, focus management la schimbarea conversației, `aria-live` politicos pentru stream (nu fiecare token), contrast, navigare completă din tastatură.

**Acceptare:** axe-core fără erori serioase; test manual cu VoiceOver documentat.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
