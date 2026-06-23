import type {
  EvidenceFindingDto,
  RadarDetailDto,
  RadarRunCandidatesDto,
  RadarRunDossierDto,
  RadarRunJournalDto,
  RadarRunSummaryDto,
  RadarRunTechnicalTraceDto,
  SourceUsageDto,
} from '../../../api/radarApi';
import type {
  ICPRadarCatalogArtifact,
  ICPRadarCatalogItem,
  LiveICPRadarRunArtifact,
  LiveRadarRunDossier,
  LiveRadarTechnicalTrace,
  LiveRadarSignalResult,
  QualificationAssessmentStatus,
  QualificationCrossValidation,
  QualificationEvidenceFinding,
  QualificationRequirementEvaluation,
  QualificationRequirementLevel,
  QualificationReviewDecision,
  QualificationSourceOrigin,
  QualificationSourceUsage,
  QualificationTrustPolicy,
  RadarDefinition,
  SignalEvidenceFinding,
  SignalScoreEvaluation,
  SignalValidationDecision,
} from '../../../types';

// API DTOs are normalized here so UI components keep rendering the established artifact-shaped contracts.

export function apiDetailsToCatalogArtifact(
  details: RadarDetailDto[],
  fallback: ICPRadarCatalogArtifact | null,
): ICPRadarCatalogArtifact {
  return {
    artifact_type: 'icp_radar_catalog',
    artifact_version: '0.6.5.2',
    radars: details.map(apiDetailToCatalogItem),
    workflow_metadata: fallback?.workflow_metadata ?? {
      workflow_name: 'power-web-os-backend-api',
      artifact_version: '0.7.6',
      active_fixture_radar_id: 'toir-sibur',
      radar_count: details.length,
    },
  };
}

export function apiDetailToCatalogItem(detail: RadarDetailDto): ICPRadarCatalogItem {
  const definition = detail.active_definition?.definition_payload as RadarDefinition | undefined;
  return {
    radar_id: detail.radar_id,
    name: detail.name,
    status: detail.status,
    owner: detail.owner,
    profile: {
      icp_profile: stringField(detail.profile.icp_profile, detail.name),
      product: stringField(detail.profile.product, ''),
      segment: stringField(detail.profile.segment, ''),
      scope: stringField(detail.profile.scope, ''),
    },
    summary: {
      cadence: stringField(detail.summary.cadence, 'weekly'),
      last_run: stringField(detail.summary.last_run, detail.latest_run?.completed_at ?? detail.latest_run?.queued_at ?? ''),
      candidate_count: numberField(detail.summary.candidate_count, detail.latest_run?.output?.candidate_count ?? 0),
      needs_review_count: numberField(detail.summary.needs_review_count, 0),
      accepted_count: numberField(detail.summary.accepted_count, 0),
      run_mode: stringField(detail.summary.run_mode, 'backend_api'),
    },
    definition: definition ?? emptyDefinition(detail),
    artifact_path: detail.artifact_path,
  };
}

export function apiRunToLiveArtifact(
  run: RadarRunSummaryDto,
  candidates: RadarRunCandidatesDto,
  radar: ICPRadarCatalogItem,
  journal?: RadarRunJournalDto,
  dossier?: RadarRunDossierDto,
  technicalTrace?: RadarRunTechnicalTraceDto,
): LiveICPRadarRunArtifact {
  const normalizedDossier = dossier ? runDossier(dossier) : undefined;
  return {
    artifact_type: 'icp_radar_live_run',
    artifact_version: '0.6.3.4',
    radar: {
      radar_id: radar.radar_id,
      name: radar.name,
      description: radar.definition.metadata.description || radar.profile.scope,
      qualification_criteria: flattenQualificationRules(radar.definition.account_qualification.rule_group).map((item) => ({
        code: item.rule_id,
        label: item.name,
        rule: item.description,
      })),
      intent_signals: radar.definition.intent_signals.map((item) => ({
        code: item.code,
        label: item.name,
        rule: item.description,
      })),
      source_policy: radar.definition.global_search_policy,
    },
    run_metadata: {
      workflow_name: stringField(run.run_metadata.workflow_name, 'power-web-os-backend-api'),
      runtime: stringField(run.run_metadata.runtime, 'backend-api'),
      framework_available: Boolean(run.run_metadata.framework_available ?? true),
      runtime_mode: stringField(run.run_metadata.runtime_mode, 'queued-worker'),
      node_name: stringField(run.run_metadata.node_name, 'radar-api'),
      task_id: stringField(run.run_metadata.task_id, run.run_id),
      correlation_id: run.correlation_id,
      model: nullableString(run.run_metadata.model),
      web_mode: nullableString(run.run_metadata.web_mode),
      query_count: numberField(run.run_metadata.query_count, 0),
      source_count: run.output?.source_count ?? candidates.sources.length,
      candidate_count: run.output?.candidate_count ?? candidates.candidates.length,
      run_at: run.completed_at ?? run.started_at ?? run.queued_at ?? new Date().toISOString(),
    },
    search_plan: {
      radar_id: radar.radar_id,
      queries: normalizedDossier?.search_plan.map((query) => ({
        query_id: query.query_id,
        query: query.query,
        purpose: query.purpose,
        expected_evidence: query.expected_evidence,
        stage: query.stage,
        subject_type: query.subject_type,
        subject_id: query.subject_id,
        rule_snapshot: query.rule_snapshot,
        source_scope: query.source_scope,
        source_ids: query.source_ids,
        external_source_hints: query.external_source_hints,
        depends_on: query.depends_on,
        candidate_scope: query.candidate_scope,
      })) ?? [],
    },
    sources: candidates.sources.map((source) => ({
      evidence_ref: source.evidence_ref,
      title: source.title,
      url: source.url,
      snippet: source.snippet,
      query_id: source.query_id,
      source_type: source.source_type,
    })),
    candidates: candidates.candidates.map((candidate) => ({
      candidate_id: candidate.candidate_id,
      legal_name: candidate.legal_name,
      description: candidate.description,
      qualification: candidate.qualification.map((item) => ({
        criterion_code: item.criterion_code,
        criterion: item.criterion,
        status: liveQualificationStatus(item.status),
        confidence: item.confidence,
        rationale: item.rationale,
        evidence_refs: item.evidence_refs,
        rule_id: item.rule_id,
        rule_text_snapshot: item.rule_text_snapshot,
        operator: liveOperator(item.operator),
        requirement_level: liveRequirementLevel(item.requirement_level),
        confidence_policy: liveTrustPolicy(item.confidence_policy),
        source_usages: item.source_usages.map(sourceUsage),
        evidence_findings: item.evidence_findings.map(qualificationFinding),
        cross_validation: crossValidation(item.cross_validation),
        requirement_evaluation: requirementEvaluation(item.requirement_evaluation),
        final_assessment: liveAssessment(item.final_assessment),
        review_decision: qualificationReviewDecision(item.review_decision),
      })),
      signals: candidate.signals.map((item) => signalResult(item, candidate.candidate_id, radar.radar_id)),
      score: {
        fit_score: candidate.score.fit_score ?? 0,
        intent_score: candidate.score.intent_score ?? 0,
        tier: candidate.score.tier ?? 'Tier 3',
      },
      review_flags: candidate.review_flags,
      evidence_refs: candidate.evidence_refs,
    })),
    journal_events: journal?.events.map((event) => ({
      event_id: event.event_id,
      run_id: event.run_id,
      sequence: event.sequence,
      event_type: event.event_type,
      phase: event.phase,
      actor: event.actor,
      node_name: event.node_name,
      visibility: event.visibility,
      summary: event.summary,
      payload: event.payload,
      source_refs: event.source_refs,
      candidate_refs: event.candidate_refs,
      created_at: event.created_at,
    })) ?? [],
    dossier: normalizedDossier,
    technical_trace: technicalTrace ? runTechnicalTrace(technicalTrace) : undefined,
    contract_validation: candidates.contract_validation.map((item) => ({
      severity: item.severity === 'error' ? 'error' : 'warning',
      path: stringField(item.path, ''),
      message: stringField(item.message, ''),
    })),
  };
}

function runTechnicalTrace(trace: RadarRunTechnicalTraceDto): LiveRadarTechnicalTrace {
  return {
    run_id: trace.run_id,
    radar_id: trace.radar_id,
    traces: trace.traces.map((item) => ({
      trace_id: item.trace_id,
      run_id: item.run_id,
      sequence: item.sequence,
      phase: item.phase,
      node_name: item.node_name,
      trace_type: item.trace_type,
      title: item.title,
      summary: item.summary,
      duration_ms: item.duration_ms,
      payload: item.payload,
      redaction_report: item.redaction_report,
      created_at: item.created_at,
    })),
  };
}

function runDossier(dossier: RadarRunDossierDto): LiveRadarRunDossier {
  return {
    run_context: dossier.run_context,
    runtime_config: dossier.runtime_config ?? {},
    runtime_config_warnings: dossier.runtime_config_warnings ?? [],
    radar_snapshot: dossier.radar_snapshot,
    definition_snapshot: dossier.definition_snapshot,
    discovery_plan: {
      ...dossier.discovery_plan,
      plan_summary: stringField(dossier.discovery_plan.plan_summary, ''),
      steps: arrayField(dossier.discovery_plan.steps).map((item) => ({
        step_id: stringField(item.step_id, ''),
        stage: stringField(item.stage, ''),
        subject_rule_ids: stringArray(item.subject_rule_ids),
        source_scope: stringField(item.source_scope, ''),
        source_ids: stringArray(item.source_ids),
        query: stringField(item.query, ''),
        purpose: stringField(item.purpose, ''),
        expected_evidence: stringArray(item.expected_evidence),
        acceptance_criteria: stringArray(item.acceptance_criteria),
        skip_rationale: nullableString(item.skip_rationale),
        depends_on: stringArray(item.depends_on),
        candidate_scope: stringArray(item.candidate_scope),
      })),
      source_policy_decisions: arrayField(dossier.discovery_plan.source_policy_decisions).map(sourcePolicyDecision),
      coverage_hypotheses: arrayField(dossier.discovery_plan.coverage_hypotheses),
      warnings: stringArray(dossier.discovery_plan.warnings),
    },
    source_policy_decisions: dossier.source_policy_decisions.map(sourcePolicyDecision),
    coverage_summary: {
      ...dossier.coverage_summary,
      hypotheses: arrayField(dossier.coverage_summary.hypotheses),
      warnings: stringArray(dossier.coverage_summary.warnings),
      analyzed_source_count: numberField(dossier.coverage_summary.analyzed_source_count, dossier.summary.analyzed_source_count),
      used_source_count: numberField(dossier.coverage_summary.used_source_count, dossier.summary.used_source_count),
      rejected_candidate_count: numberField(dossier.coverage_summary.rejected_candidate_count, 0),
      coverage_check_count: numberField(dossier.coverage_summary.coverage_check_count, dossier.coverage_checks.length),
      unresolved_candidate_gap_count: numberField(dossier.coverage_summary.unresolved_candidate_gap_count, dossier.unresolved_candidate_gaps.length),
      discovery_iteration_count: numberField(dossier.coverage_summary.discovery_iteration_count, dossier.discovery_iteration_count),
      analyzed_source_reasons: stringArray(dossier.coverage_summary.analyzed_source_reasons),
    },
    candidate_universe: arrayField(dossier.candidate_universe).map((item) => ({
      candidate_id: stringField(item.candidate_id, ''),
      legal_name: stringField(item.legal_name, ''),
      status: stringField(item.status, 'discovered'),
      origin_task_id: stringField(item.origin_task_id, ''),
      source_refs: stringArray(item.source_refs),
      gate_results: arrayField(item.gate_results),
      rejection_reasons: stringArray(item.rejection_reasons),
      coverage_flags: stringArray(item.coverage_flags),
    })),
    coverage_checks: arrayField(dossier.coverage_checks),
    coverage_warnings: stringArray(dossier.coverage_warnings),
    unresolved_candidate_gaps: arrayField(dossier.unresolved_candidate_gaps),
    discovery_iteration_count: numberField(dossier.discovery_iteration_count, 0),
    search_plan: dossier.search_plan,
    sources: dossier.sources,
    source_lifecycle: arrayField(dossier.source_lifecycle).map((item) => ({
      evidence_ref: stringField(item.evidence_ref, ''),
      title: stringField(item.title, ''),
      url: stringField(item.url, ''),
      query_id: nullableString(item.query_id),
      source_type: stringField(item.source_type, 'web'),
      state: stringField(item.state, 'discarded'),
      reason: stringField(item.reason, 'unknown'),
      origin: stringField(item.origin, 'unknown'),
      verification_state: nullableString(item.verification_state),
      verification_mode: nullableString(item.verification_mode),
      verification_reason: nullableString(item.verification_reason),
      verification_status_code: nullableNumber(item.verification_status_code),
      usages: arrayField(item.usages).map((usage) => ({
        candidate_id: stringField(usage.candidate_id, ''),
        candidate_name: stringField(usage.candidate_name, ''),
        subject_type: stringField(usage.subject_type, ''),
        subject_id: stringField(usage.subject_id, ''),
        subject_label: stringField(usage.subject_label, ''),
      })),
    })),
    source_lifecycle_summary: {
      total_count: numberField(dossier.source_lifecycle_summary?.total_count, 0),
      by_state: recordNumberField(dossier.source_lifecycle_summary?.by_state),
      by_reason: recordNumberField(dossier.source_lifecycle_summary?.by_reason),
    },
    validation: dossier.validation,
    timeline: dossier.timeline.map((event) => ({
      event_id: event.event_id,
      run_id: event.run_id,
      sequence: event.sequence,
      event_type: event.event_type,
      phase: event.phase,
      actor: event.actor,
      node_name: event.node_name,
      visibility: event.visibility,
      summary: event.summary,
      payload: event.payload,
      source_refs: event.source_refs,
      candidate_refs: event.candidate_refs,
      created_at: event.created_at,
    })),
    summary: dossier.summary,
  };
}

function sourcePolicyDecision(value: Record<string, unknown>) {
  return {
    source_id: stringField(value.source_id, ''),
    source_label: stringField(value.source_label, ''),
    decision: stringField(value.decision, ''),
    reason: stringField(value.reason, ''),
    rule_ids: stringArray(value.rule_ids),
  };
}

function recordNumberField(value: unknown): Record<string, number> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return {};
  }
  return Object.fromEntries(
    Object.entries(value).map(([key, entry]) => [key, numberField(entry, 0)]),
  );
}

function signalResult(
  item: RadarRunCandidatesDto['candidates'][number]['signals'][number],
  candidateId: string,
  radarId: string,
): LiveRadarSignalResult {
  return {
    signal_code: item.signal_code,
    signal: item.signal,
    status: liveSignalStatus(item.status),
    score: item.score,
    confidence: item.confidence,
    summary: item.summary,
    evidence_refs: item.evidence_refs,
    source_usages: item.source_usages.map(sourceUsage),
    evidence_findings: item.evidence_findings.map(signalFinding),
    cross_validation: crossValidation(item.cross_validation),
    score_evaluation: scoreEvaluation(item.score_evaluation),
    review_decision: signalReviewDecision(item.review_decision, item.signal_code, candidateId, radarId, item.score, item.evidence_refs),
  };
}

function sourceUsage(item: SourceUsageDto): QualificationSourceUsage {
  return {
    source_ref: item.source_ref,
    source_name: item.source_name,
    source_origin: liveSourceOrigin(item.source_origin),
    trust_policy: liveTrustPolicy(item.trust_policy),
    used_for: item.used_for,
    url: item.url,
  };
}

function qualificationFinding(item: EvidenceFindingDto): QualificationEvidenceFinding {
  return {
    source_ref: item.source_ref,
    fact: item.fact,
    excerpt: item.excerpt,
    excerpt_type: excerptType(item.excerpt_type),
    why_it_matches_rule: item.why_it_matches_rule ?? '',
    evidence_strength: evidenceStrength(item.evidence_strength),
    contradicts_rule: Boolean(item.contradicts_rule),
  };
}

function signalFinding(item: EvidenceFindingDto): SignalEvidenceFinding {
  return {
    source_ref: item.source_ref,
    fact: item.fact,
    excerpt: item.excerpt,
    excerpt_type: excerptType(item.excerpt_type),
    why_it_matches_signal: item.why_it_matches_signal ?? '',
    why_score_applies: item.why_score_applies ?? '',
    evidence_strength: evidenceStrength(item.evidence_strength),
    contradicts_signal: Boolean(item.contradicts_signal),
  };
}

function qualificationReviewDecision(value: Record<string, unknown> | null) {
  if (!value || (value.status !== 'approved' && value.status !== 'rejected' && value.status !== 'corrected')) {
    return null;
  }
  const status = value.status as QualificationReviewDecision['status'];
  return {
    status,
    corrected_assessment: liveAssessment(value.corrected_assessment),
    comment: stringField(value.comment, ''),
    reviewed_at: stringField(value.reviewed_at, ''),
  };
}

function signalReviewDecision(
  value: Record<string, unknown> | null,
  signalCode: string,
  candidateId: string,
  radarId: string,
  originalScore: number,
  evidenceRefs: string[],
): SignalValidationDecision | null {
  if (!value || !['confirmed', 'rejected', 'stale', 'corrected'].includes(String(value.status))) {
    return null;
  }
  const adjustedScore = typeof value.adjusted_score === 'number' ? value.adjusted_score : null;
  return {
    radar_id: radarId,
    account_id: candidateId,
    signal_code: signalCode,
    status: value.status as SignalValidationDecision['status'],
    original_score: originalScore,
    adjusted_score: adjustedScore,
    confidence: nullableString(value.confidence),
    corrected_summary: nullableString(value.corrected_summary),
    evidence_refs: Array.isArray(value.evidence_refs) ? value.evidence_refs.map(String) : evidenceRefs,
    comment: stringField(value.comment, ''),
    reviewed_at: stringField(value.reviewed_at, ''),
  };
}

function emptyDefinition(detail: RadarDetailDto): RadarDefinition {
  return {
    definition_id: detail.active_definition?.definition_id ?? `${detail.radar_id}-definition`,
    metadata: {
      name: detail.name,
      description: '',
      owner: detail.owner,
      status: detail.status,
    },
    global_search_policy: {
      sources: [],
      keywords: [],
      exclusions: [],
      allow_system_sources: true,
    },
    account_qualification: {
      rule_group: {
        group_id: 'empty',
        name: 'Empty qualification model',
        operator: 'AND',
        rules: [],
        groups: [],
      },
    },
    intent_signals: [],
    monitoring_policy: {
      cadence: '',
      lookback_window: '',
      run_mode: '',
      deduplication: '',
      stale_after: '',
    },
    scoring_model: {
      fit_model: {
        formula_preset: '',
        description: '',
        custom_formula: '',
        uses: [],
      },
      intent_model: {
        formula_preset: '',
        description: '',
        custom_formula: '',
        uses: [],
      },
      tier_model: {
        basis: '',
        description: '',
      },
      tier_thresholds: {},
      confidence_penalties: {},
    },
    validation_report: {
      errors: [],
      warnings: [],
      info: [],
    },
  };
}

function flattenQualificationRules(group: RadarDefinition['account_qualification']['rule_group']): Array<{ rule_id: string; name: string; description: string }> {
  return [
    ...group.rules,
    ...group.groups.flatMap((child) => flattenQualificationRules(child)),
  ];
}

function crossValidation(value: Record<string, unknown>): QualificationCrossValidation {
  return {
    required: Boolean(value.required),
    status: value.status === 'passed' || value.status === 'weak' || value.status === 'failed' ? value.status : 'not_required',
    source_count: numberField(value.source_count, 0),
    notes: stringField(value.notes, ''),
  };
}

function requirementEvaluation(value: Record<string, unknown>): QualificationRequirementEvaluation {
  return {
    requirement_level: liveRequirementLevel(value.requirement_level),
    satisfied: typeof value.satisfied === 'boolean' ? value.satisfied : null,
    explanation: stringField(value.explanation, ''),
  };
}

function scoreEvaluation(value: Record<string, unknown> | null): SignalScoreEvaluation | null {
  if (!value) {
    return null;
  }
  return {
    scale: stringField(value.scale, '0..2'),
    applied_score: numberField(value.applied_score, 0),
    max_score: numberField(value.max_score, 2),
    rule_snapshot: stringField(value.rule_snapshot, ''),
    explanation: stringField(value.explanation, ''),
  };
}

function liveQualificationStatus(value: string) {
  return value === 'confirmed' || value === 'weak' || value === 'rejected' ? value : 'unknown';
}

function liveSignalStatus(value: string) {
  return value === 'observed' || value === 'not_observed' ? value : 'unclear';
}

function liveOperator(value: unknown) {
  return value === 'OR' || value === 'AND_NOT' || value === 'OR_NOT' ? value : 'AND';
}

function liveRequirementLevel(value: unknown): QualificationRequirementLevel {
  return value === 'recommended' ? 'recommended' : 'required';
}

function liveSourceOrigin(value: string): QualificationSourceOrigin {
  return value === 'global' || value === 'local' ? value : 'additional';
}

function liveTrustPolicy(value: unknown): QualificationTrustPolicy {
  return value === 'trusted' || value === 'cross_checked' ? value : 'hitl_required';
}

function liveAssessment(value: unknown): QualificationAssessmentStatus {
  if (value === 'matches' || value === 'partially_matches' || value === 'does_not_match') {
    return value;
  }
  return 'unknown';
}

function evidenceStrength(value: string) {
  return value === 'strong' || value === 'medium' ? value : 'weak';
}

function excerptType(value: string) {
  return value === 'quote' || value === 'paraphrase' ? value : 'not_available';
}

function stringField(value: unknown, fallback: string) {
  return typeof value === 'string' && value.length > 0 ? value : fallback;
}

function nullableString(value: unknown) {
  return typeof value === 'string' && value.length > 0 ? value : null;
}

function numberField(value: unknown, fallback: number) {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function nullableNumber(value: unknown) {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function arrayField(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value) ? value.filter((item): item is Record<string, unknown> => item !== null && typeof item === 'object' && !Array.isArray(item)) : [];
}

function stringArray(value: unknown) {
  return Array.isArray(value) ? value.map(String).filter(Boolean) : [];
}
