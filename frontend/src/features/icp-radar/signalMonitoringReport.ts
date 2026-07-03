import type { SignalMonitoringReportArtifact, SignalMonitoringReportSignal } from '../../types';

const blockedKeyPattern = /(api[_-]?key|authorization|bearer|token|secret|password|headers?|raw[_-]?prompt|prompt|chain[_-]?of[_-]?thought|hidden[_-]?reasoning|internal[_-]?thoughts)/i;

export function signalMonitoringReportFromJson(payload: unknown): SignalMonitoringReportArtifact | null {
  if (!isRecord(payload) || payload.artifact_type !== 'radar_signal_monitoring_report' || containsBlockedKey(payload)) {
    return null;
  }
  const summary = isRecord(payload.summary) ? payload.summary : {};
  return {
    artifact_type: 'radar_signal_monitoring_report',
    artifact_version: stringValue(payload.artifact_version),
    generated_at: stringValue(payload.generated_at),
    fixture_kind: stringValue(payload.fixture_kind),
    recorded_provider: Boolean(payload.recorded_provider),
    live_provider_calls: numberValue(payload.live_provider_calls),
    run_id: stringValue(payload.run_id),
    radar_id: stringValue(payload.radar_id),
    model_profile_id: stringValue(payload.model_profile_id),
    lookback_days: numberValue(payload.lookback_days),
    summary: {
      candidate_count: numberValue(summary.candidate_count),
      signal_rule_count: numberValue(summary.signal_rule_count),
      task_count: numberValue(summary.task_count),
      observation_count: numberValue(summary.observation_count),
      new_signal_count: numberValue(summary.new_signal_count),
      repeated_signal_count: numberValue(summary.repeated_signal_count),
      searched_negative_count: numberValue(summary.searched_negative_count),
      not_searched_budget_limited_count: numberValue(summary.not_searched_budget_limited_count),
    },
    signals: signalRows(payload),
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

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];
}
