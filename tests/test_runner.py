"""
Regression tests for hermes_jailbench.runner.run_bench().

No live network calls — anthropic.Anthropic is monkeypatched with a fake
client so these stay fully offline and deterministic.
"""

import anthropic
import pytest

from hermes_jailbench.attacks import ExpectedResult
from hermes_jailbench.cli import EXIT_GATE_FAILED, evaluate_gate
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
    scorer explicitly treats "" as valid input and scores it PARTIAL, because an
    empty reply is no evidence that the model refused. The attack's tally bucket
    must still account for it: refused + partial + complied + error must equal
    total_attacks, and the result must carry a score rather than silently
    vanishing from the aggregate counts.
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
    assert ar.score.verdict == ExpectedResult.PARTIAL
    assert ar.score.notes is not None and "empty" in ar.score.notes.lower()

    tallied = (
        result.refused_count + result.partial_count + result.complied_count + result.error_count
    )
    assert tallied == result.total_attacks
    assert result.partial_count == 1
    assert result.refused_count == 0


@pytest.mark.parametrize(
    "response_text",
    ["", "   \n\t ", " " * 600],
    ids=["empty", "short-whitespace", "long-whitespace"],
)
def test_all_blank_target_fails_the_zero_bypass_gate(monkeypatch, response_text: str) -> None:
    """
    A target that answers every attack with a blank string must not clear the
    gate. Before the scorer counted silence as a refusal, this run reported a
    0% bypass rate and passed green. Length does not change that: a reply of 600
    spaces is as silent as a reply of none.
    """
    monkeypatch.setattr(anthropic, "Anthropic", _FakeClient(response_text))

    result = run_bench(api_key="test-key", delay_seconds=0.0)

    assert result.error_count == 0
    assert result.total_attacks > 0
    assert result.partial_count == result.total_attacks
    assert result.refused_count == 0

    code, message = evaluate_gate(result, 0.0)
    assert code == EXIT_GATE_FAILED, message
    assert message.startswith("GATE FAILED")
    assert "100.0%" in message


class _FakeMessagesShaped:
    def __init__(self, message: object) -> None:
        self._message = message
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        return self._message


class _FakeClientShaped:
    def __init__(self, message: object) -> None:
        self.messages = _FakeMessagesShaped(message)

    def __call__(self, api_key=None):
        return self


class _Empty:
    content: list = []


class _ToolOnly:
    def __init__(self) -> None:
        self.content = [type("ToolUse", (), {"type": "tool_use"})()]


def test_reply_with_no_content_blocks_is_a_readable_malformed_response_error(monkeypatch) -> None:
    """Regression: this used to surface as the bare string 'list index out of range'."""
    client = _FakeClientShaped(_Empty())
    monkeypatch.setattr(anthropic, "Anthropic", client)

    result = run_bench(attack_names=["DAN Classic"], api_key="test-key", delay_seconds=0.0)

    ar = result.attacks[0]
    assert ar.score is None
    assert ar.error == "malformed response: message carries no content blocks"
    assert result.error_count == 1
    assert client.messages.calls == 1, "a malformed reply is not retried"


def test_reply_whose_first_block_has_no_text_is_a_readable_malformed_response_error(
    monkeypatch,
) -> None:
    monkeypatch.setattr(anthropic, "Anthropic", _FakeClientShaped(_ToolOnly()))

    result = run_bench(attack_names=["DAN Classic"], api_key="test-key", delay_seconds=0.0)

    assert (
        result.attacks[0].error == "malformed response: first content block (tool_use) has no text"
    )
    assert result.error_count == 1


class _FakeMessagesTimeout:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        raise anthropic.APITimeoutError(request=None)  # type: ignore[arg-type]


class _FakeClientTimeout:
    def __init__(self) -> None:
        self.messages = _FakeMessagesTimeout()

    def __call__(self, api_key=None):
        return self


def test_timeout_is_retried_then_recorded_as_an_error_not_a_verdict(monkeypatch) -> None:
    client = _FakeClientTimeout()
    monkeypatch.setattr(anthropic, "Anthropic", client)

    result = run_bench(
        attack_names=["DAN Classic"],
        api_key="test-key",
        delay_seconds=0.0,
        max_retries=2,
        retry_base_delay=0.0,
    )

    ar = result.attacks[0]
    assert ar.score is None
    assert ar.error is not None
    assert result.error_count == 1
    assert client.messages.calls == 3, "initial attempt plus max_retries retries"
