"""Opt-in live GitHub metadata discovery for specialist domain tasks.

This discovers and compares *candidates*, never runs or installs their code.
GitHub popularity/ranking is not evidence of biological validity.
"""
from __future__ import annotations

from .analysis import discover
from .domain_router import plan_specialist_tools
from .github import GitHubClient, GitHubError

def discover_specialist_repositories(
    task: str,
    limit: int = 5,
    client: GitHubClient | None = None,
) -> dict:
    """Check curated candidates and live-search up to two relevant GitHub queries."""
    if not isinstance(limit, int) or not 1 <= limit <= 8:
        raise ValueError("limit must be between 1 and 8")
    plan = plan_specialist_tools(task, max_candidates=limit)
    curated = []
    searched = []
    errors: list[str] = []
    search_queries = plan.get("github_discovery_queries")
    if not search_queries:
        search_queries = [plan.get("github_discovery_query", "")]

    def run(github: GitHubClient) -> None:
        for candidate in plan["suggested_repositories_not_connected"][:limit]:
            try:
                meta = github.repo(candidate["repo"])
                curated.append({
                    "repo": meta["repo"],
                    "url": meta["url"],
                    "description": meta["description"],
                    "language": meta["language"],
                    "stars": meta["stars"],
                    "last_push": meta["pushed_at"],
                    "license_reported": meta["license"],
                    "reason_for_consideration": candidate["reason"],
                    "status": "GITHUB_METADATA_CHECKED_NOT_EXECUTED",
                })
            except (GitHubError, ValueError) as exc:
                errors.append(f"{candidate['repo']}: {type(exc).__name__}: {exc}")
        for query in search_queries[:2]:
            try:
                results = discover(github, query, min(limit, 5))
                searched.append({
                    "query": query,
                    "results": results,
                    "note": "GitHub relevance is not scientific validation or proof of suitability.",
                })
            except (GitHubError, ValueError) as exc:
                errors.append(f"Search '{query}': {type(exc).__name__}: {exc}")

    if client is None:
        with GitHubClient() as github:
            run(github)
    else:
        run(client)

    return {
        "task": task,
        "domain": plan["domain"],
        "subfields": plan.get("subfields", []),
        "curated_metadata_checked": curated,
        "live_discovery": searched,
        "errors": errors,
        "status": "DISCOVERED_ONLY_NO_REPO_INSTALLED_OR_BENCHMARKED",
        "selection_requirements": plan.get("evaluation_checks", [
            "Compare actual task fit, maintainability, permissions and representative tests."
        ]),
        "next_step": "Inspect top candidates' documentation and code, benchmark on representative data, then integrate only using approved permissions and sandboxed tests.",
    }
