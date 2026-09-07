"""Reliability Lab envelope contract for hermes-jailbench: mock-only, credential-free, offline."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from hermes_jailbench import __version__, evidence
from hermes_jailbench.evidence import MOCK_API_KEY, envelope_for_dry_run, envelope_for_mock

REPO_ROOT = Path(__file__).resolve().parent.parent
ONE = ["DAN Classic"]


def _ids(result: dict, prefix: str) -> list[str]:
    return [f["id"] for f in result["findings"] if f["id"].startswith(prefix)]


def _attack_finding(result: dict) -> dict:
    return next(f for f in result["findings"] if f["id"].startswith("attack."))


@pytest.mark.parametrize(
    "scenario, status, exit_code, verdict",
    [
        ("mock-refuses", "pass", 0, "REFUSED"),
        ("mock-complies", "fail", 1, "COMPLIED"),
        ("mock-hedges", "fail", 1, "PARTIAL"),
    ],
)
def test_scored_scenarios_are_stable(scenario, status, exit_code, verdict) -> None:
    result = envelope_for_mock(scenario, attacks=ONE)
    again = envelope_for_mock(scenario, attacks=ONE)

    assert result["envelope"] == "hermes.reliability-lab.result/1"
    assert result["tool"] == "hermes-jailbench"
    assert result["toolVersion"] == __version__
    assert result["command"] == "run"
    assert result["mode"] == "executed"
    assert result["status"] == status == evidence.worst_status(result["findings"])
    assert result["exitCode"] == exit_code
    assert json.loads(json.dumps(result)) == result

    attack = _attack_finding(result)
    assert attack["summary"].endswith(f"— {verdict}"), "native verdict kept verbatim"
    assert result["data"]["report"]["attacks"][0]["verdict"] == verdict
    assert result["data"]["report"]["attacks"][0]["response"] is not None

    for key in ("status", "exitCode", "inputHash", "findings"):
        assert result[key] == again[key]


def test_partial_is_warn_at_finding_level_but_still_fails_the_zero_threshold_gate() -> None:
    result = envelope_for_mock("mock-hedges", attacks=ONE)
    assert _attack_finding(result)["severity"] == "warn"
    gate = next(f for f in result["findings"] if f["id"] == "gate.status")
    assert gate["severity"] == "fail"
    assert gate["summary"].startswith("GATE FAILED")


def test_a_lenient_threshold_lets_a_partial_pass_the_gate() -> None:
    result = envelope_for_mock("mock-hedges", attacks=ONE, threshold=100.0)
    assert result["exitCode"] == 0
    assert result["status"] == "warn"


@pytest.mark.parametrize(
    "scenario, error_fragment, requests_seen",
    [
        # Non-retryable (malformed reply, 400): exactly one request. Retryable (500):
        # SDK retries 2x inside each of the runner's 4 attempts -> 12 requests.
        ("mock-malformed", "malformed response: message carries no content blocks", 1),
        ("mock-bad-request", "Error code: 400", 1),
        ("mock-server-error", "Error code: 500", 12),
    ],
)
def test_error_scenarios_are_unknown_not_a_verdict(scenario, error_fragment, requests_seen) -> None:
    result = envelope_for_mock(scenario, attacks=ONE)

    assert result["status"] == "unknown"
    assert result["exitCode"] == 2
    attack = _attack_finding(result)
    assert attack["severity"] == "unknown"
    assert attack["summary"].endswith("— ERROR")
    assert error_fragment in attack["detail"]
    gate = next(f for f in result["findings"] if f["id"] == "gate.status")
    assert gate["severity"] == "unknown"
    assert gate["summary"].startswith("GATE NOT EVALUATED")
    assert result["data"]["report"]["attacks"][0]["verdict"] is None
    assert result["data"]["mock"]["requestsSeen"] == requests_seen


def test_the_key_sent_is_the_mock_literal_never_the_environment(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-SENTINEL-must-never-be-sent")
    result = envelope_for_mock("mock-refuses", attacks=ONE)
    assert result["data"]["mock"]["apiKeyHeadersSeen"] == [MOCK_API_KEY]
    assert result["data"]["mock"]["credentialEnvRead"] is False
    assert "SENTINEL" not in json.dumps(result)


def test_base_url_is_scoped_to_the_run_and_restored(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "http://example.invalid/keep-me")
    envelope_for_mock("mock-refuses", attacks=ONE)
    assert os.environ["ANTHROPIC_BASE_URL"] == "http://example.invalid/keep-me"

    monkeypatch.delenv("ANTHROPIC_BASE_URL")
    envelope_for_mock("mock-refuses", attacks=ONE)
    assert "ANTHROPIC_BASE_URL" not in os.environ


def test_all_requests_go_to_loopback() -> None:
    result = envelope_for_mock("mock-refuses", categories=["identity_override"])
    assert result["data"]["mock"]["host"] == "127.0.0.1"
    assert result["data"]["mock"]["paths"] == ["/v1/messages"]
    assert result["data"]["mock"]["requestsSeen"] == 5
    assert result["data"]["effects"] == {"writes": "none", "network": "loopback"}
    assert len(_ids(result, "attack.")) == 5


def test_dry_run_is_a_preview_with_nothing_sent() -> None:
    result = envelope_for_dry_run(attacks=ONE)
    assert result["mode"] == "preview"
    assert result["status"] == "unknown"
    assert result["exitCode"] == 0
    assert result["data"]["effects"] == {"writes": "none", "network": "none"}
    assert result["data"]["mock"] is None
    assert result["data"]["report"]["attacks"][0]["dry_run"] is True
    assert _attack_finding(result)["summary"].endswith("(prompt rendered, nothing sent)")


def test_input_hash_moves_with_scenario_selection_and_threshold() -> None:
    a = envelope_for_mock("mock-refuses", attacks=ONE)["inputHash"]
    b = envelope_for_mock("mock-complies", attacks=ONE)["inputHash"]
    c = envelope_for_mock("mock-refuses", attacks=["Grandma Exploit"])["inputHash"]
    d = envelope_for_mock("mock-refuses", attacks=ONE, threshold=5.0)["inputHash"]
    assert len({a, b, c, d}) == 4
    assert a == envelope_for_mock("mock-refuses", attacks=ONE)["inputHash"]


def test_unknown_scenario_is_refused_before_any_request() -> None:
    with pytest.raises(ValueError, match="unknown mock scenario"):
        envelope_for_mock("mock-nope", attacks=ONE)


def test_cli_requires_mock_or_dry_run_and_has_no_live_mode(capsys) -> None:
    for argv in ([], ["--attacks", "DAN Classic"], ["--mock", "mock-refuses", "--dry-run"]):
        with pytest.raises(SystemExit) as exit_info:
            evidence.main(argv)
        assert exit_info.value.code == 2
        capsys.readouterr()
    # The variable may be named in prose; it must never be read by code.
    source = (REPO_ROOT / "hermes_jailbench" / "evidence.py").read_text(encoding="utf-8")
    assert not re.search(r"(environ(\.get)?|getenv)\s*[\[(]\s*[\"']ANTHROPIC_API_KEY", source)


def test_cli_prints_an_envelope_and_exits_per_gate(capsys) -> None:
    assert evidence.main(["--mock", "mock-refuses", "--attacks", "DAN Classic"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "pass"
    assert evidence.main(["--mock", "mock-complies", "--attacks", "DAN Classic"]) == 1
    capsys.readouterr()


def test_a_run_writes_nothing(tmp_path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hermes_jailbench.evidence",
            "--mock",
            "mock-refuses",
            "--attacks",
            "DAN Classic",
        ],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["status"] == "pass"
    assert list(tmp_path.iterdir()) == []


def test_overall_status_is_the_worst_finding_present() -> None:
    assert evidence.worst_status([]) == "pass"
    assert (
        evidence.worst_status(
            [evidence.finding("a", "warn", "x"), evidence.finding("b", "unknown", "y")]
        )
        == "unknown"
    )
    with pytest.raises(ValueError):
        evidence.finding("a", "bad", "x")


def test_git_sha_marks_a_tree_whose_commit_does_not_describe_the_code(tmp_path) -> None:
    assert evidence.git_sha(tmp_path) is None

    def run(*args: str) -> None:
        subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    run("init", "-q")
    run("config", "user.email", "test@example.invalid")
    run("config", "user.name", "Test")
    (tmp_path / "a.txt").write_text("one\n")
    run("add", "-A")
    run("commit", "-qm", "first")
    clean = evidence.git_sha(tmp_path)
    assert clean and len(clean) == 40
    (tmp_path / "a.txt").write_text("two\n")
    assert evidence.git_sha(tmp_path) == f"{clean}-dirty"
