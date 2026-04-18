# Paper decision - jailbreak-bench

## Recommendation
**blog-only** now, with an option to upgrade to **publish-workshop** after three months of multi-vendor baseline data are collected.

## Confidence
0.7 that the blog-only call is right for the 2026-Q2 window.

What would raise confidence to 0.9 for publish-workshop: a dataset of refusal rates on three or more models across two or more releases each, showing a measurable regression we caught ahead of any vendor advisory. That turns the paper from "we built a test suite" into "we caught an industry-wide silent regression."

## Reasoning
- The engineering contribution is strong, but the novel-research contribution is moderate. The framing "negative-result corpus" is a useful operational idea, not a new theoretical claim.
- Better venues than arxiv cs.CL proper: NeurIPS ML Safety Workshop or DEFCON AI Village tools track.
- The real paper-worthy artifact is the longitudinal refusal-rate dataset we do not yet have. Three months of measured regressions across Claude + GPT + Gemini releases is what makes the paper cite-able.
- The blog post (`_launch/outreach/blog-post.md`) carries the idea into the community now and seeds citations for the later paper.

## Novelty signals found
- Deterministic keyword-only scorer with the explicit design goal of CI-tick-friendliness - not a contribution, but a clean framing.
- Category taxonomy (8 categories, 45 patterns) is reproducible and inspectable, which is rare in published jailbreak work.
- The "negative-result corpus" operational framing does not appear (we checked) in existing LLM-safety tool papers.

## Prior art contact
- Perez et al., Red-Teaming Language Models (2022) - adversarial generation, not regression.
- PromptFoo / Garak / Giskard - open-source LLM testing frameworks. Our tool is narrower by design (regression baseline only), and ships with a static + conversational sibling (rule-audit, colony-probe).
- No exact prior art for "keep a curated refused corpus as a CI regression baseline" as a published tools-paper contribution.

## Action queued in ACTIONABLES.md
- Launch the blog post and the HN thread now.
- Collect refusal rates on Claude + GPT + Gemini across three successive releases each over Q2-Q3 2026.
- Reopen the decision in Q4 2026 with the three-month dataset in hand.
