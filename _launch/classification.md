# Classification — jailbreak-bench

## Prior-art signal
- `find_tool.py "jailbreak-bench"`: indexed in the Hermes Labs tool registry as a jailbreak / fuzzing / red-team / safety-testing tool (already registered post-hackathon).
- Memory grep hits:
  - `project_round8_21_products.md` — Round 8 model-break hackathon output, 251 tests, part of the AI Audit Toolkit core 3.
  - `project_modelbreak_hackathon.md` — 16-agent hackathon context; Sonnet held against all 45 patterns; negative-result corpus is the product.
  - `feedback_content_filter_launch.md` — subagent content-filter risk for marketing copy on security tools. Relevant: write marketing copy in main context, not subagents.
- Classification not contradicted by prior-art signal.

## Category
**cli-tool** (primary) + **library** (secondary).

Installable Python package `jailbreak-bench` on PyPI. Exposes a CLI entry point (`jailbreak-bench`) and a programmatic API (`run_bench`, `generate_report`). The package is small, pure-Python for the scorer, optional Anthropic SDK for live runs.

## Audience
AI platform operators, red-team consultancies, AI-governance teams, and LLM-product engineering leads who need a regression baseline against known refused patterns and want a commit-to-git refusal-rate number across model updates.

## Normalized repo root
`/Users/rbr_lpci/Documents/projects/hermes-labs-hackathon/round-8-modelbreak/agent-10/jailbreak-bench`

Remote: `https://github.com/roli-lpci/jailbreak-bench.git`

Last commit: `66a0035 Initial commit: jailbreak-bench v0.1.0` (pushed to origin/main, CI green on GitHub Actions).
