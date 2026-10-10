# Income Operator: OpenClaw + Capability Hunter

**Stage:** tested offline opportunity underwriting and a reviewable OpenClaw skill. **Not:** deployed OpenClaw, connected ChatGPT MCP, live lead scraper, automatic income or self-operating company.

## What was integrated

The existing Python Capability Hunter remains the discovery/research component. The `skills/income-operator/SKILL.md` file is a valid OpenClaw workspace skill that directs an authorised operator to research, verify and evaluate business opportunities. `python -m capability_hunter.income` is a dependency-free, offline opportunity triage/underwriting command, shared by OpenClaw and any other authorised client. It returns explicit review dispositions and economics without reading external private data or performing transactions.

Install the package in the OpenClaw agent's execution environment before running the skill. The skill file by itself cannot install OpenClaw or create a running agent.

```sh
python -m pip install -e '.[dev]'
python -m pytest -q tests/test_income.py
python -m capability_hunter.income --input examples/income-opportunities.sample.json
# separately, on an authorised OpenClaw host:
openclaw skills install ./skills/income-operator
openclaw skills list
openclaw skills check
openclaw security audit
```

If OpenClaw sandboxed execution is used, install Python and this package **inside the actual sandbox** or make a carefully reviewed API available to the sandbox. Do not disable sandboxing to make the first command work. The example data is deliberately fictional and must never be described as current paid work.

## Monetisation opportunity map

| Route | Who pays / value delivered | Income mechanism | Speed / constraints |
|---|---|---|---|
| Paid code bounties | Maintainers or sponsors pay for merged fixes | Per accepted issue / contract | Sometimes relatively quick, but assignment, review and payout can take days or longer. Avoid work without transparent eligibility. |
| AI workflow implementation | Small organisations pay to reduce repetitive work | Fixed-scope setup + approved support retainer | Best practical recurring-income candidate if there is a buyer. Measure hours saved and error rate. |
| Research and verified lead intelligence | Businesses pay for specialised, permission-based market or account research | Custom report / subscription | Differentiate verified evidence from machine-generated lists; respect privacy and outreach rules. |
| Website / CRM / inbox integration | Businesses pay for a real working integration | Project fee and maintenance | More reliable than selling generic AI agents if it solves a defined problem. |
| Managed support agents | Client pays for FAQ triage / routing with handoff and audit | Implementation + monthly monitoring | Humans must approve high-stakes responses, refunds and commitments. Separate each client's gateway and data. |
| Digital research briefs | Individual readers/teams buy a useful specialist brief | Report fee or membership | Audience-building effort; open/public sources need licensing checks. |
| Templates / vetted skills / training | Teams purchase deployment help, workflow templates or workshops | One-off digital product / consulting | Open source is compatible with selling expertise; maintain licence notices. |
| Managed data products | Teams buy **lawfully collected** and updated public signals | Usage or subscription | Monitoring/retention costs and data licences matter. |
| Education and tutorials | Users pay for teaching automation, decision systems or practical integrations | Workshops / courses | Requires demonstrable outcome, not guaranteed credentials. |
| Affiliate/referral partnerships | Provider pays a disclosed commission | Qualified referral | Comply with advertising disclosure, no misleading comparison or spam. |
| Grants, prize competitions | Sponsor or organiser rewards qualifying work | Grant/prize, intermittent | Eligibility, acceptance and payment delays are material; not reliable daily income. |
| Authorised security bounties | Programme pays for qualifying, in-scope findings | Per accepted report | Only targets and methods expressly in programme scope. Never probe third parties without authorisation. |
| Plugin/integration products | Customers pay for hosted orchestration or maintained integrations | SaaS / metered service | Hosting, API costs, privacy, support and multi-tenancy create additional risk. Avoid one gateway for untrusted customers. |
| Productised creative services | Clients pay for finished sites, assets or edited content | Fixed-fee deliverables | Quality, ownership and provenance require human review. |

**No capital at risk priority:** First validate paid client demand or clearly funded bounties. Avoid paid-to-bid schemes, courses claiming guaranteed profit, deposits, leveraged trading, yield farming, gambling, prohibited scraping or mass unsolicited messages. A source may be real while the specific listing is closed or payment is uncertain.

## Engine architecture

```text
official/public sources + authorised client referrals
    -> provenance and availability checks (human or permitted APIs)
    -> structured opportunity records
    -> offline scorer (this change)
    -> safety gates + verification queue
    -> human selects target
    -> separate approved proposal / execution workflow
    -> human reviews deliverables and external sending
    -> independently confirmed invoice/payment
    -> profit ledger + evidence-led revision of assumptions
```

OpenClaw can *coordinate* this workflow after an authenticated gateway, model provider, tools and a scheduler are deliberately configured. It is not the money source and cannot make acceptance or payment happen. Keep opportunity source terms and login permissions attached to every lead. GitHub Actions hourly catalogue discovery is **not** a paid job hunter. No new cron job or auto-submission is included.

## Unit economics

- **Gross contingent hourly:** stated gross payout ÷ estimated labour hours. This is **not** earned hourly pay.
- **Optional subjective expected payout:** gross payout × user-entered success probability − external cash costs. Never auto-fill this probability from the model. The score is illustrative, not a forecast or an objective confidence value.
- **Actual net receipt:** confirmed collected amount − fees − external service/model spend − refunds. Track labour separately; compute effective hourly from actual net receipts and actual time.
- **Retention economics:** monthly service margin should account for hosting, model usage, customer support, quality assurance, taxes and downtime; no extrapolation from one hypothetical customer.

Example, **not an offer**: a $200 funded task estimated at 4 hours has *contingent* gross value of $50/hour. If there is an assumed 25% success chance and no cash outlay, expected value **under that assumption** is $12.50/hour, before tax and opportunity cost. The scorer outputs both and marks unverified opportunities for manual verification.

## Near-term execution sequence

1. Pick one of (a) funded developer bounties, (b) a fixed-fee automation service with demonstrable ROI, (c) a bespoke research/data brief. These differ in selling cycle and technical requirements.
2. Identify 10 genuinely current, source-linked opportunities on official sites or through authorised client enquiry. Do not manufacture prospects; confirm eligibility and payer.
3. Score them offline, identify missing evidence, take the top 3 back through a human decision gate.
4. Deliver one **small, reviewable** proof of value, negotiate acceptance criteria and documented payment terms **before** expanding scope.
5. Track pipeline: discovered → verified → contacted with approval → agreement → delivered → accepted → paid. Revise strategy based on realised payment and labour, not headlines or model confidence.

## Security and permissions

- Use OpenClaw's own supported Skill mechanism, not vendored upstream OpenClaw code. Its Gateway requires a separate trusted runtime and credentials.
- Public repo MUST NOT contain client data, prospect private contact information, session tokens, gateway credentials, account details or patient data.
- A `SKILL.md` can instruct an agent but does not enforce access control. Apply OpenClaw sandboxing, host permissions, per-tool allowlists, human approvals and secret management in the actual host.
- Do not expose a full-trust OpenClaw Gateway or the current unauthenticated Capability Hunter MCP gateway to untrusted customers. Separate gateway/credentials by client or deploy a properly authenticated, restricted service.
- Do not merge untrusted OpenClaw community skills, remote code or self-written agents without review and tests. Never do unconsented purchases, platform applications, external messaging, trading or autonomous self-modifying deployments.

## Authoritative references checked 2026-10-09

- OpenClaw source: https://github.com/openclaw/openclaw (MIT, separate runtime)
- Skill format and testing: https://docs.openclaw.ai/tools/creating-skills
- Gateway security: https://docs.openclaw.ai/gateway/security
- Skills architecture: https://docs.openclaw.ai/tools/skills
- Paid OSS work: https://algora.io/pricing/ and https://docs.opire.dev/overview/getting-started
- Evidence of demand for automation services: https://www.upwork.com/research/upwork-monthly-hiring-insights-august-2026

These are reference sources, not evidence of any particular active paid job.
