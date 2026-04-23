# SHIP-REPORT - jailbreak-bench

Pre-ship gate: **10/10 PASS**. No waivers.

## What landed in this repo
- Code + tests: 251 passing, ruff clean, mypy clean.
- CLI: `jailbreak-bench --help` / `--dry-run` / `--demo` / `--list-attacks` / `--list-categories` all working.
- Repo hygiene: README (with Limitations), SPEC, ROADMAP, CLAUDE.md, AGENTS.md, llms.txt, CHANGELOG, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY.md, CITATION.cff, LICENSE (MIT).
- CI + release: `.github/workflows/{ci.yml,release.yml}` (Py 3.10-3.12 matrix, PyPI Trusted Publishing on tag push).
- Launch bundle: `_launch/` (classification, claim, hygiene-report, positioning, gh-metadata.sh, release.sh, images/hero.jpg + social-1200x630.jpg, outreach/* with First-hour plan, paper/DECISION.md + abstract.md, LAUNCH-PLAN.md, preship-gate.md).
- Manifest registered at `~/ai-infra/manifests/jailbreak-bench.yaml`; `find_tool.py "jailbreak"` returns this tool at rank 1.

## Roli's remaining steps (ordered)
1. Read `_launch/outreach/hn-show.md`, `_launch/outreach/linkedin.md` (250-word variant), `_launch/outreach/blog-post.md` once for voice.
2. `cd` into the repo and run `bash _launch/gh-metadata.sh` AFTER public-flip (not before - description and topics get indexed immediately).
3. PyPI Trusted Publishing: log in to pypi.org, reserve project `jailbreak-bench`, add trusted publisher (repo `hermes-labs-ai/jailbreak-bench`, workflow `release.yml`, environment `pypi`). In GitHub: Settings -> Environments -> add `pypi`.
4. Flip repo public: `gh repo edit hermes-labs-ai/jailbreak-bench --visibility public --accept-visibility-change-consequences`.
5. Upload `_launch/images/social-1200x630.jpg` via GitHub Settings -> Social preview (web UI only).
6. Run `bash _launch/release.sh` on launch day to tag v0.1.0 and trigger PyPI publish.
7. Submit Show HN 08:00-10:00 PT Tue/Wed/Thu using `_launch/outreach/hn-show.md`. First-hour plan is inside the file.
8. 1 hour later: X thread from `_launch/outreach/x-thread.md`. Next day: DEV.to + Medium + LinkedIn.

## Paper decision
`blog-only` now, `publish-workshop` option reopened Q4 2026 after 3 months of multi-vendor refusal-rate data. Confidence 0.7. See `_launch/paper/DECISION.md`.

## Gates Roli should reconsider (none waived, listed anyway)
- `pre-commit` config skipped. Ruff is in CI already; a pre-commit layer can ride in as v0.2.
- Cold-email `email-targets.csv` not populated (enrichment pending). Launch-plan queues this for T+7.
