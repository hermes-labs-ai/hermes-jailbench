"""
Generates reports from a BenchResult.

Supported formats:
  - markdown (default): summary table, per-category breakdown, per-attack details
  - json: machine-readable JSON conforming to the Report JSON schema in SPEC.md

Shows pass/fail per attack, per-category breakdown, and summary stats.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from .attacks import Category, ExpectedResult
from .runner import AttackResult, BenchResult

logger = logging.getLogger(__name__)

# Verdict badge text
VERDICT_BADGE = {
    ExpectedResult.REFUSED: "REFUSED",
    ExpectedResult.PARTIAL: "PARTIAL",
    ExpectedResult.COMPLIED: "COMPLIED",
}

VERDICT_ICON = {
    ExpectedResult.REFUSED: "REFUSED",
    ExpectedResult.PARTIAL: "PARTIAL",
    ExpectedResult.COMPLIED: "COMPLIED",
}

CATEGORY_LABELS = {
    Category.IDENTITY_OVERRIDE: "Identity Override",
    Category.PROMPT_EXTRACTION: "Prompt Extraction",
    Category.ENCODING_BYPASS: "Encoding Bypass",
    Category.FRAMING_BYPASS: "Framing Bypass",
    Category.SOCIAL_ENGINEERING: "Social Engineering",
    Category.INJECTION: "Injection",
    Category.META_REASONING: "Meta-Reasoning",
}


def _pct(num: int, denom: int) -> str:
    if denom == 0:
        return "N/A"
    return f"{100 * num / denom:.1f}%"


def _pct_float(num: int, denom: int) -> float:
    if denom == 0:
        return 0.0
    return round(num / denom, 4)


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------


def _generate_markdown(
    result: BenchResult,
    include_responses: bool = False,
    title: Optional[str] = None,
) -> str:
    """Generate a markdown report string from a BenchResult."""
    lines: list[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report_title = title or f"jailbreak-bench Report — {result.model}"

    lines.append(f"# {report_title}")
    lines.append("")
    lines.append(f"**Generated:** {now}")
    lines.append(f"**Model:** `{result.model}`")
    lines.append(f"**Target payload:** `{result.target_payload}`")
    lines.append("")

    # ---------------------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------------------
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total attacks | {result.total_attacks} |")
    lines.append(
        f"| Refused | {result.refused_count} ({_pct(result.refused_count, result.total_attacks)}) |"
    )
    lines.append(
        f"| Partial | {result.partial_count} ({_pct(result.partial_count, result.total_attacks)}) |"
    )
    lines.append(
        f"| Complied | {result.complied_count} ({_pct(result.complied_count, result.total_attacks)}) |"
    )
    lines.append(f"| Errors | {result.error_count} |")
    lines.append(
        f"| **Bypass rate** | **{_pct(result.partial_count + result.complied_count, result.total_attacks - result.error_count)}** |"
    )
    lines.append(
        f"| **Refusal rate** | **{_pct(result.refused_count, result.total_attacks - result.error_count)}** |"
    )
    lines.append("")

    # ---------------------------------------------------------------------------
    # Per-category breakdown
    # ---------------------------------------------------------------------------
    lines.append("## Per-Category Breakdown")
    lines.append("")
    lines.append("| Category | Total | Refused | Partial | Complied | Bypass Rate |")
    lines.append("|----------|-------|---------|---------|----------|-------------|")

    by_category: dict[Category, list[AttackResult]] = {cat: [] for cat in Category}
    for ar in result.attacks:
        by_category[ar.attack.category].append(ar)

    for cat, cat_results in by_category.items():
        if not cat_results:
            continue
        total = len(cat_results)
        refused = sum(
            1 for r in cat_results if r.score and r.score.verdict == ExpectedResult.REFUSED
        )
        partial = sum(
            1 for r in cat_results if r.score and r.score.verdict == ExpectedResult.PARTIAL
        )
        complied = sum(
            1 for r in cat_results if r.score and r.score.verdict == ExpectedResult.COMPLIED
        )
        bypass = partial + complied
        label = CATEGORY_LABELS.get(cat, cat.value)
        lines.append(
            f"| {label} | {total} | {refused} | {partial} | {complied} | {_pct(bypass, total)} |"
        )

    lines.append("")

    # ---------------------------------------------------------------------------
    # Per-attack results
    # ---------------------------------------------------------------------------
    lines.append("## Attack-by-Attack Results")
    lines.append("")

    current_cat: Optional[Category] = None
    for ar in result.attacks:
        cat = ar.attack.category
        if cat != current_cat:
            current_cat = cat
            lines.append(f"### {CATEGORY_LABELS.get(cat, cat.value)}")
            lines.append("")

        if ar.dry_run:
            verdict_str = "DRY-RUN"
            icon = "DRY"
        elif ar.error:
            verdict_str = "ERROR"
            icon = "ERR"
        elif ar.score:
            verdict_str = VERDICT_BADGE[ar.score.verdict]
            icon = VERDICT_ICON[ar.score.verdict]
        else:
            verdict_str = "UNKNOWN"
            icon = "???"

        lines.append(f"#### [{icon}] `{ar.attack.name}` — {verdict_str}")
        lines.append("")
        lines.append(f"**Category:** {CATEGORY_LABELS.get(cat, cat.value)}  ")
        lines.append(f"**Tags:** {', '.join(ar.attack.tags) if ar.attack.tags else '—'}  ")

        if ar.score:
            lines.append(f"**Confidence:** {ar.score.confidence:.0%}  ")
            if ar.score.matched_refusal:
                lines.append(f"**Refusal signals:** `{', '.join(ar.score.matched_refusal[:3])}`  ")
            if ar.score.matched_compliance:
                lines.append(
                    f"**Compliance signals:** `{', '.join(ar.score.matched_compliance[:3])}`  "
                )
            if ar.score.notes:
                lines.append(f"**Notes:** {ar.score.notes}  ")

        if ar.error:
            lines.append(f"**Error:** {ar.error}  ")

        lines.append(f"**Elapsed:** {ar.elapsed_seconds:.2f}s  ")
        lines.append("")

        prompt_preview = ar.prompt[:300].replace("\n", " ↩ ")
        if len(ar.prompt) > 300:
            prompt_preview += "…"
        lines.append("<details><summary>Prompt preview</summary>")
        lines.append("")
        lines.append(f"```\n{ar.prompt[:600]}\n```")
        lines.append("</details>")
        lines.append("")

        if include_responses and ar.response:
            lines.append("<details><summary>Response</summary>")
            lines.append("")
            lines.append(f"```\n{ar.response[:1000]}\n```")
            lines.append("</details>")
            lines.append("")

    # ---------------------------------------------------------------------------
    # Footer
    # ---------------------------------------------------------------------------
    lines.append("---")
    lines.append("")
    lines.append(
        "*Generated by [jailbreak-bench](https://github.com/roli-lpci/jailbreak-bench) — Hermes Labs*"
    )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON report
# ---------------------------------------------------------------------------


def _generate_json(
    result: BenchResult,
    include_responses: bool = False,
) -> str:
    """Generate a JSON report string from a BenchResult."""
    from . import __version__

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    attempted = result.total_attacks - result.error_count

    by_category: dict[Category, list[AttackResult]] = {cat: [] for cat in Category}
    for ar in result.attacks:
        by_category[ar.attack.category].append(ar)

    category_breakdown = []
    for cat, cat_results in by_category.items():
        if not cat_results:
            continue
        total = len(cat_results)
        refused = sum(
            1 for r in cat_results if r.score and r.score.verdict == ExpectedResult.REFUSED
        )
        partial = sum(
            1 for r in cat_results if r.score and r.score.verdict == ExpectedResult.PARTIAL
        )
        complied = sum(
            1 for r in cat_results if r.score and r.score.verdict == ExpectedResult.COMPLIED
        )
        category_breakdown.append(
            {
                "category": cat.value,
                "label": CATEGORY_LABELS.get(cat, cat.value),
                "total": total,
                "refused": refused,
                "partial": partial,
                "complied": complied,
                "bypass_rate": _pct_float(partial + complied, total),
            }
        )

    attacks_list = []
    for ar in result.attacks:
        entry: dict = {
            "name": ar.attack.name,
            "category": ar.attack.category.value,
            "tags": ar.attack.tags,
            "expected_result": ar.attack.expected_result.value,
            "prompt": ar.prompt,
            "elapsed_seconds": round(ar.elapsed_seconds, 4),
            "error": ar.error,
            "dry_run": ar.dry_run,
        }
        if include_responses:
            entry["response"] = ar.response
        else:
            entry["response"] = None

        if ar.score:
            entry["verdict"] = ar.score.verdict.value
            entry["confidence"] = round(ar.score.confidence, 4)
            entry["matched_refusal"] = ar.score.matched_refusal
            entry["matched_compliance"] = ar.score.matched_compliance
            entry["matched_partial"] = ar.score.matched_partial
            entry["notes"] = ar.score.notes
        else:
            entry["verdict"] = None
            entry["confidence"] = None
            entry["matched_refusal"] = []
            entry["matched_compliance"] = []
            entry["matched_partial"] = []
            entry["notes"] = None

        attacks_list.append(entry)

    report: dict = {
        "generated_at": now,
        "version": __version__,
        "model": result.model,
        "target_payload": result.target_payload,
        "summary": {
            "total_attacks": result.total_attacks,
            "refused_count": result.refused_count,
            "partial_count": result.partial_count,
            "complied_count": result.complied_count,
            "error_count": result.error_count,
            "bypass_rate": _pct_float(result.partial_count + result.complied_count, attempted),
            "refusal_rate": _pct_float(result.refused_count, attempted),
        },
        "by_category": category_breakdown,
        "attacks": attacks_list,
    }

    return json.dumps(report, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_report(
    result: BenchResult,
    include_responses: bool = False,
    title: Optional[str] = None,
    output_format: str = "markdown",
) -> str:
    """
    Generate a report from a BenchResult.

    Args:
        result:            The BenchResult from run_bench().
        include_responses: If True, include full model responses in the report.
        title:             Optional report title override (markdown only).
        output_format:     "markdown" (default) or "json".

    Returns:
        A report string in the requested format.

    Raises:
        ValueError: If output_format is not "markdown" or "json".
    """
    logger.debug(
        "Generating %s report for model=%s (%d attacks).",
        output_format,
        result.model,
        result.total_attacks,
    )

    if output_format == "markdown":
        return _generate_markdown(result, include_responses=include_responses, title=title)
    elif output_format == "json":
        return _generate_json(result, include_responses=include_responses)
    else:
        raise ValueError(f"Unknown output_format {output_format!r}. Expected 'markdown' or 'json'.")


def save_report(
    result: BenchResult,
    path: str,
    include_responses: bool = False,
    output_format: str = "markdown",
) -> None:
    """
    Save a report to disk.

    Args:
        result:            The BenchResult from run_bench().
        path:              File path to write to.
        include_responses: If True, include full model responses in the report.
        output_format:     "markdown" (default) or "json".

    Raises:
        ValueError: If output_format is not recognized.
        OSError:    If the file cannot be written.
    """
    content = generate_report(
        result, include_responses=include_responses, output_format=output_format
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("Report saved to: %s", path)
