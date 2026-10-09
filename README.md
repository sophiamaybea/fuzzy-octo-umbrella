# Capability Hunter

An open-source **GitHub capability discovery and MCP gateway**. It searches public GitHub repositories, ranks candidates, inspects source files without executing them, creates source-linked context packs, compares alternatives, proposes integration plans, and records human-reviewed candidates.

> **Finding code is not the same as installing a capability.** This service does not train ChatGPT, execute downloaded third-party code, or automatically install tools. Actual adoption requires a reviewed adapter, tests, deployment, and permissions.

## What is included

- Public GitHub search and transparent heuristic ranking.
- Bounded source inspection with source URLs, SHA identifiers and explicit truncation warnings.
- Read-only MCP tools: `search_github_capabilities`, `inspect_github_repository`, `create_repo_context_pack`, `compare_capability_repositories`, `propose_repository_skill`, `list_reviewed_capabilities`.
- SQLite candidate registry; decisions can only be changed through local CLI, **not** remote MCP.
- Hourly GitHub Actions discovery reports and automated tests.
- Docker/Render deployment for a remotely accessible `/mcp` endpoint.

## How to run

Requires Python 3.11+.

```bash
pip install -e '.[dev]'
pytest -q
capability-hunter search "argument mining"
capability-hunter inspect "modelcontextprotocol/python-sdk"
capability-hunter propose "modelcontextprotocol/python-sdk" --goal "MCP tools"
capability-hunter scan --queries config/queries.txt --out reports/latest.json
uvicorn capability_hunter.server:app --host 0.0.0.0 --port 8000
```

Health: `http://localhost:8000/health`. MCP: `http://localhost:8000/mcp`.

## Render / ChatGPT

In Render, create a **Blueprint** from this repository; `render.yaml` uses Docker. The public MCP URL will be `https://YOUR-SERVICE.onrender.com/mcp`. Configure host validation via `MCP_ALLOWED_HOSTS` if your environment doesn't expose `RENDER_EXTERNAL_HOSTNAME`. Add a custom MCP server in ChatGPT's supported plugin/connector setup, using that URL.

A GitHub API token is optional; if supplied to an unauthenticated deployment, **it must not have private-repository access**. Protect a deployed service with authentication, rate limits and quotas before exposing it to substantial public traffic.

The default registry is local SQLite. Free cloud storage may be ephemeral; hourly GitHub Actions reports are downloadable artifacts, **not** a persistent synchronised DB.

## Why this MCP?

The official [GitHub MCP server](https://github.com/github/github-mcp-server) already supports GitHub operations. This MCP adds a specialised discovery/analysis workflow and proposal/approval ledger. It is not a substitute for a secure runtime.

Candidate integrations to evaluate: [Repomix](https://github.com/yamadashy/repomix), [Gitingest](https://github.com/coderamp-labs/gitingest), [repo-to-skill](https://github.com/zhangguiping-xydt/repo-to-skill), [Crawl4AI RAG MCP](https://github.com/coleam00/mcp-crawl4ai-rag).

See `SECURITY.md` and `AGENTS.md`. Project licensed MIT. Third-party licences remain independent.

## Capability-aware task execution briefs

Run `capability-hunter compile 'your task'` to generate a structured, faithful task brief without model or network calls. With the deployed MCP gateway connected, assistants can call `compile_task_brief`. Copy [the reusable orchestration prompt](prompts/AUTO_CAPABILITY_ORCHESTRATOR.md) into a supported instruction context to guide actual execution with already-connected tools. See [prompt optimisation architecture](docs/prompt-optimisation.md). The compiler does **not** improve the model's weights or automatically install GitHub tools.


## Research MCP and REST API (v0.2)

Capability Hunter now has a scholarly research adapter that searches [OpenAlex](https://help.openalex.org/api/), [Crossref](https://www.crossref.org/documentation/retrieve-metadata/rest-api/), and [Europe PMC](https://europepmc.org/RestfulWebService). It works for general academic and biomedical literature, although it does **not** search all relevant books, philosophy archives, websites, primary records or licensed papers.

**MCP tools** (available alongside the existing GitHub tools after the service is deployed):
- search_scholarly_literature(question, limit=10, domain="general")
- build_research_dossier(question, limit=10, domain="biomedical")
- look_up_paper_doi(doi)

These tools return DOI-linked records, source provenance, dates, short abstracts where available and a verification checklist. This is **evidence discovery**, not an autonomous literature review, experimental execution, claim validation, or a direct installation of Stanford Biomni.

**REST API** (requires RESEARCH_API_KEY set as a hosting secret; otherwise research HTTP routes return 503):
- GET /api/v1/research/search?q=critical%20reasoning&limit=10&domain=general
- POST /api/v1/research/dossier (JSON: {"question":"postpartum psychosis risk","domain":"biomedical","limit":10})
- GET /api/v1/research/doi?doi=10.1234%2Fexample

Set the Authorization header to Bearer YOUR_RESEARCH_API_KEY. Do not put secrets in browser JavaScript or the repository. Optional provider settings: OPENALEX_API_KEY, CROSSREF_CONTACT_EMAIL. See docs/research-gateway.md for setup and limitations.

The existing Dockerfile, Render blueprint and /mcp path are reused. Hosted MCP authentication and quotas are **not yet implemented**, so restrict deployment access before large-scale production use.

## Domain-first specialist discovery

Use `capability-hunter specialist 'analyse single-cell RNA-seq data'` for a local, deterministic domain→subfield→tool plan. Add `--live` to verify curated repository metadata and discover further current candidates on public GitHub. Via the deployed read-only MCP gateway, `route_domain_specialists` and `discover_domain_specialists` expose these two steps. The `compile` command also incorporates the specialist path into the execution brief. Biology coverage includes single-cell omics, RNA-seq, genetics, molecular modelling, drug discovery, biomedical sources, microbiome, microscopy and neuroscience. This ranks *plausible candidates* and plans further discovery; it does not empirically determine a universal winner or install specialist software. Extend `domain_router.py` with other fields after source and test review.
