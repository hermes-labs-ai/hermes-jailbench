# AGENTS.md

`hermes-jailbench` is a deterministic jailbreak regression benchmark for LLM endpoints.

## Use it for

- rerunning known jailbreak patterns after a model or prompt change
- producing a structured refusal, partial, and complied report
- smoke-testing the CLI with `--demo` or `--dry-run` before using real credentials

## Do not use it for

- claiming a model is safe against novel attacks
- multi-turn adversarial testing
- semantic judgment of ambiguous responses without human review

## Install

Product use — published package, no clone needed, and the demo needs no API key:

```bash
pip install hermes-jailbench
hermes-jailbench --demo
```

Contributor use — run from a clone of this repository:

```bash
git clone https://github.com/hermes-labs-ai/hermes-jailbench
cd hermes-jailbench
pip install -e ".[dev]"
```

End-user usage and the full CLI flag list live in [README.md](README.md). Contributor
standards live in [CONTRIBUTING.md](CONTRIBUTING.md).

## Minimal commands

```bash
hermes-jailbench --demo             # offline showcase run
hermes-jailbench --dry-run          # print prompts, no API calls
pytest -q                           # from a clone
ruff check hermes_jailbench tests   # from a clone
```

## Output shape

- terminal summary for demo and standard runs
- markdown or JSON report for saved output
- per-attack verdicts: `REFUSED`, `PARTIAL`, `COMPLIED`, or `ERROR`

## Success means

- attacks run without mutating the library state
- demo and dry-run work without an API key
- scorer output stays deterministic for the same response text
- tests stay offline and green

## Common failure cases

- users expect this tool to generate novel jailbreaks instead of replaying known ones
- API credentials or model IDs are invalid
- a response is ambiguous enough that the deterministic scorer needs manual review

## Maintainer notes

- keep the scorer deterministic and offline
- keep `run_bench()` and CLI behavior aligned with README examples
- do not add live-network behavior to tests
