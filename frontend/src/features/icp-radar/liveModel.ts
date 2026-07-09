import type {
  LiveRadarCandidate,
  LiveRadarQualificationResult,
  LiveRadarSignalResult,
  LiveRadarSourceEvidence,
  QualificationAssessmentStatus,
  QualificationReviewDecision,
  QualificationSourceUsage,
} from '../../types';

export function liveTotalScore(candidate: LiveRadarCandidate): number {
  return candidate.score.fit_score + candidate.score.intent_score;
}

export function liveFitScoreMax(candidate: LiveRadarCandidate): number {
  return Math.max(candidate.qualification.length, candidate.score.fit_score);
}

export function liveIntentScoreMax(candidate: LiveRadarCandidate): number {
  return Math.max(candidate.signals.length * 2, candidate.score.intent_score);
}

export function liveTotalScoreMax(candidate: LiveRadarCandidate): number {
  return liveFitScoreMax(candidate) + liveIntentScoreMax(candidate);
}

export function scoreWithMax(score: number, maxScore: number): string {
  return `${score} / ${Math.max(score, maxScore)}`;
}

export function cadenceKey(cadence: string) {
  if (cadence === 'weekly') {
    return 'icpRadar.cadence.weekly';
  }
  if (cadence === 'monthly') {
    return 'icpRadar.cadence.monthly';
  }
  return 'icpRadar.cadence.unknown';
}

export function lastRunKey(lastRun: string) {
  return ({
    not_run: 'icpRadar.lastRun.notRun',
    not_scheduled: 'icpRadar.lastRun.notScheduled',
    backend_run: 'icpRadar.lastRun.backendRun',
  } as Record<string, string>)[lastRun] ?? 'icpRadar.lastRun.fixture';
}

export function runModeKey(runMode: string) {
  return ({
    incremental_signal_monitoring: 'icpRadar.runMode.incremental',
    configured_not_generated: 'icpRadar.runMode.configured',
    planned: 'icpRadar.runMode.planned',
    fixture_import: 'icpRadar.runMode.fixtureImport',
    benchmark: 'icpRadar.runMode.benchmark',
    live_cli: 'icpRadar.runMode.backendApi',
    backend_api: 'icpRadar.runMode.backendApi',
  } as Record<string, string>)[runMode] ?? 'icpRadar.runMode.unknown';
}

export function liveRuntimeKey(runtime: string) {
  if (runtime === 'openrouter_live') {
    return 'icpRadar.live.runtimeOpenRouter';
  }
  if (runtime === 'langgraph_dai') {
    return 'icpRadar.live.runtimeLanggraph';
  }
  if (runtime === 'recorded') {
    return 'icpRadar.live.runtimeRecorded';
  }
  return 'icpRadar.live.runtimeUnknown';
}

export function liveQualificationTone(status: LiveRadarQualificationResult['status']) {
  if (status === 'confirmed') {
    return 'ally';
  }
  if (status === 'rejected') {
    return 'blocker';
  }
  if (status === 'weak') {
    return 'unsurfaced';
  }
  return 'neutral';
}

export function qualificationRuleId(item: LiveRadarQualificationResult) {
  return item.rule_id || item.criterion_code;
}

export function qualificationRuleText(item: LiveRadarQualificationResult) {
  return item.rule_text_snapshot || item.criterion || item.criterion_code;
}

export function effectiveQualificationAssessment(
  item: LiveRadarQualificationResult,
  decision: QualificationReviewDecision | null,
): QualificationAssessmentStatus {
  if (decision?.status === 'approved') {
    return item.final_assessment || qualificationStatusToAssessment(item.status);
  }
  if (decision?.status === 'rejected') {
    return 'does_not_match';
  }
  if (decision?.status === 'corrected' && decision.corrected_assessment) {
    return decision.corrected_assessment;
  }
  return item.final_assessment || qualificationStatusToAssessment(item.status);
}

export function qualificationStatusToAssessment(status: LiveRadarQualificationResult['status']): QualificationAssessmentStatus {
  if (status === 'confirmed') {
    return 'matches';
  }
  if (status === 'weak') {
    return 'partially_matches';
  }
  if (status === 'rejected') {
    return 'does_not_match';
  }
  return 'unknown';
}

export function qualificationAssessmentTone(status: QualificationAssessmentStatus) {
  if (status === 'matches') {
    return 'ally';
  }
  if (status === 'does_not_match') {
    return 'blocker';
  }
  if (status === 'partially_matches') {
    return 'unsurfaced';
  }
  return 'neutral';
}

export function qualificationDecisionTone(status: QualificationReviewDecision['status']) {
  if (status === 'approved') {
    return 'ally';
  }
  if (status === 'rejected') {
    return 'blocker';
  }
  return 'unsurfaced';
}

export function qualificationTrustTone(status: string) {
  if (status === 'trusted' || status === 'cross_checked') {
    return 'ally';
  }
  return 'unsurfaced';
}

export function qualificationCrossValidationTone(status?: string) {
  if (status === 'passed') {
    return 'ally';
  }
  if (status === 'failed') {
    return 'blocker';
  }
  if (status === 'weak') {
    return 'unsurfaced';
  }
  return 'neutral';
}

export type QualificationRequirementEvaluationView = {
  requirementLevel: 'required' | 'recommended';
  evidenceStrength: 'strong' | 'weak' | 'none';
  confidence: 'high' | 'medium' | 'low' | 'unknown';
  recommendedAction: 'none' | 'review' | 'reject';
};

export function qualificationRequirementEvaluationView(
  item: LiveRadarQualificationResult,
): QualificationRequirementEvaluationView {
  const evidenceStrength = item.evidence_findings?.some((finding) => finding.evidence_strength === 'strong')
    ? 'strong'
    : item.evidence_findings?.length
      ? 'weak'
      : 'none';
  const assessment = item.final_assessment || qualificationStatusToAssessment(item.status);
  const confidence = item.confidence === 'high' || item.confidence === 'medium' || item.confidence === 'low'
    ? item.confidence
    : 'unknown';
  const recommendedAction = assessment === 'does_not_match'
    ? 'reject'
    : assessment === 'partially_matches' || confidence !== 'high'
      ? 'review'
      : 'none';

  return {
    requirementLevel: item.requirement_level === 'recommended' ? 'recommended' : 'required',
    evidenceStrength,
    confidence,
    recommendedAction,
  };
}

export function qualificationOperatorLabel(operator: string) {
  if (operator === 'AND_NOT') {
    return 'AND NOT';
  }
  if (operator === 'OR_NOT') {
    return 'OR NOT';
  }
  return operator || 'AND';
}

export function fallbackQualificationSourceUsages(
  item: LiveRadarQualificationResult,
  sourcesByRef: Map<string, LiveRadarSourceEvidence>,
): QualificationSourceUsage[] {
  return item.evidence_refs
    .map((ref) => sourcesByRef.get(ref))
    .filter((source): source is LiveRadarSourceEvidence => Boolean(source))
    .map((source) => ({
      source_ref: source.evidence_ref,
      source_name: source.title,
      source_origin: 'additional',
      trust_policy: item.confidence === 'high' ? 'trusted' : 'hitl_required',
      used_for: 'verification',
      url: source.url,
    }));
}

export function qualificationReviewKey(radarId: string, candidateId: string, ruleId: string) {
  return `${radarId}:${candidateId}:${ruleId}`;
}

export function liveSignalTone(status: LiveRadarSignalResult['status']) {
  if (status === 'observed') {
    return 'ally';
  }
  if (status === 'unclear') {
    return 'unsurfaced';
  }
  return 'neutral';
}
