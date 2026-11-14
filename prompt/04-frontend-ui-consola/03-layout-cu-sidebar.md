# 04.03 — Layout cu sidebar

**Secțiune:** Frontend — UI-ul consolei  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Layout principal: sidebar stânga (New chat, căutare, Projects, Starred, Recents grupate pe Azi/Ieri/7 zile/30 zile, profil jos), zona de chat centrală cu lățime maximă de lectură, panou artifacts dreapta. Sidebar colapsabil, persistat.

**Acceptare:** funcționează la 375px (drawer), 768px și 1440px; nu există scroll orizontal.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
