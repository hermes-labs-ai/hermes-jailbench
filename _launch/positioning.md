# Positioning - jailbreak-bench

## Why now
Three forces converge in April 2026. First, model updates have become continuous - Anthropic, OpenAI, and Google ship new checkpoints every 4-8 weeks, each with documented behavioral differences. Second, the EU AI Act's Article 15 robustness-testing obligations kick in on 2026-08-02 for high-risk deployments, requiring documented evidence of continuous measurement. Third, the open-source AI-testing space has converged on one-shot evaluation (PromptFoo, Garak) and novel-attack generation (red-team research), but not on regression-baseline tooling for operational teams who need a commit-to-git refusal-rate number. `jailbreak-bench` is the narrow tool that fills that gap.

## ICP
A lead engineer on an AI-product safety or reliability team at a series-B-to-D company running an LLM-backed product. They already ran a safety evaluation at launch; it is stale; they have been asked by their board or their compliance counsel to produce evidence of continuous monitoring, and they do not yet have a one-command way to do it. Willingness-to-try is high because the tool is pip-installable and drops into an existing pytest-shaped CI with no new infrastructure.

## Competitor delta
- **Do nothing** (one-off evals at launch, nothing after). This is the current default. The cost is silent-decay: vendor updates weaken refusals without triggering any alarm. `jailbreak-bench` makes that decay visible as a git-diff.
- **PromptFoo / Giskard / Garak** (OSS LLM-test frameworks). Broader, more complex, more configuration. Our tool is narrower by design: one command, one corpus, one refusal-rate number. Pairs cleanly with the broader frameworks rather than competing with them.
- **Robust Intelligence / Protect AI / other commercial platforms**. Priced for enterprise, gated behind sales cycles. We are MIT, pip-installable, runnable in 30 seconds. Different wedge.

## Adjacent interests
- If you like `ruff` (fast, deterministic, single-purpose), you will like `jailbreak-bench` - same design philosophy applied to LLM safety regression.
- If you like `bandit` or `semgrep` for code-security static analysis, you will like `rule-audit` (sibling tool, static analyzer for system prompts).
- If you like the NIST AI RMF or ISO/IEC 42001 measurement framing, you will like the three-tool Hermes Labs AI Audit Toolkit: static (rule-audit) + dynamic (jailbreak-bench) + conversational (colony-probe).
