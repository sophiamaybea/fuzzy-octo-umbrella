"""Deterministic tests: no live GitHub, scholar network, packages or executed repos."""
import pytest

from capability_hunter.evolution import (
    DiscoveryRequiredError, domains_for, queries_for, run_research, update_catalogue,
)
from capability_hunter.github import GitHubError


def row(repo="sample/research-agent", stars=400):
    return {
        "repo": repo, "url": "https://github.com/" + repo,
        "description": "biomedical research literature mcp evidence reasoning",
        "stars": stars, "forks": 20, "updated_at": "2026-10-01T00:00:00Z",
        "pushed_at": "2026-10-01T00:00:00Z", "default_branch": "main",
        "language": "Python", "topics": ["research"], "license": "MIT",
        "archived": False, "private": False,
    }


class FakeGitHub:
    def __init__(self, fails=False):
        self.queries = []
        self.fails = fails

    def search(self, query, limit=8):
        self.queries.append(query)
        if self.fails:
            raise GitHubError("mock rate limit")
        return [row()]

    def repo(self, slug):
        return row(slug)

    def tree(self, slug, ref):
        return {"tree_sha": "deadbeef", "truncated": False, "paths": [
            {"path": "README.md", "size": 200, "sha": "aabbcc"},
        ]}

    def read_text_file(self, slug, path, ref):
        return {"path": path, "sha": "aabbcc", "bytes": 24,
                "content": "MCP biological research tools",
                "source_url": "https://github.com/sample/research-agent/blob/main/README.md"}


def test_queries_are_bounded_domain_specific():
    assert "biomedical" in domains_for("research postpartum psychosis")
    assert "philosophy" in domains_for("Socratic argument")
    assert queries_for("postpartum psychosis research")[0] == "biomedical research mcp"
    assert len(queries_for("software research medical philosophy")) <= 4
    assert "biomedical" in domains_for("analyse single-cell RNA-seq counts")
    assert any("single cell" in q for q in queries_for("analyse single-cell RNA-seq counts"))
    with pytest.raises(ValueError):
        queries_for("")


def test_each_run_performs_fresh_github_search_even_without_scholarship():
    client = FakeGitHub()
    run_research("biology and evidence", github_client=client, include_literature=False)
    first = len(client.queries)
    run_research("biology and evidence", github_client=client, include_literature=False)
    assert len(client.queries) == first * 2


def test_discovery_is_mandatory_before_literature():
    called = []
    with pytest.raises(DiscoveryRequiredError, match="research is blocked"):
        run_research(
            "biomedical research",
            github_client=FakeGitHub(fails=True),
            literature_fn=lambda *a, **k: called.append(True),
        )
    assert not called


def test_research_includes_sourced_candidates_without_installing():
    client = FakeGitHub()
    def mock_literature(task, limit, domain):
        assert client.queries
        assert domain == "biomedical"
        return {"question": task, "results": [{"doi": "10.1234/example"}]}
    run = run_research("perinatal medical research", github_client=client, literature_fn=mock_literature)
    assert run["github_discovery"]["successful_searches"] > 0
    assert run["github_discovery"]["inspections"][0]["source_tree_sha"] == "deadbeef"
    assert run["integration_status"].startswith("REVIEW_REQUIRED")
    assert run["literature"]["results"][0]["doi"] == "10.1234/example"
    assert run["installed_capabilities"] == []


def test_catalogue_accumulates_without_approving_skills():
    client = FakeGitHub()
    first = run_research("philosophy evidence", github_client=client, include_literature=False)
    data = update_catalogue({}, first)
    assert data["schema_version"] == 1
    assert data["candidates"][0]["status"] == "CANDIDATE_NOT_INSTALLED"
    assert data["candidates"][0]["source_tree_sha"] == "deadbeef"
    second = run_research("philosophy evidence", github_client=client, include_literature=False)
    updated = update_catalogue(data, second)
    assert updated["candidates"][0]["observations"] == 2
    assert updated["candidates"][0]["first_seen_utc"] == data["candidates"][0]["first_seen_utc"]
    assert updated["candidates"][0]["url"].startswith("https://github.com/")


def test_invalid_options():
    with pytest.raises(ValueError):
        run_research("research", limit=0, github_client=FakeGitHub())
    with pytest.raises(ValueError):
        run_research("research", include_literature="false", github_client=FakeGitHub())
