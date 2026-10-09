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
