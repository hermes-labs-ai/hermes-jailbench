# jailbreak-bench Roadmap

**Product:** Automated red-team testing CLI for LLM endpoints  
**Target users:** AI audit firms, red-team consultancies, enterprise security teams  
**Maintained by:** Hermes Labs

---

## v0.1.0 — Current (Shipped)

**Theme:** Single-turn baseline benchmark

- 37 single-turn attacks across 7 categories
- Keyword-based scorer (no LLM dependency for scoring)
- Markdown report with per-attack and per-category breakdown
- CLI with dry-run, category/attack filtering, live progress output
- `on_result` callback for library integration
- 58 passing tests (no API key required)
- Published to PyPI as `jailbreak-bench`

---

## v0.2.0 — Multi-Turn Attacks

**Theme:** Conversation-level jailbreaking

**Problem:** Many real-world bypasses require multiple turns. A single-turn refusal doesn't mean the model is safe across a conversation.

### Features

- **Multi-turn attack sequences** — define attacks as `List[str]` (ordered turns)
- **Ant colony pattern** — iterative refinement attacks: start with a benign framing, progressively escalate payload across 3–8 turns, score final compliance
- **Conversation-level scoring** — new `ConversationScorer` that tracks trajectory: if model refuses at turn 3 after partial compliance at turn 2, it's still a PARTIAL
- **`ConversationResult`** dataclass — stores full message history, per-turn scores, final verdict
- **Escalation heuristics** — detect when a model "breaks" mid-conversation vs. holds through all turns
- `run_bench()` extended with `multiturn=True` parameter and `max_turns: int`
- Report updated to show conversation traces for multi-turn attacks

### New Attack Patterns (20+)

- Incremental normalization (slowly shift context across turns)
- Persona lock-in (establish persona before injecting harmful request)
- Forgetfulness exploit (claim model "forgot" its guidelines)
- Memory poisoning (inject false context in early turns)

### Accuracy Targets

- False negative rate on multi-turn compliance: <= 15% (harder than single-turn)

---

## v0.3.0 — Output Formats and CI Integration

**Theme:** Fit into engineering workflows

**Problem:** Security teams need jailbreak results in their existing pipelines — not just markdown files read by humans.

### Features

- **HTML dashboard report** — self-contained single-file HTML with:
  - Summary scorecard with color-coded bypass rate
  - Per-category radar chart (Chart.js, bundled inline)
  - Collapsible per-attack drill-down with full prompt/response
  - Mobile-friendly layout
- **SARIF output** (`--format sarif`) — Static Analysis Results Interchange Format 2.1.0
  - Each attack result becomes a SARIF `result` entry
  - `COMPLIED` → `error` severity, `PARTIAL` → `warning`, `REFUSED` → `note`
  - Enables GitHub Advanced Security integration (upload SARIF to PR checks)
- **JUnit XML output** (`--format junit`) — for Jenkins/CircleCI/GitLab CI
- **`--fail-on-bypass` CLI flag** — exit code 1 if bypass rate exceeds threshold (default: 0%)
- GitHub Actions example workflow in `docs/ci-integration.md`
- Pre-built Docker image: `ghcr.io/hermes-labs-ai/jailbreak-bench:v0.3.0`

### `generate_report()` signature change

`output_format` gains values: `"html"`, `"sarif"`, `"junit"` (in addition to existing `"markdown"`, `"json"`)

---

## v1.0.0 — SaaS API and Scheduled Audits

**Theme:** Productized for enterprise deployment

**Problem:** One-time audits don't catch regressions. Enterprise buyers need recurring audits, historical trends, and multi-model comparison dashboards.

### Features

#### SaaS API
- REST API (`POST /v1/bench`) — submit a bench job, get async results
- Authentication via API key
- Webhook support for result delivery
- Rate limiting and job queuing per tenant
- Multi-provider support: Anthropic, OpenAI, Azure OpenAI, Ollama (self-hosted)

#### Scheduled Recurring Audits
- Cron-based scheduling (daily/weekly/monthly)
- Notification channels: Slack, email, PagerDuty
- Alert on regression: bypass rate increased vs. previous run
- Configurable alert thresholds per category

#### Historical Comparison
- Audit history stored per model, per payload, per date
- Trend charts: bypass rate over time
- Diff view: which attacks changed verdict between runs
- Side-by-side model comparison (run same attacks against gpt-4 vs. claude-sonnet vs. llama3)

#### Enterprise Features
- Custom attack library (upload your own attack templates via API)
- Role-based access control
- SOC 2 compliant audit log
- On-premises deployment option (Helm chart)
- Bulk model testing: test 10 models in parallel

### CLI backward compatibility

`jailbreak-bench` CLI remains fully functional offline. v1.0.0 adds `--remote` flag to submit to SaaS API instead of running locally.

---

## Backlog / Future Considerations

- **LLM-assisted scoring** (opt-in) — use a secondary model to score ambiguous PARTIAL verdicts
- **Attack effectiveness metrics** — track which attacks succeed most often across models
- **Community attack registry** — crowdsourced attack library with versioning
- **Multilingual attacks** — attack templates in French, Mandarin, Arabic
- **Vision attacks** — image-based jailbreak prompts for multimodal models
- **Embedding-based semantic scorer** — cosine distance from "refusal cluster" as scoring signal
- **Plugin system** — custom scorer plugins via Python entry points

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| v0.1.0 | 2025-Q2 | 37 attacks, keyword scorer, markdown report, 58 tests |
