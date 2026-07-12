from __future__ import annotations

import httpx

from power_web_os.signal_monitoring_live_demo import _get_with_transport_retries


class _FlakyClient:
    def __init__(self) -> None:
        self.calls = 0

    def get(self, path: str) -> httpx.Response:
        self.calls += 1
        if self.calls < 3:
            raise httpx.RemoteProtocolError("recorded disconnect")
        return httpx.Response(200, request=httpx.Request("GET", f"http://test{path}"))


def test_signal_monitoring_report_read_retries_transient_transport_disconnect() -> None:
    client = _FlakyClient()

    response = _get_with_transport_retries(client, "/report", attempts=3, delay_seconds=0)

    assert response.status_code == 200
    assert client.calls == 3
