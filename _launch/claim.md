# Claim — jailbreak-bench

## One-sentence falsifiable claim
Running the 45-pattern `jailbreak-bench` suite against a well-aligned production LLM endpoint yields a refusal rate of 95% or higher, and a drop of more than 5 percentage points across consecutive releases of the same model family indicates a safety-posture regression worth investigating.

## Why it is falsifiable
- **Test**: run the CLI twice, against two successive model versions from the same vendor, at the same temperature and max-tokens.
- **Result shape**: two refusal-rate numbers plus per-category breakdowns.
- **Failure mode**: if the tool reports a large drop but manual review of the flagged responses shows they were actually refusals mis-scored as partial, the claim is weakened. If it reports a flat refusal rate but adversaries are already bypassing the model in the wild, the claim is falsified — the corpus is stale.

## What the claim is NOT
- Not a claim about novel jailbreak discovery. The corpus is curated *refused* patterns; it does not generate new attacks.
- Not a verdict tool. "COMPLIED" on this benchmark is a signal, not a judgment; ambiguous cases still require human review of the response text.
- Not a replacement for a full safety evaluation. It is a regression alarm — it tells you when behavior changes across releases, not whether the current behavior is globally safe.
