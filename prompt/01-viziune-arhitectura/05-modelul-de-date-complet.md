# 01.05 — Modelul de date complet

**Secțiune:** Viziune & arhitectură  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Proiectează schema relațională pentru consolă: `Organization`, `Project`, `ProjectKnowledgeFile`, `Conversation`, `Message` (cu arbore de ramuri pentru „edit & regenerate”), `ContentBlock` (text, thinking, tool_use, tool_result, image, document), `Artifact` + `ArtifactVersion`, `Attachment`, `ShareLink`, `UsageEvent`, `UserPreference`, `Style`.

**Acceptare:** `docs/console/DATA-MODEL.md` cu ERD Mermaid, indexuri propuse și justificarea fiecărui câmp JSON.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
