You are a senior Django/Python full-stack developer specializing in CPQ (Configure, Price, Quote) systems. Your task is to build a complete, production-ready CPQ configurator application in Django with PostgreSQL.

## Context

**Reference file:** `GeorgeAI - Portfolio.html` — This is a bundled HTML file with embedded, compressed service data. Extract and parse all services, pricing tiers, features, options, and configurable attributes from the embedded content.

**Technology Stack:**
- Backend: Django + PostgreSQL
- Frontend: HTML templates (classic template rendering, not HTMX)
- Database: PostgreSQL

**Completeness Level:** Production-ready implementation with solid engineering practices—complete models, robust validation, error handling, and documentation. No automated tests required. No rapid prototype shortcuts.

## Backend Requirements

**Django Models:**
- Represent each service, configurable options, pricing tiers, and rules extracted from the HTML file
- Use appropriate field types and add database indexing where needed
- Include clean `__str__` methods for all models
- Implement validation at the model level for pricing rules and configuration constraints

**CPQ Pricing Engine:**
- Calculate total price dynamically based on selected configurations
- Support base price + add-ons + quantity multipliers + any conditional pricing logic found in the source
- Keep pricing logic in a dedicated service layer, separate from views
- Handle edge cases and invalid configurations gracefully

**Quote Generation:**
- Produce structured quote summaries with itemized breakdowns
- Include service name, selected options, pricing per item, and total
- Generate and download quotes as PDF (use WeasyPrint or ReportLab)

**Django Admin Interface:**
- Provide full management of services, configuration options, and pricing rules

**REST API Endpoints (Django REST Framework):**
- Endpoint for configuration selection and validation
- Endpoint for quote retrieval and generation
- Include proper error responses and input validation

## Frontend Requirements

**Configurator UI:**
- Multi-step interface that mirrors the visual structure and service categories from `GeorgeAI - Portfolio.html`
- Clean, professional presentation using HTML templates
- Real-time price calculation that updates as users make selections
- Quote summary view with itemized breakdown

## Code Quality & Structure

- Production-ready error handling and input validation throughout
- Service layer separation—keep business logic out of views
- Include `requirements.txt` with all dependencies
- Django settings structure: `settings/base.py`, `settings/dev.py`
- URL routing organized by feature
- `README.md` with setup instructions, environment variables, and deployment notes

## Extraction & Mapping

Extract every service name, description, pricing detail, feature list, and configuration option from `GeorgeAI - Portfolio.html`. Map all extracted data faithfully into Django models and the configurator UI. Do not invent services, pricing, or features—use only what is present in the provided file.