# 02.07 — Regenerare și ramuri

**Secțiune:** Backend Django & API  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

`POST /messages/{id}/regenerate` creează un frate nou al mesajului asistent; `PATCH` pe un mesaj user creează o ramură nouă (edit). Endpoint care returnează calea activă + numărul de frați pentru navigarea „< 2/3 >”.

**Acceptare:** reconstrucția istoricului trimis la model folosește doar calea activă; teste pe 3 niveluri de ramuri.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
