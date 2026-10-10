---
name: income-operator
description: Investigate legitimate paid work and product opportunities, score economics, and prepare human-reviewed next actions without sending or spending.
user-invocable: true
---

# Income Operator for OpenClaw

Operate as a **read → verify → calculate → propose** agent. This skill does not earn money by itself. Its executable scoring backend is the local `capability_hunter.income` Python module from the same repository, installed separately in the runtime.

## Appropriate requests

When asked to find paid GitHub issues, AI automation clients, research gigs, paid troubleshooting, digital products or other ethical income opportunities, build a source-linked candidate queue. Prioritise the person's skills, jurisdiction, working hours, access and **zero upfront spend**. Start with official listings and APIs permitted by their terms. Do not guess that a listing is open or payable.

## Method

1. Identify concrete buyer, desired deliverable, payment terms, effort, eligibility and official listing URL. Record **source checked at timestamp** as narrative alongside each lead. Discovery/search is not proof of payout.
2. Categorise: `bounty`, `client_service`, `productised_service`, `digital_product`, `license`, `education`, `research`, `support`, `affiliate`, `grant_competition`, or `other`. These are triage labels, not guaranteed markets.
3. If concrete evidence for the payout/eligibility is unavailable, set `payout_confirmed=false` and/or `eligibility_confirmed=false`. Never invent a success probability. If one is supplied, label it a subjective assumption.
4. Prepare a local JSON list and run the read-only scorer via the `exec` tool **only when execution is enabled and approved**:

   `python -m capability_hunter.income --input /path/to/leads.json --output /path/to/triage.json`

   The command performs no network requests and no writes except the explicit output file. If Python or the package is unavailable, give the schema and state that scoring was not executed.
5. Inspect the resulting `disposition`. Exclude `BLOCKED`. Validate each `VERIFY` item at the primary source before proceeding. `REVIEW` means human decision required, **not** permission to apply.
6. Present the top feasible 3 candidates with economic assumptions, time-to-cash uncertainties and one concrete next action for each. Separate buyer existence, payment evidence, and opportunity forecast.
7. Never autonomously buy anything, bid, trade, claim bounties, message strangers, submit proposals/PRs, access private accounts, install a skill, publish content or exchange personal details. Require explicit user approval for the exact external action. Comply with site terms and relevant laws. Never scrape against access controls or harvest private contact data.
8. Only report revenue when an actual payment has been independently confirmed. Record gross receipts, transaction fees, hosting/model costs, refunds and time spent separately. Unpaid leads and awarded-but-unpaid contracts are not earnings.

## Input JSON

See `examples/income-opportunities.sample.json` in the source repository. It is a list of records with `title`, `url` (HTTPS), `payout_usd`, `hours_estimate`, optional `cash_cost_usd`, `success_probability` (0–1, subjective), `eligibility_confirmed`, `payout_confirmed`, `evidence_note`, and boolean safety flags. All amounts are USD-equivalent assumptions until verified; convert currencies with a separately cited current rate. The scorer never checks links.

## Installation / runtime boundary

Clone a reviewed commit of the repository onto a machine with Python 3.11+, install `pip install -e .`, then install this skill from the **local** directory using `openclaw skills install ./skills/income-operator` and validate with `openclaw skills list` / `openclaw skills check`. Configure the OpenClaw Gateway and model separately. Do **not** grant shell or host access merely to load the skill; an operator may use a sandboxed, narrowly allowlisted execution environment. This repository does **not** deploy OpenClaw, create a ChatGPT connector, or enable background monitoring automatically.

See `docs/income-engine.md` for monetisation channels, risk controls, economics and rollout.

## Official agent-eligible bounty discovery (optional)

Superteam Earn publishes a documented agent API for `AGENT_ALLOWED` and `AGENT_ONLY` bounties, projects and hackathons. Once an operator has registered an agent **themselves** and privately configured `SUPERTEAM_EARN_AGENT_API_KEY`, fetch read-only live listings:

`python -m capability_hunter.superteam --take 20 --type bounty --output /private/path/superteam-leads.json`

Never put the API key or claim code into prompts, GitHub, logs or client proposals. The module does not register agents, submit entries or claim rewards. Read full official eligibility and prize rules before translating any source listing into the underwriting format; agent eligible does not mean payment guaranteed. A human must claim any payout. Source: https://superteam.fun/earn/agents . Do not automatically submit work merely because the external platform permits agents.
