# Autentificare, securitate & GDPR

Conturi, sesiuni, protecția datelor și conformitatea legală germană/UE — consola stochează conversații, deci date personale.

> **Context comun (lipește-l înaintea promptului dacă agentul nu are CLAUDE.md):**
> Repo `georgeai_dev` — Django 5.2 + DRF (SessionAuthentication, user custom pe email în `backend/accounts`), PostgreSQL în containerul `gethub-postgres`, deploy pe VPS `85.215.69.83` în spatele Traefik. Ținta: **GeorgeAI Console**, o consolă de chat AI cu paritate funcțională și de UX față de **claude.ai** (sidebar cu conversații, proiecte cu knowledge, artifacts în panou lateral, streaming token-cu-token, model picker, upload fișiere, căutare, share, setări, limite de utilizare). Paleta live: `brand/palette.json` (canvas `#02060a`, accent `#fb5e31`/`#b23c0a`, Plus Jakarta Sans). Nu edita niciodată `site/` sau `frontend/template/` — sunt build output.

| # | Prompt | Fișier |
|---|---|---|
| 01 | Extinderea auth-ului existent | [01-extinderea-auth-ului-existent.md](01-extinderea-auth-ului-existent.md) |
| 02 | Login cu Google | [02-login-cu-google.md](02-login-cu-google.md) |
| 03 | Magic link | [03-magic-link.md](03-magic-link.md) |
| 04 | 2FA | [04-2fa.md](04-2fa.md) |
| 05 | Gestionarea sesiunilor | [05-gestionarea-sesiunilor.md](05-gestionarea-sesiunilor.md) |
| 06 | Hardening Django | [06-hardening-django.md](06-hardening-django.md) |
| 07 | CSP pentru consolă | [07-csp-pentru-consola.md](07-csp-pentru-consola.md) |
| 08 | Protecție prompt injection | [08-protectie-prompt-injection.md](08-protectie-prompt-injection.md) |
| 09 | Gestionarea secretelor | [09-gestionarea-secretelor.md](09-gestionarea-secretelor.md) |
| 10 | Criptarea datelor sensibile | [10-criptarea-datelor-sensibile.md](10-criptarea-datelor-sensibile.md) |
| 11 | Datenschutzerklärung pentru consolă | [11-datenschutzerklarung-pentru-consola.md](11-datenschutzerklarung-pentru-consola.md) |
| 12 | AGB / Terms of Service | [12-agb-terms-of-service.md](12-agb-terms-of-service.md) |
| 13 | AVV / DPA cu clienții B2B | [13-avv-dpa-cu-clientii-b2b.md](13-avv-dpa-cu-clientii-b2b.md) |
| 14 | Politica de retenție | [14-politica-de-retentie.md](14-politica-de-retentie.md) |
| 15 | Consimțământ și cookies | [15-consimtamant-si-cookies.md](15-consimtamant-si-cookies.md) |
| 16 | EU AI Act — transparență | [16-eu-ai-act-transparenta.md](16-eu-ai-act-transparenta.md) |
| 17 | Protecție anti-abuz | [17-protectie-anti-abuz.md](17-protectie-anti-abuz.md) |
| 18 | Permisiuni admin și staff | [18-permisiuni-admin-si-staff.md](18-permisiuni-admin-si-staff.md) |
| 19 | Pen-test intern | [19-pen-test-intern.md](19-pen-test-intern.md) |
| 20 | Răspuns la incidente | [20-raspuns-la-incidente.md](20-raspuns-la-incidente.md) |
