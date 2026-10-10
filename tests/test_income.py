"""No network and no OpenClaw runtime required."""
import json

import pytest

from capability_hunter.income import main, underwrite


def example(**overrides):
    row = {
        "title": "Example development bounty", "url": "https://example.org/issues/1",
        "payout_usd": "150", "hours_estimate": "3", "cash_cost_usd": "0",
        "eligibility_confirmed": True, "payout_confirmed": True,
    }
    row.update(overrides)
    return row


def test_review_and_expected_value_are_assumptions():
    item = underwrite([example(success_probability="0.5")])["opportunities"][0]
    assert item["disposition"] == "REVIEW"
    assert item["gross_hourly_if_paid_usd"] == "50.00"
    assert item["expected_hourly_usd_assumption"] == "25.00"
    assert item["source_verified_by_software"] is False


def test_unproven_candidate_requires_verification():
    item = underwrite([example(eligibility_confirmed=False, payout_confirmed=False)])
    assert item["opportunities"][0]["disposition"] == "VERIFY"
    assert item["opportunities"][0]["expected_net_usd_assumption"] is None


@pytest.mark.parametrize("risk", [
    "requires_upfront_payment", "requires_unauthorised_access",
    "requires_deceptive_outreach", "violates_platform_terms",
    "requires_gambling_or_speculation",
])
def test_high_risk_blocked(risk):
    assert underwrite([example(**{risk: True})])["opportunities"][0]["disposition"] == "BLOCKED"


def test_cash_cost_flags_manual_review():
    item = underwrite([example(cash_cost_usd="5")])["opportunities"][0]
    assert item["disposition"] == "MANUAL_REVIEW"


def test_duplicate_links_are_collapsed_and_ordered():
    rows = underwrite([
        example(url="https://example.org/issues/1#comments"),
        example(url="https://example.org/issues/1"),
        example(url="https://example.org/issues/2", payout_usd="200"),
    ])
    assert rows["scored"] == 2
    assert rows["opportunities"][0]["gross_hourly_if_paid_usd"] == "66.67"


@pytest.mark.parametrize("row", [
    example(success_probability="1.1"), example(payout_usd="NaN"),
    example(hours_estimate="0"), example(eligibility_confirmed="yes"),
    example(url="http://example.org/issue"), example(url="https://user:pass@example.org/a"),
])
def test_validation(row):
    with pytest.raises(ValueError):
        underwrite([row])


def test_cli_round_trip(tmp_path):
    inp, out = tmp_path / "in.json", tmp_path / "out.json"
    inp.write_text(json.dumps([example()]), encoding="utf-8")
    assert main(["--input", str(inp), "--output", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["status"] == "HUMAN_REVIEW_ONLY"
