"""Domain-first specialist tool discovery and recursive capability planning.

This module contains *verified repository names*, not installed tools.
Its priority ordering is heuristic and does not establish benchmark superiority.
No external code or APIs are run by this module.
"""
from __future__ import annotations

import re
from typing import Sequence

BIOLOGY_SIGNALS = (
    r"\bbiolog\w*\b", r"\bbiomedic\w*\b", r"\bbiotech\w*\b",
    r"\bgenom\w*\b", r"\bgenetic\w*\b", r"\bgene(s|tic|s)?\b",
    r"\bprotein(s)?\b", r"\bDNA\b", r"\bRNA\b", r"\bCRISPR\b",
    r"\bsequenc\w*\b", r"\bsingle.cell\b", r"\bscRNA.seq\b",
    r"\bcellular\b", r"\bmicrobiom\w*\b", r"\bmetagenom\w*\b",
    r"\bneuroscien\w*\b", r"\bpharmacolog\w*\b", r"\bpathogen\w*\b",
    r"\bepigenetic\w*\b", r"\btranscriptom\w*\b", r"\bmetabolom\w*\b",
    r"\bclinical trials?\b", r"\bPubMed\b", r"\bmicroscop\w*\b",
    r"\bmolecular biology\b",
)

# Specialized signals are ordered by *precision*, not claimed scientific quality.
SUBFIELDS = {
    "single_cell": (
        r"\bsingle.cell\b", r"\bscRNA.seq\b", r"\bscATAC\b",
        r"\bcell.type annotat\w*\b", r"\bcell cluster\w*\b",
    ),
    "rna_seq": (
        r"\bbulk RNA\b", r"\bRNA.seq\b", r"\btranscriptom\w*\b",
        r"\bFASTQ\b", r"\bdifferential gene expression\b",
    ),
    "genetics": (
        r"\bgenom\w*\b", r"\bgenetic\w*\b", r"\bvariant\w*\b",
        r"\bGWAS\b", r"\bCRISPR\b", r"\bDNA\b",
        r"\bsequence alignment\b",
    ),
    "molecular_modelling": (
        r"\bprotein structur\w*\b", r"\bmolecular dynamics\b",
        r"\bmolecular docking\b", r"\bprotein fold\w*\b",
        r"\bbiophysics\b",
    ),
    "drug_discovery": (
        r"\bdrug\b", r"\bADMET\b", r"\bcheminformatic\w*\b",
        r"\bcompound\b", r"\bpharmacolog\w*\b",
    ),
    "biomedical_evidence": (
        r"\bPubMed\b", r"\bclinical trials?\b", r"\bliterature\b",
        r"\bbiomedical evidence\b", r"\bclinical studies\b",
        r"\bdisease association\w*\b",
    ),
    "microbiome": (
        r"\bmicrobiom\w*\b", r"\b16S\b", r"\bmetagenom\w*\b",
        r"\bmicrobial communit\w*\b",
    ),
    "bioimaging": (
        r"\bmicroscop\w*\b", r"\bcell imag\w*\b",
        r"\bbiological imag\w*\b", r"\bsegmentation\b",
    ),
    "neuroscience": (
        r"\bneuroscien\w*\b", r"\bEEG\b", r"\bMEG\b",
        r"\bbrain imag\w*\b", r"\bfMRI\b",
    ),
}

# Each entry points to a public repository verified at curation time.
# Priority reflects suitability for the subfield, NOT comparative benchmark scores.
BIOLOGY_CANDIDATES = {
    "general": (
        ("mims-harvard/ToolUniverse", "scientific tool discovery and orchestration"),
        ("snap-stanford/Biomni", "general biomedical agent workflow"),
        ("genomoncology/biomcp", "live biomedical source retrieval through MCP"),
    ),
    "single_cell": (
        ("scverse/scanpy", "single-cell data analysis"),
        ("scverse/scvi-tools", "probabilistic single-cell models"),
        ("snap-stanford/Biomni", "multi-step biomedical analysis orchestration"),
    ),
    "rna_seq": (
        ("nf-core/rnaseq", "reproducible bulk RNA-seq processing pipeline"),
        ("biopython/biopython", "sequence parsing and programming"),
        ("snap-stanford/Biomni", "research workflow orchestration"),
    ),
    "genetics": (
        ("biopython/biopython", "sequence utilities and data manipulation"),
        ("genomoncology/biomcp", "variant, gene and disease evidence sources"),
        ("snap-stanford/Biomni", "multi-step genomics research tasks"),
    ),
    "molecular_modelling": (
        ("openmm/openmm", "molecular dynamics simulation"),
        ("snap-stanford/Biomni", "biomedical agent integration"),
        ("mims-harvard/ToolUniverse", "scientific model and software discovery"),
    ),
    "drug_discovery": (
        ("rdkit/rdkit", "molecular representation and cheminformatics"),
        ("genomoncology/biomcp", "drug and trial evidence retrieval"),
        ("mims-harvard/ToolUniverse", "discovery of further scientific tools"),
    ),
    "biomedical_evidence": (
        ("genomoncology/biomcp", "biomedical publications, trials and source-linked data"),
        ("mims-harvard/ToolUniverse", "multi-source research tool discovery"),
        ("snap-stanford/Biomni", "integrated biomedical research workflows"),
    ),
    "microbiome": (
        ("qiime2/qiime2", "microbiome and marker-gene analysis"),
        ("scikit-bio/scikit-bio", "biological statistics and ecology utilities"),
        ("mims-harvard/ToolUniverse", "discovery of compatible analysis tools"),
    ),
    "bioimaging": (
        ("napari/napari", "multidimensional microscopy image exploration"),
        ("mims-harvard/ToolUniverse", "discovery of segmentation methods"),
        ("snap-stanford/Biomni", "biomedical workflow orchestration"),
    ),
    "neuroscience": (
        ("mne-tools/mne-python", "EEG and MEG analysis"),
        ("mims-harvard/ToolUniverse", "discovery of specialised scientific tools"),
        ("snap-stanford/Biomni", "general biomedical research orchestration"),
    ),
}

# Methods to check before upgrading from a suggestion to an executable tool.
CHECKS = (
    "Confirm that the tool directly performs the required operation, using primary documentation.",
    "Compare task-relevant benchmarks, validated use cases and output accuracy.",
    "Verify data compatibility, dependencies, licence, maintenance and computational cost.",
    "Review security, data privacy and execution permissions before any integration.",
    "Test the exact operation with a representative input and independent checks.",
)

def _matches(text: str, patterns: Sequence[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def plan_specialist_tools(task: str, max_candidates: int = 5, max_rounds: int = 3) -> dict:
    """Build a domain->subfield->tool->gap planning cascade.

    Produces a finite workflow *proposal*. Calls no API, executes nothing and
    does not grant permissions. Further domains can be added to the registry.
    """
    if not isinstance(task, str) or not task.strip() or len(task) > 12_000:
        raise ValueError("Task must be non-empty and at most 12000 characters")
    if not isinstance(max_candidates, int) or not 1 <= max_candidates <= 15:
        raise ValueError("max_candidates must be between 1 and 15")
    if not isinstance(max_rounds, int) or not 1 <= max_rounds <= 5:
        raise ValueError("max_rounds must be between 1 and 5")
    if not (_matches(task, BIOLOGY_SIGNALS) or
            any(_matches(task, patterns) for patterns in SUBFIELDS.values())):
        return {
            "domain": "unclassified",
            "status": "DISCOVERY_REQUIRED",
            "approach": "Infer exact discipline, specific task and inputs; search for task-specific tools rather than general-purpose repositories.",
            "github_discovery_query": f"{task.strip()[:160]} open source tools library MCP",
            "suggested_repositories_not_connected": [],
            "max_capability_discovery_rounds": max_rounds,
        }
    subfields = [name for name, terms in SUBFIELDS.items() if _matches(task, terms)]
    if not subfields:
        subfields = ["general"]

    suggestions: list[dict] = []
    included: set[str] = set()
    for subfield in subfields:
        for repo, purpose in BIOLOGY_CANDIDATES[subfield]:
            if repo not in included:
                included.add(repo)
                suggestions.append({
                    "repo": repo, "reason": purpose,
                    "matched_subfield": subfield,
                    "status": "CURATED_CANDIDATE_NOT_INSTALLED",
                    "evidence": "Repository identity verified; no task-specific superiority benchmark run.",
                })
    # Add general orchestrators as fallback when there is capacity.
    if len(suggestions) < max_candidates:
        for repo, purpose in BIOLOGY_CANDIDATES["general"]:
            if repo not in included:
                included.add(repo)
                suggestions.append({
                    "repo": repo, "reason": purpose,
                    "matched_subfield": "general_fallback",
                    "status": "CURATED_CANDIDATE_NOT_INSTALLED",
                    "evidence": "Repository identity verified; no task-specific superiority benchmark run.",
                })
    suggestions = suggestions[:max_candidates]
    discovery_queries = [
        f"{subfield.replace('_', ' ')} reproducible scientific analysis tools MCP GitHub"
        for subfield in subfields
    ]
    if subfields == ["general"]:
        discovery_queries = [
            "biomedical research tool selection MCP",
            "biomedical multi-step agent open source",
        ]
    return {
        "domain": "biology",
        "subfields": subfields,
        "status": "SHORTLIST_NOT_BENCHMARKED",
        "selection_principle": "Select for the exact subtask and validated performance; no single biological repository is universally strongest.",
        "provisional_first_repo": suggestions[0]["repo"] if suggestions else None,
        "provisional_first_repo_status": "NOT_PROVEN_BEST_OR_CONNECTED",
        "suggested_repositories_not_connected": suggestions,
        "github_discovery_queries": discovery_queries,
        "evaluation_checks": list(CHECKS),
        "iterative_workflow": [
            "Classify domain, subfield and concrete operation; list required data and desired result.",
            "Check actually connected tools. Evaluate specialised candidates against the same representative task.",
            "Choose the best *verified* compatible tool, then perform the permitted task.",
            "Inspect outputs for missing evidence, methods or analysis capabilities.",
            "If the next subtask needs another capability, repeat discovery, evaluation and execution with the new subtask.",
            "Stop when acceptance criteria are met, when no validated tool is available, or at the discovery-round limit.",
        ],
        "max_capability_discovery_rounds": max_rounds,
        "execution_status": "NOT_EXECUTED",
        "limitations": [
            "Curated candidates are not automatically installed, callable or connected.",
            "No empirical head-to-head superiority comparison is performed by this planner.",
            "Biomedical model outputs and sources require independent scientific validation.",
        ],
    }
