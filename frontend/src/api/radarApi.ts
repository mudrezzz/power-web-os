import type { QualificationAssessmentStatus, SignalValidationStatus } from '../types';

const defaultBaseUrl = 'http://127.0.0.1:8000';

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

export type RadarDetailDto = RadarSummaryDto & {
  active_definition: RadarDefinitionDto | null;
  runs: RadarRunSummaryDto[];
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
  output: RadarRunOutputSummaryDto | null;
};

export type RadarRunOutputSummaryDto = {
  artifact_version: string;
  source_count: number;
  candidate_count: number;
  contract_issue_count: number;
  updated_at: string | null;
};

export type RadarRunRequestDto = {
  live: boolean;
  idempotency_key?: string;
  correlation_id?: string;
  requester: string;
  task_context: Record<string, unknown>;
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

export type RadarRunDossierSummaryDto = {
  output_state: 'pending' | 'available' | 'failed' | string;
  query_count: number;
  source_count: number;
  used_source_count: number;
  candidate_count: number;
  validation_issue_count: number;
  review_flag_count: number;
};

export type RadarRunDossierDto = {
  run_context: RadarRunDossierContextDto;
  radar_snapshot: Record<string, unknown>;
  definition_snapshot: RadarRunDossierDefinitionDto | null;
  search_plan: RadarRunDossierQueryDto[];
  sources: RadarRunDossierSourceDto[];
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

  listRadars() {
    return this.request<RadarSummaryDto[]>('/api/radars');
  }

  getRadar(radarId: string) {
    return this.request<RadarDetailDto>(`/api/radars/${encodeURIComponent(radarId)}`);
  }

  queueRadarRun(radarId: string, request: RadarRunRequestDto) {
    return this.request<RadarRunSummaryDto>(`/api/radars/${encodeURIComponent(radarId)}/runs`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  getRun(runId: string) {
    return this.request<RadarRunSummaryDto>(`/api/radar-runs/${encodeURIComponent(runId)}`);
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
    try {
      response = await fetch(`${this.baseUrl}${path}`, {
        ...init,
        headers: {
          Accept: 'application/json',
          ...(init.body ? { 'Content-Type': 'application/json' } : {}),
          ...init.headers,
        },
      });
    } catch (error) {
      throw new RadarApiError(error instanceof Error ? error.message : 'Radar API is unavailable', 'network');
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
