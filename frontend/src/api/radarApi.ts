import type { QualificationAssessmentStatus, SignalValidationStatus } from '../types';

const defaultBaseUrl = 'http://127.0.0.1:8001';
const requestTimeoutMs = 60000;

export type RadarApiErrorKind = 'http' | 'network' | 'conflict' | 'validation';

export class RadarApiError extends Error {
  readonly kind: RadarApiErrorKind;
  readonly status: number | null;

  constructor(message: string, kind: RadarApiErrorKind, status: number | null = null) {
    super(message);
    this.name = 'RadarApiError';
    this.kind = kind;
    this.status = status;
  }
}

export type RadarRunStatus = 'queued' | 'running' | 'completed' | 'failed' | string;

export type RadarSummaryDto = {
  radar_id: string;
  name: string;
  status: string;
  owner: string;
  profile: Record<string, unknown>;
  summary: Record<string, unknown>;
  artifact_path: string | null;
  run_count: number;
  latest_run: RadarRunSummaryDto | null;
};

export type RadarDefinitionDto = {
  definition_id: string;
  radar_id: string;
  definition_version: string;
  definition_payload: Record<string, unknown>;
  is_active: boolean;
  updated_at: string | null;
};

export type RadarDefinitionUpdateDto = {
  definition_payload: Record<string, unknown>;
  definition_version?: string | null;
  is_active?: boolean;
};

export type RadarDetailDto = RadarSummaryDto & {
  active_definition: RadarDefinitionDto | null;
  runs: RadarRunSummaryDto[];
};

export type RadarPreflightCheckDto = {
  code: string;
  status: 'passed' | 'failed' | 'warning' | 'skipped' | string;
  severity: 'info' | 'warning' | 'error' | string;
  message: string;
  details: Record<string, unknown>;
  remediation: string;
};

export type RadarRuntimeConfigDto = {
  artifact_type: string;
  component: string;
  fingerprint: string;
  config: Record<string, unknown>;
  values: Array<Record<string, unknown>>;
  checks: RadarPreflightCheckDto[];
  summary: Record<string, unknown>;
};

export type RadarPreflightDto = {
  artifact_type: 'radar_execution_preflight_report' | string;
  radar_id: string;
  definition_id: string | null;
  definition_version: string | null;
  ready_for_live_run: boolean;
  summary: Record<string, unknown>;
  checks: RadarPreflightCheckDto[];
  runtime_config?: RadarRuntimeConfigDto;
};

export type RadarRunSummaryDto = {
  run_id: string;
  radar_id: string;
  status: RadarRunStatus;
  queued_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  idempotency_key: string | null;
  correlation_id: string | null;
  error_message: string | null;
  error_metadata: Record<string, unknown>;
  run_metadata: Record<string, unknown>;
  display_metadata: Record<string, unknown>;
  output: RadarRunOutputSummaryDto | null;
};

export type RadarRunConfigurationDto = {
  run_id: string;
  radar_id: string;
  definition_id: string | null;
  definition_version: string | null;
  definition_payload: Record<string, unknown>;
  run_profile: string;
  task_context_overrides: Record<string, unknown>;
  snapshot_basis: string;
};

export type RadarRunOutputSummaryDto = {
  artifact_version: string;
  source_count: number;
  candidate_count: number;
  contract_issue_count: number;
  visible_candidate_count: number;
  accepted_candidate_count: number;
  review_needed_candidate_count: number;
  updated_at: string | null;
};

export type RadarRunRequestDto = {
  live: boolean;
  idempotency_key?: string;
  correlation_id?: string;
  requester: string;
  task_context: Record<string, unknown>;
};

export type SignalMonitoringRunRequestDto = {
  source_candidate_run_id: string;
  candidate_scope_mode: 'accepted_and_review_needed' | 'accepted_only';
  candidate_ids: string[];
  signal_codes: string[];
  lookback_days: number | null;
  run_profile: 'signal_monitoring_smoke' | 'signal_monitoring_quality';
  idempotency_key?: string;
  correlation_id?: string;
  requester: string;
};

export type SignalMonitoringPreflightDto = {
  artifact_type: string;
  pipeline_id: 'signal_monitoring';
  radar_id: string;
  source_candidate_run_id: string;
  ready_for_live_run: boolean;
  issues: string[];
  candidate_count: number;
  signal_rule_count: number;
  lookback_days: number;
  budget: Record<string, unknown>;
  effective_signal_policies: Array<Record<string, unknown>>;
};

export type SignalMonitoringOutputSummaryDto = {
  artifact_version: string;
  completion_state: string;
  candidate_count: number;
  observation_count: number;
  provider_call_count: number;
  updated_at: string | null;
};

export type SignalMonitoringRunSummaryDto = {
  run_id: string;
  radar_id: string;
  pipeline_id: 'signal_monitoring';
  source_run_id: string;
  status: RadarRunStatus;
  queued_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  idempotency_key: string | null;
  correlation_id: string | null;
  error_message: string | null;
  error_metadata: Record<string, unknown>;
  run_metadata: Record<string, unknown>;
  output: SignalMonitoringOutputSummaryDto | null;
};

export type SourceUsageDto = {
  source_ref: string;
  source_name: string;
  source_origin: string;
  trust_policy: string;
  used_for: string;
  url: string;
};

export type EvidenceFindingDto = {
  source_ref: string;
  fact: string;
  excerpt: string;
  excerpt_type: string;
  evidence_strength: string;
  contradicts_rule: boolean | null;
  contradicts_signal: boolean | null;
  why_it_matches_rule: string | null;
  why_it_matches_signal: string | null;
  why_score_applies: string | null;
};

export type QualificationDto = {
  criterion_code: string;
  criterion: string;
  status: string;
  confidence: string;
  rationale: string;
  evidence_refs: string[];
  rule_id: string;
  rule_text_snapshot: string;
  operator: string;
  requirement_level: string;
  confidence_policy: string;
  source_usages: SourceUsageDto[];
  evidence_findings: EvidenceFindingDto[];
  cross_validation: Record<string, unknown>;
  requirement_evaluation: Record<string, unknown>;
  final_assessment: string;
  review_decision: Record<string, unknown> | null;
};

export type SignalDto = {
  signal_code: string;
  signal: string;
  status: string;
  score: number;
  confidence: string;
  summary: string;
  evidence_refs: string[];
  source_usages: SourceUsageDto[];
  evidence_findings: EvidenceFindingDto[];
  cross_validation: Record<string, unknown>;
  score_evaluation: Record<string, unknown> | null;
  review_decision: Record<string, unknown> | null;
};

export type RadarCandidateDto = {
  candidate_id: string;
  legal_name: string;
  description: string;
  entity_type?: string;
  upstream_discovery_outcome?: string;
  product_acceptance_status?: string;
  upstream_confidence?: string;
  upstream_reason?: string;
  upstream_source_refs?: string[];
  public_result_status?: string;
  public_projection_reason?: string;
  product_acceptance_reason?: string;
  candidate_surface_status?: string;
  candidate_surface_reason?: string;
  candidate_surface_rank?: number | null;
  score: {
    fit_score: number | null;
    intent_score: number | null;
    tier: string | null;
  };
  review_flags: string[];
  evidence_refs: string[];
  qualification: QualificationDto[];
  signals: SignalDto[];
};

export type RadarSourceDto = {
  evidence_ref: string;
  title: string;
  url: string;
  snippet: string;
  query_id: string | null;
  source_type: string;
};

export type RadarRunCandidatesDto = {
  run_id: string;
  radar_id: string;
  candidates: RadarCandidateDto[];
  sources: RadarSourceDto[];
  contract_validation: Array<Record<string, unknown>>;
  candidate_discovery_reconciliation?: Record<string, unknown>;
  product_acceptance_ledger?: Array<Record<string, unknown>>;
};

export type RadarRunJournalEventDto = {
  event_id: string;
  run_id: string;
  sequence: number;
  event_type: string;
  phase: string;
  actor: string;
  node_name: string;
  visibility: 'user' | 'operator' | 'debug' | string;
  summary: string;
  payload: Record<string, unknown>;
  source_refs: string[];
  candidate_refs: string[];
  created_at: string | null;
};

export type RadarRunJournalDto = {
  run_id: string;
  radar_id: string;
  events: RadarRunJournalEventDto[];
};

export type RadarRunDossierContextDto = {
  run_id: string;
  radar_id: string;
  status: string;
  live: boolean;
  requester: string;
  correlation_id: string | null;
  idempotency_key: string | null;
  queued_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  model: string | null;
  web_mode: string | null;
  runtime: string;
  task_context: Record<string, unknown>;
};

export type RadarRunDossierDefinitionDto = {
  definition_id: string | null;
  definition_version: string | null;
  is_active: boolean | null;
  payload_summary: Record<string, unknown>;
};

export type RadarRunDossierQueryDto = {
  query_id: string;
  query: string;
  purpose: string;
  expected_evidence: string[];
  stage?: string | null;
  subject_type?: string | null;
  subject_id?: string | null;
  rule_snapshot?: string;
  source_scope: string;
  source_base?: string | null;
  application_scope?: string | null;
  source_ids: string[];
  external_source_hints: string[];
  depends_on?: string[];
  candidate_scope?: string[];
  source_count: number;
  source_refs: string[];
  candidate_refs: string[];
};

export type RadarRunDossierSourceUsageDto = {
  candidate_id: string;
  candidate_name: string;
  subject_type: string;
  subject_id: string;
  subject_label: string;
};

export type RadarRunDossierSourceDto = {
  evidence_ref: string;
  title: string;
  url: string;
  snippet: string;
  query_id: string | null;
  source_type: string;
  usage_status: 'used' | 'collected_not_used' | string;
  usages: RadarRunDossierSourceUsageDto[];
};

export type RadarRunDossierSourceLifecycleItemDto = {
  evidence_ref: string;
  title: string;
  url: string;
  query_id: string | null;
  source_type: string;
  state: string;
  reason: string;
  origin: string;
  verification_state?: string | null;
  verification_mode?: string | null;
  verification_reason?: string | null;
  verification_status_code?: number | null;
  usages: RadarRunDossierSourceUsageDto[];
};

export type RadarRunDossierSourceLifecycleSummaryDto = {
  total_count: number;
  by_state: Record<string, number>;
  by_reason: Record<string, number>;
};

export type RadarRunDossierSummaryDto = {
  output_state: 'pending' | 'available' | 'failed' | string;
  query_count: number;
  source_count: number;
  used_source_count: number;
  retrieved_source_count?: number;
  linked_source_count?: number;
  linking_failed_source_count?: number;
  schema_rejected_source_count?: number;
  analyzed_source_count: number;
  analyzed_only_source_count?: number;
  diagnostic_source_count?: number;
  skipped_source_count: number;
  candidate_count: number;
  validation_issue_count: number;
  review_flag_count: number;
  coverage_warning_count?: number;
};

export type RadarRunDossierDto = {
  run_context: RadarRunDossierContextDto;
  runtime_config: Record<string, unknown>;
  runtime_config_warnings: Array<Record<string, unknown>>;
  radar_snapshot: Record<string, unknown>;
  definition_snapshot: RadarRunDossierDefinitionDto | null;
  discovery_plan: Record<string, unknown>;
  source_policy_decisions: Array<Record<string, unknown>>;
  source_obligations: Array<Record<string, unknown>>;
  source_obligation_decisions: Array<Record<string, unknown>>;
  source_obligation_summary: Record<string, unknown>;
  coverage_summary: Record<string, unknown>;
  budget_summary: Record<string, unknown>;
  budget_exhaustion_events: Array<Record<string, unknown>>;
  external_call_budget_settings: Record<string, unknown>;
  external_call_budget_counters: Record<string, number>;
  external_call_budget_counters_by_role: Record<string, number>;
  external_call_budget_exhaustion_events: Array<Record<string, unknown>>;
  candidate_universe: Array<Record<string, unknown>>;
  coverage_checks: Array<Record<string, unknown>>;
  coverage_warnings: string[];
  unresolved_candidate_gaps: Array<Record<string, unknown>>;
  discovery_iteration_count: number;
  search_plan: RadarRunDossierQueryDto[];
  sources: RadarRunDossierSourceDto[];
  source_lifecycle: RadarRunDossierSourceLifecycleItemDto[];
  source_lifecycle_summary: RadarRunDossierSourceLifecycleSummaryDto;
  validation: Array<Record<string, unknown>>;
  timeline: RadarRunJournalEventDto[];
  summary: RadarRunDossierSummaryDto;
};

export type RadarRunTechnicalTraceItemDto = {
  trace_id: string;
  run_id: string;
  sequence: number;
  phase: string;
  node_name: string;
  trace_type: string;
  title: string;
  summary: string;
  duration_ms: number | null;
  payload: Record<string, unknown>;
  redaction_report: Record<string, unknown>;
  created_at: string | null;
};

export type RadarRunTechnicalTraceDto = {
  run_id: string;
  radar_id: string;
  traces: RadarRunTechnicalTraceItemDto[];
};

export type RadarReviewDecisionRequestDto = {
  status: string;
  reviewer: string;
  comment: string;
  corrected_assessment?: QualificationAssessmentStatus | null;
  adjusted_score?: number | null;
  confidence?: string | null;
  corrected_summary?: string | null;
  evidence_refs?: string[];
  reviewed_at?: string;
};

export type RadarReviewDecisionDto = {
  decision_id: string;
  run_id: string;
  radar_id: string;
  candidate_id: string;
  subject_type: 'qualification' | 'signal' | string;
  subject_id: string;
  status: SignalValidationStatus | 'approved' | string;
  reviewer: string;
  comment: string;
  decision_payload: Record<string, unknown>;
  score_impact: Record<string, unknown>;
  reviewed_at: string | null;
  updated_at: string | null;
};

export class RadarApiClient {
  readonly baseUrl: string;

  constructor(baseUrl = radarApiBaseUrl()) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  listRadars(signal?: AbortSignal) {
    return this.request<RadarSummaryDto[]>('/api/radars', { signal });
  }

  getRadar(radarId: string) {
    return this.request<RadarDetailDto>(`/api/radars/${encodeURIComponent(radarId)}`);
  }

  listRadarRuns(radarId: string, limit = 20) {
    return this.request<RadarRunSummaryDto[]>(
      `/api/radars/${encodeURIComponent(radarId)}/runs?limit=${encodeURIComponent(String(limit))}`,
    );
  }

  getRadarPreflight(radarId: string) {
    return this.request<RadarPreflightDto>(`/api/radars/${encodeURIComponent(radarId)}/preflight`);
  }

  updateRadarDefinition(radarId: string, request: RadarDefinitionUpdateDto) {
    return this.request<RadarDetailDto>(`/api/radars/${encodeURIComponent(radarId)}/definition`, {
      method: 'PUT',
      body: JSON.stringify(request),
    });
  }

  queueRadarRun(radarId: string, request: RadarRunRequestDto) {
    return this.request<RadarRunSummaryDto>(`/api/radars/${encodeURIComponent(radarId)}/runs`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  queueCandidateDiscoveryRun(radarId: string, request: RadarRunRequestDto) {
    return this.queueRadarRun(radarId, {
      ...request,
      task_context: {
        ...request.task_context,
        pipeline_id: 'candidate_discovery',
        run_kind: 'candidate_discovery',
      },
    });
  }

  getSignalMonitoringPreflight(radarId: string, request: SignalMonitoringRunRequestDto) {
    const params = signalMonitoringQuery(request);
    return this.request<SignalMonitoringPreflightDto>(
      `/api/radars/${encodeURIComponent(radarId)}/signal-monitoring/preflight?${params.toString()}`,
    );
  }

  queueSignalMonitoringRun(radarId: string, request: SignalMonitoringRunRequestDto) {
    return this.request<SignalMonitoringRunSummaryDto>(
      `/api/radars/${encodeURIComponent(radarId)}/signal-monitoring-runs`,
      { method: 'POST', body: JSON.stringify(request) },
    );
  }

  listSignalMonitoringRuns(radarId: string, limit = 20) {
    return this.request<SignalMonitoringRunSummaryDto[]>(
      `/api/radars/${encodeURIComponent(radarId)}/signal-monitoring-runs?limit=${encodeURIComponent(String(limit))}`,
    );
  }

  getSignalMonitoringRun(runId: string) {
    return this.request<SignalMonitoringRunSummaryDto>(
      `/api/signal-monitoring-runs/${encodeURIComponent(runId)}`,
    );
  }

  getSignalMonitoringReport(runId: string) {
    return this.request<unknown>(`/api/signal-monitoring-runs/${encodeURIComponent(runId)}/report`);
  }

  getSignalMonitoringCandidateSurface(runId: string) {
    return this.request<unknown>(
      `/api/signal-monitoring-runs/${encodeURIComponent(runId)}/candidate-surface`,
    );
  }

  getRun(runId: string) {
    return this.request<RadarRunSummaryDto>(`/api/radar-runs/${encodeURIComponent(runId)}`);
  }

  getRunConfiguration(runId: string) {
    return this.request<RadarRunConfigurationDto>(
      `/api/radar-runs/${encodeURIComponent(runId)}/configuration`,
    );
  }

  getRunCandidates(runId: string) {
    return this.request<RadarRunCandidatesDto>(`/api/radar-runs/${encodeURIComponent(runId)}/candidates`);
  }

  getRunJournal(runId: string) {
    return this.request<RadarRunJournalDto>(`/api/radar-runs/${encodeURIComponent(runId)}/journal`);
  }

  getRunDossier(runId: string) {
    return this.request<RadarRunDossierDto>(`/api/radar-runs/${encodeURIComponent(runId)}/dossier`);
  }

  getRunTechnicalTrace(runId: string) {
    return this.request<RadarRunTechnicalTraceDto>(`/api/radar-runs/${encodeURIComponent(runId)}/technical-trace`);
  }

  saveQualificationReview(
    runId: string,
    candidateId: string,
    ruleId: string,
    request: RadarReviewDecisionRequestDto,
  ) {
    return this.request<RadarReviewDecisionDto>(
      `/api/radar-runs/${encodeURIComponent(runId)}/candidates/${encodeURIComponent(candidateId)}/qualification/${encodeURIComponent(ruleId)}/review`,
      { method: 'PUT', body: JSON.stringify(request) },
    );
  }

  deleteQualificationReview(runId: string, candidateId: string, ruleId: string) {
    return this.request<void>(
      `/api/radar-runs/${encodeURIComponent(runId)}/candidates/${encodeURIComponent(candidateId)}/qualification/${encodeURIComponent(ruleId)}/review`,
      { method: 'DELETE' },
    );
  }

  saveSignalReview(
    runId: string,
    candidateId: string,
    signalCode: string,
    request: RadarReviewDecisionRequestDto,
  ) {
    return this.request<RadarReviewDecisionDto>(
      `/api/radar-runs/${encodeURIComponent(runId)}/candidates/${encodeURIComponent(candidateId)}/signals/${encodeURIComponent(signalCode)}/review`,
      { method: 'PUT', body: JSON.stringify(request) },
    );
  }

  deleteSignalReview(runId: string, candidateId: string, signalCode: string) {
    return this.request<void>(
      `/api/radar-runs/${encodeURIComponent(runId)}/candidates/${encodeURIComponent(candidateId)}/signals/${encodeURIComponent(signalCode)}/review`,
      { method: 'DELETE' },
    );
  }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    let response: Response;
    const controller = new AbortController();
    const abortFromCaller = () => controller.abort();
    init.signal?.addEventListener('abort', abortFromCaller, { once: true });
    const timeoutId = window.setTimeout(() => controller.abort(), requestTimeoutMs);
    try {
      response = await fetch(`${this.baseUrl}${path}`, {
        ...init,
        signal: controller.signal,
        headers: {
          Accept: 'application/json',
          ...(init.body ? { 'Content-Type': 'application/json' } : {}),
          ...init.headers,
        },
      });
    } catch (error) {
      throw new RadarApiError(error instanceof Error ? error.message : 'Radar API is unavailable', 'network');
    } finally {
      window.clearTimeout(timeoutId);
      init.signal?.removeEventListener('abort', abortFromCaller);
    }

    if (!response.ok) {
      const message = await responseMessage(response);
      const kind = response.status === 409 ? 'conflict' : response.status === 422 ? 'validation' : 'http';
      throw new RadarApiError(message, kind, response.status);
    }
    if (response.status === 204) {
      return undefined as T;
    }
    return response.json() as Promise<T>;
  }
}

function signalMonitoringQuery(request: SignalMonitoringRunRequestDto) {
  const params = new URLSearchParams({
    source_candidate_run_id: request.source_candidate_run_id,
    candidate_scope_mode: request.candidate_scope_mode,
    run_profile: request.run_profile,
  });
  for (const candidateId of request.candidate_ids) {
    params.append('candidate_ids', candidateId);
  }
  for (const signalCode of request.signal_codes) {
    params.append('signal_codes', signalCode);
  }
  if (request.lookback_days !== null) {
    params.set('lookback_days', String(request.lookback_days));
  }
  return params;
}

export function radarApiBaseUrl() {
  return import.meta.env.VITE_POWER_WEB_OS_API_BASE_URL || defaultBaseUrl;
}

async function responseMessage(response: Response) {
  try {
    const payload = await response.json() as { detail?: unknown };
    return typeof payload.detail === 'string' ? payload.detail : `${response.status} ${response.statusText}`;
  } catch {
    return `${response.status} ${response.statusText}`;
  }
}
