"""Stateless, remote, read-only MCP gateway for public GitHub capability discovery."""
from __future__ import annotations
import os
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

from .analysis import compare, discover, inspect, make_context_pack, propose_integration
from .catalogue import connect, list_records
from .github import GitHubClient
from .task_router import compile_task

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
