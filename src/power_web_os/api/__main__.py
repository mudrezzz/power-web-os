"""Run the local API with uvicorn when the optional api extra is installed."""

from __future__ import annotations


def main() -> None:
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover - depends on optional extra.
        raise SystemExit(
            "Install API runtime dependencies first: python -m pip install -e \".[api,dev]\""
        ) from exc

    uvicorn.run("power_web_os.api.app:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
