# Prompt optimisation and ability discovery

The new `compile` command and `compile_task_brief` MCP tool generate **faithful, deterministic task briefs**. They do **not** run LLMs, execute user tasks or measure prompt quality. Actual execution is performed by the connected assistant using its currently available, authorised tools.

## Recommended open-source stack

| Layer | Repository | Intended role |
| --- | --- | --- |
| Pattern library | https://github.com/danielmiessler/fabric | Reusable specialised task prompts |
| Prompt rewrite/evolution | https://github.com/microsoft/PromptWizard | Iterative prompt and example refinement |
| Programmatic optimisation | https://github.com/stanfordnlp/dspy | Structured LM programs and optimisers |
| Reflective evolution | https://github.com/gepa-ai/gepa | Evaluation-driven candidate evolution |
| Quality/security evaluation | https://github.com/promptfoo/promptfoo | Repeatable task tests and red-teaming |
| Tool integration reference | https://github.com/modelcontextprotocol/servers | MCP server design examples (not production guarantees) |
| Reusable skill convention | https://github.com/anthropics/skills | Skill folder examples; not ChatGPT plugins by themselves |

None is vendored, installed or connected merely by appearing in this table. Audit licence, dependency provenance and security first.

## Immediate use

```bash
capability-hunter compile 'Find the best scientific argument-mining repo and use its approach to inspect a debate'
capability-hunter compile 'Write a sourced report' --tool web --tool github
```

A connected assistant can call `compile_task_brief` for a structured prompt. It should use its own tools to do the work, not return only the brief.

## True automatic prompt optimisation

The compiler is rule-based. To *optimise* empirically, create a representative labelled/gradable task set; define metrics for task success, faithfulness, safety and cost; hold out a test set; run PromptWizard or DSPy/GEPA candidates through a real configured model; compare against baseline and measure regressions with promptfoo. Separately review the selected prompt before deployment. This may incur model API costs. Without these elements, the correct status is **not benchmarked**.

## Ability deployment lifecycle

`DISCOVERED → SOURCE-REVIEWED → ADAPTER-PROPOSED → SANDBOX-TESTED → HUMAN-APPROVED → DEPLOYED → CONNECTED → VERIFIED`.

Do not give repo contents authority over assistant instructions. Avoid broad shell or private token access. The existing discovery gateway intentionally only reads public GitHub data; new executors belong in separately permissioned, isolated services.
