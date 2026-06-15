import { Check, ChevronDown, ChevronRight, ExternalLink, RotateCcw, ShieldCheck, SlidersHorizontal, X } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Eyebrow, Mono } from '../../components/primitives';
import type {
  CriterionEvidenceExplanation,
  ICPRadarArtifact,
  ICPRadarCandidate,
  IntentSignalDefinition,
  SignalValidationDecision,
  SignalValidationOverlay,
  SignalValidationStatus,
  ValidatedCandidateScore,
} from '../../types';
import {
  formatDelta,
  signalValidationKey,
  validationRank,
  validationStatusKey,
  validationTone,
} from './model';

// The C1-C20 breakdown is table-first: scan rows first, expand only when reviewing evidence or editing local validation.

type CriterionFilter = 'all' | 'needs_review' | 'confirmed' | 'corrected' | 'rejected' | 'stale';
type CriterionSort = 'score_desc' | 'status' | 'confidence';

export function CriteriaBreakdown({
  artifact,
  candidate,
  onDecisionChange,
  radarId,
  signalValidation,
  validatedScore,
}: {
  artifact: ICPRadarArtifact;
  candidate: ICPRadarCandidate;
  onDecisionChange: (decision: SignalValidationDecision) => void;
  radarId: string;
  signalValidation: SignalValidationOverlay;
  validatedScore: ValidatedCandidateScore;
}) {
  const { t } = useTranslation();
  const [expandedCriterionCode, setExpandedCriterionCode] = useState<string | null>(null);
  const [filter, setFilter] = useState<CriterionFilter>('all');
  const [sort, setSort] = useState<CriterionSort>('score_desc');
  const rows = useMemo(() => (
    artifact.radar.definition.intent_signals
      .map((criterion) => {
        const evidence = candidate.criteria_evidence[criterion.code];
        const decision = signalValidation[signalValidationKey(radarId, candidate.account_id, criterion.code)];
        const signalScore = validatedScore.signal_scores[criterion.code];
        return {
          criterion,
          decision,
          evidence,
          signalScore,
          score: signalScore?.original_score ?? evidence?.score ?? candidate.criteria_scores[criterion.code] ?? 0,
        };
      })
      .filter((row) => matchesCriterionFilter(row.evidence, row.decision, filter))
      .sort((left, right) => compareCriterionRows(left, right, sort))
  ), [
    artifact.radar.definition.intent_signals,
    candidate.account_id,
    candidate.criteria_evidence,
    candidate.criteria_scores,
    filter,
    radarId,
    signalValidation,
    sort,
    validatedScore.signal_scores,
  ]);

  const filterOptions: CriterionFilter[] = ['all', 'needs_review', 'confirmed', 'corrected', 'rejected', 'stale'];
  const sortOptions: CriterionSort[] = ['score_desc', 'status', 'confidence'];

  return (
    <div className="criteria-evidence-list" aria-label={t('icpRadar.criterionEvidence')}>
      <div className="criteria-review-toolbar" aria-label={t('icpRadar.criteriaReviewToolbar')}>
        <div className="criteria-review-control">
          <Mono>{t('icpRadar.filter')}</Mono>
          <div className="criteria-review-segmented">
            {filterOptions.map((option) => (
              <button
                aria-pressed={filter === option}
                className={`criteria-chip${filter === option ? ' criteria-chip-active' : ''}`}
                key={option}
                type="button"
                onClick={() => setFilter(option)}
              >
                {t(criterionFilterKey(option))}
              </button>
            ))}
          </div>
        </div>

        <label className="criteria-sort-field">
          <SlidersHorizontal aria-hidden="true" />
          <span>{t('icpRadar.sort')}</span>
          <select value={sort} onChange={(event) => setSort(event.target.value as CriterionSort)}>
            {sortOptions.map((option) => (
              <option key={option} value={option}>
                {t(criterionSortKey(option))}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="criteria-review-table">
        <div className="criteria-review-head">
          <span>{t('icpRadar.criteriaColumns.code')}</span>
          <span>{t('icpRadar.criteriaColumns.criterion')}</span>
          <span>{t('icpRadar.criteriaColumns.score')}</span>
          <span>{t('icpRadar.criteriaColumns.status')}</span>
          <span>{t('icpRadar.criteriaColumns.confidence')}</span>
          <span>{t('icpRadar.criteriaColumns.facts')}</span>
          <span>{t('icpRadar.criteriaColumns.review')}</span>
          <span className="criteria-action-head" aria-label={t('icpRadar.criteriaColumns.action')} />
        </div>

        {rows.map(({ criterion, decision, evidence, score, signalScore }) => {
          const expanded = expandedCriterionCode === criterion.code;
          const effectiveScore = signalScore?.effective_score ?? score;
          const adjusted = effectiveScore !== score;
          const statusLabel = evidence ? t(evidenceStatusKey(evidence.evidence_status)) : t('icpRadar.notObserved');
          const confidenceLabel = evidence ? t(confidenceKey(evidence.confidence)) : t('icpRadar.confidenceValues.none');
          const validationStatus = decision?.status ?? 'unreviewed';

          return (
            <div className={`criteria-review-record${expanded ? ' criteria-review-record-expanded' : ''}`} key={criterion.code}>
              <button
                aria-expanded={expanded}
                className="criteria-review-row"
                type="button"
                onClick={() => setExpandedCriterionCode(expanded ? null : criterion.code)}
              >
                <Mono>{criterion.code}</Mono>
                <span className="criteria-review-name">
                  <strong>{criterion.name}</strong>
                  <small>{criterion.description}</small>
                </span>
                <span className="criteria-score-inline">
                  <Mono>{score}</Mono>
                  {adjusted && (
                    <>
                      <span aria-hidden="true">-&gt;</span>
                      <Mono>{effectiveScore}</Mono>
                      <small className="score-delta">{formatDelta(effectiveScore - score)}</small>
                    </>
                  )}
                </span>
                <span>
                  <Badge tone={evidenceBadgeTone(evidence?.evidence_status ?? 'not_observed')}>{statusLabel}</Badge>
                </span>
                <span>
                  <Badge tone={confidenceTone(evidence?.confidence)}>{confidenceLabel}</Badge>
                </span>
                <Mono>{evidence?.facts.length ?? 0}</Mono>
                <span>
                  <Badge tone={validationTone(validationStatus)}>{t(validationStatusKey(validationStatus))}</Badge>
                </span>
                <span className="row-action">
                  {expanded ? <ChevronDown aria-hidden="true" /> : <ChevronRight aria-hidden="true" />}
                </span>
              </button>

              {expanded && evidence && (
                <CriterionEvidenceDetail
                  candidate={candidate}
                  criterion={criterion}
                  decision={decision}
                  evidence={evidence}
                  radarId={radarId}
                  signalScore={signalScore}
                  onDecision={onDecisionChange}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CriterionEvidenceDetail({
  candidate,
  criterion,
  decision,
  evidence,
  onDecision,
  radarId,
  signalScore,
}: {
  candidate: ICPRadarCandidate;
  criterion: IntentSignalDefinition;
  decision: SignalValidationDecision | undefined;
  evidence: CriterionEvidenceExplanation;
  onDecision: (decision: SignalValidationDecision) => void;
  radarId: string;
  signalScore: ValidatedCandidateScore['signal_scores'][string] | undefined;
}) {
  const { t } = useTranslation();
  const [draftScore, setDraftScore] = useState(decision?.adjusted_score ?? signalScore?.effective_score ?? evidence.score);
  const [confidence, setConfidence] = useState(decision?.confidence ?? evidence.confidence);
  const [correctedSummary, setCorrectedSummary] = useState(decision?.corrected_summary ?? '');
  const [selectedEvidenceRefs, setSelectedEvidenceRefs] = useState<string[]>(
    decision?.evidence_refs?.length ? decision.evidence_refs : evidence.evidence_refs,
  );
  const [comment, setComment] = useState(decision?.comment ?? '');
  const commentRequired = !comment.trim();

  function submitDecision(status: SignalValidationStatus) {
    const needsComment = status === 'corrected' || status === 'rejected' || status === 'stale';
    if (needsComment && commentRequired) {
      return;
    }
    onDecision({
      radar_id: radarId,
      account_id: candidate.account_id,
      signal_code: criterion.code,
      status,
      original_score: evidence.score,
      adjusted_score: status === 'corrected' ? draftScore : null,
      confidence: status === 'corrected' ? confidence : null,
      corrected_summary: status === 'corrected' ? correctedSummary : null,
      evidence_refs: status === 'corrected' ? selectedEvidenceRefs : evidence.evidence_refs,
      comment,
      reviewed_at: new Date().toISOString(),
    });
  }

  function toggleEvidenceRef(ref: string) {
    setSelectedEvidenceRefs((current) => (
      current.includes(ref) ? current.filter((item) => item !== ref) : [...current, ref]
    ));
  }

  return (
    <div className="criterion-evidence-detail">
      <div className="criterion-detail-topline">
        <Badge tone={evidenceBadgeTone(evidence.evidence_status)}>{t(evidenceStatusKey(evidence.evidence_status))}</Badge>
        <Badge tone={confidenceTone(evidence.confidence)}>{t(confidenceKey(evidence.confidence))}</Badge>
        <Badge tone={validationTone(decision?.status ?? 'unreviewed')}>{t(validationStatusKey(decision?.status ?? 'unreviewed'))}</Badge>
        <span className="criterion-origin-note">{t(evidenceOriginKey(evidence.evidence_origin))}</span>
      </div>

      <section>
        <Eyebrow>{t('icpRadar.rationale')}</Eyebrow>
        <p>{evidence.rationale}</p>
      </section>

      {evidence.facts.length ? (
        <section>
          <Eyebrow>{t('icpRadar.facts')}</Eyebrow>
          <div className="criterion-fact-list">
            {evidence.facts.map((fact) => (
              <div className="criterion-fact" key={`${criterion.code}-${fact.evidence_ref}-${fact.fact}`}>
                <ShieldCheck aria-hidden="true" />
                <div>
                  <strong>{fact.fact}</strong>
                  <small>{fact.why_it_matters}</small>
                  <a href={fact.source_url || undefined} target="_blank" rel="noreferrer">
                    <Mono>{fact.evidence_ref || t('icpRadar.source')}</Mono>
                    {fact.source_url && <ExternalLink aria-hidden="true" />}
                  </a>
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : (
        <p className="criterion-empty-note">{t('icpRadar.noCriterionFacts')}</p>
      )}

      <section className="criterion-review-panel">
        <div>
          <Eyebrow>{t('icpRadar.localValidation')}</Eyebrow>
          <p>{t('icpRadar.localValidationCopy')}</p>
        </div>
        <div className="criterion-review-form">
          <label>
            <span>{t('icpRadar.adjustedScore')}</span>
            <select value={draftScore} onChange={(event) => setDraftScore(Number(event.target.value))}>
              {[0, 1, 2, 3].map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>{t('icpRadar.confidenceOverride')}</span>
            <select
              value={confidence}
              onChange={(event) => setConfidence(event.target.value as CriterionEvidenceExplanation['confidence'])}
            >
              {(['high', 'medium', 'low', 'none'] as const).map((value) => (
                <option key={value} value={value}>
                  {t(confidenceKey(value))}
                </option>
              ))}
            </select>
          </label>
          <label className="criterion-comment-field">
            <span>{t('icpRadar.correctedSummary')}</span>
            <textarea
              placeholder={t('icpRadar.correctedSummaryPlaceholder')}
              value={correctedSummary}
              onChange={(event) => setCorrectedSummary(event.target.value)}
            />
          </label>
          {evidence.evidence_refs.length > 0 && (
            <fieldset className="criterion-evidence-ref-picker">
              <legend>{t('icpRadar.selectedEvidenceRefs')}</legend>
              {evidence.evidence_refs.map((ref) => (
                <label key={ref}>
                  <input
                    checked={selectedEvidenceRefs.includes(ref)}
                    type="checkbox"
                    onChange={() => toggleEvidenceRef(ref)}
                  />
                  <Mono>{ref}</Mono>
                </label>
              ))}
            </fieldset>
          )}
          <label className="criterion-comment-field">
            <span>{t('icpRadar.comment')}</span>
            <textarea
              placeholder={t('icpRadar.commentPlaceholder')}
              value={comment}
              onChange={(event) => setComment(event.target.value)}
            />
          </label>
          <div className="criterion-review-actions">
            <Button
              icon={<Check aria-hidden="true" />}
              variant="default"
              onClick={() => submitDecision('confirmed')}
            >
              {t('icpRadar.confirmSignal')}
            </Button>
            <Button
              disabled={commentRequired}
              icon={<X aria-hidden="true" />}
              variant="default"
              onClick={() => submitDecision('rejected')}
            >
              {t('icpRadar.rejectSignal')}
            </Button>
            <Button
              disabled={commentRequired}
              icon={<RotateCcw aria-hidden="true" />}
              variant="default"
              onClick={() => submitDecision('stale')}
            >
              {t('icpRadar.markSignalStale')}
            </Button>
            <Button
              disabled={commentRequired}
              icon={<SlidersHorizontal aria-hidden="true" />}
              variant="default"
              onClick={() => submitDecision('corrected')}
            >
              {t('icpRadar.correctSignal')}
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}

function matchesCriterionFilter(
  evidence: CriterionEvidenceExplanation | undefined,
  decision: SignalValidationDecision | undefined,
  filter: CriterionFilter,
) {
  if (filter === 'all') {
    return true;
  }
  if (filter === 'needs_review') {
    return !decision && (
      evidence?.evidence_status !== 'supported'
      || evidence.confidence === 'low'
      || evidence.confidence === 'none'
    );
  }
  return decision?.status === filter;
}

function compareCriterionRows(
  left: {
    evidence: CriterionEvidenceExplanation | undefined;
    decision: SignalValidationDecision | undefined;
    score: number;
    criterion: IntentSignalDefinition;
  },
  right: {
    evidence: CriterionEvidenceExplanation | undefined;
    decision: SignalValidationDecision | undefined;
    score: number;
    criterion: IntentSignalDefinition;
  },
  sort: CriterionSort,
) {
  if (sort === 'status') {
    return validationRank(left.decision?.status ?? 'unreviewed') - validationRank(right.decision?.status ?? 'unreviewed')
      || right.score - left.score
      || left.criterion.code.localeCompare(right.criterion.code);
  }
  if (sort === 'confidence') {
    return confidenceRank(right.evidence?.confidence) - confidenceRank(left.evidence?.confidence)
      || right.score - left.score
      || left.criterion.code.localeCompare(right.criterion.code);
  }
  return right.score - left.score
    || statusRank(left.evidence?.evidence_status) - statusRank(right.evidence?.evidence_status)
    || left.criterion.code.localeCompare(right.criterion.code);
}

function statusRank(status: CriterionEvidenceExplanation['evidence_status'] | undefined) {
  if (status === 'supported') {
    return 0;
  }
  if (status === 'inferred') {
    return 1;
  }
  return 2;
}

function confidenceRank(confidence: CriterionEvidenceExplanation['confidence'] | undefined) {
  if (confidence === 'high') {
    return 3;
  }
  if (confidence === 'medium') {
    return 2;
  }
  if (confidence === 'low') {
    return 1;
  }
  return 0;
}

function criterionFilterKey(filter: CriterionFilter) {
  return `icpRadar.criteriaFilters.${filter}`;
}

function criterionSortKey(sort: CriterionSort) {
  return `icpRadar.criteriaSort.${sort}`;
}

function confidenceTone(confidence: CriterionEvidenceExplanation['confidence'] | undefined) {
  if (confidence === 'high' || confidence === 'medium') {
    return 'ally';
  }
  if (confidence === 'low') {
    return 'unsurfaced';
  }
  return 'neutral';
}

function evidenceBadgeTone(status: CriterionEvidenceExplanation['evidence_status']) {
  if (status === 'supported') {
    return 'ally';
  }
  if (status === 'inferred') {
    return 'unsurfaced';
  }
  return 'neutral';
}

function evidenceStatusKey(status: CriterionEvidenceExplanation['evidence_status']) {
  if (status === 'supported') {
    return 'icpRadar.supported';
  }
  if (status === 'inferred') {
    return 'icpRadar.inferred';
  }
  return 'icpRadar.notObserved';
}

function confidenceKey(confidence: CriterionEvidenceExplanation['confidence']) {
  if (confidence === 'high') {
    return 'icpRadar.confidenceValues.high';
  }
  if (confidence === 'medium') {
    return 'icpRadar.confidenceValues.medium';
  }
  if (confidence === 'low') {
    return 'icpRadar.confidenceValues.low';
  }
  return 'icpRadar.confidenceValues.none';
}

function evidenceOriginKey(origin: CriterionEvidenceExplanation['evidence_origin']) {
  if (origin === 'synthetic_demo_annotation') {
    return 'icpRadar.syntheticAnnotation';
  }
  return 'icpRadar.workbookFallback';
}
