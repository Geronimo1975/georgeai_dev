# Planuri, plăți & limite de utilizare

Modelul de business al consolei — Free/Pro/Team ca la claude.ai — legat de Stripe-ul deja folosit pe `/pricing/` și de lanțul n8n existent.

> **Context comun (lipește-l înaintea promptului dacă agentul nu are CLAUDE.md):**
> Repo `georgeai_dev` — Django 5.2 + DRF (SessionAuthentication, user custom pe email în `backend/accounts`), PostgreSQL în containerul `gethub-postgres`, deploy pe VPS `85.215.69.83` în spatele Traefik. Ținta: **GeorgeAI Console**, o consolă de chat AI cu paritate funcțională și de UX față de **claude.ai** (sidebar cu conversații, proiecte cu knowledge, artifacts în panou lateral, streaming token-cu-token, model picker, upload fișiere, căutare, share, setări, limite de utilizare). Paleta live: `brand/palette.json` (canvas `#02060a`, accent `#fb5e31`/`#b23c0a`, Plus Jakarta Sans). Nu edita niciodată `site/` sau `frontend/template/` — sunt build output.

| # | Prompt | Fișier |
|---|---|---|
| 01 | Strategia de planuri | [01-strategia-de-planuri.md](01-strategia-de-planuri.md) |
| 02 | Modelul Subscription | [02-modelul-subscription.md](02-modelul-subscription.md) |
| 03 | Stripe Checkout pentru abonamente | [03-stripe-checkout-pentru-abonamente.md](03-stripe-checkout-pentru-abonamente.md) |
| 04 | Webhook-uri Stripe | [04-webhook-uri-stripe.md](04-webhook-uri-stripe.md) |
| 05 | Customer Portal | [05-customer-portal.md](05-customer-portal.md) |
| 06 | Limite de utilizare în ferestre | [06-limite-de-utilizare-in-ferestre.md](06-limite-de-utilizare-in-ferestre.md) |
| 07 | Metering și facturare pe consum | [07-metering-si-facturare-pe-consum.md](07-metering-si-facturare-pe-consum.md) |
| 08 | Pagina de upgrade | [08-pagina-de-upgrade.md](08-pagina-de-upgrade.md) |
| 09 | Trial și cupoane | [09-trial-si-cupoane.md](09-trial-si-cupoane.md) |
| 10 | Facturi și TVA | [10-facturi-si-tva.md](10-facturi-si-tva.md) |
| 11 | Dunning | [11-dunning.md](11-dunning.md) |
| 12 | Planul Team | [12-planul-team.md](12-planul-team.md) |
| 13 | Dashboard de utilizare pentru user | [13-dashboard-de-utilizare-pentru-user.md](13-dashboard-de-utilizare-pentru-user.md) |
| 14 | Dashboard financiar admin | [14-dashboard-financiar-admin.md](14-dashboard-financiar-admin.md) |
| 15 | Protecția costurilor | [15-protectia-costurilor.md](15-protectia-costurilor.md) |
| 16 | Legarea cu /pricing/ existent | [16-legarea-cu-pricing-existent.md](16-legarea-cu-pricing-existent.md) |
| 17 | Checklist go-live Stripe | [17-checklist-go-live-stripe.md](17-checklist-go-live-stripe.md) |
| 18 | Teste end-to-end plăți | [18-teste-end-to-end-plati.md](18-teste-end-to-end-plati.md) |
| 19 | Emailuri tranzacționale | [19-emailuri-tranzactionale.md](19-emailuri-tranzactionale.md) |
| 20 | Analiza unit economics | [20-analiza-unit-economics.md](20-analiza-unit-economics.md) |
