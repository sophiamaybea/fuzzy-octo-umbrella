"""Offline, deterministic income-opportunity triage for OpenClaw and CLI callers.

No fetching, messaging, purchases, submissions or remote tool execution.
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit

MAX_OPPORTUNITIES = 200
MAX_INPUT_CHARS = 300_000
RISK_FLAGS = (
    "requires_upfront_payment",
    "requires_unauthorised_access",
    "requires_deceptive_outreach",
    "violates_platform_terms",
    "requires_gambling_or_speculation",
)


def _number(value: object, field: str, *, zero_ok: bool = True) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field} must be a finite non-negative number")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite non-negative number") from exc
    if not number.is_finite() or number < 0 or (not zero_ok and number == 0):
        raise ValueError(f"{field} must be a finite non-negative number")
    if number > Decimal("10000000"):
        raise ValueError(f"{field} exceeds input limit")
    return number


def _bool(value: object, field: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field} must be true or false")
    return value


def _url(value: object) -> str:
    if not isinstance(value, str) or len(value) > 1000:
        raise ValueError("url must be a short HTTPS URL")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("url must be a public HTTPS listing URL without credentials")
    if parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("url must not refer to a local service")
    return value


def _money(number: Decimal) -> str:
    return format(number.quantize(Decimal("0.01")), "f")


def underwrite(items: list[dict]) -> dict:
    """Rank supplied opportunities; provenance flags are caller claims, not verified facts."""
    if not isinstance(items, list) or len(items) > MAX_OPPORTUNITIES:
        raise ValueError("Expected a list of at most 200 opportunities")
    results: list[dict] = []
    seen: set[str] = set()
    for index, row in enumerate(items):
        if not isinstance(row, dict):
            raise ValueError(f"opportunity {index} must be an object")
        title = row.get("title")
        if not isinstance(title, str) or not 3 <= len(title.strip()) <= 180:
            raise ValueError(f"opportunity {index} requires a title (3-180 characters)")
        url = _url(row.get("url"))
        key = url.split("#", 1)[0].rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        payout = _number(row.get("payout_usd"), "payout_usd")
        hours = _number(row.get("hours_estimate"), "hours_estimate", zero_ok=False)
        costs = _number(row.get("cash_cost_usd", "0"), "cash_cost_usd")
        win_prob_raw = row.get("success_probability")
        win_prob = None if win_prob_raw is None else _number(win_prob_raw, "success_probability")
        if win_prob is not None and win_prob > 1:
            raise ValueError("success_probability must be between 0 and 1")
        risks = [flag for flag in RISK_FLAGS if _bool(row.get(flag, False), flag)]
        eligible = _bool(row.get("eligibility_confirmed", False), "eligibility_confirmed")
        payout_confirmed = _bool(row.get("payout_confirmed", False), "payout_confirmed")
        rationale = row.get("evidence_note", "")
        if not isinstance(rationale, str) or len(rationale) > 1200:
            raise ValueError("evidence_note must be at most 1200 characters")
        if risks:
            disposition = "BLOCKED"
            reasons = ["Risk flag: " + flag for flag in risks]
        elif costs > 0:
            disposition = "MANUAL_REVIEW"
            reasons = ["Cash outlay conflicts with zero-upfront-cost preference"]
        elif not eligible or not payout_confirmed:
            disposition = "VERIFY"
            reasons = (["Confirm eligibility with official listing"] if not eligible else []) + (
                ["Confirm payer and payout terms"] if not payout_confirmed else []
            )
        else:
            disposition = "REVIEW"
            reasons = ["Human decision required before any application or work"]
        expected_net = (payout * win_prob - costs) if win_prob is not None else None
        results.append({
            "title": title.strip(), "url": url, "disposition": disposition,
            "reasons": reasons, "payout_usd": _money(payout),
            "cash_cost_usd": _money(costs), "hours_estimate": str(hours),
            "gross_hourly_if_paid_usd": _money(payout / hours),
            "success_probability_assumption": str(win_prob) if win_prob is not None else None,
            "expected_net_usd_assumption": _money(expected_net) if expected_net is not None else None,
            "expected_hourly_usd_assumption": _money(expected_net / hours) if expected_net is not None else None,
            "evidence_note": rationale,
            "source_verified_by_software": False,
        })
    priority = {"REVIEW": 0, "VERIFY": 1, "MANUAL_REVIEW": 2, "BLOCKED": 3}
    results.sort(key=lambda r: (
        priority[r["disposition"]],
        -Decimal(r["expected_hourly_usd_assumption"] or "-1"),
        -Decimal(r["gross_hourly_if_paid_usd"]),
        r["url"],
    ))
    return {
        "status": "HUMAN_REVIEW_ONLY", "scored": len(results),
        "source_check": "NOT_PERFORMED", "automatic_applications": False,
        "automatic_payments": False, "opportunities": results,
        "method": "Gross/hour and optional user-assumed probability. Not earnings forecasts.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rank income opportunities without external side effects")
    parser.add_argument("--input", required=True, help="JSON list file; - for stdin")
    parser.add_argument("--output", default="-", help="JSON output file; - for stdout")
    args = parser.parse_args(argv)
    try:
        if args.input == "-":
            content = sys.stdin.read(MAX_INPUT_CHARS + 1)
        else:
            if Path(args.input).stat().st_size > MAX_INPUT_CHARS:
                raise ValueError("input too large")
            content = Path(args.input).read_text(encoding="utf-8")
        if len(content) > MAX_INPUT_CHARS:
            raise ValueError("input too large")
        output = json.dumps(underwrite(json.loads(content)), indent=2, ensure_ascii=False)
        if args.output == "-":
            print(output)
        else:
            Path(args.output).write_text(output + "\n", encoding="utf-8")
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"Income triage error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
