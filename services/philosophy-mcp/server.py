"""Philosophy MCP: local, reviewable tools rather than simulated wisdom."""
from __future__ import annotations
import os
from mcp.server.fastmcp import FastMCP
from philosophy_core import (
    choose_methods, socratic_questions, reconstruct_argument, argument_to_argdown,
    verify_formal, argumentation_graph, conclusion_audit, lookup_scholarly_sources,
    METHODS,
)

mcp = FastMCP("Philosophical Reasoning Engine", json_response=True)

@mcp.tool()
def select_philosophical_methods(question: str, count: int = 3) -> dict:
    """Choose transparent methodological lenses for a question; results are suggestions."""
    return choose_methods(question, count)

@mcp.tool()
def conduct_socratic_examination(claim: str, assumptions: list[str] | None = None) -> dict:
    """Ask non-leading questions about meaning, premises, comparisons and falsifiers."""
    return socratic_questions(claim, assumptions)

@mcp.tool()
def extract_explicit_argument(text: str) -> dict:
    """Conservatively extract explicitly marked premise/conclusion fragments from supplied text."""
    return reconstruct_argument(text)

@mcp.tool()
def export_argument_map(premises: list[str], conclusion: str, objections: list[str] | None = None) -> dict:
    """Export supplied premises, conclusion and objections as Argdown source for visualisation."""
    return argument_to_argdown(premises, conclusion, objections)

@mcp.tool()
def test_propositional_validity(premises: list[str], conclusion: str) -> dict:
    """Check classical propositional validity. Use A >> B, A and B, not A, A == B."""
    return verify_formal(premises, conclusion)

@mcp.tool()
def evaluate_argument_attack_graph(arguments: list[str], attacks: list[list[str]]) -> dict:
    """Compute grounded, preferred and stable extensions for <=12 abstract arguments."""
    return argumentation_graph(arguments, attacks)

@mcp.tool()
def compare_philosophical_lenses(question: str, methods: list[str]) -> dict:
    """Compare explicitly chosen philosophical methods without conflating their conclusions."""
    if not question.strip(): raise ValueError("question cannot be empty")
    if not 1 <= len(methods) <= 8 or any(m not in METHODS for m in methods):
        raise ValueError(f"choose 1-8 IDs from {sorted(METHODS)}")
    return {"question": question, "lenses": [{"method": m, "focus": METHODS[m][0], "inquiry": METHODS[m][1], "limit": METHODS[m][2]} for m in methods],
            "warning": "This is a method comparison, not an assertion that any philosopher personally endorsed a particular answer."}

@mcp.tool()
def find_counterexample_questions(claim: str) -> dict:
    """Generate counterexample search plans; does not fabricate empirical exceptions."""
    return {"claim": claim, "probes": socratic_questions(claim)["questions"][1:5],
            "requests": ["Specify the quantified domain and any explicit exceptions.",
                         "Supply one realistic and verifiable boundary case.",
                         "Distinguish an actual counterexample from a merely different situation."],
            "warning": "These are tests to pursue, not proof that an exception exists."}

@mcp.tool()
def audit_philosophical_conclusion(claim: str, premises: list[str], evidence: list[str] | None = None,
                                   objections: list[str] | None = None, sources: list[str] | None = None) -> dict:
    """Create an inspectable gap/evidence record without making up a truth verdict."""
    return conclusion_audit(claim, premises, evidence, objections, sources)

@mcp.tool()
def search_philosophy_references(query: str, limit: int = 5) -> dict:
    """Search Crossref bibliographic metadata live; abstracts/full texts are NOT verified."""
    return lookup_scholarly_sources(query, limit)

@mcp.prompt()
def philosophical_review(text: str) -> str:
    """A review protocol for a human or AI researcher."""
    return ("Reconstruct the exact source claim faithfully, marking quotation vs inference. "
            "Separate validity, premise evidence, definitions, ethical premises and rhetorical persuasion. "
            "Select relevant philosophical methods; seek charitable alternatives and serious counterexamples. "
            "Do not infer motives, equate persuasive success with truth, or declare fallacies without justification. "
            "Check sources, record uncertainty, and scrutinise your own objections using the same standards. "
            f"SOURCE TEXT:\n{text}")

if __name__ == "__main__":
    transport = os.getenv("PHILOSOPHY_TRANSPORT", "stdio")
    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport == "http":
        # Public HTTP needs upstream access control and a proper allowed-host configuration.
        if os.getenv("PHILOSOPHY_ALLOW_HTTP") != "I_HAVE_CONFIGURED_AUTH":
            raise SystemExit("HTTP mode disabled: secure the endpoint and set PHILOSOPHY_ALLOW_HTTP only after configuration.")
        mcp.run(transport="streamable-http")
    else:
        raise SystemExit("PHILOSOPHY_TRANSPORT must be stdio or http")
