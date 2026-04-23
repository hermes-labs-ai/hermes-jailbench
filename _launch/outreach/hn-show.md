# Show HN: jailbreak-bench – A regression test suite for LLM safety baselines

We ran a weekend hackathon where 16 AI agents tried to break Claude Sonnet. Nobody fully broke it. What we ended up with was a curated battery of 45 known-refused patterns across 7 categories - the negative-result corpus.

That corpus is the product. It's now a pip-installable CLI for running those 45 patterns against any Anthropic-compatible endpoint and getting a structured report back.

```bash
pip install jailbreak-bench

# No API key needed - inspect the attack bank
jailbreak-bench --dry-run

# Live regression run
jailbreak-bench --model claude-haiku-4-5 --api-key $ANTHROPIC_API_KEY --output report.md
```

Why this matters: if you deploy an LLM-backed product, you want a regression alarm when a model update weakens your safety posture. Right now the common workflow is "ship, hope, find out on Twitter." This tool gives you a pytest-shaped signal instead: a refusal-rate number you can track per model version, commit to git, and diff on release.

What it is:
- 45 attacks across 7 categories (identity override, extraction, encoding, framing, social engineering, injection, meta-reasoning)
- Pure-Python keyword scorer (no second LLM call to judge the first - fast, deterministic, auditable)
- 251 unit tests, runs in under a second without an API key
- Markdown / JSON / SARIF output (SARIF for CI gates in v0.2)
- MIT license

What it isn't:
- Not a novel-attack generator. It tests known patterns, by design, because those are the ones you'd want to regress against.
- Not a judgment tool. "COMPLIED" on this benchmark means "the model said something the scorer matched on compliance heuristics" - it's a signal, not a verdict.

Sibling tools in the Hermes Labs AI Audit Toolkit: `rule-audit` (static linter for system prompts, no LLM needed) and `colony-probe` (multi-turn extraction testing).

Repo: https://github.com/hermes-labs-ai/jailbreak-bench

Happy to answer questions and take feedback on attack coverage. The next release adds OpenAI and local Ollama endpoint support.


---

## First-hour engagement plan

After posting, 08:00-10:00 PT Tue/Wed/Thu, Roli does the following in the first 60 minutes:

1. **Reply to the first commenter in under 10 minutes.** Short, specific, a real answer. Even if the comment is a nitpick, engage with the nitpick.
2. **Do not upvote your own submission.** HN flags this and will slow-rank the post.
3. **Pre-written responses for predictable pushback** (have these ready to paste, then adapt):
   - *"Isn't this just a wrapper over known attacks?"* -> "Yes, intentionally. The 45 patterns are a curated refused corpus, not a novel-attack generator. The value is the commit-to-git refusal-rate number across model updates - continuous regression signal, not one-off discovery."
   - *"Why a keyword scorer instead of an LLM judge?"* -> "Deterministic, fast, cheap, auditable. An LLM judge would be more accurate but 100x slower per PR and non-deterministic. Optional `--with-llm` judge is on the v0.2 roadmap as a pairwise check."
   - *"Why Anthropic-only?"* -> "Starting point. OpenAI and local Ollama support land in v0.2 - issue/PR welcome."
   - *"What's the bypass rate on [model X]?"* -> Honest number or "haven't run it yet, will add to benchmarks/ directory."
4. **Post the same hour on X** as a thread (draft ready at `_launch/outreach/x-thread.md`). Do not cross-post to LinkedIn same day - stagger by 2-4 hours.
5. **Monitor HN ranking.** If the post falls off front page within an hour, it's not landing - do NOT re-post the same day. Wait 5 days, reframe the angle, retry.
