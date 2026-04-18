Every AI product I've shipped has had the same story:

1. Pick a model.
2. Do some safety evals.
3. Ship.
4. Provider updates the model six weeks later.
5. Nothing breaks in your tests. One thing breaks in production. You find out from a customer.

Step 5 is the interesting one. The reason it happens is that most "AI safety evals" are one-off artifacts. You ran them the day you launched. You do not run them on every deploy. You definitely do not run them when the *vendor* deploys.

What I wanted was a regression baseline. A pytest-shaped number I could track over time - "refusal rate on the 45 known patterns, for this model, on this date." If the number drops, someone paged.

This is `jailbreak-bench`.

## The negative-result corpus

I ran a weekend hackathon where 16 AI agents tried every known prompt-extraction and safety-bypass technique on Claude Sonnet. Nobody fully broke it. The output was a curated set of 45 patterns across 7 categories, each with an expected outcome of REFUSED.

That's a corpus. Every pattern is a known-refused on a well-aligned model. You point the tool at your endpoint and you get a refusal rate. That number is your baseline.

## How it works

```bash
pip install jailbreak-bench

# Inspect the bank without calling any API
jailbreak-bench --dry-run

# Run against a model
jailbreak-bench --model claude-haiku-4-5 --api-key $KEY --output report.md
```

The scorer is pure-Python keyword heuristics - no second LLM call to judge the first one. That matters because:

- It's deterministic. The same response always gets the same score.
- It's fast. 45 attacks + scoring runs in seconds once API latency is out.
- It's auditable. You can read exactly what it's matching on.

The trade-off: it has a false-negative rate on elaborate indirect compliance. That's OK - the tool is a regression alarm, not a verdict. If you see a number move, you read the responses and decide.

## What I learned

- **Safety evals decay silently.** A benchmark you ran once is a benchmark you no longer run.
- **Regression > novelty.** The attacks I care about for production are the ones that used to be refused and aren't anymore. Novel attacks are an R&D problem; regressions are an operations problem.
- **Keyword scoring is good enough for alarms.** An LLM judge would be more accurate. It would also be 100x slower, 100x more expensive, and non-deterministic. Alarms should be cheap.

## The rest of the toolkit

`jailbreak-bench` is one of three OSS tools Hermes Labs is shipping this week:

- **rule-audit** - static linter for system prompts. Finds contradictions, coverage gaps, priority ambiguities. No LLM calls.
- **colony-probe** - multi-turn probing tool that tests whether your system prompt structure leaks through innocuous conversational questions.

Together they're the dynamic and static halves of LLM safety testing.

Repo: https://github.com/roli-lpci/jailbreak-bench
License: MIT
Homepage: https://hermes-labs.ai

Feedback on attack coverage welcome. The v0.2 roadmap adds OpenAI and Ollama endpoint support, SARIF output for CI gates, and a nightly-run GitHub Action template.
