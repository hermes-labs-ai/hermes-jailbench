"""
The openai-compat provider: URL handling, response reading, and a real
end-to-end run through the loopback mock target.

Nothing here touches the network beyond 127.0.0.1, and no API key is used.
"""

from __future__ import annotations

import json

import pytest

from hermes_jailbench.attacks import ExpectedResult
from hermes_jailbench.cli import EXIT_GATE_FAILED, EXIT_GATE_PASSED, evaluate_gate, main
from hermes_jailbench.mock_target import serve
from hermes_jailbench.providers import (
    PROVIDER_ANTHROPIC,
    PROVIDER_OPENAI_COMPAT,
    PROVIDERS,
    OpenAICompatClient,
    ProviderHTTPError,
    ProviderResponseError,
    completion_text,
    normalize_base_url,
    redact_url,
)
from hermes_jailbench.runner import run_bench

ONE_ATTACK = ["DAN Classic"]


# ---------------------------------------------------------------------------
# base URL handling
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "given,expected",
    [
        ("http://localhost:11434/v1", "http://localhost:11434/v1/chat/completions"),
        ("http://localhost:11434/v1/", "http://localhost:11434/v1/chat/completions"),
        ("http://localhost:11434", "http://localhost:11434/v1/chat/completions"),
        ("http://localhost:11434/", "http://localhost:11434/v1/chat/completions"),
        ("https://openrouter.ai/api/v1", "https://openrouter.ai/api/v1/chat/completions"),
        (
            "https://openrouter.ai/api/v1/chat/completions",
            "https://openrouter.ai/api/v1/chat/completions",
        ),
    ],
)
def test_base_url_resolves_to_the_chat_completions_route(given: str, expected: str) -> None:
    """A bare host gets /v1; a URL that already names the route is left alone."""
    assert normalize_base_url(given) == expected


@pytest.mark.parametrize(
    "given", ["", "   ", "localhost:11434", "ftp://localhost/v1", "http://", "https:///v1"]
)
def test_unusable_base_url_is_rejected_with_a_readable_error(given: str) -> None:
    with pytest.raises(ValueError):
        normalize_base_url(given)


# ---------------------------------------------------------------------------
# response reading
# ---------------------------------------------------------------------------


def _body(content: object, finish_reason: str = "stop") -> dict:
    return {
        "choices": [
            {"message": {"role": "assistant", "content": content}, "finish_reason": finish_reason}
        ]
    }


def test_plain_string_content_is_the_reply() -> None:
    assert completion_text(_body("I cannot help with that.")) == "I cannot help with that."


def test_typed_content_parts_are_joined_in_order() -> None:
    parts = [{"type": "text", "text": "I cannot "}, {"type": "text", "text": "help."}]
    assert completion_text(_body(parts)) == "I cannot help."


def test_reasoning_only_parts_without_text_are_not_a_reply() -> None:
    """A gateway that returns only a reasoning part gave us nothing to score."""
    with pytest.raises(ProviderResponseError, match="no assistant text"):
        completion_text(_body([{"type": "reasoning", "reasoning": "thinking..."}]))


def test_empty_string_content_is_scored_not_an_error() -> None:
    """Silence is a verdict (PARTIAL), not a transport failure — same as the SDK path."""
    assert completion_text(_body("")) == ""


def test_content_filter_is_reported_as_a_provider_refusal() -> None:
    with pytest.raises(ProviderResponseError, match="provider refusal"):
        completion_text(_body(None, finish_reason="content_filter"))


def test_body_without_choices_reports_the_endpoints_own_error() -> None:
    with pytest.raises(ProviderResponseError, match="model 'nope' not found"):
        completion_text({"error": {"message": "model 'nope' not found"}})


def test_non_object_body_is_malformed() -> None:
    with pytest.raises(ProviderResponseError, match="malformed response"):
        completion_text(["not", "an", "object"])


# ---------------------------------------------------------------------------
# client behaviour against the loopback mock
# ---------------------------------------------------------------------------


def test_no_api_key_sends_no_authorization_header() -> None:
    """A local Ollama needs no credential, and none is invented for it."""
    with serve() as target:
        client = OpenAICompatClient(base_url=f"{target.base_url}/v1")
        assert "step 1" in client.complete("mock-complies", 64, "hi").lower()
        assert target.requests[0].authorization_header is None


def test_api_key_is_sent_as_a_bearer_token() -> None:
    with serve() as target:
        client = OpenAICompatClient(base_url=f"{target.base_url}/v1", api_key="sk-test")
        client.complete("mock-refuses", 64, "hi")
        assert target.requests[0].authorization_header == "Bearer sk-test"


def test_http_error_carries_the_status_and_the_endpoints_message() -> None:
    with serve() as target:
        client = OpenAICompatClient(base_url=f"{target.base_url}/v1")
        with pytest.raises(ProviderHTTPError) as exc_info:
            client.complete("mock-bad-request", 64, "hi")
        assert exc_info.value.status_code == 400
        assert exc_info.value.retryable is False
        assert "mock bad request" in str(exc_info.value)


def test_server_error_is_marked_retryable() -> None:
    with serve() as target:
        client = OpenAICompatClient(base_url=f"{target.base_url}/v1")
        with pytest.raises(ProviderHTTPError) as exc_info:
            client.complete("mock-server-error", 64, "hi")
        assert exc_info.value.status_code == 500
        assert exc_info.value.retryable is True


def test_unreachable_endpoint_is_a_connection_error_not_a_crash() -> None:
    # Port 1 on loopback: nothing listens there, and the refusal is immediate.
    client = OpenAICompatClient(base_url="http://127.0.0.1:1/v1", timeout=5.0)
    with pytest.raises(Exception) as exc_info:
        client.complete("mock-refuses", 64, "hi")
    assert getattr(exc_info.value, "retryable", None) is True


# ---------------------------------------------------------------------------
# run_bench end to end over the openai-compat provider
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "model,verdict",
    [
        ("mock-refuses", ExpectedResult.REFUSED),
        ("mock-complies", ExpectedResult.COMPLIED),
        ("mock-hedges", ExpectedResult.PARTIAL),
    ],
)
def test_openai_compat_run_scores_the_same_verdicts_as_the_sdk_path(
    model: str, verdict: ExpectedResult
) -> None:
    with serve() as target:
        result = run_bench(
            model=model,
            provider=PROVIDER_OPENAI_COMPAT,
            base_url=f"{target.base_url}/v1",
            attack_names=ONE_ATTACK,
            delay_seconds=0.0,
        )

    assert result.error_count == 0
    assert result.attacks[0].score is not None
    assert result.attacks[0].score.verdict is verdict
    assert result.provider == PROVIDER_OPENAI_COMPAT
    assert result.base_url == f"{target.base_url}/v1"
    assert target.requests[0].path.endswith("/v1/chat/completions")


def test_the_rendered_attack_prompt_reaches_the_endpoint() -> None:
    with serve() as target:
        run_bench(
            model="mock-refuses",
            provider=PROVIDER_OPENAI_COMPAT,
            base_url=f"{target.base_url}/v1",
            attack_names=ONE_ATTACK,
            target_payload="do the forbidden thing",
            delay_seconds=0.0,
        )

    assert "do the forbidden thing" in target.requests[0].prompt


def test_a_filtered_reply_is_an_error_and_fails_the_gate_rather_than_passing_it() -> None:
    """
    A reply the endpoint's own filter stopped carries no text to score. It is an
    ERROR, so the gate reports "not evaluated" instead of counting a free refusal.
    """
    with serve() as target:
        result = run_bench(
            model="mock-filtered",
            provider=PROVIDER_OPENAI_COMPAT,
            base_url=f"{target.base_url}/v1",
            attack_names=ONE_ATTACK,
            delay_seconds=0.0,
            max_retries=0,
        )

    assert result.error_count == 1
    assert result.refused_count == 0
    assert "provider refusal" in (result.attacks[0].error or "")
    assert evaluate_gate(result, 0.0)[0] not in (EXIT_GATE_PASSED, EXIT_GATE_FAILED)


def test_a_malformed_reply_is_an_error_and_is_not_retried() -> None:
    with serve() as target:
        result = run_bench(
            model="mock-malformed",
            provider=PROVIDER_OPENAI_COMPAT,
            base_url=f"{target.base_url}/v1",
            attack_names=ONE_ATTACK,
            delay_seconds=0.0,
            max_retries=3,
        )
        assert len(target.requests) == 1, "a reply that arrived is never retried"

    assert result.error_count == 1
    assert "malformed response" in (result.attacks[0].error or "")


def test_a_4xx_is_not_retried_but_a_5xx_is() -> None:
    with serve() as target:
        base = f"{target.base_url}/v1"
        run_bench(
            model="mock-bad-request",
            provider=PROVIDER_OPENAI_COMPAT,
            base_url=base,
            attack_names=ONE_ATTACK,
            delay_seconds=0.0,
            max_retries=2,
        )
        assert len(target.requests) == 1

        target.requests.clear()
        run_bench(
            model="mock-server-error",
            provider=PROVIDER_OPENAI_COMPAT,
            base_url=base,
            attack_names=ONE_ATTACK,
            delay_seconds=0.0,
            max_retries=2,
            retry_base_delay=0.0,
        )
        assert len(target.requests) == 3, "initial attempt plus two retries"


# ---------------------------------------------------------------------------
# configuration errors
# ---------------------------------------------------------------------------


def test_unknown_provider_is_rejected_before_any_attack_runs() -> None:
    with pytest.raises(ValueError, match="unknown provider"):
        run_bench(provider="openai", dry_run=True, attack_names=ONE_ATTACK)


def test_openai_compat_without_a_base_url_is_rejected() -> None:
    with pytest.raises(ValueError, match="base_url is required"):
        run_bench(
            model="llama3.2",
            provider=PROVIDER_OPENAI_COMPAT,
            attack_names=ONE_ATTACK,
            delay_seconds=0.0,
        )


def test_a_dry_run_needs_no_endpoint_and_no_key(capsys) -> None:
    """--dry-run is unchanged by the new flags: it renders prompts and stops."""
    result = run_bench(
        model="llama3.2",
        provider=PROVIDER_OPENAI_COMPAT,
        dry_run=True,
        attack_names=ONE_ATTACK,
    )
    assert result.attacks[0].dry_run is True
    assert result.attacks[0].response is None


def test_providers_tuple_is_the_cli_choice_list() -> None:
    assert PROVIDERS == (PROVIDER_ANTHROPIC, PROVIDER_OPENAI_COMPAT)


# ---------------------------------------------------------------------------
# the CLI wiring
# ---------------------------------------------------------------------------


def test_cli_runs_the_openai_compat_provider_end_to_end(capsys, monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with serve() as target:
        main(
            [
                "--provider",
                "openai-compat",
                "--base-url",
                f"{target.base_url}/v1",
                "--model",
                "mock-refuses",
                "--attacks",
                "DAN Classic",
                "--delay",
                "0",
                "--format",
                "json",
            ]
        )
    out = capsys.readouterr().out
    assert "Provider: openai-compat" in out
    assert "REFUSED" in out
    report = json.loads(out[out.index("{") : out.rindex("}") + 1])
    assert report["model"] == "mock-refuses"


def test_cli_requires_a_model_for_openai_compat(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--provider", "openai-compat", "--base-url", "http://127.0.0.1:1/v1"])
    assert exc_info.value.code == 2
    assert "--model is required" in capsys.readouterr().err


def test_cli_requires_a_base_url_for_a_live_openai_compat_run(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--provider", "openai-compat", "--model", "llama3.2"])
    assert exc_info.value.code == 2
    assert "--base-url is required" in capsys.readouterr().err


def test_cli_needs_no_anthropic_key_for_an_openai_compat_run(capsys, monkeypatch) -> None:
    """The Anthropic key check must not fire for a provider that does not use it."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with serve() as target:
        main(
            [
                "--provider",
                "openai-compat",
                "--base-url",
                f"{target.base_url}/v1",
                "--model",
                "mock-complies",
                "--attacks",
                "DAN Classic",
                "--delay",
                "0",
            ]
        )
        assert target.requests[0].authorization_header is None
    assert "No API key provided" not in capsys.readouterr().err


def test_cli_reports_an_unusable_base_url_as_a_configuration_error(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "--provider",
                "openai-compat",
                "--base-url",
                "not-a-url",
                "--model",
                "llama3.2",
                "--attacks",
                "DAN Classic",
                "--delay",
                "0",
            ]
        )
    assert exc_info.value.code == 2
    assert "must start with http" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# a credential pasted into --base-url must not reach the artifact or the log
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://user:sk-secret@gateway.example/v1", "https://***@gateway.example/v1"),
        ("https://sk-secret@gateway.example/v1", "https://***@gateway.example/v1"),
        ("http://u:p@127.0.0.1:8000/v1", "http://***@127.0.0.1:8000/v1"),
        ("http://localhost:11434/v1", "http://localhost:11434/v1"),
        ("", ""),
        (None, None),
        # urlsplit() accepts this; SplitResult.port raises on read. Redaction
        # must not let that ValueError escape with the URL in the traceback.
        ("https://user:secret@example.test:not-a-port/v1", "<unparseable base_url>"),
    ],
)
def test_redact_url_strips_userinfo_and_leaves_everything_else(url, expected) -> None:
    assert redact_url(url) == expected


def test_client_error_messages_name_the_redacted_url() -> None:
    """A connection failure is logged; the message must not carry the secret."""
    client = OpenAICompatClient(base_url="http://user:sk-secret@127.0.0.1:1/v1")

    assert "sk-secret" not in client.display_url
    with pytest.raises(Exception) as exc_info:
        client.complete(model="x", max_tokens=8, prompt="hi")
    assert "sk-secret" not in str(exc_info.value)


def test_bench_result_records_the_base_url_redacted() -> None:
    """The JSON report is committed as a baseline and uploaded from CI."""
    result = run_bench(
        provider=PROVIDER_OPENAI_COMPAT,
        base_url="https://user:sk-secret@gateway.example/v1",
        model="llama3.2",
        attack_names=ONE_ATTACK,
        dry_run=True,
        delay_seconds=0,
    )

    assert result.base_url == "https://***@gateway.example/v1"
    assert "sk-secret" not in json.dumps(result.base_url)
