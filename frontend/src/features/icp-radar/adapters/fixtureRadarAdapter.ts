import type { ICPRadarArtifact, ICPRadarCandidate, ICPRadarCatalogItem } from '../../../types';
import { radarOperationalStatus } from '../domain/radarStatus';
import type { RadarCandidateViewModel, RadarViewModel } from './viewModels';

// Fixture artifacts are normalized here so UI components do not learn XLSX-specific shapes.
export function fixtureRadarToViewModel(radar: ICPRadarCatalogItem, artifact: ICPRadarArtifact | null): RadarViewModel {
  return {
    id: radar.radar_id,
    name: radar.name,
    description: radar.definition.metadata.description || radar.profile.scope,
    status: radarOperationalStatus(radar.definition.metadata.status || radar.status),
    owner: radar.definition.metadata.owner || radar.owner,
    sourceKind: 'fixture',
    hasArtifact: Boolean(artifact),
    tabs: ['shortlist', 'settings'],
  };
}

export function fixtureCandidateToViewModel(candidate: ICPRadarCandidate): RadarCandidateViewModel {
  return {
    id: candidate.account_id,
    legalName: candidate.legal_name,
    description: candidate.description,
    tier: candidate.score.tier,
    evidenceCount: candidate.evidence_refs.length,
    scoreSlots: [
      { key: 'total', value: candidate.score.total_score },
      { key: 'fit', value: candidate.score.fit_score },
      { key: 'intent', value: candidate.score.intent_score },
      { key: 'trigger', value: candidate.score.trigger_score },
    ],
    qualificationRows: [],
    signalRows: Object.entries(candidate.criteria_scores).map(([code, score]) => ({
      id: code,
      label: candidate.criteria_evidence[code]?.criterion_code ?? code,
      status: candidate.criteria_evidence[code]?.evidence_status ?? 'unknown',
      score,
    })),
    sourceRows: candidate.evidence_refs.map((ref) => ({ id: ref, label: ref, url: null })),
    journalRows: [],
  };
}
