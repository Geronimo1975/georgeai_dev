# 06.06 — Hardening Django

**Secțiune:** Autentificare, securitate & GDPR  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Rulează `manage.py check --deploy` și rezolvă tot: HSTS, SECURE_PROXY_SSL_HEADER pentru Traefik, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, admin pe URL neevident, `DEBUG=False`.
**Acceptare:** zero avertismente; documentat în `docs/console/SECURITY.md`.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
