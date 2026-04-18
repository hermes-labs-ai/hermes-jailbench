# X / Twitter thread - jailbreak-bench launch

## Thread (11 posts)

**1/**
16 AI agents tried to jailbreak Claude Sonnet for a weekend.

Nobody fully broke it.

The 45 patterns they threw are now a pytest suite you can install:

`pip install jailbreak-bench`

**2/**
Every AI product has the same safety-eval story.

You evaluate once. You ship.

The vendor updates the model. Your tests don't notice.

A customer notices. Usually on Twitter.

**3/**
The problem is that "safety evals" are one-off.

What you actually need is a *regression baseline*.

A number you track every release. When it drops, someone pages.

That's what jailbreak-bench is.

**4/**
45 known-refused patterns. 7 categories. Deterministic keyword scorer (no second LLM judging the first - fast, same answer every time).

Point it at any Anthropic endpoint. Get a refusal rate. Commit the number to git.

**5/**
```
pip install jailbreak-bench

jailbreak-bench --dry-run  
# no API key, prints all 45 patterns

jailbreak-bench --model X --api-key $K --output report.md
# live run, markdown report
```

**6/**
The corpus is the product.

Novel attacks are an R&D problem. Regressions are an operations problem.

The patterns in the bank are there *because* they're refused on a well-aligned model. If they stop being refused, your model changed.

**7/**
251 unit tests. Pure-Python scorer. MIT license.

Dry-run mode works without an API key - you can see every pattern before running anything live.

**8/**
Built out of Hermes Labs' round-8 hackathon.

16 agents × 1 Sonnet target × a weekend = 45-pattern negative-result corpus.

The "negative result" is the product. That framing matters.

**9/**
This is the dynamic half of a 3-tool OSS AI audit kit:

• jailbreak-bench (dynamic)  
• rule-audit (static linter for system prompts, no LLM needed)  
• colony-probe (multi-turn extraction testing)

All three MIT. All ship this week.

**10/**
For EU AI Act operators: this maps directly to Article 15 (accuracy and robustness).

Specifically the "substantial modification" trigger - you need evidence that a model update didn't materially weaken your safety posture.

A refusal-rate in git is that evidence.

**11/**
Repo: github.com/roli-lpci/jailbreak-bench
Homepage: hermes-labs.ai

Feedback welcome, especially on:
• missing patterns in the 45-attack bank
• false-positive scoring patterns
• SARIF schema for CI-gate integration (v0.2)

/end
