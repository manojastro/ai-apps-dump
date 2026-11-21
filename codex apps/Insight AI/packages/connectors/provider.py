"""OpenAI-compatible transport with explicit, server-owned destination policy."""

import ipaddress
import json
import os
import random
import socket
import time
from urllib.parse import urlparse

import httpx


def validate_endpoint(url, allowed_hosts, dev_hosts):
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if host not in allowed_hosts or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("PROVIDER_DESTINATION_DENIED")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and host in dev_hosts):
        raise ValueError("PROVIDER_DESTINATION_REQUIRES_HTTPS")
    try:
        addresses = {row[4][0] for row in socket.getaddrinfo(host, parsed.port or 443)}
    except OSError:
        raise ValueError("PROVIDER_DESTINATION_DNS_FAILED") from None
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if (
            ip.is_link_local
            or ip.is_multicast
            or ip.is_unspecified
            or (not ip.is_global and host not in dev_hosts)
        ):
            raise ValueError("PROVIDER_DESTINATION_DENIED")
    return url.rstrip("/")


class Provider:
    def __init__(self):
        self.key = os.environ.get("MODEL_API_KEY", "")
        self.model = os.environ.get("MODEL_ID", "")
        if not self.key or not self.model:
            raise ValueError("PROVIDER_NOT_CONFIGURED: set MODEL_API_KEY and MODEL_ID on the server")
        self.url = validate_endpoint(
            os.environ.get("MODEL_BASE_URL", "https://api.openai.com/v1"),
            set(os.environ.get("MODEL_ALLOWED_HOSTS", "api.openai.com").split(",")),
            set(filter(None, os.environ.get("MODEL_DEV_HOSTS", "").split(","))),
        )

    def complete(self, messages, tools=None, **kwargs):
        body = {"model": self.model, "messages": messages, "temperature": 0, "max_tokens": 1800, **kwargs}
        if tools:
            body["tools"] = tools
        for attempt in range(3):
            try:
                with httpx.Client(timeout=20, follow_redirects=False, trust_env=False) as client:
                    with client.stream(
                        "POST",
                        self.url + "/chat/completions",
                        headers={"Authorization": "Bearer " + self.key},
                        json=body,
                    ) as response:
                        if response.status_code in {429, 502, 503, 504} and attempt < 2:
                            time.sleep(0.2 * 2**attempt + random.random() * 0.15)
                            continue
                        if response.status_code != 200:
                            raise ValueError(f"PROVIDER_HTTP_{response.status_code}")
                        data = b""
                        for part in response.iter_bytes():
                            data += part
                            if len(data) > 131072:
                                raise ValueError("PROVIDER_RESPONSE_TOO_LARGE")
                        payload = json.loads(data)
                        if not isinstance(payload.get("choices"), list) or not payload["choices"]:
                            raise ValueError("PROVIDER_MALFORMED_RESPONSE")
                        return payload
            except httpx.TimeoutException:
                if attempt == 2:
                    raise ValueError("PROVIDER_TIMEOUT") from None
            except (httpx.HTTPError, json.JSONDecodeError):
                raise ValueError("PROVIDER_CONNECTION_OR_RESPONSE_ERROR") from None
        raise ValueError("PROVIDER_UNAVAILABLE")

    def test(self):
        function = {
            "type": "function",
            "function": {
                "name": "connection_probe",
                "description": "Verify tool-use support",
                "parameters": {
                    "type": "object",
                    "properties": {"ok": {"type": "boolean"}},
                    "required": ["ok"],
                    "additionalProperties": False,
                },
            },
        }
        result = self.complete(
            [{"role": "user", "content": "Call connection_probe with ok=true."}],
            [function],
            tool_choice={"type": "function", "function": {"name": "connection_probe"}},
        )
        calls = result["choices"][0]["message"].get("tool_calls", [])
        if not calls or calls[0]["function"]["name"] != "connection_probe":
            raise ValueError("PROVIDER_TOOL_USE_UNSUPPORTED")
        schema = {
            "type": "json_schema",
            "json_schema": {"name": "probe", "strict": True, "schema": function["function"]["parameters"]},
        }
        structured = self.complete(
            [{"role": "user", "content": 'Return {"ok":true}.'}], response_format=schema
        )
        try:
            assert json.loads(structured["choices"][0]["message"]["content"]) == {"ok": True}
        except (KeyError, ValueError, AssertionError):
            raise ValueError("PROVIDER_STRUCTURED_OUTPUT_UNSUPPORTED") from None
        return {
            "status": "connected",
            "tool_use": "verified",
            "structured_output": "verified",
            "model": self.model,
            "usage": [result.get("usage"), structured.get("usage")],
        }
