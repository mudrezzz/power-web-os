from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from power_web_os.application.radar_records import RadarDefinitionRecord, RadarRecord, RadarRunRecord, RadarRunStatus
from power_web_os.demo import build_icp_radar_catalog_from_workbook
from power_web_os.persistence import (
    Base,
    SqlAlchemyRadarDefinitionRepository,
    SqlAlchemyRadarRepository,
    SqlAlchemyRadarRunRepository,
    create_database_engine,
    create_session_factory,
    session_scope,
)
from power_web_os.persistence.seed import seed_radar_catalog


def sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_radar_repositories_roundtrip_catalog_and_run_state(tmp_path: Path) -> None:
    engine = create_database_engine(database_url=sqlite_url(tmp_path / "radars.db"))
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_scope(session_factory) as session:
        radar_repo = SqlAlchemyRadarRepository(session)
        definition_repo = SqlAlchemyRadarDefinitionRepository(session)
        run_repo = SqlAlchemyRadarRunRepository(session)

        radar = radar_repo.upsert(
            RadarRecord(
                radar_id="toir-sibur",
                name="TOIR / SIBUR",
                status="configured",
                owner="Industrial ABM",
                profile={"segment": "industrial"},
                summary={"run_mode": "fixture"},
                artifact_path="/demo/icp_radar.json",
            )
        )
        definition = definition_repo.upsert(
            RadarDefinitionRecord(
                definition_id="radar-def-toir",
                radar_id=radar.radar_id,
                definition_payload={"definition_id": "radar-def-toir", "metadata": {"name": "TOIR"}},
                definition_version="0.7.1-test",
            )
        )
        run = run_repo.create(
            RadarRunRecord(
                run_id="run-1",
                radar_id=radar.radar_id,
                idempotency_key="radar:toir-sibur:2026-06-16",
                correlation_id="corr-1",
                run_metadata={"mode": "manual"},
            )
        )

        assert radar_repo.get("toir-sibur") == radar
        assert definition_repo.get_active("toir-sibur") == definition
        assert run_repo.find_by_idempotency_key("radar:toir-sibur:2026-06-16") == run

        running = run_repo.update_status("run-1", RadarRunStatus.RUNNING)
        completed = run_repo.update_status("run-1", RadarRunStatus.COMPLETED)

        assert running.status is RadarRunStatus.RUNNING
        assert running.started_at is not None
        assert completed.status is RadarRunStatus.COMPLETED
        assert completed.completed_at is not None
        assert run_repo.list_for_radar("toir-sibur") == (completed,)


def test_seed_radar_catalog_upserts_current_demo_radars(tmp_path: Path) -> None:
    engine = create_database_engine(database_url=sqlite_url(tmp_path / "seed.db"))
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    catalog = build_icp_radar_catalog_from_workbook(Path("demo/fixtures/icp_radar/sibur_icp_pass1.xlsx"))

    with session_scope(session_factory) as session:
        result = seed_radar_catalog(session, catalog)
        result_again = seed_radar_catalog(session, catalog)
        radars = SqlAlchemyRadarRepository(session).list()
        active_definition = SqlAlchemyRadarDefinitionRepository(session).get_active("toir-sibur")

    assert result.radar_count == len(catalog["radars"])
    assert result_again == result
    assert {radar.radar_id for radar in radars} >= {"toir-sibur", "toir-quick-live"}
    assert active_definition is not None
    assert active_definition.definition_payload["definition_id"] == "radar-def-toir-sibur"


def test_alembic_initial_migration_creates_radar_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "migration.db"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", sqlite_url(db_path))

    command.upgrade(config, "head")

    engine = create_database_engine(database_url=sqlite_url(db_path))
    table_names = set(inspect(engine).get_table_names())

    assert {"radars", "radar_definitions", "radar_runs", "alembic_version"} <= table_names


def test_alembic_respects_database_url_environment_for_seed_command_path(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "env-selected.db"
    monkeypatch.setenv("POWER_WEB_OS_DATABASE_URL", sqlite_url(db_path))
    config = Config("alembic.ini")

    command.upgrade(config, "head")

    engine = create_database_engine(database_url=sqlite_url(db_path))
    table_names = set(inspect(engine).get_table_names())

    assert {"radars", "radar_definitions", "radar_runs"} <= table_names
