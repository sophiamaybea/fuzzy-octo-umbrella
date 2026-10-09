import base64

import httpx
import pytest

from capability_hunter.analysis import discover, inspect, make_context_pack, propose_integration
from capability_hunter.catalogue import connect, list_records, review, upsert
from capability_hunter.github import GitHubClient, GitHubError, validate_slug

def repo_payload(name="example/tool", stars=120):
    return {
        "full_name": name, "name": name.split("/")[-1],
        "owner": {"login": name.split("/")[0]}, "html_url": "https://github.com/" + name,
        "private": False, "archived": False, "stargazers_count": stars,
        "default_branch": "main", "description": "reasoning graph tools",
        "license": {"spdx_id": "MIT"}, "pushed_at": "2026-10-01T00:00:00Z",
        "topics": ["reasoning", "graph"],
    }

def mock_client():
    def handle(request):
        assert request.url.host == "api.github.com"
        path = request.url.path
        if path == "/search/repositories":
            assert "is:public" in request.url.params["q"]
            return httpx.Response(200, json={"items": [
                repo_payload(), dict(repo_payload("private/example"), private=True)]})
        if path == "/repos/example/tool":
            return httpx.Response(200, json=repo_payload())
        if path == "/repos/example/tool/git/trees/main":
            return httpx.Response(200, json={"sha": "abc123", "tree": [
                {"path": "README.md", "size": 38, "type": "blob", "sha": "file1"},
                {"path": "src/server.py", "size": 25, "type": "blob", "sha": "file2"},
                {"path": "image.png", "size": 200, "type": "blob", "sha": "file3"},
            ]})
        if path in {"/repos/example/tool/contents/README.md", "/repos/example/tool/contents/src/server.py"}:
            code = "MCP server API\n" if path.endswith("README.md") else "def tool(): return 1\n"
            return httpx.Response(200, json={
                "type": "file", "size": len(code), "encoding": "base64",
                "content": base64.b64encode(code.encode()).decode(),
                "sha": "blobhash", "html_url": "https://github.com/example/tool/blob/main/readme",
            })
        return httpx.Response(404, json={"error": "not found"})
    return GitHubClient(token="test-public-only", transport=httpx.MockTransport(handle))

def test_slug_validation_and_no_path_traversal():
    assert validate_slug("example/repo") == "example/repo"
    for invalid in ["../x", "x/../y", "https://github.com/x/y", "x/y/z", "x/.hidden"]:
        with pytest.raises(ValueError):
            validate_slug(invalid)

def test_search_filters_private_and_ranks():
    with mock_client() as client:
        records = discover(client, "reasoning graph", 10)
    assert len(records) == 1
    assert records[0]["repo"] == "example/tool"
    assert records[0]["score"]["total"] >= 20

def test_inspection_and_pack_are_source_linked_and_do_not_execute():
    with mock_client() as client:
        result = inspect(client, "example/tool")
    assert result["files_read"] == 2
    assert result["tree_sha"] == "abc123"
    assert all(e["source_url"].startswith("https://github.com") for e in result["excerpts"])
    pack = make_context_pack(result)
    assert "UNTRUSTED THIRD-PARTY TEXT" in pack
    assert "blob SHA" in pack
    proposal = propose_integration(result, "Argument analysis")
    assert proposal["status"] == "PROPOSED_NOT_INSTALLED"
    assert "human approval" in " ".join(proposal["acceptance_tests"])

def test_catalogue_review_not_overwritten_by_recrawl(tmp_path):
    with connect(tmp_path / "catalogue.sqlite") as db:
        upsert(db, {"repo": "example/tool", "stars": 100}, "reasoning")
        assert list_records(db, "CANDIDATE")[0]["repo"] == "example/tool"
        review(db, "example/tool", "APPROVED", "Manually reviewed 2026-10")
        upsert(db, {"repo": "example/tool", "stars": 101}, "new query")
        approved = list_records(db, "APPROVED")
        assert len(approved) == 1
        assert approved[0]["metadata"]["stars"] == 101
        assert approved[0]["reviewer_note"] == "Manually reviewed 2026-10"
        with pytest.raises(ValueError):
            review(db, "example/unknown", "APPROVED", "x")

def test_rate_limit_error_is_reported():
    transport = httpx.MockTransport(lambda _: httpx.Response(403, headers={"X-RateLimit-Remaining": "0"}))
    with GitHubClient(transport=transport) as client:
        with pytest.raises(GitHubError, match="rate limit"):
            client.search("argument-mining")

def test_private_metadata_cannot_be_read():
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json={"private": True}))
    with GitHubClient(transport=transport) as client:
        with pytest.raises(GitHubError, match="Private"):
            client.repo("owner/repo")
