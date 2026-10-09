"""Fresh GitHub-first research orchestration and reviewable catalogue evolution.

Public-source discovery is mandatory on every invocation. Repository code is never
installed, imported, executed, or used as an instruction. Improvement means a
provenance-bearing capability catalogue and review proposals, not self-training.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .analysis import discover, inspect
from .github import GitHubClient, GitHubError
from .research import ResearchError, research_dossier

DOMAIN_QUERIES = {
    "biomedical": ("biomedical research mcp", "bioinformatics research agent"),
    "philosophy": ("argument mining reasoning", "socratic reasoning evaluation"),
    "software": ("github mcp capability discovery", "agent tool evaluation"),
    "research": ("deep research academic agent", "scientific literature evidence"),
    "general": ("deep research agent", "research tools mcp"),
}
DOMAIN_TERMS = {
    "biomedical": r"\b(biolog\w*|biomed\w*|genom\w*|medic\w*|clinical|health\w*|psychiatr\w*|neuroscien\w*|disease|pubmed|biomni|perinatal)\b",
    "philosophy": r"\b(philosoph\w*|socrati\w*|argument\w*|rhetoric|debate|epistem\w*|logic|ethic\w*)\b",
    "software": r"\b(github|program\w*|api|code|develop\w*|app|mcp|repository|software|build)\b",
    "research": r"\b(research\w*|academic|study|literature|papers?|evidence|systematic|experiment\w*)\b",
}
MAX_CATALOGUE = 180


class DiscoveryRequiredError(RuntimeError):
    """No successful fresh GitHub search: downstream research must not run."""


def domains_for(task: str) -> list[str]:
    names = [name for name, term in DOMAIN_TERMS.items() if re.search(term, task, re.I)]
    return names or ["general"]


def queries_for(task: str) -> list[str]:
    """Diverse, bounded GitHub searches, with a domain-specific search first."""
    if not isinstance(task, str) or not 3 <= len(task.strip()) <= 400:
        raise ValueError("Task must contain between 3 and 400 characters")
    domains = domains_for(task)
    queries = []
    for domain in domains + ["general"]:
        for q in DOMAIN_QUERIES[domain]:
            if q not in queries:
                queries.append(q)
    return queries[:4]


def run_research(
    task: str,
    limit: int = 6,
    include_literature: bool = True,
    *,
    github_client: GitHubClient | None = None,
    literature_fn: Callable = research_dossier,
) -> dict:
    """Fail closed if live GitHub discovery fails; always label non-installed tools.

    A supplied client is for deterministic testing; production creates a fresh one.
    """
    queries = queries_for(task)
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 10:
        raise ValueError("limit must be an integer from 1 to 10")
    if not isinstance(include_literature, bool):
        raise ValueError("include_literature must be a boolean")
    owns_client = github_client is None
    client = github_client or GitHubClient()
    discovered: dict[str, dict] = {}
    failures: dict[str, str] = {}
    successes = 0
    try:
        for query in queries:
            try:
                rows = discover(client, query, min(limit, 8))
                successes += 1
            except (GitHubError, ValueError) as exc:
                failures[query] = str(exc)[:180]
                continue
            for row in rows:
                slug = row["repo"]
                if slug not in discovered or row["score"]["total"] > discovered[slug]["score"]["total"]:
                    discovered[slug] = dict(row, matched_query=query)
        if not successes:
            raise DiscoveryRequiredError(
                "Fresh GitHub capability discovery did not succeed; research is blocked. "
                + "; ".join(f"{q}: {msg}" for q, msg in failures.items())
            )
        ordered = sorted(discovered.values(), key=lambda x: x["score"]["total"], reverse=True)
        inspections: list[dict] = []
        for row in ordered[:2]:
            try:
                snapshot = inspect(client, row["repo"], max_files=3)
                inspections.append({
                    "repo": row["repo"], "source_tree_sha": snapshot["tree_sha"],
                    "source_urls": [e["source_url"] for e in snapshot["excerpts"]],
                    "licence": snapshot["repository"]["license"],
                    "warnings": snapshot["warnings"],
                    "status": "DOCUMENTS_INSPECTED_NOT_INSTALLED",
                })
            except (GitHubError, ValueError) as exc:
                inspections.append({
                    "repo": row["repo"], "status": "INSPECTION_FAILED",
                    "error": str(exc)[:180],
                })
    finally:
        if owns_client:
            client.http.close()

    primary = domains_for(task)
    result = {
        "task": task.strip(),
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "domains": primary,
        "github_discovery": {
            "mandatory": True, "attempted": True, "successful_searches": successes,
            "queries": queries, "errors": failures,
            "ranked_candidates": ordered[:18],
            "inspections": inspections,
            "ranking_warning": "Relevance/popularity/activity heuristic, NOT a validated benchmark.",
        },
        "installed_capabilities": [],
        "integration_status": "REVIEW_REQUIRED; NO_THIRD_PARTY_CODE_EXECUTED",
        "recommended_next_step": (
            "Review licences and pinned commits, benchmark on representative tasks, "
            "build a least-privilege adapter, test in isolation, and propose a PR for human review."
        ),
    }
    if include_literature:
        domain = "biomedical" if "biomedical" in primary else "general"
        try:
            result["literature"] = literature_fn(task, limit=min(limit, 10), domain=domain)
        except (ResearchError, ValueError) as exc:
            result["literature"] = {"status": "failed", "error": str(exc)[:250]}
        result["research_status"] = "EVIDENCE_DISCOVERY_ONLY_NOT_CONCLUSION"
    else:
        result["research_status"] = "GITHUB_DISCOVERY_ONLY"
    return result


def update_catalogue(previous: dict, run: dict) -> dict:
    """Accumulate bounded, versioned observations; never approve or install a repo."""
    if not isinstance(previous, dict):
        raise ValueError("Previous catalogue must be a JSON object")
    existing = previous.get("candidates") or []
    if not isinstance(existing, list):
        raise ValueError("Invalid candidate catalogue")
    by_slug = {v["repo"]: dict(v) for v in existing
               if isinstance(v, dict) and isinstance(v.get("repo"), str)}
    inspected = {x["repo"]: x for x in run["github_discovery"]["inspections"]}
    timestamp = run["run_at_utc"]
    for item in run["github_discovery"]["ranked_candidates"]:
        slug = item["repo"]
        prior = by_slug.get(slug, {})
        pin = inspected.get(slug, {})
        by_slug[slug] = {
            "repo": slug, "url": item["url"],
            "description": item.get("description", "")[:350],
            "licence_reported": item.get("license", "UNKNOWN"),
            "pushed_at": item.get("pushed_at"),
            "stars": item.get("stars", 0),
            "heuristic_score": item["score"]["total"],
            "source_tree_sha": pin.get("source_tree_sha", prior.get("source_tree_sha")),
            "status": "CANDIDATE_NOT_INSTALLED",
            "first_seen_utc": prior.get("first_seen_utc", timestamp),
            "last_seen_utc": timestamp,
            "observations": min(100000, prior.get("observations", 0) + 1),
        }
    ranked = sorted(by_slug.values(), key=lambda x: (
        x.get("last_seen_utc") or "", x.get("heuristic_score") or 0), reverse=True)
    return {
        "schema_version": 1,
        "updated_at_utc": timestamp,
        "description": "Unverified external repo suggestions; NO auto-install or approval",
        "candidates": ranked[:MAX_CATALOGUE],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Mandatory GitHub-first research and evolution")
    parser.add_argument("--task", default="scientific biomedical psychological philosophy research")
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument("--no-literature", action="store_true")
    parser.add_argument("--catalogue", default="data/capability_catalogue.json")
    parser.add_argument("--report", default="evolution-report.json")
    args = parser.parse_args()
    run = run_research(args.task, args.limit, include_literature=not args.no_literature)
    target = Path(args.catalogue)
    old = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}
    data = update_catalogue(old, run)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(run, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": run["research_status"], "github_searches": run["github_discovery"]["successful_searches"],
        "candidate_count": len(run["github_discovery"]["ranked_candidates"]),
        "catalogue": str(target), "report": str(report),
        "code_installed": False, "code_modified": False, "human_review_required": True,
    }))


if __name__ == "__main__":
    main()
