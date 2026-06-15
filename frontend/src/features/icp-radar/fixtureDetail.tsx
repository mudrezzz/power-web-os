import { ArrowLeft, ChevronRight, ExternalLink, RotateCcw, ShieldCheck, Target } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Card, Eyebrow, Mono } from '../../components/primitives';
import type {
  ICPRadarArtifact,
  ICPRadarCandidate,
  SignalValidationDecision,
  SignalValidationOverlay,
  SourceDefinition,
  ValidatedCandidateScore,
} from '../../types';
import { CandidateDetailTabs, Metric, ScoreBox } from './detailPrimitives';
import { CriteriaBreakdown } from './criteriaBreakdown';
import {
  type CandidateDetailTab,
  buildValidatedCandidateScore,
  fitSignalCodes,
  formatDuration,
  intentSignalCodes,
  signalCodes,
  triggerSignalCodes,
  validationForCandidate,
  validationRank,
  validationStatusKey,
  validationTone,
  scoreWithMax,
} from './model';
import { topCriteriaByCodes } from './fixturePreview';

// Fixture detail hosts signal validation; keep score recalculation visible and isolated from shortlist scan behavior.

export function FixtureRadarCandidateDetailView({
  activeTab,
  artifact,
  candidate,
  onBack,
  onDecisionChange,
  onResetValidation,
  onTabChange,
  radarId,
  radarName,
  signalValidation,
  sourcesById,
  validatedScore,
}: {
  activeTab: CandidateDetailTab;
  artifact: ICPRadarArtifact;
  candidate: ICPRadarCandidate;
  onBack: () => void;
  onDecisionChange: (decision: SignalValidationDecision) => void;
  onResetValidation: () => void;
  onTabChange: (tab: CandidateDetailTab) => void;
  radarId: string;
  radarName: string;
  signalValidation: SignalValidationOverlay;
  sourcesById: Map<string, SourceDefinition>;
  validatedScore: ValidatedCandidateScore;
}) {
  const { t } = useTranslation();
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
            <Target aria-hidden="true" />
          </span>
          <div>
            <Eyebrow>{t('icpRadar.detailEyebrow')}</Eyebrow>
            <h1>{candidate.legal_name}</h1>
            <p>{candidate.main_signal}</p>
          </div>
          <div className="icp-profile-meta">
            <Badge tone={validatedScore.effective_score.tier === 'Tier 1' ? 'ally' : 'neutral'}>{validatedScore.effective_score.tier}</Badge>
            <Mono>{t('icpRadar.total')} {validatedScore.effective_score.total_score}</Mono>
          </div>
        </header>
        <CandidateDetailTabs activeTab={activeTab} onTabChange={onTabChange} />
      </div>

      <div className="icp-candidate-detail-panel">
        {activeTab === 'overview' && (
          <Card>
            <CandidateScoreGrid candidate={candidate} validatedScore={validatedScore} />
            <CompanyContext candidate={candidate} />
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.canonicalDetail.mainInsight')}</Eyebrow>
              <p>{candidate.signal_summary || candidate.comment || candidate.main_signal}</p>
            </section>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.signalValidation')}</Eyebrow>
              <ValidationSummary score={validatedScore} />
              <Button icon={<RotateCcw aria-hidden="true" />} variant="default" onClick={onResetValidation}>
                {t('icpRadar.resetLocalValidation')}
              </Button>
            </section>
          </Card>
        )}

        {activeTab === 'qualification' && (
          <Card>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.canonicalDetail.qualification')}</Eyebrow>
              <div className="canonical-detail-table">
                {topCriteriaByCodes(artifact, candidate, fitSignalCodes, 10).map(({ criterion, value }) => (
                  <details className="canonical-detail-record" key={criterion.code}>
                    <summary>
                      <Mono>{criterion.code}</Mono>
                      <strong>{criterion.name}</strong>
                      <Mono>{value}</Mono>
                    </summary>
                    <p>{criterion.description}</p>
                    {candidate.criteria_evidence[criterion.code]?.facts.slice(0, 3).map((fact) => (
                      <div className="canonical-journal-row" key={`${criterion.code}-${fact.evidence_ref}`}>
                        <Mono>{fact.evidence_ref}</Mono>
                        <strong>{fact.fact}</strong>
                        <small>{fact.why_it_matters}</small>
                      </div>
                    ))}
                  </details>
                ))}
              </div>
            </section>
          </Card>
        )}

        {activeTab === 'signals' && (
          <Card>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.canonicalDetail.signals')}</Eyebrow>
              <CriteriaBreakdown
                artifact={artifact}
                candidate={candidate}
                radarId={radarId}
                signalValidation={signalValidation}
                validatedScore={validatedScore}
                onDecisionChange={onDecisionChange}
              />
            </section>
          </Card>
        )}

        {activeTab === 'sources' && (
          <Card>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.canonicalDetail.sources')}</Eyebrow>
              <EvidenceList candidate={candidate} sourcesById={sourcesById} />
              <SourceUrlList candidate={candidate} />
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
                  <dd>{artifact.workflow_metadata.workflow_name}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.live.sources')}</dt>
                  <dd>{artifact.workflow_metadata.source_count}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.criteria')}</dt>
                  <dd>{artifact.workflow_metadata.criteria_count}</dd>
                </div>
              </dl>
              <p>{t('icpRadar.canonicalDetail.fixtureJournalCopy')}</p>
            </section>
          </Card>
        )}
      </div>
    </section>
  );
}

function CandidateScoreGrid({ candidate, validatedScore }: { candidate: ICPRadarCandidate; validatedScore: ValidatedCandidateScore }) {
  const { t } = useTranslation();
  const delta = validatedScore.effective_score.total_score - validatedScore.original_score.total_score;
  return (
    <div className="icp-score-grid">
      <ScoreBox label={t('icpRadar.fit')} value={scoreWithMax(validatedScore.effective_score.fit_score, 15)} />
      <ScoreBox label={t('icpRadar.intent')} value={scoreWithMax(validatedScore.effective_score.intent_score, 33)} />
      <ScoreBox label={t('icpRadar.trigger')} value={scoreWithMax(validatedScore.effective_score.trigger_score, 12)} />
      <ScoreBox delta={delta} label={t('icpRadar.total')} value={scoreWithMax(validatedScore.effective_score.total_score, 60)} />
    </div>
  );
}

function CompanyContext({ candidate }: { candidate: ICPRadarCandidate }) {
  const { t } = useTranslation();
  return (
    <section className="icp-detail-section">
      <Eyebrow>{t('icpRadar.companyContext')}</Eyebrow>
      <dl className="icp-definition-list">
        <div>
          <dt>{t('icpRadar.revenue')}</dt>
          <dd>{candidate.revenue || t('icpRadar.unknown')}</dd>
        </div>
        <div>
          <dt>{t('icpRadar.inn')}</dt>
          <dd>{candidate.inn || t('icpRadar.unknown')}</dd>
        </div>
        <div>
          <dt>{t('icpRadar.site')}</dt>
          <dd>{candidate.site || t('icpRadar.unknown')}</dd>
        </div>
        <div>
          <dt>{t('icpRadar.confidence')}</dt>
          <dd>{candidate.confidence || t('icpRadar.unknown')}</dd>
        </div>
      </dl>
    </section>
  );
}

function EvidenceList({
  candidate,
  sourcesById,
  compact = false,
}: {
  candidate: ICPRadarCandidate;
  sourcesById: Map<string, SourceDefinition>;
  compact?: boolean;
}) {
  const refs = compact ? candidate.evidence_refs.slice(0, 5) : candidate.evidence_refs;
  return (
    <div className={`icp-evidence-list${compact ? ' icp-evidence-list-compact' : ''}`}>
      {refs.map((ref) => {
        const source = sourcesById.get(ref);
        return (
          <a href={source?.reference ?? ref} key={ref} target="_blank" rel="noreferrer">
            <ShieldCheck aria-hidden="true" />
            <span>
              <strong>{ref}</strong>
              <small>{source?.label ?? ref}</small>
            </span>
            <ExternalLink aria-hidden="true" />
          </a>
        );
      })}
    </div>
  );
}

function SourceUrlList({ candidate }: { candidate: ICPRadarCandidate }) {
  const { t } = useTranslation();
  if (!candidate.source_urls.length) {
    return <p>{t('icpRadar.unknown')}</p>;
  }

  return (
    <div className="icp-evidence-list">
      {candidate.source_urls.map((url) => (
        <a href={url} key={url} target="_blank" rel="noreferrer">
          <ExternalLink aria-hidden="true" />
          <span>
            <strong>{url}</strong>
          </span>
        </a>
      ))}
    </div>
  );
}

function ValidationSummary({ score }: { score: ValidatedCandidateScore }) {
  const { t } = useTranslation();
  const reviewedCount = score.status_counts.confirmed
    + score.status_counts.corrected
    + score.status_counts.rejected
    + score.status_counts.stale;
  const needsReviewCount = signalCodes.length - reviewedCount;
  return (
    <div className="validation-summary-grid">
      <span>
        <Mono>{t('icpRadar.reviewStatus.confirmed')}</Mono>
        <strong>{score.status_counts.confirmed}</strong>
      </span>
      <span>
        <Mono>{t('icpRadar.reviewStatus.corrected')}</Mono>
        <strong>{score.status_counts.corrected}</strong>
      </span>
      <span>
        <Mono>{t('icpRadar.reviewStatus.rejected')}</Mono>
        <strong>{score.status_counts.rejected}</strong>
      </span>
      <span>
        <Mono>{t('icpRadar.reviewStatus.stale')}</Mono>
        <strong>{score.status_counts.stale}</strong>
      </span>
      <span>
        <Mono>{t('icpRadar.criteriaFilters.needs_review')}</Mono>
        <strong>{needsReviewCount}</strong>
      </span>
    </div>
  );
}
