"""No-live-network contract tests for the scholarly MCP backend."""
import httpx
import pytest
from capability_hunter.research import (
    ScholarlyClient, ResearchError, search_scholarship, research_dossier,
    lookup_doi_metadata, validate,
)


def mocked(req):
    assert req.url.host in {"api.openalex.org", "api.crossref.org", "www.ebi.ac.uk"}
    if req.url.host == "api.openalex.org":
        return httpx.Response(200, json={"results": [{
            "doi": "https://doi.org/10.1234/ABC",
            "display_name": "Test paper", "publication_year": 2025,
            "primary_location": {"source": {"display_name": "Journal"}},
        }]})
    if req.url.raw_path.decode() == "/works/10.1234%2Fabc":
        return httpx.Response(200, json={"message": {
            "DOI": "10.1234/abc", "title": ["Test paper"],
        }})
    if req.url.host == "api.crossref.org":
        return httpx.Response(200, json={"message": {"items": [
            {"DOI": "10.1234/abc", "title": ["Test paper"],
             "abstract": "<jats:p>Abstract &amp; detail.</jats:p>",
             "published": {"date-parts": [[2025]]}},
            {"DOI": "10.1234/def", "title": ["Another paper"]},
        ]}})
    return httpx.Response(200, json={"resultList": {"result": [{
        "doi": "10.1234/abc", "title": "Test paper", "pubYear": "2025",
        "abstractText": "Different abstract",
    }]}})


def test_validation():
    for q in ("", "a", "x" * 301):
        with pytest.raises(ValueError):
            validate(q, 5, "general")
    for lim in (0, 16, True):
        with pytest.raises(ValueError):
            validate("medical methods", lim, "general")
    with pytest.raises(ValueError):
        validate("medical methods", 5, "bad")


def test_federated_search_and_doi_merge():
    with ScholarlyClient(httpx.MockTransport(mocked)) as client:
        result = search_scholarship("medical methods", 8, client=client)
    assert result["total_deduplicated_in_sample"] == 2
    assert result["results"][0]["providers"] == ["crossref", "europepmc", "openalex"]
    assert result["results"][0]["abstract_excerpt"] == "Abstract & detail."
    assert result["results"][0]["url"] == "https://doi.org/10.1234/abc"
    assert result["results"][0]["evidence_scope"] == "abstract_and_metadata"


def test_dossier_is_clear_about_limitations():
    with ScholarlyClient(httpx.MockTransport(mocked)) as client:
        result = research_dossier("medical methods", client=client)
    assert result["research_protocol"]["epistemic_status"].startswith("SOURCE_DISCOVERY_ONLY")


def test_upstream_failure_is_visible():
    def partial(req):
        return httpx.Response(429) if req.url.host == "api.openalex.org" else mocked(req)
    with ScholarlyClient(httpx.MockTransport(partial)) as client:
        result = search_scholarship("medical methods", client=client)
    assert result["providers"]["openalex"].startswith("error:")
    assert result["results"]


def test_size_and_host_limits():
    with ScholarlyClient(httpx.MockTransport(
        lambda _: httpx.Response(200, content=b"x" * 1_500_001))) as client:
        with pytest.raises(ResearchError, match="too large"):
            client.search("openalex", "medical methods", 3)
        with pytest.raises(ValueError):
            client.get("attacker", "/")


def test_doi_lookup_and_invalid_inputs():
    with ScholarlyClient(httpx.MockTransport(mocked)) as client:
        assert lookup_doi_metadata("https://doi.org/10.1234/ABC", client)["title"] == "Test paper"
        for invalid in ("../../etc/passwd", "https://evil.example/page", "10.bad/x"):
            with pytest.raises(ValueError):
                lookup_doi_metadata(invalid, client)
