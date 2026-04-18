# LinkedIn drafts - Roli Bosch

## Variant A - 100 words

Shipped an open-source tool today: `jailbreak-bench`.

If you operate an LLM product, you know the problem: the safety eval you ran at launch is not the safety eval you're running on every vendor model update. This is a pytest-shaped regression baseline - 45 known-refused patterns, one command, structured report.

Built during a weekend hackathon where 16 agents tried to break Claude Sonnet. Nobody fully broke it. The 45 patterns they threw are now the baseline.

MIT licensed. `pip install jailbreak-bench`.

Next week: EU AI Act Article 15 mapping doc.

Hermes Labs → hermes-labs.ai

---

## Variant B - 250 words

Every AI team I've talked to has the same safety-eval story. You do a careful evaluation when you pick a model. You ship. Six weeks later the provider updates the model. Nothing in your CI notices. Something breaks in production. You find out from a customer or a tweet.

Static safety evals age fast because nobody runs them on every release.

Today I'm open-sourcing `jailbreak-bench` - a regression baseline, not an evaluation. The difference matters:

- **Evaluation** = "is this model safe?" (answered once, subjective, heavy)
- **Regression baseline** = "is this model *less* safe than it was?" (answered per release, objective, cheap)

The tool runs 45 known-refused patterns against any Anthropic-compatible endpoint and reports a refusal rate. You commit the number to git. When it drops, something paged.

```
pip install jailbreak-bench
jailbreak-bench --model claude-haiku-4-5 --output report.md
```

Built out of a Hermes Labs hackathon corpus. 251 tests. Pure-Python scorer (no second LLM to judge the first). MIT license.

For EU AI Act operators: this is Article 15 (accuracy and robustness testing) tooling - specifically the "substantial modification" trigger that flags when a model update materially changes behavior. We're publishing an Article 15 mapping doc next week.

Part of the Hermes Labs AI Audit Toolkit: `rule-audit` (static prompt linting) and `colony-probe` (extraction testing) ship alongside.

github.com/roli-lpci/jailbreak-bench
hermes-labs.ai

---

## Variant C - 500 words

The dirty secret of AI product safety is that most "safety evals" are one-off artifacts. You run them the day you launch. You do not run them on every deploy. You definitely do not run them when the vendor deploys. Six weeks later, a silent model update softens a refusal pattern you depended on, and you find out when a customer sees something they shouldn't.

The gap between "we evaluated this model" and "we continuously measure this model" is huge. Today I'm open-sourcing one piece of the continuous side.

`jailbreak-bench` is a regression baseline for LLM safety. Here's what that means in practice:

1. We ran a weekend hackathon where 16 AI agents threw every prompt-extraction and safety-bypass technique we could think of at Claude Sonnet.
2. Nobody fully broke it. The 45 patterns they tried all got refused.
3. That corpus - 45 known-refused patterns across 7 categories - became the benchmark.
4. You install the CLI, point it at your model endpoint, and get a refusal rate back.
5. You commit the number to git. When it drops, you know something changed.

```
pip install jailbreak-bench
jailbreak-bench --model your-model --api-key $KEY --output baseline.md
```

Why this is the shape of the tool, not a "safety eval":

- **Deterministic scoring.** Pure-Python keyword heuristics, not a second LLM. Same response always gets the same score. Fast enough to run on every commit.
- **Category-level reporting.** If your refusal rate drops on "framing_bypass" but holds on everything else, you know where to look. That's an operations signal, not a research finding.
- **SARIF output coming.** Integrates with GitHub code scanning in v0.2. Your model-safety regressions show up in the same PR view as your code-security regressions.

This is the dynamic half of an OSS AI audit toolkit Hermes Labs is shipping this week. The other halves:

- `rule-audit` - static linter for system prompts. Finds contradictions, coverage gaps, priority ambiguities. No LLM calls, runs in milliseconds. Complements `jailbreak-bench` - `rule-audit` predicts where attacks will succeed; `jailbreak-bench` measures whether they still do.
- `colony-probe` - multi-turn probing tool that tests whether your system prompt structure leaks through innocent conversational questions. The "ant colony" attack from the same hackathon.

For teams preparing for EU AI Act Article 15 (accuracy and robustness), these three tools give you the artifact trail a notified body will ask for: evidence that you continuously measure your system's resistance, across both static (prompt) and dynamic (runtime) surfaces.

All three are MIT. All three are pytest-tested. All three install with `pip`.

What I want feedback on:
- Attack coverage (what known patterns are missing from the 45?)
- Scoring heuristics (what false positive / false negative patterns do you see?)
- SARIF schema for the CI-gate use case

Repo: github.com/roli-lpci/jailbreak-bench
Homepage: hermes-labs.ai
Reach out: rbosch@hermes-labs.ai
