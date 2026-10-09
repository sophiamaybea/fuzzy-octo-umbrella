# Philosophical Reasoning Engine (MCP)

A working, inspection-friendly **Model Context Protocol** (MCP) service offering philosophical methods, cautious argument reconstruction, real propositional validity checks, abstract argumentation semantics, Argdown export, Socratic examination, citation-metadata lookup and uncertainty audits.

**Principle:** it is a reasoning toolkit, not a new model or an oracle. It does **not** prove philosophical, moral or empirical claims true, nor does it train or modify ChatGPT.

## What works in v0.1

| MCP tool | Behaviour |
|---|---|
| `select_philosophical_methods` | Explainable heuristic selector, 12 lenses |
| `conduct_socratic_examination` | Non-leading general questions and assumption probes |
| `extract_explicit_argument` | Conservative pattern extraction; never invents hidden premises |
| `export_argument_map` | Reconstructed premises/conclusion in **actual Argdown syntax** |
| `test_propositional_validity` | SymPy propositional satisfiability and countermodels, with inconsistent premises detected |
| `evaluate_argument_attack_graph` | Grounded, preferred and stable Dung semantics (max 12 arguments) |
| `compare_philosophical_lenses` | Side-by-side methods, limitations and inquiries |
| `find_counterexample_questions` | Counterexample search prompts; no fabricated examples |
| `audit_philosophical_conclusion` | Missing evidence, sources, objections and revision questions |
| `search_philosophy_references` | Live Crossref **metadata only**, not automatic fact verification |
| MCP prompt `philosophical_review` | Repeatable source-fidelity and self-critique protocol |

This service generates Argdown source but does **not** embed the Argdown JavaScript parser. Its argumentation solver implements Dung-style graph semantics independently; it does **not** claim to embed Carneades. Nor does it embed Logikon, Carnap, STORM, Lean or Z3. Those are planned, independently auditable adapters, not secretly present integrations.

## Install (Python 3.11+)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

`server.py` uses MCP **stdio**, intended for a locally configured MCP client or desktop agent. MCP uses stdout for protocol; print debugging to stderr only. To run tests:

```bash
pip install -r requirements-dev.txt
pytest -q
```

### Add as a local MCP client (example configuration)

```json
{
  "mcpServers": {
    "philosophy": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/server.py"]
    }
  }
}
```

The client must support stdio MCP. Connecting this repository to your ChatGPT account is a **separate user-authorised action** and is not automatically achieved by putting files on GitHub.

### Browser/cloud deployments

Streamable HTTP transport is implemented behind an **explicit safety gate** (`PHILOSOPHY_TRANSPORT=http` and `PHILOSOPHY_ALLOW_HTTP=I_HAVE_CONFIGURED_AUTH`), but the example has **no built-in user authentication** and uses the SDK's local defaults. Do not expose it on an open public URL or put it behind an unauthenticated reverse proxy. A real deployment needs configured TLS, OAuth/access controls, host/origin allowlists, budgets, timeouts and a secure deployment review. The container defaults to stdio.

## Worked example

A claim: “Anyone who values freedom must oppose every government intervention.”

1. Extract the exact words of the argument and ask for missing premises instead of filling them in invisibly.
2. Call `select_philosophical_methods(question=...)` and `conduct_socratic_examination(claim=...)`.
3. Build **explicit supplied** premises and a conclusion with `export_argument_map`.
4. Translate an agreed **propositional** skeleton to `test_propositional_validity`:

   `premises=["F >> O", "F"]`, `conclusion="O"` gives valid. Whether F and F >> O accurately represent the underlying natural-language argument requires separate review.
5. Map counterarguments with `evaluate_argument_attack_graph`. Record what is undecided.
6. Use `audit_philosophical_conclusion` and, for scholarship discovery, `search_philosophy_references`.

## Limitations and responsible analysis

- Method selection is transparent **keyword matching**, not a semantic expert model.
- Extraction works for **explicit markers only**, not implicit arguments or full transcripts. Human review is required.
- Formal validation accepts propositional syntax such as `P >> Q`, `P and Q`, `not P`, `P == Q`. It does not cover quantification, modal logic, probabilities or meaning.
- Abstract argument extension membership is **not the same** as factual truth or philosophical soundness.
- Bibliography hits may be unrelated. Crossref searches may encounter rate limits or outages.
- No automated source scraping, self-installing third-party code, model training or self-modification occurs.
- The program makes no assertions about people's concealed intentions or mental states.

## Roadmap, not implemented

1. Real Argdown parser/CLI adapter and image/graph export with syntax validation.
2. Native graph roundtrip and Carneades interoperability, with tests against official examples.
3. Carnap/Lean/Z3 adapters for more formal languages, using trusted grammars.
4. Multi-perspective Co-STORM-style investigator with user-approved network access, sources and budgets.
5. Eval suite with annotated arguments, adversarial counterexamples, cross-cultural method review and human grading.
6. Secured remote MCP endpoint compatible with the destination ChatGPT client.

## Attribution & licensing

Original code is MIT-licensed in the parent repository. Related upstream projects are **references**, not bundled dependencies. Read each upstream project's terms separately: Argdown (MIT), Carneades 4 (MPL-2.0), Logikon (AGPL), and others. Do not assume all projects can be merged into one distribution without licence review.