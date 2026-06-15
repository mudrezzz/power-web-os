import { ArrowLeft, Check, ChevronRight, ExternalLink, Radar, RotateCcw, Save, ShieldCheck, X } from 'lucide-react';
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
  fallbackQualificationSourceUsages,
  liveFitScoreMax,
  liveIntentScoreMax,
  liveRuntimeKey,
  liveSignalTone,
  liveTotalScore,
  liveTotalScoreMax,
  qualificationAssessmentTone,
  qualificationCrossValidationTone,
  qualificationDecisionTone,
  qualificationOperatorLabel,
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
        <span>{t('icpRadar.live.qualificationColumns.requirement')}</span>
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
  const [correctedAssessment, setCorrectedAssessment] = useState<QualificationAssessmentStatus>(
    decision?.corrected_assessment ?? effectiveQualificationAssessment(item, decision),
  );
  const effectiveAssessment = effectiveQualificationAssessment(item, decision);
  const sourceCount = item.source_usages?.length || item.evidence_refs.length;
  const canSaveCommentAction = comment.trim().length > 0;

  function saveDecision(status: QualificationReviewDecision['status'], assessment: QualificationAssessmentStatus | null) {
    if (status !== 'approved' && !canSaveCommentAction) {
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
        <Badge tone={(item.requirement_level ?? 'required') === 'required' ? 'unsurfaced' : 'neutral'}>
          {t(`icpRadar.settings.requirement.${item.requirement_level ?? 'required'}`)}
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
            {item.evidence_findings?.length ? item.evidence_findings.map((finding) => (
              <article className="qualification-finding" key={`${finding.source_ref}-${finding.fact}`}>
                <div>
                  <Mono>{finding.source_ref}</Mono>
                  <strong>{finding.fact}</strong>
                </div>
                <p>{finding.why_it_matches_rule}</p>
                <Badge tone={finding.contradicts_rule ? 'blocker' : 'neutral'}>
                  {t(`icpRadar.live.evidenceStrength.${finding.evidence_strength}`)}
                </Badge>
              </article>
            )) : (
              <p>{t('icpRadar.live.noQualificationEvidence')}</p>
            )}
          </div>
        </section>

        <section>
          <Eyebrow>{t('icpRadar.live.sourcesUsed')}</Eyebrow>
          <div className="qualification-source-table">
            <div className="qualification-source-head">
              <span>{t('icpRadar.live.sourceColumns.name')}</span>
              <span>{t('icpRadar.live.sourceColumns.origin')}</span>
              <span>{t('icpRadar.live.sourceColumns.trust')}</span>
              <span>{t('icpRadar.live.sourceColumns.usage')}</span>
            </div>
            {(item.source_usages?.length ? item.source_usages : fallbackQualificationSourceUsages(item, sourcesByRef)).map((usage) => (
              <div className="qualification-source-row" key={`${usage.source_ref}-${usage.used_for}`}>
                <span>
                  <strong>{usage.source_name}</strong>
                  <small>{usage.url || usage.source_ref}</small>
                </span>
                <Badge tone="neutral">{t(`icpRadar.live.sourceOrigin.${usage.source_origin}`)}</Badge>
                <Badge tone={qualificationTrustTone(usage.trust_policy)}>{t(`icpRadar.live.trustPolicy.${usage.trust_policy}`)}</Badge>
                <span>{usage.used_for}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="qualification-review-evaluation">
          <div>
            <Eyebrow>{t('icpRadar.live.crossValidation')}</Eyebrow>
            <p>{item.cross_validation?.notes || t('icpRadar.live.crossValidationEmpty')}</p>
          </div>
          <div>
            <Eyebrow>{t('icpRadar.live.requirementEvaluation')}</Eyebrow>
            <p>{item.requirement_evaluation?.explanation || item.rationale}</p>
          </div>
        </section>

        <section className="qualification-review-panel">
          <Eyebrow>{t('icpRadar.live.humanReview')}</Eyebrow>
          <label className="field field-full">
            <span>{t('icpRadar.live.review.comment')}</span>
            <textarea
              onChange={(event) => setComment(event.target.value)}
              placeholder={t('icpRadar.live.review.commentPlaceholder')}
              rows={3}
              value={comment}
            />
          </label>
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
          <div className="qualification-review-actions">
            <Button icon={<Check aria-hidden="true" />} variant="default" onClick={() => saveDecision('approved', null)}>
              {t('icpRadar.live.review.approve')}
            </Button>
            <Button disabled={!canSaveCommentAction} icon={<X aria-hidden="true" />} variant="default" onClick={() => saveDecision('rejected', 'does_not_match')}>
              {t('icpRadar.live.review.reject')}
            </Button>
            <Button disabled={!canSaveCommentAction} icon={<Save aria-hidden="true" />} variant="default" onClick={() => saveDecision('corrected', correctedAssessment)}>
              {t('icpRadar.live.review.correct')}
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
