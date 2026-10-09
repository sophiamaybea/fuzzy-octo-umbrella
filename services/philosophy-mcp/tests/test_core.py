import pytest
from philosophy_core import (
    choose_methods, socratic_questions, reconstruct_argument, argument_to_argdown,
    verify_formal, argumentation_graph, conclusion_audit,
)

def test_method_selection_is_explainable():
    x = choose_methods("What is justice and fairness in healthcare?")
    assert len(x["methods"]) == 3
    assert any(m["keyword_matches"] for m in x["methods"])

def test_socratic_probes_are_questions_not_verdicts():
    x = socratic_questions("All laws are just", ["legality entails justice"])
    assert len(x["questions"]) >= 8
    assert "not discovered contradictions" in x["method"]

def test_conservative_extraction():
    x = reconstruct_argument("All birds fly. Therefore, penguins fly.")
    assert x["status"] == "candidate_extraction"
    assert "penguins" in x["explicit_conclusion_fragment"]
    assert reconstruct_argument("Freedom matters.")["explicit_premise_fragments"] == []

def test_argdown_export():
    x = argument_to_argdown(["P implies Q", "P"], "Q", ["P is disputed"])
    assert "(3) Q" in x["argdown"]
    assert "-> <Main argument>" in x["argdown"]

def test_modus_ponens():
    x = verify_formal(["P >> Q", "P"], "Q")
    assert x["status"] == "valid"

def test_invalid_has_countermodel():
    x = verify_formal(["P >> Q", "Q"], "P")
    assert x["status"] == "invalid" and x["countermodel"]["P"] is False

def test_inconsistent_not_reported_sound():
    x = verify_formal(["P", "not P"], "Q")
    assert x["status"] == "inconsistent_premises"

def test_ast_rejects_code_execution():
    with pytest.raises(ValueError):
        verify_formal(["__import__('os').system('echo bad')"], "Q")

def test_attack_cycle_and_stable_extensions():
    x = argumentation_graph(["A", "B"], [["A", "B"], ["B", "A"]])
    assert x["grounded"]["undecided"] == ["A", "B"]
    assert x["stable_extensions"] == [["A"], ["B"]]

def test_unattacked_node_accepted():
    x = argumentation_graph(["A", "B", "C"], [["A", "B"], ["B", "C"]])
    assert x["grounded"]["in"] == ["A", "C"]
    assert x["grounded"]["out"] == ["B"]

def test_unknown_edges_rejected():
    with pytest.raises(ValueError):
        argumentation_graph(["A"], [["X", "A"]])

def test_audit_does_not_claim_truth():
    x = conclusion_audit("C", ["P"])
    assert x["truth_verdict"] == "not_assessed"
    assert x["gaps"]
