# Awesome-list PR drafts

## Target: awesome-llm-security

Repo: https://github.com/corca-ai/awesome-llm-security (or similar curated list — confirm latest)

**PR title**: Add jailbreak-bench (regression test suite for LLM safety baselines)

**Section**: Testing & Red-Teaming (or "Tools" if no subsection)

**Line to insert** (alphabetical within section):

```markdown
- [jailbreak-bench](https://github.com/hermes-labs-ai/jailbreak-bench) - Regression test suite for LLM safety. Runs a curated battery of 45 known-refused patterns across 7 categories against any Anthropic-compatible endpoint and reports refusal/partial/compliance rates. Pure-Python keyword scorer, 251 tests, MIT. Part of the Hermes Labs AI Audit Toolkit.
```

**PR body**:

Adding `jailbreak-bench`, a new open-source regression baseline tool shipped this week by Hermes Labs.

- 45 curated attack patterns across 7 categories (identity override, extraction, encoding, framing, social engineering, injection, meta-reasoning)
- Deterministic keyword scorer (no second LLM judging the first)
- 251 unit tests, pure Python, MIT license
- CLI + Python library, pip installable
- Integrates with CI as a regression alarm for model updates

Fills the gap between one-off "safety evals" and continuous operational measurement. Useful for anyone operating an LLM-backed product who needs a commit-to-git number for safety regressions.

Happy to revise the line or move sections if you prefer a different placement.

---

## Target: awesome-ai-safety

**PR title**: Add jailbreak-bench (CLI for safety-regression testing)

**Section**: Tools / Evaluation

**Line to insert**:

```markdown
- [jailbreak-bench](https://github.com/hermes-labs-ai/jailbreak-bench) — CLI and Python library for measuring LLM resistance to 45 known-refused patterns. Designed as a regression baseline, not a one-off evaluation. MIT, pure Python.
```

---

## Target: awesome-red-team (adversarial testing list)

**PR title**: Add jailbreak-bench (regression suite for LLM safety testing)

**Section**: AI / LLM

**Line to insert**:

```markdown
- [jailbreak-bench](https://github.com/hermes-labs-ai/jailbreak-bench) — Pytest-shaped regression baseline for LLM safety. Curated corpus of 45 known-refused patterns. Built from a weekend hackathon negative-result corpus. Part of the Hermes Labs AI Audit Toolkit.
```

---

## General PR discipline

For each list:
1. Check CONTRIBUTING.md on the target repo — some require specific formatting.
2. Check for pre-existing entries with similar scope — if there's something close, propose it as a sibling entry, not a replacement.
3. Tie the entry to an objective feature list, not a marketing pitch.
4. Keep the line under 200 characters including the link.
5. If a list has a PR review gate, be patient — maintainers are volunteers.

## Candidate additional targets

- awesome-llm-interpretability (if it has an adjacent "evaluation" section)
- awesome-claude (smaller, curated list of Claude-specific tooling)
- awesome-mlops (tools that integrate with CI for ML pipelines)
- awesome-python (very broad, but high-signal)

Save PR submission for after `jailbreak-bench v0.1.0` is published to PyPI — the pip-installable line in the description is material.
