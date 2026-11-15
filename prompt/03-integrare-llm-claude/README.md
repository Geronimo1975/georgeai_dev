# Integrare LLM (Claude API)

Tot ce ține de comunicarea cu Anthropic Messages API: streaming, tools, vision, thinking, caching, costuri.

> **Context comun (lipește-l înaintea promptului dacă agentul nu are CLAUDE.md):**
> Repo `georgeai_dev` — Django 5.2 + DRF (SessionAuthentication, user custom pe email în `backend/accounts`), PostgreSQL în containerul `gethub-postgres`, deploy pe VPS `85.215.69.83` în spatele Traefik. Ținta: **GeorgeAI Console**, o consolă de chat AI cu paritate funcțională și de UX față de **claude.ai** (sidebar cu conversații, proiecte cu knowledge, artifacts în panou lateral, streaming token-cu-token, model picker, upload fișiere, căutare, share, setări, limite de utilizare). Paleta live: `brand/palette.json` (canvas `#02060a`, accent `#fb5e31`/`#b23c0a`, Plus Jakarta Sans). Nu edita niciodată `site/` sau `frontend/template/` — sunt build output.

| # | Prompt | Fișier |
|---|---|---|
| 01 | Client Anthropic de bază | [01-client-anthropic-de-baza.md](01-client-anthropic-de-baza.md) |
| 02 | Catalog de modele | [02-catalog-de-modele.md](02-catalog-de-modele.md) |
| 03 | Extended thinking | [03-extended-thinking.md](03-extended-thinking.md) |
| 04 | Prompt caching | [04-prompt-caching.md](04-prompt-caching.md) |
| 05 | Vision: imagini în mesaje | [05-vision-imagini-in-mesaje.md](05-vision-imagini-in-mesaje.md) |
| 06 | PDF și documente | [06-pdf-si-documente.md](06-pdf-si-documente.md) |
| 07 | Files API | [07-files-api.md](07-files-api.md) |
| 08 | Tool use: cadru | [08-tool-use-cadru.md](08-tool-use-cadru.md) |
| 09 | Web search | [09-web-search.md](09-web-search.md) |
| 10 | Code execution / analiză date | [10-code-execution-analiza-date.md](10-code-execution-analiza-date.md) |
| 11 | Tools specifice georgeai.dev | [11-tools-specifice-georgeai-dev.md](11-tools-specifice-georgeai-dev.md) |
| 12 | MCP connectors | [12-mcp-connectors.md](12-mcp-connectors.md) |
| 13 | Contorizarea tokenilor și costului | [13-contorizarea-tokenilor-si-costului.md](13-contorizarea-tokenilor-si-costului.md) |
| 14 | Gestionarea erorilor API | [14-gestionarea-erorilor-api.md](14-gestionarea-erorilor-api.md) |
| 15 | Moderare și politici | [15-moderare-si-politici.md](15-moderare-si-politici.md) |
| 16 | Evaluări (evals) | [16-evaluari-evals.md](16-evaluari-evals.md) |
| 17 | System prompt GeorgeAI | [17-system-prompt-georgeai.md](17-system-prompt-georgeai.md) |
| 18 | Fallback și degradare | [18-fallback-si-degradare.md](18-fallback-si-degradare.md) |
| 19 | Batch și joburi asincrone | [19-batch-si-joburi-asincrone.md](19-batch-si-joburi-asincrone.md) |
| 20 | Observabilitate LLM | [20-observabilitate-llm.md](20-observabilitate-llm.md) |
