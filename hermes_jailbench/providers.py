"""
Target endpoints the benchmark can run against.

Two providers are supported:

``anthropic``
    The Anthropic SDK, imported lazily in :mod:`hermes_jailbench.runner` so a
    dry run still works without it installed. Unchanged behaviour.

``openai-compat``
    Any endpoint that speaks the OpenAI ``POST /v1/chat/completions`` shape:
    Ollama, vLLM, LM Studio, OpenRouter, llama.cpp's server, OpenAI itself.
    Implemented here on the standard library alone (``urllib.request``), so
    scoring a local model adds no dependency to the package.

The client raises :class:`ProviderError` subclasses that carry an explicit
``retryable`` flag. ``runner._is_retryable_error`` reads that flag, so the
retry and backoff policy is the same for both providers without the runner
importing anything from this module's exception hierarchy.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

logger = logging.getLogger(__name__)

PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_OPENAI_COMPAT = "openai-compat"

#: Every provider name accepted by ``--provider`` and ``run_bench(provider=...)``.
PROVIDERS: tuple[str, ...] = (PROVIDER_ANTHROPIC, PROVIDER_OPENAI_COMPAT)

#: Seconds to wait for a single completion before giving up on it.
DEFAULT_TIMEOUT_SECONDS = 120.0

_CHAT_COMPLETIONS_PATH = "/chat/completions"


class ProviderError(Exception):
    """An error raised while talking to a target endpoint.

    ``retryable`` tells the runner whether backing off could help. It is read
    with ``getattr`` rather than an isinstance check, so the runner keeps
    working for any caller-supplied client that sets the same attribute.
    """

    retryable: bool = False
    status_code: Optional[int] = None


class ProviderConnectionError(ProviderError):
    """The endpoint could not be reached, or did not answer in time."""

    retryable = True


class ProviderHTTPError(ProviderError):
    """The endpoint answered with a non-2xx status."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code
        # 429 and 5xx are transient; 4xx is a configuration or credential fault
        # that will fail again identically, so it is surfaced immediately.
        self.retryable = status_code == 429 or status_code >= 500


class ProviderResponseError(ProviderError):
    """The endpoint answered 2xx with a body the runner cannot score."""

    retryable = False


def normalize_base_url(base_url: str) -> str:
    """
    Return the full chat-completions URL for a user-supplied base URL.

    Accepts what people actually paste:

    >>> normalize_base_url("http://localhost:11434/v1")
    'http://localhost:11434/v1/chat/completions'
    >>> normalize_base_url("http://localhost:11434")
    'http://localhost:11434/v1/chat/completions'
    >>> normalize_base_url("https://openrouter.ai/api/v1/chat/completions")
    'https://openrouter.ai/api/v1/chat/completions'

    A bare host gets ``/v1`` because every OpenAI-compatible server mounts the
    route there; a base URL that already names the route is left alone.

    Raises:
        ValueError: If the URL is empty, has no host, or is not http(s).
    """
    candidate = (base_url or "").strip()
    if not candidate:
        raise ValueError("base_url is required for the 'openai-compat' provider")

    parsed = urllib.parse.urlsplit(candidate)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            f"base_url {base_url!r} must start with http:// or https:// "
            "(for example http://localhost:11434/v1)"
        )
    if not parsed.netloc:
        raise ValueError(f"base_url {base_url!r} names no host")

    path = parsed.path.rstrip("/")
    if path.endswith(_CHAT_COMPLETIONS_PATH):
        pass
    elif not path:
        path = "/v1" + _CHAT_COMPLETIONS_PATH
    else:
        path = path + _CHAT_COMPLETIONS_PATH

    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def redact_url(url: Optional[str]) -> Optional[str]:
    """
    Return ``url`` with any userinfo credential replaced by ``***``.

    A base URL may legitimately carry a credential in its userinfo component
    (``https://user:key@gateway/v1``). That credential must never reach a place
    the run is expected to publish: the JSON artifact a CI job uploads, the
    markdown report, the console header, or an error message in a build log.
    The URL is redacted everywhere it is *shown or recorded*; what is sent on
    the wire is unchanged.

    >>> redact_url("https://user:sk-secret@gateway.example/v1")
    'https://***@gateway.example/v1'
    >>> redact_url("http://localhost:11434/v1")
    'http://localhost:11434/v1'

    A URL that cannot be parsed is reported as ``<unparseable base_url>``
    rather than echoed, because an unparseable string may still hold a secret.
    """
    if not url:
        return url
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return "<unparseable base_url>"
    if parsed.username is None and parsed.password is None:
        return url
    host = parsed.hostname or ""
    if ":" in host:  # IPv6 literal
        host = f"[{host}]"
    netloc = f"***@{host}"
    if parsed.port is not None:
        netloc = f"{netloc}:{parsed.port}"
    return urllib.parse.urlunsplit(
        (parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment)
    )


def completion_text(payload: Any) -> str:
    """
    Return the assistant text of a chat-completions response body.

    Handles both content shapes in the wild: a plain string, and the list of
    typed parts that some gateways return. An empty string is a valid answer —
    silence is scored, not treated as an error — so only a missing or unreadable
    content field raises.

    Raises:
        ProviderResponseError: The body carries no readable assistant text. A
            response the endpoint's own safety filter stopped
            (``finish_reason == "content_filter"``) is reported as a provider
            refusal so an auditor can tell it apart from a malformed reply.
            Neither is retried: the reply arrived, it just cannot be scored.
    """
    if not isinstance(payload, dict):
        raise ProviderResponseError(
            f"malformed response: expected a JSON object, got {type(payload).__name__}"
        )

    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        error = payload.get("error")
        if isinstance(error, dict) and error.get("message"):
            raise ProviderResponseError(f"endpoint returned an error: {error['message']}")
        raise ProviderResponseError("malformed response: body carries no choices")

    choice = choices[0] if isinstance(choices[0], dict) else {}
    message = choice.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    finish_reason = choice.get("finish_reason")

    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            part["text"]
            for part in content
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        ]
        if parts:
            return "".join(parts)

    if finish_reason == "content_filter":
        raise ProviderResponseError(
            "provider refusal: the endpoint's content filter stopped the reply before any "
            "text was produced (finish_reason=content_filter); not scored"
        )
    suffix = f" (finish_reason={finish_reason})" if finish_reason else ""
    raise ProviderResponseError(f"malformed response: no assistant text in choices[0]{suffix}")


class OpenAICompatClient:
    """
    Minimal ``POST /v1/chat/completions`` client built on the standard library.

    One request per attack, no streaming, no session reuse — the benchmark
    already paces itself with ``--delay`` and the runner owns retries.
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.url = normalize_base_url(base_url)
        #: The same URL with any userinfo credential redacted. Every message
        #: this client raises names ``display_url``, never ``url``, so a
        #: credential pasted into --base-url cannot reach a CI log.
        self.display_url = redact_url(self.url) or self.url
        self.api_key = api_key or None
        self.timeout = timeout

    def complete(self, model: str, max_tokens: int, prompt: str) -> str:
        """
        Send one user turn and return the assistant text.

        Raises:
            ProviderError: Connection failure, non-2xx status, or a body with
                no readable assistant text.
        """
        body = json.dumps(
            {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            }
        ).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        request = urllib.request.Request(self.url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raise ProviderHTTPError(
                f"HTTP {exc.code} from {self.display_url}: {_error_detail(exc)}",
                status_code=exc.code,
            ) from exc
        except urllib.error.URLError as exc:
            raise ProviderConnectionError(
                f"could not reach {self.display_url}: {exc.reason}"
            ) from exc
        except TimeoutError as exc:
            raise ProviderConnectionError(
                f"no reply from {self.display_url} within {self.timeout:g}s"
            ) from exc
        except OSError as exc:
            raise ProviderConnectionError(f"could not reach {self.display_url}: {exc}") from exc

        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProviderResponseError(
                f"malformed response: {self.display_url} did not return JSON ({exc})"
            ) from exc

        return completion_text(payload)


def _error_detail(exc: urllib.error.HTTPError) -> str:
    """Return the endpoint's own error message, or its reason, for an HTTPError."""
    try:
        payload = json.loads(exc.read().decode("utf-8"))
    except Exception:
        return str(exc.reason)
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict) and error.get("message"):
            return str(error["message"])
        if isinstance(error, str):
            return error
        if payload.get("message"):
            return str(payload["message"])
    return str(exc.reason)
