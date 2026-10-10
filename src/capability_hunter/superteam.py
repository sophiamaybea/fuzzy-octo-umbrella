"""Read-only Superteam Earn agent-eligible listings through its documented official API.

No registration, claims, comments, submissions or wallet calls.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

import httpx

BASE_URL = "https://superteam.fun"
TYPES = {"bounty", "project", "hackathon"}
MAX_RESPONSE_BYTES = 1_000_000


class EarnAPIError(RuntimeError):
    """An authorised API lookup failed; no application was attempted."""


def fetch_live_listings(
    token: str, *, take: int = 20, kind: str | None = None,
    transport: httpx.BaseTransport | None = None,
) -> dict:
    if not isinstance(token, str) or not token.strip():
        raise ValueError("A privately stored Superteam Earn agent API key is required")
    if isinstance(take, bool) or not isinstance(take, int) or not 1 <= take <= 30:
        raise ValueError("take must be an integer from 1 to 30")
    if kind is not None and kind not in TYPES:
        raise ValueError("kind must be bounty, project, hackathon or omitted")
    params: dict[str, str | int] = {"take": take}
    if kind:
        params["type"] = kind
    try:
        with httpx.Client(
            base_url=BASE_URL, timeout=httpx.Timeout(12), follow_redirects=False,
            trust_env=False, transport=transport,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        ) as client:
            response = client.get("/api/agents/listings/live", params=params)
            if response.status_code == 401:
                raise EarnAPIError("Superteam Earn rejected the configured API key (401)")
            if response.status_code == 429:
                raise EarnAPIError("Superteam Earn rate limit reached (429)")
            if response.status_code != 200:
                raise EarnAPIError(f"Superteam Earn lookup returned HTTP {response.status_code}")
            if len(response.content) > MAX_RESPONSE_BYTES:
                raise EarnAPIError("Superteam Earn response exceeded size limit")
            body = response.json()
            if not isinstance(body, (dict, list)):
                raise EarnAPIError("Unexpected Superteam Earn JSON structure")
    except httpx.HTTPError as exc:
        raise EarnAPIError(f"Superteam Earn connection failed: {type(exc).__name__}") from exc
    except ValueError as exc:
        raise EarnAPIError("Superteam Earn returned invalid JSON") from exc
    return {
        "origin": "https://superteam.fun/api/agents/listings/live",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "SOURCE_DATA_ONLY_NOT_PAYMENT_VERIFIED",
        "agent_eligible_by_endpoint": True,
        "human_claim_required": True,
        "no_submission_performed": True,
        "raw_listings": body,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch permitted agent-eligible listings for review")
    parser.add_argument("--take", type=int, default=20)
    parser.add_argument("--type", choices=sorted(TYPES), default=None)
    parser.add_argument("--output", required=True, help="Local JSON destination; never prints listings by default")
    args = parser.parse_args(argv)
    try:
        result = fetch_live_listings(os.getenv("SUPERTEAM_EARN_AGENT_API_KEY", ""),
                                     take=args.take, kind=args.type)
        path = Path(args.output)
        if path.exists():
            raise ValueError("Output path must not exist; avoiding accidental overwrite")
        with path.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except (ValueError, OSError, EarnAPIError) as exc:
        print(f"Superteam Earn discovery failed: {exc}", file=__import__("sys").stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
