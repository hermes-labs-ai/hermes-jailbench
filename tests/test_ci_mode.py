"""
CI mode: the --json artifact, what the JSON report records about the target,
the exit-code contract, and the composite GitHub Action.

Offline: every run goes through the loopback mock target.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from hermes_jailbench.cli import (
    EXIT_CODE_HELP,
    EXIT_GATE_FAILED,
    EXIT_GATE_NOT_EVALUABLE,
    EXIT_GATE_PASSED,
    main,
)
from hermes_jailbench.mock_target import serve

ACTION_YML = Path(__file__).resolve().parent.parent / "action.yml"


def _run(model: str, *extra: str) -> None:
    with serve() as target:
        main(
            [
                "--provider",
                "openai-compat",
                "--base-url",
                f"{target.base_url}/v1",
                "--model",
                model,
                "--attacks",
                "DAN Classic",
                "--delay",
                "0",
                *extra,
            ]
        )


# ---------------------------------------------------------------------------
# --json
# ---------------------------------------------------------------------------


def test_json_flag_writes_a_machine_readable_report(tmp_path: Path) -> None:
    out = tmp_path / "report.json"
    _run("mock-refuses", "--json", str(out))

    report = json.loads(out.read_text())
    assert report["summary"]["bypass_rate"] == 0.0
    assert report["summary"]["total_attacks"] == 1
    assert report["model"] == "mock-refuses"
    assert report["provider"] == "openai-compat"
    assert report["base_url"].endswith("/v1")
    assert report["version"]
    assert report["generated_at"].endswith("Z")
    assert report["attacks"][0]["verdict"] == "REFUSED"


def test_json_is_written_alongside_the_markdown_report(tmp_path: Path) -> None:
    """A CI job wants both: markdown for a human, JSON for the next run to compare."""
    md = tmp_path / "report.md"
    js = tmp_path / "report.json"
    _run("mock-refuses", "--output", str(md), "--json", str(js))

    assert md.read_text().startswith("# hermes-jailbench Report")
    assert json.loads(js.read_text())["attacks"][0]["verdict"] == "REFUSED"


def test_json_only_run_does_not_dump_the_report_to_stdout(tmp_path: Path, capsys) -> None:
    out = tmp_path / "report.json"
    _run("mock-refuses", "--json", str(out))

    stdout = capsys.readouterr().out
    assert "## Per-Category Breakdown" not in stdout
    assert f"JSON report saved to: {out}" in stdout


def test_the_json_report_is_written_before_a_failing_gate_exits(tmp_path: Path) -> None:
    """The artifact has to exist on the failure path — that is the run CI uploads."""
    out = tmp_path / "report.json"
    with pytest.raises(SystemExit) as exc_info:
        _run("mock-complies", "--json", str(out), "--fail-on-bypass", "0")

    assert exc_info.value.code == EXIT_GATE_FAILED
    assert json.loads(out.read_text())["summary"]["bypass_rate"] == 1.0


def test_a_json_path_that_cannot_be_written_is_reported_not_raised(tmp_path: Path, capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        _run("mock-refuses", "--json", str(tmp_path))  # a directory

    assert exc_info.value.code == 1
    assert "--json" in capsys.readouterr().err


def test_the_markdown_report_names_the_endpoint_that_answered(tmp_path: Path) -> None:
    md = tmp_path / "report.md"
    _run("mock-refuses", "--output", str(md))

    text = md.read_text()
    assert "**Provider:** `openai-compat`" in text
    assert "**Endpoint:** `http://127.0.0.1:" in text


# ---------------------------------------------------------------------------
# exit-code contract
# ---------------------------------------------------------------------------


def test_gate_exit_codes_are_0_1_and_2(tmp_path: Path) -> None:
    # 0 — within the threshold
    _run("mock-refuses", "--fail-on-bypass", "0", "--json", str(tmp_path / "a.json"))

    # 1 — threshold exceeded
    with pytest.raises(SystemExit) as failed:
        _run("mock-complies", "--fail-on-bypass", "0", "--json", str(tmp_path / "b.json"))
    assert failed.value.code == EXIT_GATE_FAILED

    # 2 — an attack errored, so the run cannot be judged
    with pytest.raises(SystemExit) as unevaluated:
        _run(
            "mock-filtered",
            "--fail-on-bypass",
            "50",
            "--max-retries",
            "0",
            "--json",
            str(tmp_path / "c.json"),
        )
    assert unevaluated.value.code == EXIT_GATE_NOT_EVALUABLE


def test_help_states_the_exit_code_contract(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == EXIT_GATE_PASSED

    out = capsys.readouterr().out
    assert "exit codes:" in out
    for code in ("0", "1", "2"):
        assert f"\n  {code}  " in out


def test_the_exit_code_help_text_names_every_documented_code() -> None:
    assert "exit codes:" in EXIT_CODE_HELP
    assert EXIT_CODE_HELP.count("\n  0  ") == 1
    assert EXIT_CODE_HELP.count("\n  1  ") == 1
    assert EXIT_CODE_HELP.count("\n  2  ") == 1


# ---------------------------------------------------------------------------
# the composite action
# ---------------------------------------------------------------------------


def test_action_yml_parses_and_declares_a_composite_run() -> None:
    yaml = pytest.importorskip("yaml")
    action = yaml.safe_load(ACTION_YML.read_text())

    assert action["name"] == "hermes-jailbench"
    assert action["runs"]["using"] == "composite"
    assert all(step.get("shell") == "bash" for step in action["runs"]["steps"] if "run" in step)


def test_action_default_package_spec_matches_project_version() -> None:
    """The tagged Action must install the package version reviewed with it."""
    yaml = pytest.importorskip("yaml")
    action = yaml.safe_load(ACTION_YML.read_text())
    project = (ACTION_YML.parent / "pyproject.toml").read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"$', project, flags=re.MULTILINE)
    assert match, "could not locate project version in pyproject.toml"

    assert action["inputs"]["version"]["default"] == f"=={match.group(1)}"


def test_action_yml_exposes_the_inputs_the_readme_documents() -> None:
    yaml = pytest.importorskip("yaml")
    inputs = yaml.safe_load(ACTION_YML.read_text())["inputs"]

    assert {"model", "provider", "base-url", "api-key", "fail-on-bypass", "output", "json"} <= set(
        inputs
    )
    assert inputs["provider"]["default"] == "anthropic"
    # Every input is optional: an anthropic run needs only the key.
    assert not any(spec.get("required") for spec in inputs.values())


def test_action_yml_passes_the_key_through_the_environment_not_the_command_line() -> None:
    """A key interpolated into `run:` would land in the runner's process list."""
    yaml = pytest.importorskip("yaml")
    steps = yaml.safe_load(ACTION_YML.read_text())["runs"]["steps"]
    run_step = next(step for step in steps if "hermes-jailbench " in step.get("run", ""))

    assert "${{ inputs.api-key }}" not in run_step["run"]
    assert run_step["env"]["JAILBENCH_API_KEY"] == "${{ inputs.api-key }}"


def test_action_yml_never_puts_the_key_in_the_cli_argv() -> None:
    """`--api-key <secret>` is argv: readable in the runner's process list.

    Keeping the GitHub expression out of `run:` is not enough — the value
    still reaches argv if the script appends `--api-key "$JAILBENCH_API_KEY"`.
    The key must be exported for the CLI to read from the environment.
    """
    yaml = pytest.importorskip("yaml")
    steps = yaml.safe_load(ACTION_YML.read_text())["runs"]["steps"]
    script = next(step for step in steps if "hermes-jailbench " in step.get("run", ""))["run"]

    assert "--api-key" not in script
    assert 'export ANTHROPIC_API_KEY="$JAILBENCH_API_KEY"' in script
    assert 'export OPENAI_API_KEY="$JAILBENCH_API_KEY"' in script
