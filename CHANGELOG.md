# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-17

### Added
- Initial public release.
- 45 single-turn jailbreak attacks across 8 categories: `identity_override`, `prompt_extraction`, `encoding_bypass`, `framing_bypass`, `social_engineering`, `injection`, `meta_reasoning`, `multilingual`.
- Deterministic keyword-based scorer (`score_response`) classifying responses as `REFUSED`, `PARTIAL`, or `COMPLIED` with confidence. No LLM calls on the scoring path.
- `run_bench()` entry point with per-attack retry, exponential backoff, and `on_result` streaming callback.
- `generate_report()` and `save_report()` with markdown and JSON output formats.
- `prescan` module: regex-based prompt-injection prescan for input hardening.
- `conversation_integrity` module: history-fabrication and gaslighting detector with suggested-response generation.
- Argparse CLI (`jailbreak-bench`) with `--dry-run`, category and attack-name filtering, `--list-attacks`, `--list-categories`, `--include-responses`, configurable delay and max-tokens.
- PEP 561 `py.typed` marker; full type annotations on the public API.
- 251 offline tests (no API key required).
- GitHub Actions CI across Python 3.10, 3.11, 3.12: pytest, coverage, ruff, mypy, build check.
- MIT license. Packaged with hatchling, published to PyPI as `jailbreak-bench`.

### Notes
- First shipped artifact in the Hermes Labs AI Audit Toolkit; siblings `rule-audit` and `colony-probe` follow.
- Scorer is intentionally conservative. See `SPEC.md` Section 6.3 for known limitations.

[Unreleased]: https://github.com/roli-lpci/jailbreak-bench/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/roli-lpci/jailbreak-bench/releases/tag/v0.1.0
