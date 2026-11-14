# Backend Django & API

Modelele, endpoint-urile și logica server pentru conversații, mesaje și ramuri — nucleul consolei.

> **Context comun (lipește-l înaintea promptului dacă agentul nu are CLAUDE.md):**
> Repo `georgeai_dev` — Django 5.2 + DRF (SessionAuthentication, user custom pe email în `backend/accounts`), PostgreSQL în containerul `gethub-postgres`, deploy pe VPS `85.215.69.83` în spatele Traefik. Ținta: **GeorgeAI Console**, o consolă de chat AI cu paritate funcțională și de UX față de **claude.ai** (sidebar cu conversații, proiecte cu knowledge, artifacts în panou lateral, streaming token-cu-token, model picker, upload fișiere, căutare, share, setări, limite de utilizare). Paleta live: `brand/palette.json` (canvas `#02060a`, accent `#fb5e31`/`#b23c0a`, Plus Jakarta Sans). Nu edita niciodată `site/` sau `frontend/template/` — sunt build output.

| # | Prompt | Fișier |
|---|---|---|
| 01 | Modelele Conversation și Message | [01-modelele-conversation-si-message.md](01-modelele-conversation-si-message.md) |
| 02 | ContentBlock polimorf | [02-contentblock-polimorf.md](02-contentblock-polimorf.md) |
| 03 | CRUD conversații | [03-crud-conversatii.md](03-crud-conversatii.md) |
| 04 | Trimiterea unui mesaj | [04-trimiterea-unui-mesaj.md](04-trimiterea-unui-mesaj.md) |
| 05 | Endpoint de streaming SSE | [05-endpoint-de-streaming-sse.md](05-endpoint-de-streaming-sse.md) |
| 06 | Oprirea generării | [06-oprirea-generarii.md](06-oprirea-generarii.md) |
| 07 | Regenerare și ramuri | [07-regenerare-si-ramuri.md](07-regenerare-si-ramuri.md) |
| 08 | Titlu automat de conversație | [08-titlu-automat-de-conversatie.md](08-titlu-automat-de-conversatie.md) |
| 09 | Căutare în conversații | [09-cautare-in-conversatii.md](09-cautare-in-conversatii.md) |
| 10 | Preferințe utilizator | [10-preferinte-utilizator.md](10-preferinte-utilizator.md) |
| 11 | Styles (stiluri de răspuns) | [11-styles-stiluri-de-raspuns.md](11-styles-stiluri-de-raspuns.md) |
| 12 | Construcția system prompt-ului | [12-constructia-system-prompt-ului.md](12-constructia-system-prompt-ului.md) |
| 13 | Gestionarea contextului lung | [13-gestionarea-contextului-lung.md](13-gestionarea-contextului-lung.md) |
| 14 | Share link public | [14-share-link-public.md](14-share-link-public.md) |
| 15 | Export conversații | [15-export-conversatii.md](15-export-conversatii.md) |
| 16 | Rate limiting | [16-rate-limiting.md](16-rate-limiting.md) |
| 17 | Audit log | [17-audit-log.md](17-audit-log.md) |
| 18 | OpenAPI și client tipat | [18-openapi-si-client-tipat.md](18-openapi-si-client-tipat.md) |
| 19 | Performanța query-urilor | [19-performanta-query-urilor.md](19-performanta-query-urilor.md) |
| 20 | Ștergerea contului | [20-stergerea-contului.md](20-stergerea-contului.md) |
