# 04.07 — Randare Markdown

**Secțiune:** Frontend — UI-ul consolei  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Randare Markdown sigură (GFM, tabele, liste, citate) cu highlight de cod (Shiki sau Prism), buton Copy pe blocuri, LaTeX cu KaTeX, Mermaid opțional. Markdown-ul parțial din stream nu „sare” vizual.

**Acceptare:** sanitizare XSS testată; blocurile de cod neterminate se randează stabil.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
