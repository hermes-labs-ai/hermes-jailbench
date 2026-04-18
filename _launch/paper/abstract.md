# Paper abstract - future arxiv submission

## Title
**The Negative-Result Corpus: A Regression Baseline for LLM Safety Testing**

## Authors
Rolando Bosch, Hermes Labs

## Category
cs.CL (Computation and Language) - cross-listed cs.CR (Cryptography and Security)

## Abstract (250 words)

Most published LLM safety evaluations are one-off artifacts: a test suite is authored and reported once, but not re-executed against subsequent model releases. This produces a silent-decay failure mode - provider-side model updates can weaken refusal behavior without triggering any downstream alarm. We propose a complementary construct: the *negative-result corpus*, a curated set of refused-pattern tests designed to function as a commit-to-git regression baseline rather than a one-time evaluation.

This paper presents `jailbreak-bench`, an open-source implementation of this construct, consisting of 45 patterns across 7 known-refused attack categories (identity override, prompt extraction, encoding bypass, framing bypass, social engineering, injection, and meta-reasoning), each with an expected outcome of REFUSED on a well-aligned model. Patterns are evaluated with a deterministic keyword scorer (no secondary LLM invocation), producing a reproducible refusal rate per run. The corpus was derived from a structured multi-agent hackathon in which 16 adversarial agents attempted to bypass a reference Anthropic model across a full weekend of interaction; the patterns retained are those that held up against this adversarial process.

We argue that the negative-result framing is operationally distinct from (and complementary to) novel-attack research: novel attacks address the research frontier, while regression baselines address operational safety over time. We report baseline refusal rates on two production Anthropic endpoints (100% and ~100% at release) and discuss how the tool maps to EU AI Act Article 15 robustness evidence obligations. The framework is extensible: new patterns enter the corpus only after empirical confirmation of refusal on a reference-aligned model, preserving the integrity of the "negative-result" interpretation.

## Priority in the Hermes Labs paper stack

**Medium priority.** The narrative is sound and the tool is real, but the contribution is engineering-flavored rather than novel-research. Better venues than arxiv ML proper: an ML-ops-adjacent workshop, or a dedicated tools track at a security conference (DEFCON AI Village, RSA's AI security track).

The higher-priority paper from round 8 is `colony-probe`'s structural inference attack - that one has a legitimate novel-research framing (see its `launch/paper-abstract.md`). If we write only one paper this quarter, write that one.

## Timeline

- **Now**: Draft abstract saved. No rush to arxiv.
- **After 3 months of baseline data**: Populate the empirical section with multi-vendor, multi-release refusal rates. That's the paper's strongest contribution - time-series data on safety behavior across provider updates.
- **Submission target**: NeurIPS safety workshop or ICML ML4Systems workshop, whichever has an earlier CfP after the 3-month data collection window.
