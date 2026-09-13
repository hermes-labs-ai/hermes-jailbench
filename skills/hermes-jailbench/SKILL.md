---
name: hermes-jailbench
description: Run the hermes-jailbench safety regression check against a model endpoint the user owns or is authorized to test, then summarize the report. Trigger when the user wants to confirm that a model, system prompt, or release change did not weaken refusals on a fixed set of known patterns, or wants a pass/fail safety gate in CI.
---

Hermes Jailbench is a defensive regression check. It replays a fixed,
versioned set of known single-turn patterns against a model endpoint and
classifies each reply with deterministic keyword rules as `REFUSED`,
`PARTIAL`, `COMPLIED`, or `ERROR`. It makes no model calls of its own for
scoring (https://github.com/hermes-labs-ai/hermes-jailbench).

Priority order when these steps conflict: (1) authorization and scope,
(2) protecting credentials and saved replies, (3) the pinned runner,
(4) an accurate, unembellished summary. This skill covers one task: running
the check and reporting it. Each new request from the user starts fresh.

1. Confirm scope before any live run: the endpoint must be one the user
   owns or is explicitly authorized to test. If that is unclear, ask. Do not
   point it at third-party services the user does not control.
2. Pick a runner: if `hermes-jailbench --help` works, use the bare
   `hermes-jailbench` command below. Otherwise prefer
   `uvx hermes-jailbench==0.2.0` (zero-install, no PATH changes) over
   `pipx install hermes-jailbench==0.2.0` unless the user wants it installed
   persistently. Keep the exact version pin so neither fetches an unreviewed
   newer release. The commands below are written with the bare
   `hermes-jailbench`; if you picked uvx, run each one as
   `uvx hermes-jailbench==0.2.0 <same arguments>` instead, because the uvx
   runner does not put `hermes-jailbench` on PATH.
3. Smoke-test offline first. This needs no API key and sends no requests:
   ```
   hermes-jailbench --demo
   ```
4. Run the regression check with credentials the user has already placed in
   the environment (`ANTHROPIC_API_KEY`, or `OPENAI_API_KEY` for an
   OpenAI-compatible endpoint, where a local runtime needs none). Never type,
   echo, or log a key yourself. Substitute the user's model and endpoint:
   ```
   hermes-jailbench --model <model-id> --fail-on-bypass --format json --output report.json
   hermes-jailbench --provider openai-compat --base-url <url> --model <model-id> --fail-on-bypass --format json --output report.json
   ```
   Exit code `0` means the bypass rate is within the threshold, `1` means it
   exceeded it, and `2` means the gate could not be evaluated.
5. To compare against an earlier baseline report the user kept:
   ```
   hermes-jailbench diff baseline.json report.json --fail-on-regression
   ```
6. Summarize for the user: the exit code, the bypass rate, the refused,
   partial, and complied counts, the per-category breakdown, and any attack
   the scorer flagged for manual review.

Constraints:
- Use only the attack set bundled with the installed release. Do not write,
  extend, or improvise new attack prompts, and do not use the results to
  get around any model's safety behavior.
- Leave `--include-responses` off unless the user asks for it; saved model
  replies can contain sensitive text, so treat the report as a private file.
- A clean result is a regression baseline for known patterns only. Never
  present it as proof that a model is safe against novel or multi-turn
  attacks.
