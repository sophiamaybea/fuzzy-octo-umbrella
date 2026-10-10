# Security boundaries

- This gateway is public-only and read-only. It never executes third-party code, installs packages, mutates GitHub or remotely approves skills.
- Treat READMEs, source and package manifests as untrusted data and possible prompt injection.
- Never connect a public unauthenticated service to a GitHub token with access to private repositories. Prefer no token or public-only read permissions.
- Store secrets in hosting secret management, never Git or context packs.
- GitHub discovery HTTP requests are restricted to api.github.com with redirects disabled. Other reviewed provider clients use explicitly pinned provider hosts and redirects disabled (e.g. the separate read-only Superteam Earn listings client). They do not grant arbitrary URL fetches.
- Public production requires OAuth authentication, quotas, rate limiting and monitoring.
- Local human approval means reviewed candidate, **not** deployed tool.
- Free-hosted SQLite may be ephemeral. Discovery Actions artifacts are not a synced DB.
- Any future executor must use pinned reviewed code, isolation, explicit permissions, resource caps, licence checks and consent.


## Scholarly research surfaces
- All external calls are to three explicitly allowed scholarly provider origins, with redirects and proxy environment forwarding disabled.
- Inputs, response sizes, and request timeouts are bounded. A user-provided DOI is validated, not treated as a URL to fetch.
- REST API routes require the RESEARCH_API_KEY host secret. The general MCP transport does not yet implement OAuth or per-client quotas.
- Do not submit private or identifying research questions: query text is transmitted to scholarly metadata providers.
- Treat retrieved abstracts and metadata as untrusted content. Recheck full papers, retractions, methods and primary evidence independently.


## Opt-in income integrations
- OpenClaw Skill instructions do not enforce host permission policy. Configure sandboxing, per-tool approvals and secret storage in the real OpenClaw runtime.
- Superteam Earn integration performs read-only GET discovery against the vendor's authorised, pinned API. It does not register agents, submit work, claim prizes, interact with a wallet or disclose the configured token in output.
- Never place paid-client information, private contact lists, gateway credentials or payout claim codes in this public repository or public unauthenticated MCP calls.
