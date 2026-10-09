"""Stateless, remote, read-only MCP gateway for public GitHub capability discovery."""
from __future__ import annotations
import os
import asyncio
import hmac
import json
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

from .analysis import compare, discover, inspect, make_context_pack, propose_integration
from .catalogue import connect, list_records
from .github import GitHubClient
from .task_router import compile_task
from .research import ResearchError, search_scholarship, research_dossier, lookup_doi_metadata
from .evolution import DiscoveryRequiredError, run_research

mcp = MCPServer("GitHub Capability Hunter")

@mcp.tool()
def search_github_capabilities(query: str, limit: int = 8) -> list[dict]:
    """Search public repositories using transparent ranking. Results are untrusted candidates."""
    with GitHubClient() as client:
        return discover(client, query, limit)

@mcp.tool()
def inspect_github_repository(repo: str, max_files: int = 5) -> dict:
    """Read a limited, source-cited snapshot of a public GitHub repo. Never executes code."""
    with GitHubClient() as client:
        return inspect(client, repo, min(7, max_files))

@mcp.tool()
def create_repo_context_pack(repo: str, max_files: int = 4) -> str:
    """Create an AI-readable context excerpt with source links and hashes. No execution."""
    with GitHubClient() as client:
        pack = make_context_pack(inspect(client, repo, min(5, max_files)))
    return pack[:48_000] + ("\n[Context pack truncated by MCP size limit.]" if len(pack) > 48_000 else "")

@mcp.tool()
def propose_repository_skill(repo: str, goal: str) -> dict:
    """Propose an integration route and necessary reviews. Does not install or activate code."""
    with GitHubClient() as client:
        snapshot = inspect(client, repo, 7)
    return propose_integration(snapshot, goal)

@mcp.tool()
def compare_capability_repositories(left: str, right: str, goal: str) -> dict:
    """Compare two public snapshots without asserting functional superiority."""
    with GitHubClient() as client:
        one, two = inspect(client, left, 5), inspect(client, right, 5)
    return compare(one, two, goal)

@mcp.tool()
def list_reviewed_capabilities(status: str = "APPROVED", limit: int = 30) -> list[dict]:
    """Read the local review ledger. Cannot remotely approve or activate new tools."""
    with connect() as db:
        return list_records(db, status=status, limit=limit)

@mcp.tool()
def compile_task_brief(task: str, available_tools: list[str] | None = None) -> dict:
    """Build an inspectable execution prompt; does not itself optimise, install or execute."""
    return compile_task(task, available_tools)


@mcp.tool()
def search_scholarly_literature(question: str, limit: int = 10, domain: str = "general") -> dict:
    """Research OpenAlex, Crossref and Europe PMC; return source-linked paper metadata."""
    return search_scholarship(question, limit, domain)

@mcp.tool()
def build_research_dossier(question: str, limit: int = 10, domain: str = "general") -> dict:
    """Produce an auditable starting literature index and verification questions."""
    return research_dossier(question, limit, domain)

@mcp.tool()
def look_up_paper_doi(doi: str) -> dict:
    """Retrieve an exact DOI's Crossref metadata from a fixed scholarly API."""
    return lookup_doi_metadata(doi)


@mcp.tool()
def research_with_fresh_github_discovery(
    task: str, limit: int = 6, include_literature: bool = True
) -> dict:
    """MANDATORY fresh GitHub repository search before scholarly source discovery.

    Each call searches and inspects current GitHub candidates. Never installs tools.
    """
    return run_research(task, limit, include_literature)


def _require_research_key(request: Request):
    key = os.getenv("RESEARCH_API_KEY", "")
    if not key:
        return JSONResponse({"error": "REST API disabled; set RESEARCH_API_KEY"}, status_code=503)
    if not hmac.compare_digest(request.headers.get("authorization", ""), "Bearer " + key):
        return JSONResponse({"error": "unauthorised"}, status_code=401)
    return None


async def _api_result(fn):
    try:
        return JSONResponse(await asyncio.to_thread(fn))
    except (ValueError, TypeError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=422)
    except (ResearchError, DiscoveryRequiredError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=502)


@mcp.custom_route("/api/v1/research/search", methods=["GET"])
async def search_research_api(request: Request):
    denied = _require_research_key(request)
    if denied is not None:
        return denied
    params = request.query_params
    return await _api_result(lambda: search_scholarship(
        params.get("q", ""), int(params.get("limit", "10")), params.get("domain", "general")
    ))


@mcp.custom_route("/api/v1/research/dossier", methods=["POST"])
async def dossier_research_api(request: Request):
    denied = _require_research_key(request)
    if denied is not None:
        return denied
    body = await request.body()
    if len(body) > 4000:
        return JSONResponse({"error": "body too large"}, status_code=413)
    try:
        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError("Expected JSON object")
    except (ValueError, UnicodeDecodeError):
        return JSONResponse({"error": "invalid JSON object"}, status_code=400)
    return await _api_result(lambda: research_dossier(
        data.get("question", ""), data.get("limit", 10), data.get("domain", "general")
    ))


@mcp.custom_route("/api/v1/research/doi", methods=["GET"])
async def doi_research_api(request: Request):
    denied = _require_research_key(request)
    if denied is not None:
        return denied
    return await _api_result(lambda: lookup_doi_metadata(request.query_params.get("doi", "")))


@mcp.custom_route("/api/v1/research/auto", methods=["POST"])
async def auto_research_api(request: Request):
    """GitHub-first research; bearer-key guard applies to all REST access."""
    denied = _require_research_key(request)
    if denied is not None:
        return denied
    body = await request.body()
    if len(body) > 4000:
        return JSONResponse({"error": "body too large"}, status_code=413)
    try:
        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError("expected object")
    except (ValueError, UnicodeDecodeError):
        return JSONResponse({"error": "invalid JSON object"}, status_code=400)
    return await _api_result(lambda: run_research(
        data.get("task", ""), data.get("limit", 6), data.get("include_literature", True)
    ))


@mcp.custom_route("/health", methods=["GET"])
async def health(_request: Request):
    return JSONResponse({"ok": True, "service": "capability-hunter", "public_only": True})

hosts = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
external = os.getenv("MCP_ALLOWED_HOSTS") or os.getenv("RENDER_EXTERNAL_HOSTNAME", "")
if external:
    for name in external.split(","):
        if name.strip():
            hosts += [name.strip(), name.strip() + ":*"] if ":" not in name else [name.strip()]
origins = ["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"]
origins.extend(o.strip() for o in os.getenv("MCP_ALLOWED_ORIGINS", "").split(",") if o.strip())
app = mcp.streamable_http_app(
    json_response=True,
    stateless_http=True,
    host="0.0.0.0",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
        allowed_origins=origins,
    ),
)
