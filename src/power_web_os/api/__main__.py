"""Run the local API with uvicorn when the optional api extra is installed."""

from __future__ import annotations

import os


def _api_port_from_env() -> int:
    value = os.getenv("POWER_WEB_OS_API_PORT", "").strip()
    if not value:
        return 8000
    try:
        port = int(value)
    except ValueError as exc:
        raise SystemExit("POWER_WEB_OS_API_PORT must be an integer.") from exc
    if not 0 < port < 65536:
        raise SystemExit("POWER_WEB_OS_API_PORT must be between 1 and 65535.")
    return port


def main() -> None:
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover - depends on optional extra.
        raise SystemExit(
            "Install API runtime dependencies first: python -m pip install -e \".[api,dev]\""
        ) from exc

    uvicorn.run("power_web_os.api.app:app", host="127.0.0.1", port=_api_port_from_env(), reload=True)


if __name__ == "__main__":
    main()
