# Hygiene report - jailbreak-bench

Status check after polish + launch-repo passes. All items verified on 2026-04-17/18.

| Check | Status | Notes |
|---|---|---|
| README.md present + effective shape | pass | H1, tagline, badges, install, quickstart (with --demo), attack-category table, interpreting results, CLI reference, Limitations, Road to SaaS, License. 180 lines, no TOC needed. |
| llms.txt present | pass | 2.3K, repo-root, AEO-shaped. |
| CITATION.cff present | pass | cff 1.2.0. Authors: Rolando Bosch / Hermes Labs. |
| LICENSE present | pass | MIT, SPDX identifier in pyproject. |
| Badges on README | pass | PyPI, Python versions, License, CI (test.yml). Downloads + HN can be added after first publish / HN post. |
| gh repo metadata | queued | See `_launch/gh-metadata.sh` for exact command. |
| .github/ISSUE_TEMPLATE/ | pass | bug_report.md + feature_request.md. |
| Hero image | pass | `_launch/images/hero.jpg` (1024x1024). |
| Social preview | pass | `_launch/images/social-1200x630.jpg` + legacy `social-preview.png` at repo root. |
| Hermes Labs attribution | pass | README footer, pyproject maintainers, llms.txt owner line, AGENTS.md owner line, CITATION affiliation. |
| Canonical name preserved | pass | `jailbreak-bench` kept (hyphenated PyPI form, underscore import form). |
| pyproject.toml (build metadata) | pass | Hatchling backend, Python ≥3.10, CLI entry point `jailbreak-bench = "jailbreak_bench.cli:main"`, URLs set. |
| CI workflow | pass | `.github/workflows/test.yml` (test across Py 3.10-3.12 + lint + type-check + build). Currently green on origin/main. |
| Release workflow | pass | `.github/workflows/release.yml` on tag `v*` via PyPI trusted publishing. |
| AGENTS.md | pass | Machine-readable orientation at repo root. |
| CHANGELOG.md | pass | Keep a Changelog, v0.1.0 entry. |
| CONTRIBUTING.md | pass | Install + test + extend + PR conventions, 100 lines. |
| CODE_OF_CONDUCT.md | pass | Contributor Covenant 2.1 summary with link to canonical URL + contact. |
| Pre-commit config | skipped | Intentional. Ruff is wired into CI; a second layer (pre-commit-hooks) can land in v0.2 once the contributor base justifies it. |

## Items that still require Roli (after ship-time)
- Upload `_launch/images/social-1200x630.jpg` via GitHub repo Settings -> Social preview (web UI only, no API).
- Run the `gh-metadata.sh` command to set repo description + topics + homepage.
- Configure PyPI trusted publishing project-side before tagging v0.1.0, or the release workflow publish step will fail (builds still succeed).

## Notable fixes captured in polish + launch passes
- Modal-verb false-positive (not jailbreak-bench; rule-audit finding) - fixed upstream in sibling tool.
- cli.py: added `--demo` flag alias (dry-run + 3-category filter).
- cli.py: IsADirectoryError / PermissionError / OSError handlers on `--output` writes.
- README.md: added Limitations section (scorer false-negatives, known-patterns only, Anthropic SDK only, single-turn only, CI-action template pending).
