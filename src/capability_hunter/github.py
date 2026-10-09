"""GitHub REST API client with fixed-host requests and conservative response bounds."""
from __future__ import annotations

import base64
import os
import re
from urllib.parse import quote
import httpx

SLUG = re.compile(r"^[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}$")
MAX_FILE_BYTES = 45_000
MAX_TREE_ENTRIES = 4_000

class GitHubError(RuntimeError):
    """Network, GitHub API or public-only policy error."""

def validate_slug(repo: str) -> str:
    if not isinstance(repo, str) or not SLUG.fullmatch(repo):
        raise ValueError("Repository must be in owner/name form")
    if '..' in repo or repo.startswith('.') or '/.' in repo:
        raise ValueError("Unexpected repository path")
    return repo

class GitHubClient:
    def __init__(self, token: str | None = None, transport: httpx.BaseTransport | None = None):
        token = token if token is not None else os.getenv("GITHUB_TOKEN", "")
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "capability-hunter/0.1 (+public-read-only)",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.http = httpx.Client(
            base_url="https://api.github.com", headers=headers,
            timeout=httpx.Timeout(12.0), follow_redirects=False,
            trust_env=False, transport=transport,
        )

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.http.close()

    def get(self, path: str, params: dict | None = None) -> dict:
        if not path.startswith("/") or path.startswith("//") or "?" in path or "#" in path:
            raise ValueError("Invalid API path")
        try:
            r = self.http.get(path, params=params)
            if r.status_code == 403 and r.headers.get("X-RateLimit-Remaining") == "0":
                raise GitHubError("GitHub API rate limit reached. Set a public-read token or retry later.")
            if r.status_code >= 300:
                raise GitHubError(f"GitHub API HTTP {r.status_code} for {path}")
            obj = r.json()
            if not isinstance(obj, dict):
                raise GitHubError("Unexpected GitHub response")
            return obj
        except httpx.HTTPError as exc:
            raise GitHubError(f"GitHub transport error: {type(exc).__name__}") from exc
        except ValueError as exc:
            raise GitHubError("GitHub response is not JSON") from exc

    def search(self, query: str, limit: int = 10) -> list[dict]:
        if not (isinstance(query, str) and 2 <= len(query.strip()) <= 190):
            raise ValueError("Search query must be 2–190 characters")
        limit = max(1, min(int(limit), 30))
        payload = self.get("/search/repositories", {
            "q": f"{query.strip()} is:public archived:false",
            "per_page": limit, "sort": "best-match",
        })
        return [simplify_repo(x) for x in payload.get("items", []) if not x.get("private", True)]

    def repo(self, slug: str) -> dict:
        slug = validate_slug(slug)
        data = self.get(f"/repos/{slug}")
        if data.get("private", True):
            raise GitHubError("Private repositories are not supported by this public-only gateway")
        return simplify_repo(data)

    def tree(self, slug: str, ref: str) -> dict:
        slug = validate_slug(slug)
        if not ref or len(ref) > 200:
            raise ValueError("Invalid ref")
        obj = self.get(f"/repos/{slug}/git/trees/{quote(ref, safe='')}", {"recursive": "1"})
        raw = obj.get("tree") or []
        bounded = raw[:MAX_TREE_ENTRIES]
        return {
            "paths": [
                {"path": x.get("path"), "size": x.get("size", 0), "sha": x.get("sha")}
                for x in bounded if x.get("type") == "blob"
            ],
            "truncated": bool(obj.get("truncated")) or len(raw) > MAX_TREE_ENTRIES,
            "tree_sha": obj.get("sha"),
        }

    def read_text_file(self, slug: str, path: str, ref: str) -> dict:
        slug = validate_slug(slug)
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in path.split("/"):
            raise ValueError("Invalid file path")
        if any(ord(ch) < 32 for ch in path) or len(path) > 500:
            raise ValueError("Invalid file path")
        data = self.get(f"/repos/{slug}/contents/{quote(path, safe='/')}", {"ref": ref})
        if data.get("type") != "file" or data.get("encoding") != "base64":
            raise GitHubError("Path is not a supported text file")
        if int(data.get("size") or 0) > MAX_FILE_BYTES:
            raise GitHubError(f"File too large (limit {MAX_FILE_BYTES} bytes)")
        try:
            raw = base64.b64decode(data["content"], validate=False)
            if len(raw) > MAX_FILE_BYTES:
                raise GitHubError("Decoded file too large")
            value = raw.decode("utf-8")
        except (KeyError, ValueError, UnicodeError) as exc:
            raise GitHubError("File not valid UTF-8 text") from exc
        return {
            "path": path, "sha": data.get("sha"), "content": value,
            "source_url": data.get("html_url") or
                          f"https://github.com/{slug}/blob/{quote(ref, safe='')}/{quote(path)}",
            "bytes": len(raw),
        }

def simplify_repo(data: dict) -> dict:
    owner = str((data.get("owner") or {}).get("login") or "")
    name = str(data.get("name") or "")
    slug = str(data.get("full_name") or f"{owner}/{name}")
    return {
        "repo": slug,
        "url": data.get("html_url") or f"https://github.com/{slug}",
        "description": (data.get("description") or "")[:1000],
        "stars": int(data.get("stargazers_count") or 0),
        "forks": int(data.get("forks_count") or 0),
        "updated_at": data.get("updated_at"),
        "pushed_at": data.get("pushed_at"),
        "default_branch": data.get("default_branch") or "main",
        "language": data.get("language"),
        "topics": data.get("topics") or [],
        "license": (data.get("license") or {}).get("spdx_id") or "UNKNOWN",
        "archived": bool(data.get("archived", False)),
        "private": bool(data.get("private", True)),
    }
