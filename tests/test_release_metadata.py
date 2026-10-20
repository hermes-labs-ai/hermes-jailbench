"""Keep published-release citation metadata distinct from current source licensing."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _required_match(pattern: str, text: str, source: str) -> str:
    match = re.search(pattern, text, flags=re.MULTILINE)
    assert match, f"could not locate required field in {source}"
    return match.group(1)


def test_codemeta_matches_release_metadata() -> None:
    """The immutable 0.2.2 distribution remains MIT after main adopted Apache."""
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    citation = (REPO_ROOT / "CITATION.cff").read_text(encoding="utf-8")
    codemeta = json.loads((REPO_ROOT / "codemeta.json").read_text(encoding="utf-8"))

    package_name = _required_match(r'^name\s*=\s*"([^"]+)"$', pyproject, "pyproject.toml")
    release_version = "0.2.2"
    project_repository = _required_match(
        r'^Repository\s*=\s*"([^"]+)"$', pyproject, "pyproject.toml"
    )
    citation_version = _required_match(r'^version:\s*["\']?([^"\'\s]+)', citation, "CITATION.cff")
    citation_repository = _required_match(
        r'^repository-code:\s*["\']?([^"\'\s]+)', citation, "CITATION.cff"
    )
    citation_url = _required_match(r'^url:\s*["\']?([^"\'\s]+)', citation, "CITATION.cff")
    citation_license = _required_match(r"^license:\s*([^\s]+)", citation, "CITATION.cff")
    citation_orcid = _required_match(r'^\s+orcid:\s*["\']?([^"\'\s]+)', citation, "CITATION.cff")
    release_url = f"https://pypi.org/project/{package_name}/{release_version}/"
    software_doi = "https://doi.org/10.5281/zenodo.21795796"

    assert codemeta["@context"] == "https://w3id.org/codemeta/3.1"
    assert codemeta["@type"] == "SoftwareSourceCode"
    assert codemeta["name"] == package_name
    assert codemeta["version"] == release_version == citation_version
    assert codemeta["codeRepository"] == project_repository
    assert citation_repository == f"{project_repository}/tree/v{release_version}"
    assert codemeta["url"] == citation_url == release_url
    assert codemeta["license"] == "https://spdx.org/licenses/MIT"
    assert citation_license == "MIT"
    assert f"published hermes-jailbench {release_version} release" in citation
    assert set(codemeta["identifier"]) == {software_doi, release_url}
    assert not re.search(r"^doi:", citation, flags=re.MULTILINE)
    assert codemeta["author"][0]["@id"] == citation_orcid
    assert "dateModified" not in codemeta


def test_zenodo_template_uses_current_source_license_without_naming_a_release() -> None:
    """A future archive uses its release tag rather than reusing 0.2.2's identity."""
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    zenodo = json.loads((REPO_ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    source_license = _required_match(r'^license\s*=\s*"([^"]+)"$', pyproject, "pyproject.toml")

    assert zenodo["license"] == source_license == "Apache-2.0"
    assert "version" not in zenodo
