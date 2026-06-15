import { ArrowLeft, ChevronRight, ExternalLink, Radar, RotateCcw, Save, ShieldCheck } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Card, Eyebrow, Mono } from '../../components/primitives';
import type {
  LiveICPRadarRunArtifact,
  LiveRadarCandidate,
  LiveRadarQualificationResult,
  LiveRadarSignalResult,
  LiveRadarSourceEvidence,
  QualificationAssessmentStatus,
  QualificationReviewDecision,
  QualificationSourceUsage,
} from '../../types';
import { CandidateDetailTabs, Metric, ScoreBox } from './detailPrimitives';
import {
  type CandidateDetailTab,
  type QualificationReviewOverlay,
  effectiveQualificationAssessment,
  liveFitScoreMax,
  liveIntentScoreMax,
  liveRuntimeKey,
  liveSignalTone,
  liveTotalScore,
  liveTotalScoreMax,
  qualificationAssessmentTone,
  qualificationCrossValidationTone,
  qualificationDecisionTone,
  qualificationEvidenceCardViews,
  qualificationOperatorLabel,
  qualificationRequirementEvaluationView,
  qualificationReviewKey,
  qualificationRuleId,
  qualificationRuleText,
  qualificationStatusToAssessment,
  qualificationTrustTone,
  scoreWithMax,
} from './model';

// Detail tabs keep runtime/provider evidence separate from the shortlist so live radars do not fork the main UX.

export function LiveRadarCandidateDetailView({
  activeTab,
  artifact,
  candidate,
  onBack,
  onQualificationReviewChange,
  onTabChange,
  qualificationReview,
  radarId,
  radarName,
}: {
  activeTab: CandidateDetailTab;
  artifact: LiveICPRadarRunArtifact;
  candidate: LiveRadarCandidate;
  onBack: () => void;
  onQualificationReviewChange: (
    radarId: string,
    candidateId: string,
    ruleId: string,
    decision: QualificationReviewDecision | null,
  ) => void;
  onTabChange: (tab: CandidateDetailTab) => void;
  qualificationReview: QualificationReviewOverlay;
  radarId: string;
  radarName: string;
}) {
  const { t } = useTranslation();
  const sourcesByRef = useMemo(() => new Map(artifact.sources.map((source) => [source.evidence_ref, source])), [artifact.sources]);
  const usedSources = candidate.evidence_refs.map((ref) => sourcesByRef.get(ref)).filter((source): source is LiveRadarSourceEvidence => Boolean(source));
  return (
    <section className="screen icp-radar-screen icp-detail-screen" aria-label={t('icpRadar.aria')}>
      <div className="icp-detail-sticky-header">
        <div className="icp-detail-breadcrumbs" aria-label={t('icpRadar.breadcrumbs')}>
          <Button icon={<ArrowLeft aria-hidden="true" />} variant="quiet" onClick={onBack}>
            {t('icpRadar.backToTable')}
          </Button>
          <span>{t('icpRadar.aria')}</span>
          <ChevronRight aria-hidden="true" />
          <span>{radarName}</span>
          <ChevronRight aria-hidden="true" />
          <strong>{candidate.legal_name}</strong>
        </div>

        <header className="icp-radar-header icp-detail-header">
          <span className="section-icon">
            <Radar aria-hidden="true" />
          </span>
          <div>
            <Eyebrow>{t('icpRadar.live.detailEyebrow')}</Eyebrow>
            <h1>{candidate.legal_name}</h1>
            <p>{candidate.description || t('icpRadar.live.noDescription')}</p>
          </div>
          <div className="icp-profile-meta">
            <Badge tone={candidate.score.tier === 'Tier 1' ? 'ally' : 'neutral'}>{candidate.score.tier}</Badge>
            <Mono>{t('icpRadar.fit')} {candidate.score.fit_score}</Mono>
            <Mono>{t('icpRadar.intent')} {candidate.score.intent_score}</Mono>
          </div>
        </header>
        <CandidateDetailTabs activeTab={activeTab} onTabChange={onTabChange} />
      </div>

      <div className="icp-candidate-detail-panel">
        {activeTab === 'overview' && (
          <Card>
            <div className="icp-score-grid">
              <ScoreBox label={t('icpRadar.total')} value={scoreWithMax(liveTotalScore(candidate), liveTotalScoreMax(candidate))} />
              <ScoreBox label={t('icpRadar.fit')} value={scoreWithMax(candidate.score.fit_score, liveFitScoreMax(candidate))} />
              <ScoreBox label={t('icpRadar.intent')} value={scoreWithMax(candidate.score.intent_score, liveIntentScoreMax(candidate))} />
              <ScoreBox label={t('icpRadar.live.sources')} value={scoreWithMax(candidate.evidence_refs.length, artifact.sources.length)} />
            </div>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.canonicalDetail.mainInsight')}</Eyebrow>
              <p>{candidate.description || t('icpRadar.live.noDescription')}</p>
            </section>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.companyContext')}</Eyebrow>
              <dl className="icp-definition-list">
                <div>
                  <dt>{t('icpRadar.canonicalDetail.legalName')}</dt>
                  <dd>{candidate.legal_name}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.inn')}</dt>
                  <dd>{t('icpRadar.unknown')}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.revenue')}</dt>
                  <dd>{t('icpRadar.unknown')}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.canonicalDetail.affiliation')}</dt>
                  <dd>{candidate.qualification.find((item) => item.criterion_code === 'Q1')?.status === 'confirmed'
                    ? t('icpRadar.live.siburAffiliation')
                    : t('icpRadar.unknown')}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.canonicalDetail.foundAt')}</dt>
                  <dd>{artifact.run_metadata.run_at}</dd>
                </div>
              </dl>
            </section>
          </Card>
        )}

        {activeTab === 'qualification' && (
          <Card>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.live.qualification')}</Eyebrow>
              <LiveQualificationReviewTable
                candidate={candidate}
                onQualificationReviewChange={onQualificationReviewChange}
                qualificationReview={qualificationReview}
                radarId={radarId}
                sourcesByRef={sourcesByRef}
              />
            </section>
          </Card>
        )}

        {activeTab === 'signals' && (
          <Card>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.live.signals')}</Eyebrow>
              <div className="canonical-detail-table">
                {candidate.signals.map((item) => (
                  <details className="canonical-detail-record" key={item.signal_code}>
                    <summary>
                      <Mono>{item.signal_code}</Mono>
                      <strong>{item.signal}</strong>
                      <span className="live-radar-score">
                        <Mono>{item.score}</Mono>
                        <Badge tone={liveSignalTone(item.status)}>
                          {t(`icpRadar.live.signalStatus.${item.status}`)}
                        </Badge>
                      </span>
                    </summary>
                    <span>
                      <p>{item.summary}</p>
                      <LiveEvidenceList refs={item.evidence_refs} sourcesByRef={sourcesByRef} compact />
                    </span>
                  </details>
                ))}
              </div>
            </section>
          </Card>
        )}

        {activeTab === 'sources' && (
          <Card>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.live.evidence')}</Eyebrow>
              <LiveSourceSummary sources={usedSources} />
            </section>
          </Card>
        )}

        {activeTab === 'journal' && (
          <Card>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.canonicalDetail.journal')}</Eyebrow>
              <dl className="icp-definition-list">
                <div>
                  <dt>{t('icpRadar.live.runtime')}</dt>
                  <dd>{t(liveRuntimeKey(artifact.run_metadata.runtime))}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.live.model')}</dt>
                  <dd>{artifact.run_metadata.model ?? t('icpRadar.unknown')}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.live.webMode')}</dt>
                  <dd>{artifact.run_metadata.web_mode ?? t('icpRadar.unknown')}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.live.queries')}</dt>
                  <dd>{artifact.run_metadata.query_count}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.live.sources')}</dt>
                  <dd>{artifact.run_metadata.source_count}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.canonicalDetail.runAt')}</dt>
                  <dd>{artifact.run_metadata.run_at}</dd>
                </div>
              </dl>
              <div className="canonical-journal-list">
                {artifact.search_plan.queries.map((query) => (
                  <div className="canonical-journal-row" key={query.query_id}>
                    <Mono>{query.query_id}</Mono>
                    <strong>{query.query}</strong>
                    <small>{query.purpose}</small>
                  </div>
                ))}
              </div>
              {candidate.review_flags.length > 0 && (
                <div className="badge-list">
                  {candidate.review_flags.map((flag) => (
                    <Badge key={flag} tone="unsurfaced">{flag}</Badge>
                  ))}
                </div>
              )}
            </section>
          </Card>
        )}
      </div>
    </section>
  );
}

function LiveQualificationReviewTable({
  candidate,
  onQualificationReviewChange,
  qualificationReview,
  radarId,
  sourcesByRef,
}: {
  candidate: LiveRadarCandidate;
  onQualificationReviewChange: (
    radarId: string,
    candidateId: string,
    ruleId: string,
    decision: QualificationReviewDecision | null,
  ) => void;
  qualificationReview: QualificationReviewOverlay;
  radarId: string;
  sourcesByRef: Map<string, LiveRadarSourceEvidence>;
}) {
  const { t } = useTranslation();
  return (
    <div className="qualification-review-table">
      <div className="qualification-review-head">
        <span>{t('icpRadar.live.qualificationColumns.code')}</span>
        <span>{t('icpRadar.live.qualificationColumns.rule')}</span>
        <span>{t('icpRadar.live.qualificationColumns.operator')}</span>
        <span>{t('icpRadar.live.qualificationColumns.assessment')}</span>
        <span>{t('icpRadar.live.qualificationColumns.sources')}</span>
        <span>{t('icpRadar.live.qualificationColumns.crossValidation')}</span>
        <span>{t('icpRadar.live.qualificationColumns.decision')}</span>
      </div>
      {candidate.qualification.map((item) => {
        const ruleId = qualificationRuleId(item);
        const decision = qualificationReview[qualificationReviewKey(radarId, candidate.candidate_id, ruleId)] ?? item.review_decision ?? null;
        return (
          <LiveQualificationReviewRow
            candidate={candidate}
            decision={decision}
            item={item}
            key={ruleId}
            onQualificationReviewChange={onQualificationReviewChange}
            radarId={radarId}
            sourcesByRef={sourcesByRef}
          />
        );
      })}
    </div>
  );
}

function LiveQualificationReviewRow({
  candidate,
  decision,
  item,
  onQualificationReviewChange,
  radarId,
  sourcesByRef,
}: {
  candidate: LiveRadarCandidate;
  decision: QualificationReviewDecision | null;
  item: LiveRadarQualificationResult;
  onQualificationReviewChange: (
    radarId: string,
    candidateId: string,
    ruleId: string,
    decision: QualificationReviewDecision | null,
  ) => void;
  radarId: string;
  sourcesByRef: Map<string, LiveRadarSourceEvidence>;
}) {
  const { t } = useTranslation();
  const ruleId = qualificationRuleId(item);
  const [comment, setComment] = useState(decision?.comment ?? '');
  const [reviewAction, setReviewAction] = useState<QualificationReviewDecision['status']>(decision?.status ?? 'approved');
  const [correctedAssessment, setCorrectedAssessment] = useState<QualificationAssessmentStatus>(
    decision?.corrected_assessment ?? effectiveQualificationAssessment(item, decision),
  );
  const effectiveAssessment = effectiveQualificationAssessment(item, decision);
  const requirementEvaluation = qualificationRequirementEvaluationView(item);
  const sourceCount = item.source_usages?.length || item.evidence_refs.length;
  const requiresComment = reviewAction !== 'approved';
  const canSaveReview = !requiresComment || comment.trim().length > 0;
  const evidenceCards = qualificationEvidenceCardViews(item, sourcesByRef);

  function saveDecision(status: QualificationReviewDecision['status'], assessment: QualificationAssessmentStatus | null) {
    if (status !== 'approved' && !comment.trim()) {
      return;
    }
    onQualificationReviewChange(radarId, candidate.candidate_id, ruleId, {
      status,
      corrected_assessment: assessment,
      comment: status === 'approved' ? (comment.trim() || t('icpRadar.live.review.approvedDefaultComment')) : comment.trim(),
      reviewed_at: new Date().toISOString(),
    });
  }

  return (
    <details className="qualification-review-row">
      <summary>
        <Mono>{item.criterion_code}</Mono>
        <strong>{qualificationRuleText(item)}</strong>
        <Mono>{qualificationOperatorLabel(item.operator)}</Mono>
        <Badge tone={qualificationAssessmentTone(effectiveAssessment)}>
          {t(`icpRadar.live.assessment.${effectiveAssessment}`)}
        </Badge>
        <span>{t('icpRadar.live.sourceCount', { count: sourceCount })}</span>
        <Badge tone={qualificationCrossValidationTone(item.cross_validation?.status)}>
          {t(`icpRadar.live.crossValidationStatus.${item.cross_validation?.status ?? 'not_required'}`)}
        </Badge>
        <Badge tone={decision ? qualificationDecisionTone(decision.status) : 'neutral'}>
          {decision ? t(`icpRadar.live.reviewStatus.${decision.status}`) : t('icpRadar.live.reviewStatus.unreviewed')}
        </Badge>
      </summary>
      <div className="qualification-review-details">
        <section>
          <Eyebrow>{t('icpRadar.live.evidence')}</Eyebrow>
          <p>{item.rationale}</p>
          <div className="qualification-finding-list">
            {evidenceCards.length ? evidenceCards.map((card) => (
              <article className="qualification-finding" key={`${card.sourceRef}-${card.fact}`}>
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
                    <span>{t('icpRadar.live.evidenceCard.why')}</span>
                    <p>{card.whyItMatchesRule}</p>
                  </div>
                </div>
                <Badge tone={card.contradictsRule ? 'blocker' : 'neutral'}>
                  {t(`icpRadar.live.evidenceStrength.${card.evidenceStrength}`)}
                </Badge>
              </article>
            )) : (
              <p>{t('icpRadar.live.noQualificationEvidence')}</p>
            )}
          </div>
        </section>

        <section className="qualification-review-evaluation">
          <div>
            <Eyebrow>{t('icpRadar.live.requirementEvaluation')}</Eyebrow>
            <dl className="qualification-evaluation-list">
              <div>
                <dt>{t('icpRadar.live.requirementEvaluationFields.requirement')}</dt>
                <dd>{t(`icpRadar.live.requirementLevel.${requirementEvaluation.requirementLevel}`)}</dd>
              </div>
              <div>
                <dt>{t('icpRadar.live.requirementEvaluationFields.found')}</dt>
                <dd>{t(`icpRadar.live.evidenceStrength.${requirementEvaluation.evidenceStrength}`)}</dd>
              </div>
              <div>
                <dt>{t('icpRadar.live.requirementEvaluationFields.conclusion')}</dt>
                <dd>{t(`icpRadar.live.assessment.${effectiveAssessment}`)}</dd>
              </div>
              <div>
                <dt>{t('icpRadar.live.requirementEvaluationFields.confidence')}</dt>
                <dd>{t(`icpRadar.live.confidence.${requirementEvaluation.confidence}`)}</dd>
              </div>
              <div>
                <dt>{t('icpRadar.live.requirementEvaluationFields.crossValidation')}</dt>
                <dd>
                  <Badge tone={qualificationCrossValidationTone(item.cross_validation?.status)}>
                    {t(`icpRadar.live.crossValidationStatus.${item.cross_validation?.status ?? 'not_required'}`)}
                  </Badge>
                </dd>
              </div>
              <div>
                <dt>{t('icpRadar.live.requirementEvaluationFields.action')}</dt>
                <dd>{t(`icpRadar.live.requirementAction.${requirementEvaluation.recommendedAction}`)}</dd>
              </div>
            </dl>
            <p>{t(`icpRadar.live.crossValidationCopy.${item.cross_validation?.status ?? 'not_required'}`)}</p>
            <p>{item.requirement_evaluation?.explanation || item.rationale}</p>
          </div>
        </section>

        <section className="qualification-review-panel">
          <div className="qualification-review-panel-head">
            <Eyebrow>{t('icpRadar.live.humanReview')}</Eyebrow>
            <Badge tone={decision ? qualificationDecisionTone(decision.status) : 'neutral'}>
              {decision ? t(`icpRadar.live.reviewStatus.${decision.status}`) : t('icpRadar.live.reviewStatus.unreviewed')}
            </Badge>
          </div>
          <div className="qualification-review-choice" role="group" aria-label={t('icpRadar.live.review.actionLabel')}>
            {(['approved', 'rejected', 'corrected'] as QualificationReviewDecision['status'][]).map((status) => (
              <button
                className={reviewAction === status ? 'active' : ''}
                key={status}
                onClick={() => setReviewAction(status)}
                type="button"
              >
                {t(`icpRadar.live.review.actions.${status}`)}
              </button>
            ))}
          </div>
          {reviewAction === 'corrected' && (
            <label className="field">
              <span>{t('icpRadar.live.review.correctedAssessment')}</span>
              <select
                onChange={(event) => setCorrectedAssessment(event.target.value as QualificationAssessmentStatus)}
                value={correctedAssessment}
              >
                {(['matches', 'partially_matches', 'does_not_match'] as QualificationAssessmentStatus[]).map((value) => (
                  <option key={value} value={value}>{t(`icpRadar.live.assessment.${value}`)}</option>
                ))}
              </select>
            </label>
          )}
          <label className="field field-full">
            <span>{t('icpRadar.live.review.comment')}{requiresComment ? ` ${t('icpRadar.live.review.requiredMark')}` : ''}</span>
            <textarea
              onChange={(event) => setComment(event.target.value)}
              placeholder={t('icpRadar.live.review.commentPlaceholder')}
              rows={4}
              value={comment}
            />
          </label>
          {requiresComment && !comment.trim() && (
            <small className="qualification-review-error">{t('icpRadar.live.review.commentRequired')}</small>
          )}
          <div className="qualification-review-actions">
            <Button
              disabled={!canSaveReview}
              icon={<Save aria-hidden="true" />}
              variant="default"
              onClick={() => saveDecision(
                reviewAction,
                reviewAction === 'approved' ? null : reviewAction === 'rejected' ? 'does_not_match' : correctedAssessment,
              )}
            >
              {t('icpRadar.live.review.save')}
            </Button>
            {decision && (
              <Button icon={<RotateCcw aria-hidden="true" />} variant="quiet" onClick={() => onQualificationReviewChange(radarId, candidate.candidate_id, ruleId, null)}>
                {t('icpRadar.live.review.reset')}
              </Button>
            )}
          </div>
        </section>
      </div>
    </details>
  );
}

function LiveEvidenceList({
  compact = false,
  refs,
  sourcesByRef,
}: {
  compact?: boolean;
  refs: string[];
  sourcesByRef: Map<string, LiveRadarSourceEvidence>;
}) {
  return (
    <div className={`live-radar-source-list${compact ? ' icp-evidence-list-compact' : ''}`}>
      {refs.map((ref) => {
        const source = sourcesByRef.get(ref);
        return (
          <a href={source?.url ?? '#'} key={ref} rel="noreferrer" target="_blank">
            <ShieldCheck aria-hidden="true" />
            <span>
              <strong>{source?.title ?? ref}</strong>
              <small>{source?.snippet ?? ref}</small>
            </span>
            {source?.url && <ExternalLink aria-hidden="true" />}
          </a>
        );
      })}
    </div>
  );
}

function LiveSourceSummary({ sources }: { sources: LiveRadarSourceEvidence[] }) {
  const { t } = useTranslation();
  if (!sources.length) {
    return <p>{t('icpRadar.unknown')}</p>;
  }
  return (
    <div className="source-table-wrap">
      <table className="source-table">
        <thead>
          <tr>
            <th>{t('icpRadar.settings.sourceNumber')}</th>
            <th>{t('icpRadar.settings.sourceLabel')}</th>
            <th>{t('icpRadar.settings.sourceType')}</th>
            <th>{t('icpRadar.settings.sourceReference')}</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((source, index) => (
            <tr key={source.evidence_ref}>
              <td><Mono>{index + 1}</Mono></td>
              <td>
                <strong>{source.title}</strong>
                <small>{source.snippet}</small>
              </td>
              <td>{source.source_type}</td>
              <td>
                <a href={source.url} rel="noreferrer" target="_blank">{source.url}</a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
