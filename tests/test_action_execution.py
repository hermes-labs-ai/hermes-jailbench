"""
End-to-end execution of the composite action's own shell steps.

``tests/test_ci_mode.py`` checks that ``action.yml`` parses and is *shaped*
correctly (composite, bash steps, env-not-command-line for the key). This
module goes one step further and actually *runs* the "Run the battery" step
as a subprocess — the same mechanism ``lintlang``'s
``tests/test_action_metadata.py`` uses to prove a composite action's steps
propagate real exit codes, not just that the YAML looks right.

A fake ``hermes-jailbench`` on PATH stands in for the "Install hermes-jailbench"
step (which would otherwise hit PyPI) and re-execs the in-repo CLI against the
loopback mock target, so every scenario here is credential-free and offline.

Offline: every run goes through ``mock_target.serve()``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from hermes_jailbench.cli import EXIT_GATE_FAILED, EXIT_GATE_NOT_EVALUABLE, EXIT_GATE_PASSED
from hermes_jailbench.mock_target import serve

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
ACTION = yaml.safe_load((REPO_ROOT / "action.yml").read_text(encoding="utf-8"))
RUN_STEP = next(
    step for step in ACTION["runs"]["steps"] if "hermes-jailbench " in step.get("run", "")
)


def _fake_cli_bin(tmp_path: Path) -> Path:
    """A `hermes-jailbench` on PATH that re-execs the real CLI, pinned fast.

    Mirrors lintlang's `_real_lintlang_path`: a real, executable binary rather
    than a Python-level monkeypatch, so the action's own `run:` shell script —
    unmodified — is what actually executes. `--delay 0`, one attack and no
    retries keep each scenario near-instant; argparse takes the last value for
    a repeated flag, so these appended flags simply override the action's own
    (unset) defaults without changing what the action script passes.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    shim = bin_dir / "hermes-jailbench"
    shim.write_text(
        f"#!/usr/bin/env bash\n"
        f'exec "{sys.executable}" -m hermes_jailbench "$@" '
        f'--delay 0 --max-retries 0 --attacks "DAN Classic"\n',
        encoding="utf-8",
    )
    shim.chmod(0o755)
    return bin_dir


def _action_env(tmp_path: Path, base_url: str, model: str, fail_on_bypass: str) -> dict[str, str]:
    bin_dir = _fake_cli_bin(tmp_path)
    return {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        # The shim re-execs `python -m hermes_jailbench`; make the in-repo
        # package importable without a real `pip install` (the "Install
        # hermes-jailbench" step this replaces).
        "PYTHONPATH": str(REPO_ROOT),
        "JAILBENCH_MODEL": model,
        "JAILBENCH_PROVIDER": "openai-compat",
        "JAILBENCH_BASE_URL": base_url,
        "JAILBENCH_API_KEY": "",
        "JAILBENCH_FAIL_ON_BYPASS": fail_on_bypass,
        "JAILBENCH_OUTPUT": str(tmp_path / "report.md"),
        "JAILBENCH_JSON": str(tmp_path / "report.json"),
    }


def _run_action_step(
    tmp_path: Path, model: str, fail_on_bypass: str = "0"
) -> subprocess.CompletedProcess[str]:
    with serve() as target:
        env = _action_env(tmp_path, f"{target.base_url}/v1", model, fail_on_bypass)
        return subprocess.run(
            ["bash", "-e", "-o", "pipefail", "-c", RUN_STEP["run"]],
            cwd=tmp_path,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )


def test_action_run_step_exits_0_and_reports_within_threshold(tmp_path: Path) -> None:
    completed = _run_action_step(tmp_path, "mock-refuses")

    assert completed.returncode == EXIT_GATE_PASSED == 0, completed.stdout + completed.stderr
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["summary"]["bypass_rate"] == 0.0


def test_action_run_step_exits_1_when_bypass_rate_exceeds_threshold(tmp_path: Path) -> None:
    completed = _run_action_step(tmp_path, "mock-complies")

    assert completed.returncode == EXIT_GATE_FAILED == 1, completed.stdout + completed.stderr
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["summary"]["bypass_rate"] == 1.0


def test_action_run_step_exits_2_when_the_run_is_not_evaluable(tmp_path: Path) -> None:
    """A provider-filtered reply errors the attack; the gate must not pass green."""
    completed = _run_action_step(tmp_path, "mock-filtered", fail_on_bypass="50")

    assert completed.returncode == EXIT_GATE_NOT_EVALUABLE == 2, completed.stdout + completed.stderr
    # The JSON artifact still exists — it's written before the gate can exit
    # non-zero, so a CI job can upload it on the failure path too.
    assert (tmp_path / "report.json").exists()


def test_action_run_step_writes_the_files_its_outputs_point_at(tmp_path: Path) -> None:
    """`outputs.report`/`outputs.json-report` are `${{ inputs.output }}`/`${{ inputs.json }}`
    templates — this proves the file at that same path (JAILBENCH_OUTPUT/JAILBENCH_JSON,
    the env the run step reads those inputs through) is what the step actually wrote."""
    assert ACTION["outputs"]["report"]["value"] == "${{ inputs.output }}"
    assert ACTION["outputs"]["json-report"]["value"] == "${{ inputs.json }}"

    completed = _run_action_step(tmp_path, "mock-refuses")

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert (tmp_path / "report.md").read_text().startswith("# hermes-jailbench Report")
    assert json.loads((tmp_path / "report.json").read_text())["model"] == "mock-refuses"
