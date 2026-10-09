"""Opt-in bridge to the standalone Philosophy Engine v0.2 REST API.

The Philosophy Engine code itself is NOT in this repository. Admin must deploy
and configure it explicitly. URL is not provided by untrusted MCP callers.
"""
from __future__ import annotations

import os
from urllib.parse import urlsplit
import httpx


def run_inquiry(question: str, passage: str | None = None, critique: str | None = None) -> dict:
    if not isinstance(question,str) or not 3 <= len(question.strip()) <= 4000:
        raise ValueError('question must be 3–4,000 characters')
    if any(x is not None and (not isinstance(x,str) or len(x)>12000) for x in (passage,critique)):
        raise ValueError('passage and critique must be text of at most 12,000 characters')
    url=os.getenv('PHILOSOPHY_ENGINE_URL','').rstrip('/')
    secret=os.getenv('PHILOSOPHY_ENGINE_API_KEY','')
    if not (url and secret):
        return {'status':'NOT_CONFIGURED',
                'explanation':'Deploy the Philosophy Engine v0.2 and set PHILOSOPHY_ENGINE_URL and PHILOSOPHY_ENGINE_API_KEY.'}
    parsed=urlsplit(url)
    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('PHILOSOPHY_ENGINE_URL must be an absolute HTTPS base URL')
    if os.getenv('PHILOSOPHY_ALLOW_MCP_INQUIRY')!='1':
        return {'status':'DISABLED', 'explanation':'Admin must opt in to remote inquiry forwarding.'}
    # No arbitrary URLs or redirects. Confidentiality depends on the admin's remote deployment.
    try:
        with httpx.Client(timeout=18,follow_redirects=False,trust_env=False) as client:
            response=client.post(url+'/v1/inquiry',headers={'Authorization':'Bearer '+secret},
                                 json={'question':question,'passage':passage,'critique':critique})
            response.raise_for_status()
            payload=response.json()
            if not isinstance(payload,dict):
                raise ValueError('Unexpected remote Philosophy Engine response')
            return payload
    except (httpx.HTTPError,ValueError) as exc:
        return {'status':'UPSTREAM_ERROR', 'error_type':type(exc).__name__,
                'explanation':'The configured Philosophy Engine did not return a valid response.'}
