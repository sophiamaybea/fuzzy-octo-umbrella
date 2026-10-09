import pytest

from capability_hunter.domain_router import plan_specialist_tools
from capability_hunter.domain_discovery import discover_specialist_repositories
from capability_hunter.task_router import compile_task


def test_biology_general_selects_scientific_orchestrator():
    plan = plan_specialist_tools("Look into biology and determine the best research methods")
    assert plan["domain"] == "biology"
    assert plan["subfields"] == ["general"]
    assert plan["provisional_first_repo"] == "mims-harvard/ToolUniverse"
    assert plan["execution_status"] == "NOT_EXECUTED"
    assert plan["provisional_first_repo_status"] == "NOT_PROVEN_BEST_OR_CONNECTED"


def test_single_cell_prefers_specialised_omics_tools():
    plan = plan_specialist_tools("Analyse scRNA-seq single-cell data and annotate cell types")
    assert plan["domain"] == "biology"
    assert "single_cell" in plan["subfields"]
    assert plan["provisional_first_repo"] == "scverse/scanpy"
    assert plan["max_capability_discovery_rounds"] == 3


def test_literature_uses_evidence_source_not_agent_as_default():
    plan = plan_specialist_tools("Search PubMed for clinical trials and biomedical evidence")
    assert plan["provisional_first_repo"] == "genomoncology/biomcp"
    assert plan["status"] == "SHORTLIST_NOT_BENCHMARKED"


def test_technical_subfield_without_word_biology():
    plan = plan_specialist_tools("Analyse EEG and MEG recordings")
    assert plan["domain"] == "biology"
    assert plan["provisional_first_repo"] == "mne-tools/mne-python"


def test_domain_unclassified_uses_live_discovery_query_instead_of_fake_tool():
    plan = plan_specialist_tools("Translate this French poem")
    assert plan["domain"] == "unclassified"
    assert plan["status"] == "DISCOVERY_REQUIRED"
    assert plan["suggested_repositories_not_connected"] == []


def test_task_compiler_integrates_specialists_without_claiming_tool_access():
    result = compile_task("Analyse single-cell RNA-seq data")
    assert result["domains"][0] == "biology"
    assert result["specialist_route"]["domain"] == "biology"
    assert result["github_candidates_not_installed"][0]["repository"] == "scverse/scanpy"
    assert result["execution_status"] == "NOT_EXECUTED_BY_COMPILER"


def test_deduplicate_candidates_and_candidate_cap():
    result = plan_specialist_tools("Use CRISPR in single-cell RNA-seq", max_candidates=4)
    repos = [x["repo"] for x in result["suggested_repositories_not_connected"]]
    assert len(repos) == len(set(repos))
    assert len(repos) <= 4


@pytest.mark.parametrize("task", ["", " ", None, 43, "x" * 12001])
def test_reject_invalid_task(task):
    with pytest.raises(ValueError):
        plan_specialist_tools(task)


@pytest.mark.parametrize("limit,rounds", [(0, 2), (16, 2), (3, 0), (3, 6), ("5", 3)])
def test_bounded_inputs(limit, rounds):
    with pytest.raises(ValueError):
        plan_specialist_tools("biology", limit, rounds)


class FakeGithub:
    def __init__(self):
        self.searched = []

    def repo(self, slug):
        return {
            "repo": slug, "url": "https://github.com/" + slug,
            "description": "Test repo", "language": "Python", "stars": 10,
            "pushed_at": "2026-10-01T00:00:00Z", "license": "MIT",
        }

    def search(self, query, limit=5):
        self.searched.append(query)
        return []


def test_live_discovery_is_metadata_only_with_bounded_search():
    client = FakeGithub()
    report = discover_specialist_repositories("Look into biology", limit=2, client=client)
    assert report["status"] == "DISCOVERED_ONLY_NO_REPO_INSTALLED_OR_BENCHMARKED"
    assert len(report["curated_metadata_checked"]) == 2
    assert 1 <= len(client.searched) <= 2
    assert all(x["status"] == "GITHUB_METADATA_CHECKED_NOT_EXECUTED"
               for x in report["curated_metadata_checked"])


def test_non_biology_domain_search_is_generic_and_does_not_fabricate_curated_repos():
    client = FakeGithub()
    report = discover_specialist_repositories("Study medieval history", client=client)
    assert report["domain"] == "unclassified"
    assert report["curated_metadata_checked"] == []
    assert len(client.searched) == 1
