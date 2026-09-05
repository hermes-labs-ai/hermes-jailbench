"""
Tests for the CLI --fail-on-bypass gate.

No API key required — run_bench is monkeypatched to return synthetic BenchResults.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hermes_jailbench import cli
from hermes_jailbench.attacks import ALL_ATTACKS, ExpectedResult
from hermes_jailbench.cli import (
    EXIT_GATE_FAILED,
    EXIT_GATE_NOT_EVALUABLE,
    EXIT_GATE_PASSED,
    evaluate_gate,
)
from hermes_jailbench.runner import AttackResult, BenchResult
from hermes_jailbench.scorer import ScoreResult


def _bench(refused: int = 0, partial: int = 0, complied: int = 0, errors: int = 0) -> BenchResult:
    """Build a BenchResult with the given tallies and matching AttackResult rows."""
    result = BenchResult(
        model="mock-model",
        target_payload="mock payload",
        total_attacks=refused + partial + complied + errors,
        refused_count=refused,
        partial_count=partial,
        complied_count=complied,
        error_count=errors,
    )
    verdicts = (
        [ExpectedResult.REFUSED] * refused
        + [ExpectedResult.PARTIAL] * partial
        + [ExpectedResult.COMPLIED] * complied
        + [None] * errors
    )
    for i, verdict in enumerate(verdicts):
        attack = ALL_ATTACKS[i % len(ALL_ATTACKS)]
        score = (
            ScoreResult(
                verdict=verdict,
                confidence=0.9,
                matched_refusal=[],
                matched_compliance=[],
                matched_partial=[],
                raw_response="mock",
            )
            if verdict is not None
            else None
        )
        result.attacks.append(
            AttackResult(
                attack=attack,
                prompt=attack.render("mock payload"),
                response="mock" if verdict is not None else None,
                score=score,
                elapsed_seconds=0.0,
                error=None if verdict is not None else "boom",
            )
        )
    return result


# ---------------------------------------------------------------------------
# evaluate_gate — pure function
# ---------------------------------------------------------------------------


def test_gate_passes_when_no_bypass() -> None:
    code, msg = evaluate_gate(_bench(refused=45), 0.0)
    assert code == EXIT_GATE_PASSED
    assert msg.startswith("GATE PASSED")


def test_gate_fails_on_single_partial_at_zero_threshold() -> None:
    code, msg = evaluate_gate(_bench(refused=44, partial=1), 0.0)
    assert code == EXIT_GATE_FAILED
    assert msg.startswith("GATE FAILED")
    assert "1/45" in msg


def test_gate_fails_on_complied_over_threshold() -> None:
    code, _ = evaluate_gate(_bench(refused=40, complied=5), 10.0)
    assert code == EXIT_GATE_FAILED  # 11.1% > 10%


def test_gate_exact_threshold_passes_without_float_drift() -> None:
    # 1/20 == 5.0% exactly; 0.05 * 100 in float is 5.000000000000001 and must NOT fail.
    code, _ = evaluate_gate(_bench(refused=19, complied=1), 5.0)
    assert code == EXIT_GATE_PASSED


def test_gate_not_evaluable_on_any_error_even_when_rate_is_within_threshold() -> None:
    # 1 partial out of 10 scored (5 errored) would be 10% <= 10%, but an unscored
    # attack could be a bypass, so a partial run must never pass green.
    code, msg = evaluate_gate(_bench(refused=9, partial=1, errors=5), 10.0)
    assert code == EXIT_GATE_NOT_EVALUABLE
    assert msg.startswith("GATE NOT EVALUATED")
    assert "5 of 15 attack(s) errored" in msg


def test_gate_not_evaluable_on_single_error_with_zero_bypass() -> None:
    code, _ = evaluate_gate(_bench(refused=44, errors=1), 100.0)
    assert code == EXIT_GATE_NOT_EVALUABLE


def test_gate_not_evaluable_when_nothing_completed() -> None:
    code, msg = evaluate_gate(_bench(errors=3), 0.0)
    assert code == EXIT_GATE_NOT_EVALUABLE
    assert "3 of 3 attack(s) errored" in msg


def test_gate_not_evaluable_on_empty_result() -> None:
    code, msg = evaluate_gate(_bench(), 0.0)
    assert code == EXIT_GATE_NOT_EVALUABLE
    assert "no attack ran" in msg


# ---------------------------------------------------------------------------
# CLI wiring — main() with run_bench mocked
# ---------------------------------------------------------------------------


def _run_main(monkeypatch: pytest.MonkeyPatch, bench: BenchResult, argv: list[str]) -> int:
    monkeypatch.setattr(cli, "run_bench", lambda **kwargs: bench)
    try:
        cli.main(["--api-key", "test-key", *argv])
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


def test_cli_gate_passes_exit_zero(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    code = _run_main(monkeypatch, _bench(refused=45), ["--fail-on-bypass"])
    assert code == 0
    assert "GATE PASSED" in capsys.readouterr().out


def test_cli_gate_flag_without_value_means_zero_percent(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    code = _run_main(monkeypatch, _bench(refused=44, partial=1), ["--fail-on-bypass"])
    assert code == 1
    assert "GATE FAILED" in capsys.readouterr().err


def test_cli_gate_with_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _run_main(monkeypatch, _bench(refused=44, partial=1), ["--fail-on-bypass", "5"]) == 0
    assert _run_main(monkeypatch, _bench(refused=40, complied=5), ["--fail-on-bypass", "5"]) == 1


def test_cli_gate_exit_two_when_nothing_completed(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    code = _run_main(monkeypatch, _bench(errors=2), ["--fail-on-bypass"])
    assert code == 2
    assert "GATE NOT EVALUATED" in capsys.readouterr().err


def test_cli_gate_exit_two_on_partial_errors_and_report_still_written(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys
) -> None:
    # A single rate-limit/network failure must not pass green, even at a lenient threshold.
    out = tmp_path / "report.md"
    code = _run_main(
        monkeypatch,
        _bench(refused=44, errors=1),
        ["--fail-on-bypass", "50", "--output", str(out)],
    )
    assert code == 2
    assert "1 of 45 attack(s) errored" in capsys.readouterr().err
    assert out.exists()


def test_cli_no_gate_flag_exits_zero_with_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    # Backward compatibility: without the flag, errored attacks never change the exit code.
    assert _run_main(monkeypatch, _bench(refused=40, errors=5), []) == 0


def test_cli_report_is_written_before_gate_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    out = tmp_path / "report.json"
    code = _run_main(
        monkeypatch,
        _bench(refused=44, complied=1),
        ["--fail-on-bypass", "--output", str(out), "--format", "json"],
    )
    assert code == 1
    assert out.exists()
    assert '"complied_count": 1' in out.read_text(encoding="utf-8")


def test_cli_no_gate_flag_exits_zero_even_with_bypass(monkeypatch: pytest.MonkeyPatch) -> None:
    # Backward compatibility: without the flag, a bypass never changes the exit code.
    assert _run_main(monkeypatch, _bench(refused=40, complied=5), []) == 0


def test_cli_gate_rejects_dry_run(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    code = _run_main(monkeypatch, _bench(), ["--dry-run", "--fail-on-bypass"])
    assert code == 2
    assert "dry run" in capsys.readouterr().err


def test_cli_gate_rejects_demo(monkeypatch: pytest.MonkeyPatch) -> None:
    # --demo implies --dry-run, so the gate must be refused there too.
    assert _run_main(monkeypatch, _bench(), ["--demo", "--fail-on-bypass"]) == 2


@pytest.mark.parametrize("value", ["-1", "100.5", "abc"])
def test_cli_gate_rejects_out_of_range_threshold(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    assert _run_main(monkeypatch, _bench(refused=1), ["--fail-on-bypass", value]) == 2
