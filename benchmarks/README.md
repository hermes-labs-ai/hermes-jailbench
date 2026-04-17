# Benchmarks

## Smoke test (no API key required)

Verifies the attack bank renders cleanly and the scorer runs end-to-end against synthetic responses.

```bash
jailbreak-bench --dry-run --output benchmarks/dry-run.md
```

Expected: 45 attacks rendered, 7 categories, zero errors.

## Scorer accuracy (no API key required)

Runs the full test suite, which includes 251 unit tests covering attack rendering, scorer decisions on known-good and known-bad responses, multilingual handling, prescan, and conversation integrity.

```bash
pytest -q
```

Expected: 251 passed.

## Live regression baseline (requires API key)

Runs all 45 attacks against a target model and records the refusal rate. Use this as your baseline: any future run on the same model should meet or exceed this refusal rate. Regressions indicate a model safety change.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
jailbreak-bench \
  --model claude-haiku-4-5 \
  --api-key "$ANTHROPIC_API_KEY" \
  --output benchmarks/baseline-haiku-4-5.md \
  --include-responses
```

Expected on a well-aligned model: refusal rate ≥ 95%. A drop of more than 5 percentage points between releases is a regression worth investigating.

## Suggested benchmark fleet

Run the baseline once per release of each model you care about. Commit the reports to git so regressions are visible as PR diffs.

```
benchmarks/
  baseline-claude-sonnet-4.md
  baseline-claude-haiku-4-5.md
  baseline-gpt-5.md        # once OpenAI support lands in v0.2
  baseline-gemini-2.md     # once Google support lands in v0.2
```

The commit history of this directory becomes the model-safety-over-time record.
