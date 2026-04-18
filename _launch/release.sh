#!/usr/bin/env bash
# jailbreak-bench v0.1.0 release commands. DO NOT auto-execute.
# Ordered list of things to do on the day you tag the release.
set -euo pipefail

# 0. Prerequisites (one-time, manual):
#    - Create PyPI project 'jailbreak-bench'. Reserve the name.
#    - Configure PyPI Trusted Publishing for the repo:
#        PyPI project -> Settings -> Publishing -> Add trusted publisher
#          repo:       roli-lpci/jailbreak-bench
#          workflow:   release.yml
#          environment: pypi
#    - In GitHub: Settings -> Environments -> New environment 'pypi'.
#
# The Trusted-Publishing path uses OIDC, no long-lived secrets.

# 1. Confirm CI is green, tests pass, ruff+mypy clean
pytest -q
python -m ruff check jailbreak_bench/ tests/
python -m mypy jailbreak_bench/ --ignore-missing-imports --no-strict-optional

# 2. Local build + twine check as a sanity gate
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*

# 3. Tag + push. The release.yml workflow fires on tag push.
git tag -a v0.1.0 -m "jailbreak-bench v0.1.0: initial public release"
git push origin v0.1.0

# 4. Watch the workflow. If publish fails but build succeeds, debug the trusted
#    publisher config - do NOT fall back to API tokens unless explicitly needed.
gh run watch --repo roli-lpci/jailbreak-bench

# 5. After PyPI publish lands:
#    - Verify on https://pypi.org/project/jailbreak-bench/
#    - Test `pip install jailbreak-bench` in a fresh venv on a clean machine
#    - Create a GitHub Release from the tag (gh release create v0.1.0 --generate-notes)
