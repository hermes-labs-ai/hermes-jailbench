"""
Compare two JSON reports and report what got worse.

A single run tells you the bypass rate today. The question a regression
benchmark exists to answer is whether it is worse than last time, and *which*
attacks moved — an unchanged headline rate can hide one attack that started
complying and another that started refusing.

Verdicts are ordered REFUSED < PARTIAL < COMPLIED. A move up that order is a
regression; a move down is an improvement. An attack that errored has no
verdict: it is neither, and it is listed separately rather than silently
counted as a pass, because an unscored attack could be a bypass.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

#: REFUSED < PARTIAL < COMPLIED. Higher is a weaker safety result.
VERDICT_RANK: dict[str, int] = {"REFUSED": 0, "PARTIAL": 1, "COMPLIED": 2}

#: What an attack with no verdict is called in the table.
UNSCORED = "ERROR"


@dataclass
class VerdictChange:
    """One attack whose verdict differs between the two reports."""

    name: str
    category: str
    before: str
    after: str

    def arrow(self) -> str:
        return f"{self.before} → {self.after}"


@dataclass
class ReportDiff:
    """The full comparison of two reports."""

    baseline_label: str
    new_label: str
    regressions: list[VerdictChange] = field(default_factory=list)
    improvements: list[VerdictChange] = field(default_factory=list)
    unscored_changes: list[VerdictChange] = field(default_factory=list)
    unchanged: int = 0
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    baseline_bypass_rate: Optional[float] = None
    new_bypass_rate: Optional[float] = None
    #: Set when the two reports do not describe the same target.
    target_warnings: list[str] = field(default_factory=list)

    def has_regressions(self) -> bool:
        return bool(self.regressions)


def load_report(path: str) -> dict:
    """
    Read one JSON report written by ``--json`` or ``--format json``.

    Raises:
        ValueError: The file is missing, unreadable, not JSON, or not a report
            this command can compare. The message names the file and the cause.
    """
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValueError(f"{path}: no such file") from exc
    except IsADirectoryError as exc:
        raise ValueError(f"{path}: is a directory, expected a JSON report") from exc
    except OSError as exc:
        raise ValueError(f"{path}: could not be read ({exc})") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: not valid JSON ({exc})") from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("attacks"), list):
        raise ValueError(
            f"{path}: not a hermes-jailbench JSON report "
            "(no 'attacks' list) — write one with --json PATH"
        )
    return payload


def _verdict_of(entry: dict) -> str:
    verdict = entry.get("verdict")
    if isinstance(verdict, str) and verdict in VERDICT_RANK:
        return verdict
    return UNSCORED


def _label(report: dict, path: str) -> str:
    model = report.get("model")
    when = report.get("generated_at")
    parts = [str(model)] if model else []
    if when:
        parts.append(str(when))
    return f"{path} ({', '.join(parts)})" if parts else path


def compare(baseline: dict, new: dict, baseline_path: str, new_path: str) -> ReportDiff:
    """Compare two loaded reports, matching attacks by name."""
    before = {str(a.get("name")): a for a in baseline.get("attacks", []) if isinstance(a, dict)}
    after = {str(a.get("name")): a for a in new.get("attacks", []) if isinstance(a, dict)}

    diff = ReportDiff(
        baseline_label=_label(baseline, baseline_path),
        new_label=_label(new, new_path),
        added=sorted(set(after) - set(before)),
        removed=sorted(set(before) - set(after)),
        baseline_bypass_rate=_rate(baseline),
        new_bypass_rate=_rate(new),
    )

    for name in sorted(set(before) & set(after)):
        old_verdict = _verdict_of(before[name])
        new_verdict = _verdict_of(after[name])
        if old_verdict == new_verdict:
            diff.unchanged += 1
            continue

        change = VerdictChange(
            name=name,
            category=str(after[name].get("category") or before[name].get("category") or ""),
            before=old_verdict,
            after=new_verdict,
        )
        # An attack that errored on either side has no verdict to rank, so it is
        # neither a regression nor an improvement — it is a hole in the evidence.
        if UNSCORED in (old_verdict, new_verdict):
            diff.unscored_changes.append(change)
        elif VERDICT_RANK[new_verdict] > VERDICT_RANK[old_verdict]:
            diff.regressions.append(change)
        else:
            diff.improvements.append(change)

    _check_same_target(baseline, new, diff)
    return diff


def _rate(report: dict) -> Optional[float]:
    summary = report.get("summary")
    rate = summary.get("bypass_rate") if isinstance(summary, dict) else None
    return float(rate) if isinstance(rate, (int, float)) else None


def _check_same_target(baseline: dict, new: dict, diff: ReportDiff) -> None:
    """Note, without failing, when the two runs did not test the same thing."""
    for key, label in (
        ("model", "model"),
        ("provider", "provider"),
        ("base_url", "endpoint"),
        ("target_payload", "target payload"),
    ):
        old, current = baseline.get(key), new.get(key)
        if old != current and (old or current):
            diff.target_warnings.append(f"{label}: {old!r} → {current!r}")


def render(diff: ReportDiff) -> str:
    """Render the comparison as a compact plain-text table."""
    lines: list[str] = [
        "hermes-jailbench diff",
        f"  baseline: {diff.baseline_label}",
        f"  current:  {diff.new_label}",
        "",
    ]

    if diff.baseline_bypass_rate is not None and diff.new_bypass_rate is not None:
        delta = diff.new_bypass_rate - diff.baseline_bypass_rate
        lines.append(
            f"Bypass rate: {diff.baseline_bypass_rate:.1%} → {diff.new_bypass_rate:.1%} "
            f"({delta:+.1%})"
        )
        lines.append("")

    if diff.target_warnings:
        lines.append("WARNING: the two runs do not describe the same target:")
        lines.extend(f"  {warning}" for warning in diff.target_warnings)
        lines.append("")

    for title, changes in (
        ("Regressions", diff.regressions),
        ("Improvements", diff.improvements),
        ("Unscored (errored on one side — no verdict to compare)", diff.unscored_changes),
    ):
        if not changes:
            continue
        lines.append(f"{title} ({len(changes)}):")
        width = max(len(c.name) for c in changes)
        for change in changes:
            lines.append(f"  {change.name:<{width}}  {change.arrow():<22}  {change.category}")
        lines.append("")

    if diff.added:
        lines.append(f"Only in the current run ({len(diff.added)}): {', '.join(diff.added)}")
    if diff.removed:
        lines.append(f"Only in the baseline ({len(diff.removed)}): {', '.join(diff.removed)}")
    if diff.added or diff.removed:
        lines.append("")

    lines.append(
        f"{len(diff.regressions)} regression(s), {len(diff.improvements)} improvement(s), "
        f"{diff.unchanged} unchanged"
    )
    return "\n".join(lines)
