from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from power_web_os.demo import build_icp_radar_catalog_from_workbook
from power_web_os.application.radar.lifecycle.output_summary_reconciliation import (
    RadarOutputSummaryReconciliationService,
)
from power_web_os.persistence.config import DatabaseSettings
from power_web_os.persistence.engine import create_database_engine, create_session_factory, session_scope
from power_web_os.persistence.repositories import SqlAlchemyRadarRunOutputRepository
from power_web_os.persistence.seed import seed_radar_catalog


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(prog="python -m power_web_os.persistence")
    parser.add_argument("command", choices=("seed-radars", "reconcile-radar-output-summaries"))
    parser.add_argument("--database-url", default=None)
    parser.add_argument(
        "--icp-radar-input",
        type=Path,
        default=root / "demo" / "fixtures" / "icp_radar" / "sibur_icp_pass1.xlsx",
    )
    args = parser.parse_args()

    settings = DatabaseSettings.from_env(database_url=args.database_url)
    engine = create_database_engine(settings)
    session_factory = create_session_factory(engine)
    with session_scope(session_factory) as session:
        if args.command == "seed-radars":
            catalog = build_icp_radar_catalog_from_workbook(args.icp_radar_input)
            payload = seed_radar_catalog(session, catalog).to_payload()
        else:
            payload = RadarOutputSummaryReconciliationService(
                SqlAlchemyRadarRunOutputRepository(session)
            ).reconcile().to_payload()

    print(json.dumps(payload, ensure_ascii=False, indent=2))
