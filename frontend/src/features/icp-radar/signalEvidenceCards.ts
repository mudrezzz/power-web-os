import type {
  LiveRadarSignalResult,
  LiveRadarSourceEvidence,
  QualificationCrossValidation,
  QualificationSourceUsage,
  SignalEvidenceFinding,
  SignalValidationDecision,
} from '../../types';

// Owns the signal review view models: source-linked evidence cards and the
// displayed score evaluation derived from live artifacts plus local validation.
export type SignalEvidenceCardView = {
  sourceRef: string;
  sourceName: string;
  sourceUrl: string;
  sourceOrigin: QualificationSourceUsage['source_origin'];
  trustPolicy: QualificationSourceUsage['trust_policy'];
  fact: string;
  excerpt: string;
  excerptType: NonNullable<SignalEvidenceFinding['excerpt_type']>;
  whyItMatchesSignal: string;
  whyScoreApplies: string;
  evidenceStrength: SignalEvidenceFinding['evidence_strength'];
  contradictsSignal: boolean;
};

export type SignalScoreEvaluationView = {
  scale: string;
  ruleSnapshot: string;
  foundFact: string;
  originalScore: number;
  effectiveScore: number;
  delta: number;
  confidence: string;
  crossValidationStatus: NonNullable<QualificationCrossValidation['status']>;
  recommendedAction: 'none' | 'review' | 'reject';
};

export function signalEvidenceCardViews(
  item: LiveRadarSignalResult,
  sourcesByRef: Map<string, LiveRadarSourceEvidence>,
): SignalEvidenceCardView[] {
  const sourceUsages = item.source_usages?.length
    ? item.source_usages
    : fallbackSignalSourceUsages(item, sourcesByRef);
  const usagesByRef = new Map(sourceUsages.map((usage) => [usage.source_ref, usage]));
  const findings = item.evidence_findings?.length
    ? item.evidence_findings
    : fallbackSignalEvidenceFindings(item, sourcesByRef);

  return findings.map((finding) => {
    const usage = usagesByRef.get(finding.source_ref);
    const source = sourcesByRef.get(finding.source_ref);
    return {
      sourceRef: finding.source_ref,
      sourceName: usage?.source_name || source?.title || finding.source_ref,
      sourceUrl: usage?.url || source?.url || '',
      sourceOrigin: usage?.source_origin || 'additional',
      trustPolicy: usage?.trust_policy || (item.confidence === 'high' ? 'trusted' : 'hitl_required'),
      fact: finding.fact || source?.snippet || item.summary,
      excerpt: finding.excerpt || source?.snippet || '',
      excerptType: finding.excerpt_type || (finding.excerpt ? 'paraphrase' : 'not_available'),
      whyItMatchesSignal: finding.why_it_matches_signal || item.summary,
      whyScoreApplies: finding.why_score_applies || signalScoreRationale(item),
      evidenceStrength: finding.evidence_strength,
      contradictsSignal: finding.contradicts_signal,
    };
  });
}

export function signalScoreEvaluationView(
  item: LiveRadarSignalResult,
  decision: SignalValidationDecision | null,
): SignalScoreEvaluationView {
  const effectiveScore = signalEffectiveScore(item, decision);
  const evidenceCards = item.evidence_findings ?? [];
  const firstFact = evidenceCards[0]?.fact || item.summary;
  return {
    scale: item.score_evaluation?.scale || '0-2',
    ruleSnapshot: item.score_evaluation?.rule_snapshot || signalScoreRule(item.score),
    foundFact: firstFact,
    originalScore: item.score,
    effectiveScore,
    delta: effectiveScore - item.score,
    confidence: decision?.confidence || item.confidence || 'unknown',
    crossValidationStatus: item.cross_validation?.status ?? 'not_required',
    recommendedAction: signalRecommendedAction(item, decision),
  };
}

export function signalEffectiveScore(item: LiveRadarSignalResult, decision: SignalValidationDecision | null) {
  if (!decision || decision.status === 'confirmed') {
    return item.score;
  }
  if (decision.status === 'corrected') {
    return Math.max(0, Math.min(2, decision.adjusted_score ?? item.score));
  }
  return 0;
}

function fallbackSignalSourceUsages(
  item: LiveRadarSignalResult,
  sourcesByRef: Map<string, LiveRadarSourceEvidence>,
): QualificationSourceUsage[] {
  return item.evidence_refs
    .map((ref) => {
      const source = sourcesByRef.get(ref);
      if (!source) {
        return null;
      }
      const usage: QualificationSourceUsage = {
        source_ref: ref,
        source_name: source.title,
        source_origin: 'additional',
        trust_policy: item.confidence === 'high' ? 'trusted' : 'hitl_required',
        used_for: item.signal,
        url: source.url,
      };
      return usage;
    })
    .filter((usage): usage is QualificationSourceUsage => Boolean(usage));
}

function fallbackSignalEvidenceFindings(
  item: LiveRadarSignalResult,
  sourcesByRef: Map<string, LiveRadarSourceEvidence>,
): SignalEvidenceFinding[] {
  return item.evidence_refs.map((ref) => {
    const source = sourcesByRef.get(ref);
    return {
      source_ref: ref,
      fact: source?.snippet || item.summary,
      excerpt: '',
      excerpt_type: 'not_available',
      why_it_matches_signal: item.summary,
      why_score_applies: signalScoreRationale(item),
      evidence_strength: item.status === 'observed' && item.score >= 2 ? 'strong' : item.status === 'observed' ? 'medium' : 'weak',
      contradicts_signal: item.status === 'not_observed',
    };
  });
}

function signalScoreRule(score: number) {
  if (score >= 2) {
    return '2: direct source-backed signal.';
  }
  if (score === 1) {
    return '1: weak or indirect source-backed signal.';
  }
  return '0: not observed or not source-backed.';
}

function signalScoreRationale(item: LiveRadarSignalResult) {
  if (item.status !== 'observed') {
    return 'Signal is not observed or remains unclear, so it contributes 0.';
  }
  return `Score ${item.score}: ${item.summary}`;
}

function signalRecommendedAction(item: LiveRadarSignalResult, decision: SignalValidationDecision | null): SignalScoreEvaluationView['recommendedAction'] {
  if (decision?.status === 'rejected' || decision?.status === 'stale') {
    return 'reject';
  }
  if (item.status === 'unclear' || item.confidence === 'low') {
    return 'review';
  }
  return 'none';
}
