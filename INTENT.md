This tool exists to benchmark an LLM's jailbreak resistance by running 37 known attack patterns and classifying each response as REFUSED, PARTIAL, or COMPLIED.
Accepts: Model name + API key for live runs (Anthropic SDK), --dry-run mode with no API (inspects attack prompts only), category filters
Rejects: Local model endpoints without Anthropic SDK compatibility, pre-recorded conversation logs (it generates its own prompts), raw text files as input
