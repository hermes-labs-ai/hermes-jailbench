"""The repository root is one portable Agent Plugin with a single canonical skill.

  plugin.json                        portable Agent Plugins 1.0.0 manifest (Codex CLI)
  .agents/plugins/marketplace.json   Codex repo marketplace, source "./"
  .claude-plugin/plugin.json         Claude Code plugin manifest
  .claude-plugin/marketplace.json    Claude Code marketplace, source "."
  gemini-extension.json              Gemini CLI extension manifest

Every host resolves the root, so every host loads
`skills/hermes-jailbench/SKILL.md`. No manifest may carry its own copy, and every
identity field must match pyproject.toml. The live tests install into an isolated
HOME and read the result back; they skip when the host CLI is absent.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
NAME = "hermes-jailbench"
PORTABLE_MANIFEST = ROOT / "plugin.json"
CODEX_MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
CLAUDE_MANIFEST = ROOT / ".claude-plugin" / "plugin.json"
CLAUDE_MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
GEMINI_MANIFEST = ROOT / "gemini-extension.json"
CANONICAL_SKILL = ROOT / "skills" / NAME / "SKILL.md"
PYPROJECT = ROOT / "pyproject.toml"
SCHEMA_ID = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
NAME_PATTERN = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
PORTABLE_KEYS = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "extensions",
}
LOCAL_STATE = {".git", ".venv", "venv", "node_modules", ".pytest_cache", "build", "dist"}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _pyproject_field(name: str) -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(rf'^{re.escape(name)}\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    assert match, f"{name} not found in pyproject.toml"
    return match.group(1)


def test_portable_manifest_follows_agent_plugins_schema():
    manifest = _json(PORTABLE_MANIFEST)
    assert manifest["$schema"] == SCHEMA_ID
    assert NAME_PATTERN.match(manifest["name"]) and len(manifest["name"]) <= 64
    assert set(manifest) <= PORTABLE_KEYS, set(manifest) - PORTABLE_KEYS
    assert set(manifest.get("author", {})) <= {"name", "email", "url"}


def test_every_manifest_identity_matches_pyproject():
    name, version = _pyproject_field("name"), _pyproject_field("version")
    description = _pyproject_field("description")
    assert name == NAME
    for path in (PORTABLE_MANIFEST, CLAUDE_MANIFEST, GEMINI_MANIFEST):
        manifest = _json(path)
        assert manifest["name"] == name, path
        assert manifest["version"] == version, path
        assert manifest["description"] == description, path
    claude, portable = _json(CLAUDE_MANIFEST), _json(PORTABLE_MANIFEST)
    for key in ("author", "homepage", "repository", "license"):
        assert portable[key] == claude[key], key


def test_claude_marketplace_resolves_to_the_repository_root():
    marketplace = _json(CLAUDE_MARKETPLACE)
    (entry,) = marketplace["plugins"]
    assert marketplace["name"] == entry["name"] == NAME
    assert entry["source"] == "."
    assert (CLAUDE_MARKETPLACE.parents[1] / entry["source"]).resolve() == ROOT


def test_codex_marketplace_resolves_to_the_repository_root():
    marketplace = _json(CODEX_MARKETPLACE)
    (entry,) = marketplace["plugins"]
    assert marketplace["name"] == entry["name"] == NAME
    assert entry["source"] == {"source": "local", "path": "./"}
    assert (CODEX_MARKETPLACE.parents[2] / entry["source"]["path"]).resolve() == ROOT
    assert entry["policy"]["installation"] in {"AVAILABLE", "INSTALLED_BY_DEFAULT"}
    assert entry["policy"]["authentication"] in {"ON_INSTALL", "ON_USE"}
    assert entry["category"]
    assert "version" not in entry


def test_canonical_skill_frontmatter_names_the_plugin():
    text = CANONICAL_SKILL.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert match, "SKILL.md must open with YAML frontmatter"
    fields = dict(line.split(": ", 1) for line in match.group(1).splitlines())
    assert fields["name"] == NAME
    assert fields["description"].strip()
    assert f"{NAME}=={_pyproject_field('version')}" in text, "runner pin must match the release"


def test_exactly_one_skill_file_in_the_tree():
    """Every manifest resolves the root; a second SKILL.md would be a driftable fork."""
    found = [
        path.relative_to(ROOT)
        for path in ROOT.rglob("SKILL.md")
        if not LOCAL_STATE.intersection(path.relative_to(ROOT).parts)
    ]
    assert found == [CANONICAL_SKILL.relative_to(ROOT)], found
    for extra in (ROOT / ".agents" / "skills", ROOT / ".claude" / "skills", ROOT / ".gemini"):
        assert not extra.exists(), f"{extra} would be a second skill surface"


def test_documented_gemini_install_pins_a_ref():
    """v0.2.0 predates gemini-extension.json, so an unpinned install takes that release and fails."""
    pattern = re.compile(
        r"gemini extensions install https://github\.com/hermes-labs-ai/hermes-jailbench[^\n`]*"
    )
    for doc in (ROOT / "README.md", ROOT / "llms.txt"):
        commands = pattern.findall(doc.read_text(encoding="utf-8"))
        assert commands, f"{doc.name} no longer documents the Gemini install"
        for command in commands:
            assert "--ref " in command, f"{doc.name}: {command!r} must pass --ref"


def _package(tmp_path: Path) -> Path:
    pkg = tmp_path / NAME
    pkg.mkdir()
    for rel in ("plugin.json", "gemini-extension.json"):
        shutil.copy2(ROOT / rel, pkg / rel)
    for rel in (".agents", ".claude-plugin", "skills"):
        shutil.copytree(ROOT / rel, pkg / rel)
    return pkg


def _run(argv: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, capture_output=True, text=True, check=False, env=env, timeout=120)


@pytest.mark.skipif(shutil.which("codex") is None, reason="codex CLI not installed")
def test_codex_marketplace_install_reads_back_the_skill(tmp_path):
    pkg = _package(tmp_path)
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    env = {
        "HOME": str(home),
        "CODEX_HOME": str(home / ".codex"),
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
    }
    add = _run(["codex", "plugin", "marketplace", "add", str(pkg)], env)
    assert add.returncode == 0, f"{add.stdout}\n{add.stderr}"
    install = _run(["codex", "plugin", "add", f"{NAME}@{NAME}"], env)
    assert install.returncode == 0, f"{install.stdout}\n{install.stderr}"
    version = _pyproject_field("version")
    cached = (
        home / ".codex" / "plugins" / "cache" / NAME / NAME / version / "skills" / NAME / "SKILL.md"
    )
    assert cached.read_bytes() == CANONICAL_SKILL.read_bytes()


@pytest.mark.skipif(shutil.which("gemini") is None, reason="gemini CLI not installed")
def test_gemini_extension_install_discovers_the_skill(tmp_path):
    pkg = _package(tmp_path)
    home = tmp_path / "home"
    (home / ".gemini").mkdir(parents=True)
    (home / ".gemini" / "settings.json").write_text(
        '{"security":{"auth":{"selectedType":"gemini-api-key"}}}', encoding="utf-8"
    )
    env = {
        "HOME": str(home),
        "GEMINI_API_KEY": "placeholder-not-a-key",
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
    }
    install = _run(["gemini", "extensions", "install", str(pkg), "--consent"], env)
    assert install.returncode == 0, f"{install.stdout}\n{install.stderr}"
    installed = home / ".gemini" / "extensions" / NAME / "skills" / NAME / "SKILL.md"
    assert installed.read_bytes() == CANONICAL_SKILL.read_bytes()
