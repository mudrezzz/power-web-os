import { RotateCcw, Save } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Eyebrow, Mono } from '../../components/primitives';
import type {
  LiveRadarCandidate,
  LiveRadarSignalResult,
  LiveRadarSourceEvidence,
  SignalValidationDecision,
  SignalValidationOverlay,
  SignalValidationStatus,
} from '../../types';
import {
  liveSignalTone,
  qualificationCrossValidationTone,
  qualificationTrustTone,
  signalEffectiveScore,
  signalEvidenceCardViews,
  signalScoreEvaluationView,
  signalValidationKey,
} from './model';

type SignalReviewAction = Extract<SignalValidationStatus, 'confirmed' | 'rejected' | 'stale' | 'corrected'>;

export function LiveSignalReviewTable({
  candidate,
  onSignalDecisionChange,
  onSignalDecisionReset,
  radarId,
  signalValidation,
  sourcesByRef,
}: {
  candidate: LiveRadarCandidate;
  onSignalDecisionChange: (decision: SignalValidationDecision) => void;
  onSignalDecisionReset: (radarId: string, candidateId: string, signalCode: string) => void;
  radarId: string;
  signalValidation: SignalValidationOverlay;
  sourcesByRef: Map<string, LiveRadarSourceEvidence>;
}) {
  const { t } = useTranslation();
  return (
    <div className="signal-review-table">
      <div className="signal-review-head">
        <span>{t('icpRadar.live.signalColumns.code')}</span>
        <span>{t('icpRadar.live.signalColumns.signal')}</span>
        <span>{t('icpRadar.live.signalColumns.originalScore')}</span>
        <span>{t('icpRadar.live.signalColumns.effectiveScore')}</span>
        <span>{t('icpRadar.live.signalColumns.status')}</span>
        <span>{t('icpRadar.live.signalColumns.sources')}</span>
        <span>{t('icpRadar.live.signalColumns.check')}</span>
        <span>{t('icpRadar.live.signalColumns.decision')}</span>
      </div>
      {candidate.signals.map((item) => {
        const decision = signalValidation[signalValidationKey(radarId, candidate.candidate_id, item.signal_code)] ?? null;
        return (
          <LiveSignalReviewRow
            candidate={candidate}
            decision={decision}
            item={item}
            key={item.signal_code}
            onSignalDecisionChange={onSignalDecisionChange}
            onSignalDecisionReset={onSignalDecisionReset}
            radarId={radarId}
            sourcesByRef={sourcesByRef}
          />
        );
      })}
    </div>
  );
}

function LiveSignalReviewRow({
  candidate,
  decision,
  item,
  onSignalDecisionChange,
  onSignalDecisionReset,
  radarId,
  sourcesByRef,
}: {
  candidate: LiveRadarCandidate;
  decision: SignalValidationDecision | null;
  item: LiveRadarSignalResult;
  onSignalDecisionChange: (decision: SignalValidationDecision) => void;
  onSignalDecisionReset: (radarId: string, candidateId: string, signalCode: string) => void;
  radarId: string;
  sourcesByRef: Map<string, LiveRadarSourceEvidence>;
}) {
  const { t } = useTranslation();
  const [comment, setComment] = useState(decision?.comment ?? '');
  const [reviewAction, setReviewAction] = useState<SignalReviewAction>(
    (decision?.status as SignalReviewAction | undefined) ?? 'confirmed',
  );
  const [adjustedScore, setAdjustedScore] = useState(String(decision?.adjusted_score ?? item.score));
  const [confidence, setConfidence] = useState(decision?.confidence || item.confidence || 'medium');
  const effectiveScore = signalEffectiveScore(item, decision);
  const evaluation = signalScoreEvaluationView(item, decision);
  const evidenceCards = signalEvidenceCardViews(item, sourcesByRef);
  const requiresComment = reviewAction !== 'confirmed';
  const canSaveReview = !requiresComment || comment.trim().length > 0;

  function saveDecision() {
    if (!canSaveReview) {
      return;
    }
    const score = Math.max(0, Math.min(2, Number(adjustedScore)));
    onSignalDecisionChange({
      radar_id: radarId,
      account_id: candidate.candidate_id,
      signal_code: item.signal_code,
      status: reviewAction,
      original_score: item.score,
      adjusted_score: reviewAction === 'corrected' ? score : null,
      confidence: reviewAction === 'corrected' ? confidence : item.confidence,
      corrected_summary: reviewAction === 'corrected' ? (comment.trim() || item.summary) : null,
      evidence_refs: item.evidence_refs,
      comment: reviewAction === 'confirmed'
        ? (comment.trim() || t('icpRadar.live.signalReview.confirmedDefaultComment'))
        : comment.trim(),
      reviewed_at: new Date().toISOString(),
    });
  }

  return (
    <details className="signal-review-row">
      <summary>
        <Mono>{item.signal_code}</Mono>
        <strong>{item.signal}</strong>
        <Mono>{item.score}</Mono>
        <span className="signal-score-current">
          <Mono>{effectiveScore}</Mono>
          {effectiveScore !== item.score && <small>{effectiveScore > item.score ? '+' : ''}{effectiveScore - item.score}</small>}
        </span>
        <Badge tone={liveSignalTone(item.status)}>
          {t(`icpRadar.live.signalStatus.${item.status}`)}
        </Badge>
        <span>{t('icpRadar.live.sourceCount', { count: item.evidence_refs.length })}</span>
        <Badge tone={qualificationCrossValidationTone(item.cross_validation?.status)}>
          {t(`icpRadar.live.crossValidationStatus.${item.cross_validation?.status ?? 'not_required'}`)}
        </Badge>
        <Badge tone={decision ? validationDecisionTone(decision.status) : 'neutral'}>
          {decision ? t(`icpRadar.reviewStatus.${decision.status}`) : t('icpRadar.reviewStatus.unreviewed')}
        </Badge>
      </summary>
      <div className="signal-review-details">
        <section className="signal-review-evaluation">
          <Eyebrow>{t('icpRadar.live.signalScoreEvaluation')}</Eyebrow>
          <dl className="qualification-evaluation-list">
            <div>
              <dt>{t('icpRadar.live.signalEvaluationFields.signal')}</dt>
              <dd>{item.signal}</dd>
            </div>
            <div>
              <dt>{t('icpRadar.live.signalEvaluationFields.scale')}</dt>
              <dd>{evaluation.scale}</dd>
            </div>
            <div>
              <dt>{t('icpRadar.live.signalEvaluationFields.rule')}</dt>
              <dd>{evaluation.ruleSnapshot}</dd>
            </div>
            <div>
              <dt>{t('icpRadar.live.signalEvaluationFields.found')}</dt>
              <dd>{evaluation.foundFact}</dd>
            </div>
            <div>
              <dt>{t('icpRadar.live.signalEvaluationFields.originalScore')}</dt>
              <dd>{evaluation.originalScore}</dd>
            </div>
            <div>
              <dt>{t('icpRadar.live.signalEvaluationFields.effectiveScore')}</dt>
              <dd>{evaluation.effectiveScore}{evaluation.delta ? ` (${evaluation.delta > 0 ? '+' : ''}${evaluation.delta})` : ''}</dd>
            </div>
            <div>
              <dt>{t('icpRadar.live.signalEvaluationFields.confidence')}</dt>
              <dd>{t(`icpRadar.live.confidence.${evaluation.confidence}`, { defaultValue: evaluation.confidence })}</dd>
            </div>
            <div>
              <dt>{t('icpRadar.live.signalEvaluationFields.crossValidation')}</dt>
              <dd>
                <Badge tone={qualificationCrossValidationTone(evaluation.crossValidationStatus)}>
                  {t(`icpRadar.live.crossValidationStatus.${evaluation.crossValidationStatus}`)}
                </Badge>
              </dd>
            </div>
            <div>
              <dt>{t('icpRadar.live.signalEvaluationFields.action')}</dt>
              <dd>{t(`icpRadar.live.signalAction.${evaluation.recommendedAction}`)}</dd>
            </div>
          </dl>
          <p>{item.score_evaluation?.explanation || item.summary}</p>
        </section>

        <section>
          <Eyebrow>{t('icpRadar.live.evidence')}</Eyebrow>
          <div className="qualification-finding-list signal-finding-list">
            {evidenceCards.length ? evidenceCards.map((card) => (
              <article className="qualification-finding signal-finding" key={`${card.sourceRef}-${card.fact}`}>
                <header className="qualification-finding-source">
                  <Mono>{card.sourceRef}</Mono>
                  <span>
                    <strong>{card.sourceName}</strong>
                    <small>{card.sourceUrl || card.sourceRef}</small>
                  </span>
                  <Badge tone="neutral">{t(`icpRadar.live.sourceOrigin.${card.sourceOrigin}`)}</Badge>
                  <Badge tone={qualificationTrustTone(card.trustPolicy)}>{t(`icpRadar.live.trustPolicy.${card.trustPolicy}`)}</Badge>
                </header>
                <div className="qualification-finding-body">
                  <div>
                    <span>{t('icpRadar.live.evidenceCard.fact')}</span>
                    <p>{card.fact}</p>
                  </div>
                  <div>
                    <span>{t(`icpRadar.live.excerptType.${card.excerptType}`)}</span>
                    <p>{card.excerpt || t('icpRadar.live.evidenceCard.noExcerpt')}</p>
                  </div>
                  <div>
                    <span>{t('icpRadar.live.signalEvidenceCard.whySignal')}</span>
                    <p>{card.whyItMatchesSignal}</p>
                  </div>
                  <div>
                    <span>{t('icpRadar.live.signalEvidenceCard.whyScore')}</span>
                    <p>{card.whyScoreApplies}</p>
                  </div>
                </div>
                <Badge tone={card.contradictsSignal ? 'blocker' : 'neutral'}>
                  {t(`icpRadar.live.evidenceStrength.${card.evidenceStrength}`)}
                </Badge>
              </article>
            )) : (
              <p>{t('icpRadar.live.noSignalEvidence')}</p>
            )}
          </div>
        </section>

        <section className="qualification-review-panel signal-review-panel">
          <div className="qualification-review-panel-head">
            <Eyebrow>{t('icpRadar.live.humanReview')}</Eyebrow>
            <Badge tone={decision ? validationDecisionTone(decision.status) : 'neutral'}>
              {decision ? t(`icpRadar.reviewStatus.${decision.status}`) : t('icpRadar.reviewStatus.unreviewed')}
            </Badge>
          </div>
          <div className="qualification-review-choice" role="group" aria-label={t('icpRadar.live.signalReview.actionLabel')}>
            {(['confirmed', 'rejected', 'stale', 'corrected'] as SignalReviewAction[]).map((status) => (
              <button
                className={reviewAction === status ? 'active' : ''}
                key={status}
                onClick={() => setReviewAction(status)}
                type="button"
              >
                {t(`icpRadar.live.signalReview.actions.${status}`)}
              </button>
            ))}
          </div>
          {reviewAction === 'corrected' && (
            <div className="signal-correction-grid">
              <label className="field">
                <span>{t('icpRadar.live.signalReview.adjustedScore')}</span>
                <select onChange={(event) => setAdjustedScore(event.target.value)} value={adjustedScore}>
                  {[0, 1, 2].map((score) => <option key={score} value={score}>{score}</option>)}
                </select>
              </label>
              <label className="field">
                <span>{t('icpRadar.live.signalReview.confidence')}</span>
                <select onChange={(event) => setConfidence(event.target.value)} value={confidence}>
                  {['high', 'medium', 'low'].map((value) => (
                    <option key={value} value={value}>{t(`icpRadar.live.confidence.${value}`)}</option>
                  ))}
                </select>
              </label>
            </div>
          )}
          <label className="field field-full">
            <span>{t('icpRadar.live.signalReview.comment')}{requiresComment ? ` ${t('icpRadar.live.review.requiredMark')}` : ''}</span>
            <textarea
              onChange={(event) => setComment(event.target.value)}
              placeholder={t('icpRadar.live.signalReview.commentPlaceholder')}
              rows={4}
              value={comment}
            />
          </label>
          {requiresComment && !comment.trim() && (
            <small className="qualification-review-error">{t('icpRadar.live.signalReview.commentRequired')}</small>
          )}
          <div className="qualification-review-actions">
            <Button disabled={!canSaveReview} icon={<Save aria-hidden="true" />} variant="default" onClick={saveDecision}>
              {t('icpRadar.live.signalReview.save')}
            </Button>
            {decision && (
              <Button
                icon={<RotateCcw aria-hidden="true" />}
                variant="quiet"
                onClick={() => onSignalDecisionReset(radarId, candidate.candidate_id, item.signal_code)}
              >
                {t('icpRadar.live.signalReview.reset')}
              </Button>
            )}
          </div>
        </section>
      </div>
    </details>
  );
}

function validationDecisionTone(status: SignalValidationStatus) {
  if (status === 'confirmed') {
    return 'ally';
  }
  if (status === 'rejected' || status === 'stale') {
    return 'blocker';
  }
  if (status === 'corrected') {
    return 'unsurfaced';
  }
  return 'neutral';
}
