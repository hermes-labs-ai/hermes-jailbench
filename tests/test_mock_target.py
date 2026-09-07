"""The loopback mock target: bound to 127.0.0.1, scripted by model name, validates nothing."""

from __future__ import annotations

import json
import urllib.request

from hermes_jailbench.mock_target import LOOPBACK, SCENARIOS, serve


def _post(base_url: str, model: str, api_key: str = "anything") -> tuple[int, dict]:
    body = json.dumps(
        {"model": model, "max_tokens": 8, "messages": [{"role": "user", "content": "hi"}]}
    ).encode()
    request = urllib.request.Request(
        f"{base_url}/v1/messages",
        data=body,
        headers={"Content-Type": "application/json", "x-api-key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def test_mock_binds_to_loopback_only_on_an_ephemeral_port() -> None:
    with serve() as target:
        assert target.base_url.startswith(f"http://{LOOPBACK}:")
        assert int(target.base_url.rsplit(":", 1)[1]) > 0


def test_every_scenario_answers_as_documented() -> None:
    with serve() as target:
        status, body = _post(target.base_url, "mock-refuses")
        assert status == 200 and "can't" in body["content"][0]["text"].lower()
        status, body = _post(target.base_url, "mock-complies")
        assert status == 200 and "step 1" in body["content"][0]["text"].lower()
        status, body = _post(target.base_url, "mock-hedges")
        assert status == 200 and "hypothetically" in body["content"][0]["text"].lower()
        status, body = _post(target.base_url, "mock-malformed")
        assert status == 200 and body["content"] == []
        status, body = _post(target.base_url, "mock-server-error")
        assert status == 500 and body["type"] == "error"
        status, body = _post(target.base_url, "mock-bad-request")
        assert status == 400 and body["error"]["type"] == "invalid_request_error"
        status, body = _post(target.base_url, "mock-does-not-exist")
        assert status == 400 and "unknown mock model" in body["error"]["message"]
        assert len(target.requests) == 7
        assert set(SCENARIOS) >= {r.model for r in target.requests} - {"mock-does-not-exist"}


def test_mock_records_the_key_header_and_validates_nothing() -> None:
    with serve() as target:
        status, _ = _post(target.base_url, "mock-refuses", api_key="")
        assert status == 200, "an empty key is accepted: nothing is validated"
        status, _ = _post(target.base_url, "mock-refuses", api_key="literally-anything")
        assert status == 200
        assert [r.api_key_header for r in target.requests] == ["", "literally-anything"]


def test_unknown_path_is_a_404_not_a_verdict() -> None:
    with serve() as target:
        request = urllib.request.Request(
            f"{target.base_url}/v1/complete", data=b"{}", method="POST"
        )
        try:
            urllib.request.urlopen(request, timeout=5)
            raise AssertionError("expected 404")
        except urllib.error.HTTPError as error:
            assert error.code == 404
