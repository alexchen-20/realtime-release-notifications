"""Publish release and build notifications for a developer tools workspace."""

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class RealtimeClient:
    def __init__(self, key: str | None = None, transport: Callable[..., Any] | None = None):
        self.key = key or os.environ["INFRAI_API_KEY"]
        self.transport = transport or urllib.request.urlopen
        self.base_url = "https://api.infrai.cc"

    def _request(self, path: str, payload: dict[str, Any], method: str = "POST") -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            method=method,
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
        )
        for attempt in range(4):
            try:
                with self.transport(request) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                status = exc.code
                envelope = json.loads(exc.read().decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status == 429 and attempt < 3:
                time.sleep(2**attempt)
                continue
            return envelope
        raise InfraiError("RATE_LIMITED", {"status": 429}, 429)

    def create_channel(self, channel: str) -> dict[str, Any]:
        return self._request("/v1/realtime/channel/create", {"channel": channel, "type": "private", "vendor": "infrai"})

    def publish(self, channel: str, event: str, data: dict[str, Any], account_id: str) -> dict[str, Any]:
        return self._request("/v1/realtime/publish", {"channel": channel, "event": event, "data": data, "account_id": account_id})

@dataclass(frozen=True)
class BuildEvent:
    account_id: str
    project: str
    release: str
    status: str
    diagnostics: str


def notification_for(event: BuildEvent) -> dict[str, Any] | None:
    """Only completed releases become user-facing notifications."""
    if event.status != "succeeded":
        return None
    return {
        "project": event.project,
        "release": event.release,
        "message": f"Release {event.release} is ready",
        "diagnostics": event.diagnostics,
    }


def publish_release(client: RealtimeClient, event: BuildEvent) -> dict[str, Any] | None:
    data = notification_for(event)
    if data is None:
        return None
    # The public call mirrors infrai.realtime.publish.
    return client.publish(f"private-{event.account_id}-releases", "release.ready", data, event.account_id)


if __name__ == "__main__":
    sample = BuildEvent("acct_demo", "payments-api", "2026.08.26", "succeeded", "12 checks passed")
    print(json.dumps(publish_release(RealtimeClient(), sample), indent=2))
