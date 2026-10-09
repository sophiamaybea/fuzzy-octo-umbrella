# Philosophy Engine: automatic GitHub discovery and correction-based improvement

This extension connects the separate **Philosophy Engine v0.2** REST/MCP package to
your existing **Capability Hunter** MCP and gives philosophical reasoning its own
hourly discovery workflow and correction ledger. It does **not** silently import
external code, install unknown repositories or retrain the base AI model.

## What becomes automatic after merging

The scheduled **Philosophy capability evolution** workflow runs hourly (subject to
GitHub schedule delays), calls *fresh public GitHub search*, reads bounded source
metadata, and proposes updates to `catalogues/philosophy_capabilities.json` only
when material candidate metadata or a source tree SHA changes. A separate GitHub
Actions artefact records each run, even with zero new changes. It opens or updates
one human-review PR. It never merges executable code or silently deploys an adapter.

This complements, rather than replaces, the existing general-purpose hourly
Capability Hunter workflow. Discovery results are suggestions, **not verification
that a repository makes the engine reason better**.

To enable PR creation, check repository **Settings → Actions → General** and allow
GitHub Actions **read/write** permissions and creation of pull requests, where your
account's settings permit. Also enable Actions for this repository.

## Bridge to the previously built Philosophy Engine

Deploy the *separate* `philosophy-engine-mcp-api-v0.2.zip` package and configure
these **server-side environment secrets** on your existing Capability Hunter host:

```
PHILOSOPHY_ENGINE_URL=https://your-private-philosophy-engine.example
PHILOSOPHY_ENGINE_API_KEY=<matches the other service PHILOSOPHY_API_KEY>
PHILOSOPHY_ALLOW_MCP_INQUIRY=1
```

The existing MCP gateway then offers `run_philosophy_inquiry`, which delegates to
the real Philosophy Engine's `POST /v1/inquiry`. Without those settings the tool
returns `NOT_CONFIGURED` or `DISABLED`. The original philosophy code is **not**
copied into this repository, and this integration is **not live** until both
services are actually deployed, connected and verified.

**Security:** the Capability Hunter public MCP is not yet per-user authenticated.
Do **not** enable forwarding private interviews, patient data, unpublished writing
or other confidential information from the public MCP. Add MCP authentication,
quotas, proper deployment secrets and audit controls before turning this on.

## Corrections and durable, reviewable lessons

Set `RESEARCH_API_KEY` and a private, persistent volume:
`PHILOSOPHY_LESSON_DB=/persistent/private/philosophy.sqlite3`.

An authenticated request to
`POST /api/v1/philosophy/corrections`, with `Authorization: Bearer <RESEARCH_API_KEY>`,
accepts a short object:

```json
{
  "question": "Was this inference valid?",
  "alleged_error": "The answer attributed a premise the speaker did not assert.",
  "proposed_correction": "Mark that premise as hypothetical and seek the exact quote.",
  "evidence_url": "https://example.org/transcript"
}
```

Only a SHA-256 hash of the question is stored; the alleged error and correction
text are retained. **Do not submit identifying or sensitive data.** Newly recorded
feedback is `PENDING` and has no automatic effect on conclusions. The only way
to elevate it to `VERIFIED` is an explicit human review.

Review from the private admin endpoint
`POST /api/v1/philosophy/review` with bearer token
`PHILOSOPHY_REVIEW_KEY` and JSON:
```json
{"id":"<the correction id>", "decision":"VERIFIED", "reviewer_note":"Compared with the original transcript"}
```
The reviewer key must be **different** from the general research key. An absent
review key disables the endpoint.

The private `GET /api/v1/philosophy/lessons?status=VERIFIED` requires the
`RESEARCH_API_KEY`. The `list_verified_philosophy_lessons` MCP tool is **disabled by
default** because the public MCP lacks authentication. Set
`PHILOSOPHY_EXPOSE_VERIFIED_LESSONS=1` only when the MCP itself is authenticated
and the stored records are safe for the intended clients.

Persistent storage is required. Ephemeral hosting disks lose corrections at
restart. Private SQLite is excluded from the public GitHub repo and workflows.

## What is not automatic

- This change **does not** merge or deploy any new GitHub code.
- New methods still require a reviewed adapter, licence and security inspection,
  sandboxed tests and meaningful before/after benchmarks.
- Reading feedback into an inference workflow is distinct from changing model
  weights. There is no automatic retraining.
- An MCP connector cannot force ChatGPT to call it in every conversation.
- Hourly actions run only after the new workflow is merged into the default branch.
- GitHub Actions and the host require their own configuration and permissions.

Run locally:
```bash
python -m pip install '.[dev]'
python -m pytest -q
python -m capability_hunter.philosophy_evolution --catalogue catalogues/philosophy_capabilities.json
```

Philosophical methods and epistemic distinctions are based on the original
user-provided Philosophy Engine brief; repository suggestions are not validation
of the underlying systems.
