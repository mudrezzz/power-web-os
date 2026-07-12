import type {
  SignalMonitoringCandidateSurface,
  SignalMonitoringCandidateSurfaceArtifact,
  SignalMonitoringPresentationStatus,
  SignalMonitoringSurfaceEvidence,
  SignalMonitoringSurfaceOutcome,
  SignalMonitoringSurfaceState,
} from '../../types';

const blockedKeyPattern = /(api[_-]?key|authorization|bearer|token|secret|password|headers?|raw[_-]?prompt|prompt|chain[_-]?of[_-]?thought|hidden[_-]?reasoning|internal[_-]?thoughts)/i;
const statuses = new Set<SignalMonitoringPresentationStatus>([
  'found_fresh',
  'found_relevant_date_unknown',
  'found_historical_not_counted',
  'not_found_after_complete_coverage',
  'coverage_incomplete',
  'not_monitored',
]);

export function signalMonitoringCandidateSurfaceFromJson(
  payload: unknown,
): SignalMonitoringCandidateSurfaceArtifact | null {
  if (!isRecord(payload) || payload.artifact_type !== 'signal_monitoring_candidate_surface' || containsBlockedKey(payload)) {
    return null;
  }
  const summary = isRecord(payload.summary) ? payload.summary : {};
  return {
    artifact_type: 'signal_monitoring_candidate_surface',
    artifact_version: stringValue(payload.artifact_version),
    pipeline_id: 'signal_monitoring',
    radar_id: stringValue(payload.radar_id),
    selected_run_id: stringValue(payload.selected_run_id),
    source_candidate_run_id: stringValue(payload.source_candidate_run_id),
    history_run_ids: stringList(payload.history_run_ids),
    summary: {
      candidate_count: numberValue(summary.candidate_count),
      monitored_candidate_count: numberValue(summary.monitored_candidate_count),
      not_monitored_candidate_count: numberValue(summary.not_monitored_candidate_count),
      criterion_count: numberValue(summary.criterion_count),
      pair_count: numberValue(summary.pair_count),
      current_confirmed_count: numberValue(summary.current_confirmed_count),
      current_review_count: numberValue(summary.current_review_count),
      current_searched_negative_count: numberValue(summary.current_searched_negative_count),
      new_confirmed_count: numberValue(summary.new_confirmed_count),
      cumulative_confirmed_count: numberValue(summary.cumulative_confirmed_count),
      cumulative_review_count: numberValue(summary.cumulative_review_count),
      unresolved_source_ref_count: numberValue(summary.unresolved_source_ref_count),
    },
    unresolved_source_refs: stringList(payload.unresolved_source_refs),
    candidates: array(payload.candidates).map(candidateSurface),
  };
}

function candidateSurface(value: unknown): SignalMonitoringCandidateSurface {
  const item = record(value);
  const monitoringStatus = stringValue(item.monitoring_status);
  return {
    candidate_id: stringValue(item.candidate_id),
    candidate_name: stringValue(item.candidate_name),
    monitored: Boolean(item.monitored),
    monitoring_status: monitoringStatus === 'review_needed' ? 'review_needed' : presentationStatus(monitoringStatus),
    outcomes: array(item.outcomes).map(outcome),
  };
}

function outcome(value: unknown): SignalMonitoringSurfaceOutcome {
  const item = record(value);
  return {
    signal_code: stringValue(item.signal_code),
    signal_label: stringValue(item.signal_label),
    current: surfaceState(item.current),
    cumulative: surfaceState(item.cumulative),
    new_in_selected_run: Boolean(item.new_in_selected_run),
  };
}

function surfaceState(value: unknown): SignalMonitoringSurfaceState {
  const item = record(value);
  return {
    presentation_status: presentationStatus(item.presentation_status),
    technical_observation_status: stringValue(item.technical_observation_status),
    technical_search_status: stringValue(item.technical_search_status),
    summary: stringValue(item.summary),
    score: numberValue(item.score),
    coverage_complete: Boolean(item.coverage_complete),
    origin_run_id: stringValue(item.origin_run_id),
    latest_run_id: stringValue(item.latest_run_id),
    evidence: array(item.evidence).map(evidence),
    searched_sources: array(item.searched_sources).map(evidence),
    history: array(item.history).map((entry) => {
      const history = record(entry);
      return {
        run_id: stringValue(history.run_id),
        presentation_status: presentationStatus(history.presentation_status),
        technical_observation_status: stringValue(history.technical_observation_status),
        technical_search_status: stringValue(history.technical_search_status),
      };
    }),
  };
}

function evidence(value: unknown): SignalMonitoringSurfaceEvidence {
  const item = record(value);
  return {
    source_ref: stringValue(item.source_ref),
    resolved: Boolean(item.resolved),
    resolution_reason: stringValue(item.resolution_reason),
    title: stringValue(item.title),
    url: stringValue(item.url),
    snippet: stringValue(item.snippet),
    source_lane: stringValue(item.source_lane),
    fact: stringValue(item.fact),
    excerpt: stringValue(item.excerpt),
    event_at: stringValue(item.event_at),
    published_at: stringValue(item.published_at),
    temporal_status: stringValue(item.temporal_status),
    date_basis: stringValue(item.date_basis),
    date_confidence: stringValue(item.date_confidence),
    origin_run_id: stringValue(item.origin_run_id),
  };
}

function presentationStatus(value: unknown): SignalMonitoringPresentationStatus {
  const status = stringValue(value) as SignalMonitoringPresentationStatus;
  return statuses.has(status) ? status : 'coverage_incomplete';
}

function containsBlockedKey(value: unknown): boolean {
  if (Array.isArray(value)) return value.some(containsBlockedKey);
  if (!isRecord(value)) return false;
  return Object.entries(value).some(([key, nested]) => blockedKeyPattern.test(key) || containsBlockedKey(nested));
}

function record(value: unknown): Record<string, unknown> {
  return isRecord(value) ? value : {};
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function array(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function stringValue(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];
}

function numberValue(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0;
}
