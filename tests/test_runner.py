"""
Regression tests for hermes_jailbench.runner.run_bench().

No live network calls — anthropic.Anthropic is monkeypatched with a fake
client so these stay fully offline and deterministic.
"""

import anthropic

from hermes_jailbench.attacks import ExpectedResult
from hermes_jailbench.runner import run_bench


class _FakeContent:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeMessage:
    def __init__(self, text: str) -> None:
        self.content = [_FakeContent(text)]


class _FakeMessages:
    def __init__(self, text: str) -> None:
        self._text = text

    def create(self, **kwargs):
        return _FakeMessage(self._text)


class _FakeClient:
    """Stand-in for anthropic.Anthropic that always returns a fixed response text."""

    def __init__(self, response_text: str = "") -> None:
        self.messages = _FakeMessages(response_text)

    def __call__(self, api_key=None):
        return self


def test_empty_but_successful_response_is_scored_and_tallied(monkeypatch) -> None:
    """
    A successful API call that returns an empty string is not an error — the
    scorer explicitly treats "" as valid input and defaults it to REFUSED.
    The attack's tally bucket must therefore account for it: refused + partial
    + complied + error must equal total_attacks, and the result must carry a
    score rather than silently vanishing from the aggregate counts.
    """
    monkeypatch.setattr(anthropic, "Anthropic", _FakeClient(""))

    result = run_bench(
        attack_names=["DAN Classic"],
        api_key="test-key",
        delay_seconds=0.0,
    )

    assert len(result.attacks) == 1
    ar = result.attacks[0]

    assert ar.error is None
    assert ar.response == ""
    assert ar.score is not None
    assert ar.score.verdict == ExpectedResult.REFUSED

    tallied = (
        result.refused_count
        + result.partial_count
        + result.complied_count
        + result.error_count
    )
    assert tallied == result.total_attacks
