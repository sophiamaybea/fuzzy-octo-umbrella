# Research Gateway: MCP and REST

## Purpose

Extend the existing GitHub Capability Hunter MCP server with source-linked academic research. Its search protocol resembles one retrieval component of a scientific assistant, but it does not integrate or execute Stanford Biomni itself. It performs no LLM synthesis, biomedical coding, experiments, web crawling, or full-paper reading.

## Interfaces

MCP transport: https://YOUR-HOST/mcp

MCP tools:
1. search_scholarly_literature(question, limit, domain)
2. build_research_dossier(question, limit, domain)
3. look_up_paper_doi(doi)

REST API endpoints:
- GET /api/v1/research/search?q=metacognition&domain=general&limit=5
- POST /api/v1/research/dossier with JSON object containing question, domain and limit.
- GET /api/v1/research/doi?doi=10.1234%2Fabc

REST requires header Authorization: Bearer TOKEN, where TOKEN is RESEARCH_API_KEY. The REST routes remain disabled until that environment variable is set.

## Running

Requires Python 3.11+.

    pip install -e '.[dev]'
    pytest -q
    uvicorn capability_hunter.server:app --host 0.0.0.0 --port 8000

Sample command after setting a key:

    curl -H "Authorization: Bearer $RESEARCH_API_KEY" "http://localhost:8000/api/v1/research/search?q=metacognition&limit=5"

Existing Dockerfile and render.yaml can host the MCP and the REST endpoints together. Hosting and connection are separate operations; source code appearing on GitHub alone does not connect tools to ChatGPT.

## Sources and evidence boundaries

- OpenAlex: broad academic index. Without OPENALEX_API_KEY, small-scale keyless queries may work with lower usage limits.
- Crossref: publisher-deposited scholarly metadata. CROSSREF_CONTACT_EMAIL optionally identifies the requesting client.
- Europe PMC: biomedical index and limited abstracts.

Results have per-response evidence IDs, DOI where available, canonical links, dates, authors, source provider provenance and a short metadata excerpt when returned. DOI/title-and-year deduplication reduces repeated records. Results are a bounded sample ordered by provider-return order, not a systematic review or quality ranking.

A provider error is shown in the provider-status field. Each query fans out to three providers, sends the question text to them and retrieves at most eight hits per provider before deduplication. Results are capped at fifteen. Hosted public use requires quotas and authentication beyond this initial implementation.

## Future work not yet implemented

- OAuth for the MCP transport, quotas, cache, observability.
- Broader public web, books, archival/primary-source discovery and snapshot preservation.
- Full-text review with open-access/licence checks, correction and retraction verification.
- Evidence-aligned model synthesis and experimentally evaluated research quality.
- Human-reviewed, sandboxed Biomni tools for actual biomedical analyses.

Research tools cannot independently prove that retrieved claims are true or perform clinical diagnosis.
