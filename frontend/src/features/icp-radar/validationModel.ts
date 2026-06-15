import type {
  ICPRadarArtifact,
  ICPRadarCandidate,
  QualificationAssessmentStatus,
  QualificationReviewDecision,
  SignalValidationDecision,
  SignalValidationOverlay,
  SignalValidationStatus,
  ValidatedCandidateScore,
} from '../../types';
import {
  fitSignalCodes,
  intentSignalCodes,
  qualificationReviewStorageKey,
  signalCodes,
  signalValidationStorageKey,
  triggerSignalCodes,
  type QualificationReviewOverlay,
} from './modelTypes';

export function loadSignalValidationOverlay(): SignalValidationOverlay {
  try {
    const raw = window.localStorage.getItem(signalValidationStorageKey);
    if (!raw) {
      return {};
    }
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return Object.fromEntries(
      Object.entries(parsed)
        .map(([key, value]) => [key, normalizeSignalValidationDecision(value)])
        .filter((entry): entry is [string, SignalValidationDecision] => entry[1] !== null),
    );
  } catch {
    window.localStorage.removeItem(signalValidationStorageKey);
    return {};
  }
}

export function loadQualificationReviewOverlay(): QualificationReviewOverlay {
  try {
    const raw = window.localStorage.getItem(qualificationReviewStorageKey);
    if (!raw) {
      return {};
    }
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return Object.fromEntries(
      Object.entries(parsed)
        .map(([key, value]) => [key, normalizeQualificationReviewDecision(value)])
        .filter((entry): entry is [string, QualificationReviewDecision] => entry[1] !== null),
    );
  } catch {
    window.localStorage.removeItem(qualificationReviewStorageKey);
    return {};
  }
}

export function normalizeQualificationReviewDecision(value: unknown): QualificationReviewDecision | null {
  if (!value || typeof value !== 'object') {
    return null;
  }
  const item = value as Partial<QualificationReviewDecision>;
  if (item.status !== 'approved' && item.status !== 'rejected' && item.status !== 'corrected') {
    return null;
  }
  const corrected = isQualificationAssessment(item.corrected_assessment) ? item.corrected_assessment : null;
  return {
    status: item.status,
    corrected_assessment: corrected,
    comment: String(item.comment ?? ''),
    reviewed_at: String(item.reviewed_at ?? ''),
  };
}

export function isQualificationAssessment(value: unknown): value is QualificationAssessmentStatus {
  return value === 'matches'
    || value === 'partially_matches'
    || value === 'does_not_match'
    || value === 'unknown';
}

export function normalizeSignalValidationDecision(value: unknown): SignalValidationDecision | null {
  if (!value || typeof value !== 'object') {
    return null;
  }
  const item = value as Partial<SignalValidationDecision>;
  if (!item.radar_id || !item.account_id || !item.signal_code || !isSignalValidationStatus(item.status)) {
    return null;
  }
  const originalScore = Number(item.original_score);
  const adjustedScore = item.adjusted_score === null || item.adjusted_score === undefined
    ? null
    : Number(item.adjusted_score);
  return {
    radar_id: String(item.radar_id),
    account_id: String(item.account_id),
    signal_code: String(item.signal_code),
    status: item.status,
    original_score: Number.isFinite(originalScore) ? originalScore : 0,
    adjusted_score: adjustedScore !== null && Number.isFinite(adjustedScore) ? adjustedScore : null,
    confidence: item.confidence ?? null,
    corrected_summary: item.corrected_summary ?? null,
    evidence_refs: Array.isArray(item.evidence_refs) ? item.evidence_refs.map(String) : [],
    comment: item.comment ?? '',
    reviewed_at: item.reviewed_at ?? '',
  };
}

export function isSignalValidationStatus(status: unknown): status is SignalValidationStatus {
  return status === 'unreviewed'
    || status === 'confirmed'
    || status === 'corrected'
    || status === 'rejected'
    || status === 'stale';
}

export function signalValidationKey(radarId: string, accountId: string, signalCode: string) {
  return `${radarId}:${accountId}:${signalCode}`;
}

export function validationForCandidate(
  overlay: SignalValidationOverlay,
  radarId: string,
  accountId: string,
): Record<string, SignalValidationDecision> {
  return Object.fromEntries(
    Object.values(overlay)
      .filter((decision) => decision.radar_id === radarId && decision.account_id === accountId)
      .map((decision) => [decision.signal_code, decision]),
  );
}

export function validatedCandidatesForArtifact(
  artifact: ICPRadarArtifact,
  radarId: string,
  overlay: SignalValidationOverlay,
) {
  return artifact.candidates
    .map((candidate) => ({
      candidate,
      score: buildValidatedCandidateScore(candidate, validationForCandidate(overlay, radarId, candidate.account_id)),
    }))
    .sort((left, right) => right.score.effective_score.total_score - left.score.effective_score.total_score
      || right.score.effective_score.intent_score - left.score.effective_score.intent_score
      || left.candidate.legal_name.localeCompare(right.candidate.legal_name, 'ru'));
}

export function buildValidatedCandidateScore(
  candidate: ICPRadarCandidate,
  decisions: Record<string, SignalValidationDecision> = {},
): ValidatedCandidateScore {
  const status_counts: ValidatedCandidateScore['status_counts'] = {
    unreviewed: 0,
    confirmed: 0,
    corrected: 0,
    rejected: 0,
    stale: 0,
  };
  const effectiveScores: Record<string, number> = {};
  const signal_scores: ValidatedCandidateScore['signal_scores'] = {};

  signalCodes.forEach((code) => {
    const originalScore = Number(candidate.criteria_scores[code] ?? 0);
    const decision = decisions[code];
    const status = decision?.status ?? 'unreviewed';
    let effectiveScore = originalScore;
    if (status === 'corrected') {
      effectiveScore = Math.max(0, Number(decision?.adjusted_score ?? originalScore));
    }
    if (status === 'rejected' || status === 'stale') {
      effectiveScore = 0;
    }
    status_counts[status] += 1;
    effectiveScores[code] = effectiveScore;
    signal_scores[code] = {
      signal_code: code,
      original_score: originalScore,
      effective_score: effectiveScore,
      delta: effectiveScore - originalScore,
      status,
    };
  });

  return {
    original_score: candidate.score,
    effective_score: buildCandidateScore(effectiveScores),
    signal_scores,
    status_counts,
  };
}

export function buildCandidateScore(scores: Record<string, number>) {
  const sumCodes = (codes: string[]) => codes.reduce((total, code) => total + Number(scores[code] ?? 0), 0);
  const fit_score = sumCodes(fitSignalCodes);
  const intent_score = sumCodes(intentSignalCodes);
  const trigger_score = sumCodes(triggerSignalCodes);
  const total_score = fit_score + intent_score + trigger_score;
  return {
    fit_score,
    intent_score,
    trigger_score,
    total_score,
    tier: tierForTotal(total_score),
  };
}

export function tierForTotal(totalScore: number) {
  if (totalScore >= 38) {
    return 'Tier 1';
  }
  if (totalScore >= 25) {
    return 'Tier 2';
  }
  if (totalScore >= 15) {
    return 'Tier 3';
  }
  return 'Monitor';
}

export function formatDelta(delta: number) {
  return delta > 0 ? `+${delta}` : String(delta);
}

export function validationStatusKey(status: SignalValidationStatus) {
  return `icpRadar.reviewStatus.${status}`;
}

export function validationTone(status: SignalValidationStatus) {
  if (status === 'confirmed') {
    return 'ally';
  }
  if (status === 'rejected' || status === 'stale') {
    return 'blocker';
  }
  if (status === 'corrected') {
    return 'cobalt';
  }
  return 'neutral';
}

export function validationRank(status: SignalValidationStatus) {
  if (status === 'rejected' || status === 'stale') {
    return 0;
  }
  if (status === 'corrected') {
    return 1;
  }
  if (status === 'confirmed') {
    return 2;
  }
  return 3;
}
