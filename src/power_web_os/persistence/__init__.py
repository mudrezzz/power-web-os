"""Persistence adapters for Power Web OS."""

from power_web_os.persistence.config import DatabaseSettings
from power_web_os.persistence.engine import create_database_engine, create_session_factory, session_scope
from power_web_os.persistence.models import Base
from power_web_os.persistence.repositories import (
    SqlAlchemyRadarDefinitionRepository,
    SqlAlchemyRadarRepository,
    SqlAlchemyRadarReviewDecisionRepository,
    SqlAlchemyRadarRunEventRepository,
    SqlAlchemyRadarRunRepository,
    SqlAlchemyRadarRunOutputRepository,
    SqlAlchemyRadarRunTechnicalTraceRepository,
)
from power_web_os.persistence.signal_monitoring_repositories import SqlAlchemySignalMonitoringRunOutputRepository
from power_web_os.persistence.sales_playbook_repositories import SqlAlchemySalesPlaybookRepository
from power_web_os.persistence.power_web_handoff_repositories import (
    SqlAlchemyPowerWebCandidateReader,
    SqlAlchemyPowerWebHandoffRepository,
    SqlAlchemyPowerWebProductReader,
    SqlAlchemyPowerWebSignalReader,
    SqlAlchemyRadarPowerWebPolicyRepository,
)

__all__ = [
    "Base",
    "DatabaseSettings",
    "SqlAlchemyRadarDefinitionRepository",
    "SqlAlchemyRadarRepository",
    "SqlAlchemyRadarReviewDecisionRepository",
    "SqlAlchemyRadarRunEventRepository",
    "SqlAlchemyRadarRunRepository",
    "SqlAlchemyRadarRunOutputRepository",
    "SqlAlchemyRadarRunTechnicalTraceRepository",
    "SqlAlchemySignalMonitoringRunOutputRepository",
    "SqlAlchemySalesPlaybookRepository",
    "SqlAlchemyPowerWebCandidateReader",
    "SqlAlchemyPowerWebHandoffRepository",
    "SqlAlchemyPowerWebProductReader",
    "SqlAlchemyPowerWebSignalReader",
    "SqlAlchemyRadarPowerWebPolicyRepository",
    "create_database_engine",
    "create_session_factory",
    "session_scope",
]
