# r/LocalLLaMA post draft

**Title**: [Tool] jailbreak-bench - regression test suite for LLM safety (45 patterns, works on any Anthropic endpoint today, Ollama support next)

**Body**:

Built this as the output of a weekend model-break hackathon. 16 agents threw every known prompt-extraction / bypass pattern we could think of at Claude Sonnet. Nobody fully broke it. The 45 patterns that all got refused became the negative-result corpus.

Now it's a pip-installable CLI:

```bash
pip install jailbreak-bench

# Print all 45 attacks without calling any API
jailbreak-bench --dry-run

# List categories
jailbreak-bench --list-categories

# Live run (needs an API key)
jailbreak-bench --model claude-haiku-4-5 --api-key $KEY --output report.md
```

Point is: if you're running a model locally and want a regression signal on safety, this gives you a deterministic number you can re-check on every model update. Same patterns, same scoring heuristics, same format.

Scoring is keyword-based (no second LLM call to judge). Fast, deterministic, auditable. Trade-off is false negatives on elaborate compliance - fine for a regression alarm, less fine as a verdict tool.

**Ollama / local model support**: currently Anthropic SDK only. v0.2 adds OpenAI and local endpoint support. If anyone wants to help land the Ollama integration, it's a 50-line patch in `runner.py` - PR welcome.

**Positioning**: this is the dynamic half of an OSS AI audit toolkit. The other pieces:
- `rule-audit` - static linter for system prompts, no LLM needed
- `colony-probe` - multi-turn extraction testing (the "ant colony" attack - 20 innocent questions reconstruct a system prompt)

Repo: https://github.com/roli-lpci/jailbreak-bench (MIT)

Happy to answer questions about the attack bank design, scoring decisions, or the hackathon methodology behind the corpus.
