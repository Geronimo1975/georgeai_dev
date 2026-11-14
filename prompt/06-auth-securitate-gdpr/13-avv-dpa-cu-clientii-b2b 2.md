# 06.13 — AVV / DPA cu clienții B2B

**Secțiune:** Autentificare, securitate & GDPR  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Pregătește un model de Auftragsverarbeitungsvertrag (art. 28 GDPR) pentru clienții business ai consolei, cu lista de subprocesatori.
**Acceptare:** document + pagină publică „Subprocessors” actualizabilă.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
