"""Keep CodeMeta aligned with the package and citation metadata."""

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
    """CodeMeta uses stable identifiers and the packaged release coordinates."""
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    citation = (REPO_ROOT / "CITATION.cff").read_text(encoding="utf-8")
    codemeta = json.loads((REPO_ROOT / "codemeta.json").read_text(encoding="utf-8"))

    package_name = _required_match(r'^name\s*=\s*"([^"]+)"$', pyproject, "pyproject.toml")
    package_version = _required_match(r'^version\s*=\s*"([^"]+)"$', pyproject, "pyproject.toml")
    project_repository = _required_match(
        r'^Repository\s*=\s*"([^"]+)"$', pyproject, "pyproject.toml"
    )
    citation_version = _required_match(r'^version:\s*["\']?([^"\'\s]+)', citation, "CITATION.cff")
    citation_repository = _required_match(
        r'^repository-code:\s*["\']?([^"\'\s]+)', citation, "CITATION.cff"
    )
    citation_orcid = _required_match(r'^\s+orcid:\s*["\']?([^"\'\s]+)', citation, "CITATION.cff")
    release_url = f"https://pypi.org/project/{package_name}/{package_version}/"
    software_doi = "https://doi.org/10.5281/zenodo.21795796"

    assert codemeta["@context"] == "https://w3id.org/codemeta/3.1"
    assert codemeta["@type"] == "SoftwareSourceCode"
    assert codemeta["name"] == package_name
    assert codemeta["version"] == package_version == citation_version
    assert codemeta["codeRepository"] == project_repository == citation_repository
    assert codemeta["url"] == release_url
    assert release_url in codemeta["identifier"]
    assert software_doi in codemeta["identifier"]
    assert codemeta["author"][0]["@id"] == citation_orcid
    assert "dateModified" not in codemeta
