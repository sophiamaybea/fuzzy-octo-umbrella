"""Offline tests of the documented read-only endpoint."""
import httpx
import pytest

from capability_hunter.superteam import EarnAPIError, fetch_live_listings


def test_read_only_api_and_headers():
    def handler(request):
        assert request.method == "GET"
        assert request.url.host == "superteam.fun"
        assert request.url.path == "/api/agents/listings/live"
        assert request.url.params["take"] == "2"
        assert request.url.params["type"] == "bounty"
        assert request.headers["Authorization"] == "Bearer test-example-key"
        return httpx.Response(200, json={"items": [{"title": "example"}]})
    obj = fetch_live_listings("test-example-key", take=2, kind="bounty",
                              transport=httpx.MockTransport(handler))
    assert obj["no_submission_performed"] is True
    assert obj["status"] == "SOURCE_DATA_ONLY_NOT_PAYMENT_VERIFIED"
    assert obj["raw_listings"]["items"][0]["title"] == "example"


@pytest.mark.parametrize("status", [301, 401, 403, 429, 500])
def test_error_does_not_leak_key(status):
    transport = httpx.MockTransport(lambda request: httpx.Response(status))
    with pytest.raises(EarnAPIError) as exc:
        fetch_live_listings("private-example-key", transport=transport)
    assert "private-example-key" not in str(exc.value)


@pytest.mark.parametrize("args", [
    {"token": ""}, {"token": "a", "take": 0},
    {"token": "a", "take": 999}, {"token": "a", "kind": "users"},
])
def test_invalid_config(args):
    with pytest.raises(ValueError):
        fetch_live_listings(**args)
