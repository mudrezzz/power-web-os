from power_web_os.persistence import (
    create_database_engine,
    create_session_factory,
    session_scope,
    SqlAlchemyRadarRepository,
    SqlAlchemyRadarRunRepository,
    SqlAlchemyRadarRunOutputRepository,
)

engine = create_database_engine()
session_factory = create_session_factory(engine)

with session_scope(session_factory) as session:
    radar_repo = SqlAlchemyRadarRepository(session)
    run_repo = SqlAlchemyRadarRunRepository(session)
    output_repo = SqlAlchemyRadarRunOutputRepository(session)

    for radar in radar_repo.list():
        print(f"\nRadar: {radar.radar_id} | {radar.name}")

        runs = run_repo.list_for_radar(radar.radar_id)
        if not runs:
            print("  no runs")
            continue

        for run in runs:
            output = output_repo.get(run.run_id)
            artifact = output.artifact_payload if output else {}
            candidates = artifact.get("candidates", [])
            sources = artifact.get("sources", [])

            print(f"  Run: {run.run_id}")
            print(f"    status: {run.status.value}")
            print(f"    correlation_id: {run.correlation_id}")
            print(f"    completed_at: {run.completed_at}")
            print(f"    sources: {len(sources)}")
            print(f"    candidates: {len(candidates)}")

            for candidate in candidates[:5]:
                print(f"      - {candidate.get('legal_name')} | tier={candidate.get('score', {}).get('tier')}")