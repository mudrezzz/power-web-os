"""CLI for Power Web discovery architecture acceptance."""

from __future__ import annotations

import argparse
from pathlib import Path

from power_web_os.application.radar.power_web_discovery.validation import PowerWebArchitectureValidator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m power_web_os.power_web_architecture_validation")
    parser.add_argument("--slice", required=True, dest="slice_id")
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    validator = PowerWebArchitectureValidator(root=args.root)
    validator.write_benchmark_schema()
    report = validator.validate(slice_id=args.slice_id)
    print(f"validation_status={report['validation_status']}")
    print(f"benchmark_status={report['benchmark_status']}")
    print(f"hh_api_calls={report['hh_public_web_probe']['hh_api_calls']}")
    return 0 if report["validation_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
