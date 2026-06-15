import type { ICPRadarCatalogItem, LiveICPRadarRunArtifact, LiveRadarCandidate } from '../../../types';
import { liveFitScoreMax, liveIntentScoreMax, liveTotalScore, liveTotalScoreMax } from '../domain/scoring';
import { radarOperationalStatus } from '../domain/radarStatus';
import type { RadarCandidateViewModel, RadarViewModel } from './viewModels';

// Live artifacts use the same view-model contract as fixture data; provider metadata goes to journal rows.
export function liveRadarToViewModel(radar: ICPRadarCatalogItem, artifact: LiveICPRadarRunArtifact | null): RadarViewModel {
  return {
    id: radar.radar_id,
    name: radar.name,
    description: radar.definition.metadata.description || radar.profile.scope,
    status: radarOperationalStatus(radar.definition.metadata.status || radar.status),
    owner: radar.definition.metadata.owner || radar.owner,
    sourceKind: 'live',
    hasArtifact: Boolean(artifact),
    tabs: ['shortlist', 'settings'],
  };
}

export function liveCandidateToViewModel(candidate: LiveRadarCandidate, artifact: LiveICPRadarRunArtifact): RadarCandidateViewModel {
  return {
    id: candidate.candidate_id,
    legalName: candidate.legal_name,
    description: candidate.description,
    tier: candidate.score.tier,
    evidenceCount: candidate.evidence_refs.length,
    scoreSlots: [
      { key: 'total', value: liveTotalScore(candidate), maxValue: liveTotalScoreMax(candidate) },
      { key: 'fit', value: candidate.score.fit_score, maxValue: liveFitScoreMax(candidate) },
      { key: 'intent', value: candidate.score.intent_score, maxValue: liveIntentScoreMax(candidate) },
      { key: 'trigger', value: null },
    ],
    qualificationRows: candidate.qualification.map((item) => ({
      id: item.rule_id || item.criterion_code,
      label: item.rule_text_snapshot || item.criterion,
      status: item.status,
    })),
    signalRows: candidate.signals.map((item) => ({
      id: item.signal_code,
      label: item.signal,
      status: item.status,
      score: item.score,
    })),
    sourceRows: candidate.evidence_refs.map((ref) => {
      const source = artifact.sources.find((item) => item.evidence_ref === ref);
      return { id: ref, label: source?.title ?? ref, url: source?.url ?? null };
    }),
    journalRows: [
      { label: 'runtime', value: artifact.run_metadata.runtime },
      { label: 'model', value: artifact.run_metadata.model ?? '' },
      { label: 'web_mode', value: artifact.run_metadata.web_mode ?? '' },
    ],
  };
}
