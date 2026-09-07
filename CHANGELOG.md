# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `python -m hermes_jailbench.mock_target`: a loopback-only, credential-free Messages-API stand-in with behaviour chosen by model name (refuses / complies / hedges / malformed / server-error / bad-request), so the real client, retry classification, and scorer can be exercised end to end offline.
- `python -m hermes_jailbench.evidence`: emit a mock or dry run as a Hermes Reliability Lab result envelope with the JSON report embedded verbatim. No live mode; never reads `ANTHROPIC_API_KEY`.

### Fixed
- A provider reply that is well-formed JSON but carries no content blocks (or whose first block has no text) now reports `malformed response: ...` instead of the bare Python `list index out of range`. It is still an `ERROR`, still not retried.

## [Unreleased]

## [0.1.2] - 2026-09-05

### Added
- `--fail-on-bypass [PERCENT]` CLI flag: exits 1 when the bypass rate exceeds
  the threshold (0% when no value is given), 2 when any attack errored, no
  attack ran, or the flag is combined with `--dry-run`, so a partially failed
  run (network, rate limit) never passes green. The report is written before
  the exit code is set. Turns the benchmark into a CI regression gate.

## [0.1.1] - 2026-08-04

### Changed
- Align the repository, Python package, and CLI under the `hermes-jailbench`
  identity.
- Clarify that the benchmark replays known single-turn patterns and that its
  deterministic scorer does not establish safety against novel attacks.
- Refresh the public README, package links, citation metadata, and preview.
- Harden the tag-triggered PyPI workflow with immutable action pins and a
  tag-to-package-version check.

No attack catalog, scoring rule, or benchmark behavior changed.

## [0.1.0] - 2026-04-17

### Added
- Initial public release.
- 45 single-turn jailbreak attacks across 8 categories: `identity_override`, `prompt_extraction`, `encoding_bypass`, `framing_bypass`, `social_engineering`, `injection`, `meta_reasoning`, `multilingual`.
- Deterministic keyword-based scorer (`score_response`) classifying responses as `REFUSED`, `PARTIAL`, or `COMPLIED` with confidence. No LLM calls on the scoring path.
- `run_bench()` entry point with per-attack retry, exponential backoff, and `on_result` streaming callback.
- `generate_report()` and `save_report()` with markdown and JSON output formats.
- `prescan` module: regex-based prompt-injection prescan for input hardening.
- `conversation_integrity` module: history-fabrication and gaslighting detector with suggested-response generation.
- Argparse CLI (`hermes-jailbench`) with `--dry-run`, category and attack-name filtering, `--list-attacks`, `--list-categories`, `--include-responses`, configurable delay and max-tokens.
- PEP 561 `py.typed` marker; full type annotations on the public API.
- 251 offline tests (no API key required).
- GitHub Actions CI across Python 3.10, 3.11, 3.12: pytest, coverage, ruff, mypy, build check.
- MIT license. Packaged with hatchling, published to PyPI as `hermes-jailbench`.

### Notes
- First shipped artifact in the Hermes Labs AI Audit Toolkit; siblings `rule-audit` and `colony-probe` follow.
- Scorer is intentionally conservative. See `SPEC.md` Section 6.3 for known limitations.

[Unreleased]: https://github.com/hermes-labs-ai/hermes-jailbench/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/hermes-labs-ai/hermes-jailbench/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/hermes-labs-ai/hermes-jailbench/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/hermes-labs-ai/hermes-jailbench/releases/tag/v0.1.0
