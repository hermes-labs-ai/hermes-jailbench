# Owner: Hermes Labs - https://hermes-labs.ai

# AGENTS.md — jailbreak-bench

Guide for AI coding agents (Claude Code, Cursor, Aider, Copilot, etc.) working in this repo.

## Orientation

1. Read `CLAUDE.md` first. That is the canonical architecture + dev-workflow doc.
2. Read `SPEC.md` for data-model and public-function contracts. That is the source of truth — if code disagrees with SPEC, fix the code.
3. Read `ROADMAP.md` for versioning and scope. Do not invent features outside the roadmap without asking.

## Repo Entry Points

| Path | Purpose |
|------|---------|
| `jailbreak_bench/__init__.py` | Public API surface. If you export a new symbol, add it to `__all__`. |
| `jailbreak_bench/cli.py` | argparse CLI. User-facing `print()` is allowed here. |
| `jailbreak_bench/runner.py` | `run_bench()` — calls Anthropic SDK. |
| `jailbreak_bench/scorer.py` | `score_response()` — keyword heuristics only, no LLM. |
| `jailbreak_bench/attacks.py` | 45 attack dataclasses. New attacks go here. |
| `jailbreak_bench/prescan.py` | Regex-based prompt injection prescan. |
| `jailbreak_bench/conversation_integrity.py` | History-fabrication + gaslighting detector. |
| `jailbreak_bench/report.py` | Markdown + JSON report generators. |
| `tests/` | 251 tests. No API key required. |

## How to Extend

### Add an attack
1. Open `jailbreak_bench/attacks.py`.
2. Create an `Attack(...)` inside the matching category list (e.g. `FRAMING_BYPASS_ATTACKS`).
3. Use `{TARGET}` as the payload placeholder, or write a standalone prompt with no placeholder.
4. `ALL_ATTACKS` and `ATTACKS_BY_CATEGORY` auto-include it.
5. Add a structural check in `tests/test_attacks.py` if notable.

### Extend the scorer
1. Open `jailbreak_bench/scorer.py`.
2. Append phrases to `REFUSAL_PHRASES`, `COMPLIANCE_SIGNALS`, or `PARTIAL_PHRASES`. Lowercase, substring-match.
3. Add labeled response fixtures to `tests/test_scorer.py` with `assert score_response(text).verdict == ...`.
4. Do NOT add LLM calls to the scorer. The scorer is deterministic by design (see SPEC Section 6.1).

### Add an endpoint (OpenAI, Ollama, etc.)
1. Add a `--provider` CLI flag in `cli.py`.
2. Branch in `runner.py` on provider. Keep the `score_response()` call identical.
3. Add a dev-dep for the client; do NOT make it a hard install requirement.

## Tests are the contract

- `pytest` must stay green. 251 tests, all offline.
- If you change behavior, update tests first or at the same time.
- No network calls in tests. No API key in tests. No fixtures that hit real endpoints.

## Agent dos and don'ts

Do:
- Preserve the `{TARGET}` placeholder convention.
- Use stdlib `logging` for library-code diagnostics (`logger = logging.getLogger(__name__)`).
- Use full type annotations on public functions (`py.typed` is shipped).
- Keep the scorer deterministic.

Don't:
- Don't add `print()` inside `jailbreak_bench/` except `cli.py` user-facing output.
- Don't widen the dependency footprint without justification. `anthropic` is the only required dep.
- Don't call an LLM from inside the scorer. Ever.
- Don't commit real API keys, real harmful payloads, or unredacted attack responses.

## Sibling products

This repo is one of three in the Hermes Labs AI Audit Toolkit:
- `rule-audit` — static analyzer for system prompts
- `colony-probe` — multi-turn extraction / ant-colony attacks

If a change would fit better in one of those, say so instead of duplicating code here.
