# jailbreak-bench — LAUNCH-READY

**Date**: 2026-04-17
**Version**: 0.1.0
**Test status**: 251 passed

## Distribution infrastructure

- `pyproject.toml` ✓ (pre-existing, PyPI-ready)
- `LICENSE` ✓ (MIT)
- `.github/workflows/ci.yml` ✓
- `.github/workflows/release.yml` ✓ (new; PyPI trusted publishing)
- `.github/ISSUE_TEMPLATE/bug_report.md` ✓
- `.github/ISSUE_TEMPLATE/feature_request.md` ✓

## Repo docs

- `README.md` ✓
- `SPEC.md` ✓
- `ROADMAP.md` ✓
- `CLAUDE.md` ✓
- `AGENTS.md` ✓ (new)
- `llms.txt` ✓ (new)
- `CHANGELOG.md` ✓ (new, v0.1.0 entry)
- `CONTRIBUTING.md` ✓ (new)
- `CODE_OF_CONDUCT.md` ✓ (new)
- `SECURITY.md` ✓ (new)
- `CITATION.cff` ✓ (new)
- `benchmarks/README.md` ✓ (new, smoke-test + baseline-regression workflow)

## Launch drafts (in launch/)

- `launch/show-hn.md` ✓
- `launch/dev-to.md` ✓
- `launch/reddit-r-localllama.md` ✓
- `launch/linkedin.md` ✓ (3 variants: 100/250/500 words)
- `launch/x-twitter.md` ✓ (11-post thread)
- `launch/awesome-list-pr.md` ✓ (awesome-llm-security, awesome-ai-safety, awesome-red-team)
- `launch/demo-gif-shotlist.md` ✓ (5-shot sequence)
- `launch/social-preview.md` ✓ (Pollinations.ai prompt + SVG fallback notes)
- `launch/cold-email-targets.md` ✓ (10 archetypes)
- `launch/paper-abstract.md` ✓ ("The Negative-Result Corpus" — medium-priority paper)

## What's intentionally NOT done (Roli decides)

- No git commits, no tags, no push
- No PyPI publish (set up trusted publisher in PyPI project settings first, then tag v0.1.0)
- No GitHub release
- No actual social-preview PNG (prompt is ready; run Pollinations or hand-SVG)
- No submitted awesome-list PRs (drafts only)
- No sent cold emails (target list only; feeds Bravo's draft_batch pipeline)

## Go / No-go checklist before pushing public

- [ ] Review all launch/* drafts for voice (Roli should read and redline)
- [ ] Confirm `hermes-labs.ai` contact emails are routable: `conduct@`, `security@`
- [ ] Verify PyPI project name `jailbreak-bench` is available (or reserve it)
- [ ] Decide PyPI trusted publisher setup vs. token-based
- [ ] Generate social-preview.png (Pollinations or hand-SVG)
- [ ] Create GitHub repo `roli-lpci/jailbreak-bench` (private until ready)
- [ ] Push code, verify CI runs green
- [ ] Tag v0.1.0, verify release workflow publishes to PyPI
- [ ] Move repo to public
- [ ] Post Show HN (Monday morning US, best timing)
- [ ] Crosspost to DEV.to the same day
- [ ] Submit awesome-list PRs the same day
- [ ] LinkedIn + X posts immediately after Show HN lands on front page

## Polish notes from this pass

- No library-code `print()` calls needed converting to `logging` (only `cli.py` prints, which are user-facing; `conversation_integrity.py` has a `print` inside a docstring example — not a real call)
- All public functions already had type hints
- `pip install -e .` works cleanly
- Benchmarks directory created with smoke-test + baseline documentation

## Known concerns

- None blocking. Positioning is consistent across all launch drafts: this is a **regression baseline**, not a research jailbreak framework. That framing avoids the competitive-attack-tool perception that would hurt adoption.
