"""Architecture and provider-neutral contracts for Power Web discovery."""

from .benchmark import PowerWebBenchmark, PowerWebBenchmarkFreeze
from .contracts import (
    EmploymentClaim,
    IdentityHypothesis,
    InfluenceHypothesis,
    PersonIdentity,
    PersonProfile,
    PowerWebArtifact,
    PowerWebGap,
    RelationshipClaim,
    RoleDemand,
    SourceEvidence,
)
from .source_capabilities import PowerWebSourceCapabilityCard

__all__ = [
    "EmploymentClaim",
    "IdentityHypothesis",
    "InfluenceHypothesis",
    "PersonIdentity",
    "PersonProfile",
    "PowerWebArtifact",
    "PowerWebBenchmark",
    "PowerWebBenchmarkFreeze",
    "PowerWebGap",
    "PowerWebSourceCapabilityCard",
    "RelationshipClaim",
    "RoleDemand",
    "SourceEvidence",
]
