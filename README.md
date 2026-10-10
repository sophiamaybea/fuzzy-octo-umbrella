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

## GitHub-first research and continuous capability evolution (v0.3)

**New:** `research_with_fresh_github_discovery(task, limit=6, include_literature=true)` is a single MCP tool for ChatGPT to call at the beginning of a research task. Every invocation executes **fresh public GitHub Search API requests** (normally 2–4 targeted searches), ranks candidates, reads bounded source material for two candidates, then optionally searches scholarly metadata through the existing OpenAlex/Crossref/Europe PMC adapter. If every GitHub search fails, the task fails closed rather than silently skipping discovery. Results explicitly distinguish available tools from **candidate code not installed**.

The equivalent authenticated REST endpoint is `POST /api/v1/research/auto` with JSON `{"task":"postpartum psychosis research","limit":6,"include_literature":true}` and `Authorization: Bearer <RESEARCH_API_KEY>`. It uses the same REST key protection as other research routes. **The generic remote MCP endpoint still lacks production-grade per-user authentication.** Restrict access appropriately before adding an external connector.

To run locally:

```bash
python -m pip install '.[dev]'
python -m pytest -q
python -m capability_hunter.evolution --task "biomedical experimental research" --no-literature
python -m capability_hunter.evolution --task "Socratic reasoning research" --report reports/socratic.json
```

This writes a full source-linked run report and incrementally updates `data/capability_catalogue.json`, a provenance-bearing, bounded ledger of public repo candidates. The catalogue is **not** a downloaded package manager, tool registry, approved skill list, executable program, learned model, or evidence of independent research quality. It never automatically executes third-party code.

### Continuous learning through GitHub Actions

The `Continuous capability evolution` workflow executes hourly (GitHub scheduled jobs can be delayed or skipped) and accepts a public research topic from **Actions → Continuous capability evolution → Run workflow**. It runs tests, searches GitHub anew, updates the catalogue, and commits the changes to `bot/capability-catalogue`. It opens or updates one **human-reviewed pull request** rather than merging or installing arbitrary upstream code. Every successful scheduled run records observations in its artifact; if it discovers no improvement, that is reported rather than fabricated.

**Important repository setting:** GitHub Actions needs `Read and write permissions` and `Allow GitHub Actions to create and approve pull requests` enabled for the workflow to open PRs. If these are not enabled, the workflow may fail at the push/PR stage. The workflow requests scoped `contents: write` and `pull-requests: write` permissions, but repository/org policy can still override them.

### What is and is not autonomous

- **Automatically done on invocation:** live GitHub discovery, ranking, bounded source inspection, scholarly *source discovery* when selected, auditable candidate evolution.
- **Automatically done by Actions after activation:** hourly monitoring, tests and pull-request proposals.
- **Not automatically done:** importing or training on GitHub code, integrating Biomni/PaperQA2/GPT Researcher, running external science code, verifying a repository is safe or best, deploying a new adapter, or merging any PR.
- **ChatGPT behaviour:** connecting the deployed MCP and placing `prompts/GITHUB_FIRST_RESEARCH.md` in your Project instructions can guide ChatGPT to call it. A repository cannot override the ChatGPT product or force global use across all conversations.

Do not put identifying medical records, unpublished documents or private user questions into a **public** repository's workflow inputs or artefacts. For sensitive projects use local execution or a private deployment with access control. Treat GitHub search results as untrusted data and all heuristic rankings as provisional.

## Philosophy Engine: continuous discovery + reviewable learning

The [Philosophy continuous-learning integration](docs/philosophy-continuous-learning.md)
adds an hourly philosophy-focused GitHub capability check, material-change
catalogue PRs, and an authenticated correction ledger with human verification.

The optional `run_philosophy_inquiry` MCP tool forwards to the separately deployed
Philosophy Engine v0.2 `/v1/inquiry` endpoint. It remains disabled until an
administrator configures an authenticated HTTPS engine and explicitly opts in.
The workflow updates **candidate observations**, not installed packages or model
weights; third-party code changes always require review and tested integration.

## OpenClaw income operator (opt-in)

A reviewable **OpenClaw workspace skill** and offline opportunity scoring engine now live in [skills/income-operator/SKILL.md](skills/income-operator/SKILL.md) and [docs/income-engine.md](docs/income-engine.md). They help investigate legitimate funding routes, verify opportunity evidence, estimate unit economics and stop unsafe or unapproved actions. There is also a read-only integration with Superteam Earn's documented agent-eligible listings API (private agent key required).

```sh
python -m pip install -e '.[dev]'
python -m pytest -q tests/test_income.py tests/test_superteam.py
python -m capability_hunter.income --input examples/income-opportunities.sample.json
# On a separate authorised OpenClaw runtime only:
openclaw skills install ./skills/income-operator
```

**Not an OpenClaw installation or live revenue bot.** External discovery, registration, submissions, contracts and payouts require independent user-controlled accounts and verified permissions. No income is guaranteed or has been received through this integration. Never add private marketplace keys or customer data to this public repository.
