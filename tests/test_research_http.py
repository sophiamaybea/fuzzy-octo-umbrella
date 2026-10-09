"""Contract tests for key-guarded REST custom routes; no live provider traffic."""
import asyncio
import json

from starlette.requests import Request

from capability_hunter import server


def request(method, path, headers=None, query_string=b"", body=b""):
    headers = headers or {}
    sent = False

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    scope = {
        "type": "http", "http_version": "1.1", "method": method,
        "scheme": "http", "path": path, "root_path": "",
        "query_string": query_string, "server": ("localhost", 8000),
        "client": ("127.0.0.1", 1111),
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
    }
    return Request(scope, receive)


def unpack(response):
    return response.status_code, json.loads(response.body)


def test_rest_disabled_without_key(monkeypatch):
    monkeypatch.delenv("RESEARCH_API_KEY", raising=False)
    req = request("GET", "/api/v1/research/search", query_string=b"q=research")
    assert unpack(asyncio.run(server.search_research_api(req)))[0] == 503


def test_rest_rejects_missing_or_wrong_bearer(monkeypatch):
    monkeypatch.setenv("RESEARCH_API_KEY", "test-secret-value")
    req = request("GET", "/api/v1/research/search", query_string=b"q=research")
    assert unpack(asyncio.run(server.search_research_api(req)))[0] == 401
    wrong = request("GET", "/api/v1/research/search",
                    headers={"authorization": "Bearer wrong"}, query_string=b"q=research")
    assert unpack(asyncio.run(server.search_research_api(wrong)))[0] == 401


def test_rest_calls_shared_research_engine(monkeypatch):
    monkeypatch.setenv("RESEARCH_API_KEY", "test-secret-value")
    monkeypatch.setattr(server, "search_scholarship",
                        lambda question, limit, domain: {
                            "question": question, "limit": limit, "domain": domain,
                        })
    req = request("GET", "/api/v1/research/search",
                  headers={"authorization": "Bearer test-secret-value"},
                  query_string=b"q=metacognition&limit=4&domain=general")
    status, payload = unpack(asyncio.run(server.search_research_api(req)))
    assert status == 200
    assert payload == {"question": "metacognition", "limit": 4, "domain": "general"}


def test_rest_validates_limit(monkeypatch):
    monkeypatch.setenv("RESEARCH_API_KEY", "test-secret-value")
    req = request("GET", "/api/v1/research/search",
                  headers={"authorization": "Bearer test-secret-value"},
                  query_string=b"q=research&limit=bad")
    status, payload = unpack(asyncio.run(server.search_research_api(req)))
    assert status == 422 and "error" in payload


def test_dossier_rejects_invalid_json(monkeypatch):
    monkeypatch.setenv("RESEARCH_API_KEY", "test-secret-value")
    req = request("POST", "/api/v1/research/dossier",
                  headers={"authorization": "Bearer test-secret-value"},
                  body=b"{not JSON}")
    assert unpack(asyncio.run(server.dossier_research_api(req)))[0] == 400
