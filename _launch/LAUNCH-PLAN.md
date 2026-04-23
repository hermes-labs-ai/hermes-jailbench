# Launch plan - jailbreak-bench

T-0 is the day the repo flips public and the Show HN goes up.

## T-3 days
- **Gate**: hygiene pass, images ready, `_launch/gh-metadata.sh` inspected but not yet executed, voice-lint clean across `_launch/outreach/`.
- **Actions**: final tests green (`pytest -q`, `ruff check`, `mypy`); confirm `pip install -e ".[dev]"` works in a fresh venv; Roli reads every `_launch/outreach/*.md` once for voice.
- **Fallback if gate fails**: fix and re-run. Do not advance timeline.

## T-2 days
- **Gate**: Show HN + DEV.to + LinkedIn drafts reviewed and redlined by Roli. HN karma check - if brand-new account, submit a few good comments elsewhere first to clear the 50-karma threshold.
- **Actions**: finalize headline and subtitle for Show HN. Decide whether to include the `--demo` GIF inline on launch (yes if one can be recorded in a single take; no if not - ship without rather than ship bad).

## T-1 day
- **Gate**: PyPI project name reserved (even if Trusted Publishing config is still pending); GitHub repo private-ready-to-flip; `gh-metadata.sh` armed.
- **Actions**: draft the first-hour HN replies (`_launch/outreach/hn-show.md` has the starters). Stage cold-email targets for the draft_batch pipeline but do NOT queue the send.

## T+0 (launch day)
- **Gate**: Tuesday, Wednesday, or Thursday. 08:00-10:00 PT window. Roli at a keyboard for the next 2 hours.
- **Actions** in order:
  1. Flip repo public: `gh repo edit hermes-labs-ai/jailbreak-bench --visibility public --accept-visibility-change-consequences`.
  2. Upload `_launch/images/social-1200x630.jpg` via GitHub Settings -> Social preview (web UI only).
  3. Run `_launch/gh-metadata.sh`.
  4. Tag v0.1.0 and push, watch the release workflow land the wheel on PyPI.
  5. Submit Show HN with the `_launch/outreach/hn-show.md` draft.
  6. First-hour engagement plan from `hn-show.md` goes live.
- **Fallback if PyPI publish fails but build succeeds**: wheel lands as a GitHub Actions artifact; fix Trusted Publishing config; re-run via `gh workflow run release.yml` on the tag.

## T+1 hour
- X thread goes live using `_launch/outreach/x-thread.md`.
- Keep monitoring HN for comments - keep replies specific and short.

## T+1 day
- Publish DEV.to (`_launch/outreach/blog-post.devto.md` with `published: true`).
- Publish Medium mirror (`_launch/outreach/blog-post.md`).
- Post LinkedIn (250-word variant from `_launch/outreach/linkedin.md`).

## T+3 days
- Reddit posts, staggered one-per-day across r/LocalLLaMA and r/MachineLearning. Use per-sub drafts in `_launch/outreach/reddit/`.

## T+7 days
- Cold-email batch wave 1 of 25. Feed `_launch/outreach/email-targets.csv` (once populated via Echo enrichment) into `python3 ~/ai-infra/pipeline/draft_batch.py --dry-run` first, review drafts, then send.

## T+14 days
- Submit awesome-list PRs from `_launch/outreach/awesome-prs/README.md` (awesome-llm-security, awesome-ai-safety, awesome-red-team).
- Post a "first two weeks" reflection on LinkedIn + blog if adoption is tracking.

## Rollback notes
- If the launch flops (no HN traction, no PyPI downloads), wait 5 days, reframe the angle around a specific vendor regression you discovered, retry.
- If the tool triggers an unexpected public-relations concern (vendor reaches out), pause further amplification, respond via security@hermes-labs.ai, revisit scope statement.
