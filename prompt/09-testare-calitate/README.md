# Testare & calitate

Strategia de testare care ține consola stabilă pe măsură ce crește — de la unit tests la teste vizuale față de reperul claude.ai.

> **Context comun (lipește-l înaintea promptului dacă agentul nu are CLAUDE.md):**
> Repo `georgeai_dev` — Django 5.2 + DRF (SessionAuthentication, user custom pe email în `backend/accounts`), PostgreSQL în containerul `gethub-postgres`, deploy pe VPS `85.215.69.83` în spatele Traefik. Ținta: **GeorgeAI Console**, o consolă de chat AI cu paritate funcțională și de UX față de **claude.ai** (sidebar cu conversații, proiecte cu knowledge, artifacts în panou lateral, streaming token-cu-token, model picker, upload fișiere, căutare, share, setări, limite de utilizare). Paleta live: `brand/palette.json` (canvas `#02060a`, accent `#fb5e31`/`#b23c0a`, Plus Jakarta Sans). Nu edita niciodată `site/` sau `frontend/template/` — sunt build output.

| # | Prompt | Fișier |
|---|---|---|
| 01 | Strategia de testare | [01-strategia-de-testare.md](01-strategia-de-testare.md) |
| 02 | Provider LLM fake | [02-provider-llm-fake.md](02-provider-llm-fake.md) |
| 03 | Fixtures și factories | [03-fixtures-si-factories.md](03-fixtures-si-factories.md) |
| 04 | Teste de model și ramuri | [04-teste-de-model-si-ramuri.md](04-teste-de-model-si-ramuri.md) |
| 05 | Teste de contract SSE | [05-teste-de-contract-sse.md](05-teste-de-contract-sse.md) |
| 06 | Teste de permisiuni | [06-teste-de-permisiuni.md](06-teste-de-permisiuni.md) |
| 07 | Teste frontend unitare | [07-teste-frontend-unitare.md](07-teste-frontend-unitare.md) |
| 08 | E2E Playwright — fluxul principal | [08-e2e-playwright-fluxul-principal.md](08-e2e-playwright-fluxul-principal.md) |
| 09 | E2E — artifacts și proiecte | [09-e2e-artifacts-si-proiecte.md](09-e2e-artifacts-si-proiecte.md) |
| 10 | Regresie vizuală | [10-regresie-vizuala.md](10-regresie-vizuala.md) |
| 11 | Teste de accesibilitate automate | [11-teste-de-accesibilitate-automate.md](11-teste-de-accesibilitate-automate.md) |
| 12 | Teste de performanță frontend | [12-teste-de-performanta-frontend.md](12-teste-de-performanta-frontend.md) |
| 13 | Teste de webhook Stripe | [13-teste-de-webhook-stripe.md](13-teste-de-webhook-stripe.md) |
| 14 | Teste de securitate automate | [14-teste-de-securitate-automate.md](14-teste-de-securitate-automate.md) |
| 15 | Contract cu suita de plăți existentă | [15-contract-cu-suita-de-plati-existenta.md](15-contract-cu-suita-de-plati-existenta.md) |
| 16 | Smoke tests post-deploy | [16-smoke-tests-post-deploy.md](16-smoke-tests-post-deploy.md) |
| 17 | Testarea pe dispozitive | [17-testarea-pe-dispozitive.md](17-testarea-pe-dispozitive.md) |
| 18 | Code review checklist | [18-code-review-checklist.md](18-code-review-checklist.md) |
| 19 | Mutation testing | [19-mutation-testing.md](19-mutation-testing.md) |
| 20 | Raport de calitate periodic | [20-raport-de-calitate-periodic.md](20-raport-de-calitate-periodic.md) |
