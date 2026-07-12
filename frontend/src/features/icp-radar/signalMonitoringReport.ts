import type { SignalMonitoringReportArtifact, SignalMonitoringReportSignal } from '../../types';

const blockedKeyPattern = /(api[_-]?key|authorization|bearer|token|secret|password|headers?|raw[_-]?prompt|prompt|chain[_-]?of[_-]?thought|hidden[_-]?reasoning|internal[_-]?thoughts)/i;

export function signalMonitoringReportFromJson(payload: unknown): SignalMonitoringReportArtifact | null {
  if (!isRecord(payload) || payload.artifact_type !== 'radar_signal_monitoring_report' || containsBlockedKey(payload)) {
    return null;
  }
  const summary = isRecord(payload.summary) ? payload.summary : {};
  const budgets = isRecord(payload.budgets) ? payload.budgets : {};
  const counters = isRecord(budgets.counters)
    ? budgets.counters
    : isRecord(payload.budget_counters) ? payload.budget_counters : {};
  const settings = isRecord(budgets.settings)
    ? budgets.settings
    : isRecord(payload.budget_settings) ? payload.budget_settings : {};
  const exhaustionEvents = Array.isArray(budgets.exhaustion_events)
    ? budgets.exhaustion_events.filter(isRecord)
    : Array.isArray(payload.budget_exhaustion_events) ? payload.budget_exhaustion_events.filter(isRecord) : [];
  const signals = signalRows(payload);
  return {
    artifact_type: 'radar_signal_monitoring_report',
    artifact_version: stringValue(payload.artifact_version),
    pipeline_id: 'signal_monitoring',
    generated_at: stringValue(payload.generated_at),
    fixture_kind: stringValue(payload.fixture_kind),
    recorded_provider: Boolean(payload.recorded_provider),
    live_provider_calls: numberValue(payload.live_provider_calls),
    run_id: stringValue(payload.run_id),
    signal_run_id: stringValue(payload.signal_run_id) || stringValue(payload.run_id),
    radar_id: stringValue(payload.radar_id),
    source_candidate_run_id: stringValue(payload.source_candidate_run_id),
    completion_state: stringValue(payload.completion_state) || 'completed',
    candidate_scope_mode: stringValue(payload.candidate_scope_mode),
    model_profile_id: stringValue(payload.model_profile_id),
    provider_runtime: stringValue(payload.provider_runtime),
    lookback_days: numberValue(payload.lookback_days),
    summary: {
      candidate_count: numberValue(summary.candidate_count),
      accepted_candidate_count: numberValue(summary.accepted_candidate_count),
      review_needed_candidate_count: numberValue(summary.review_needed_candidate_count),
      signal_rule_count: numberValue(summary.signal_rule_count),
      task_count: numberValue(summary.task_count),
      observation_count: numberValue(summary.observation_count),
      provider_call_count: numberValue(summary.provider_call_count) || numberValue(counters.signal_provider_calls),
      retry_count: numberValue(summary.retry_count) || numberValue(counters.signal_extraction_retries),
      new_signal_count: numberValue(summary.new_signal_count)
        || signals.filter((item) => item.novelty === 'new_signal').length,
      repeated_signal_count: numberValue(summary.repeated_signal_count)
        || signals.filter((item) => item.novelty.includes('duplicate')).length,
      searched_negative_count: numberValue(summary.searched_negative_count)
        || signals.filter((item) => item.observation_status === 'not_observed').length,
      not_searched_budget_limited_count: numberValue(summary.not_searched_budget_limited_count)
        || signals.filter((item) => item.search_status.includes('budget')).length,
      observations_by_search_status: numberRecord(summary.observations_by_search_status),
      observations_by_observation_status: numberRecord(summary.observations_by_observation_status),
    },
    budgets: {
      settings,
      counters: numberRecord(counters),
      exhaustion_events: exhaustionEvents,
    },
    signals,
  };
}

function signalRows(payload: Record<string, unknown>): SignalMonitoringReportSignal[] {
  if (Array.isArray(payload.signals)) {
    return payload.signals.filter(isRecord).map(signalRow);
  }
  if (!Array.isArray(payload.observations)) {
    return [];
  }
  return payload.observations.filter(isRecord).map(signalRow);
}

function signalRow(item: Record<string, unknown>): SignalMonitoringReportSignal {
  return {
    candidate_id: stringValue(item.candidate_id),
    candidate_name: stringValue(item.candidate_name),
    signal_code: stringValue(item.signal_code),
    signal_label: stringValue(item.signal_label),
    search_status: stringValue(item.search_status),
    observation_status: stringValue(item.observation_status),
    novelty: stringValue(item.novelty),
    summary: stringValue(item.summary),
    evidence_refs: stringList(item.evidence_refs),
    source_lane: stringValue(item.source_lane),
    source_ids: stringList(item.source_ids),
  };
}

function containsBlockedKey(value: unknown): boolean {
  if (Array.isArray(value)) {
    return value.some(containsBlockedKey);
  }
  if (!isRecord(value)) {
    return false;
  }
  return Object.entries(value).some(([key, nested]) => blockedKeyPattern.test(key) || containsBlockedKey(nested));
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function stringValue(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

function numberValue(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0;
}

function numberRecord(value: unknown): Record<string, number> {
  if (!isRecord(value)) {
    return {};
  }
  return Object.fromEntries(
    Object.entries(value).filter((entry): entry is [string, number] => (
      typeof entry[1] === 'number' && Number.isFinite(entry[1])
    )),
  );
}

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];
}
