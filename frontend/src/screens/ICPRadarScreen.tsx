import { ArrowLeft, ArrowRight, ChevronDown, ChevronRight, ExternalLink, Radar, ShieldCheck, Target } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Card, Eyebrow, Mono } from '../components/primitives';
import type { EvidenceSource, ICPRadarArtifact, ICPRadarCandidate, SignalCriterion } from '../types';

export function ICPRadarScreen({
  artifact,
  error,
}: {
  artifact: ICPRadarArtifact | null;
  error: string | null;
}) {
  const { t } = useTranslation();
  const [expandedCandidateId, setExpandedCandidateId] = useState<string | null>(null);
  const [detailCandidateId, setDetailCandidateId] = useState<string | null>(null);
  const detailCandidate = artifact?.candidates.find((item) => item.account_id === detailCandidateId) ?? null;
  const sourcesById = useMemo(() => {
    const entries = artifact?.radar.sources.map((source) => [source.source_id, source]) ?? [];
    return new Map(entries as Array<[string, EvidenceSource]>);
  }, [artifact]);

  if (error || !artifact) {
    return (
      <section className="screen status-screen" aria-label={t('icpRadar.aria')}>
        <Card>
          <Eyebrow>{t('icpRadar.statusEyebrow')}</Eyebrow>
          <h1>{error ? t('icpRadar.notReadyTitle') : t('icpRadar.loadingTitle')}</h1>
          <p>{error ? t('icpRadar.notReadyCopy') : t('icpRadar.loadingCopy')}</p>
          {error && <code>{error}</code>}
        </Card>
      </section>
    );
  }

  if (detailCandidate) {
    return (
      <section className="screen icp-radar-screen" aria-label={t('icpRadar.aria')}>
        <div className="icp-detail-sticky-header">
          <div className="icp-detail-breadcrumbs" aria-label={t('icpRadar.breadcrumbs')}>
            <Button icon={<ArrowLeft aria-hidden="true" />} variant="quiet" onClick={() => setDetailCandidateId(null)}>
              {t('icpRadar.backToTable')}
            </Button>
            <span>{t('icpRadar.aria')}</span>
            <ChevronRight aria-hidden="true" />
            <strong>{detailCandidate.legal_name}</strong>
          </div>

          <header className="icp-radar-header icp-detail-header">
            <span className="section-icon">
              <Target aria-hidden="true" />
            </span>
            <div>
              <Eyebrow>{t('icpRadar.detailEyebrow')}</Eyebrow>
              <h1>{detailCandidate.legal_name}</h1>
              <p>{detailCandidate.main_signal}</p>
            </div>
            <div className="icp-profile-meta">
              <Badge tone={detailCandidate.score.tier === 'Tier 1' ? 'ally' : 'neutral'}>{detailCandidate.score.tier}</Badge>
              <Mono>#{detailCandidate.rank}</Mono>
            </div>
          </header>
        </div>

        <div className="icp-candidate-detail-grid">
          <Card>
            <div className="icp-detail-card">
              <CandidateScoreGrid candidate={detailCandidate} />
              <CompanyContext candidate={detailCandidate} />
              <section className="icp-detail-section">
                <Eyebrow>{t('icpRadar.signalSummary')}</Eyebrow>
                <p>{detailCandidate.signal_summary || detailCandidate.comment}</p>
              </section>
              <section className="icp-detail-section">
                <Eyebrow>{t('icpRadar.plannedValidation')}</Eyebrow>
                <p>{t('icpRadar.validationPlannedCopy')}</p>
              </section>
            </div>
          </Card>

          <Card>
            <div className="icp-detail-card">
              <section className="icp-detail-section">
                <Eyebrow>{t('icpRadar.evidence')}</Eyebrow>
                <EvidenceList candidate={detailCandidate} sourcesById={sourcesById} />
              </section>
              <section className="icp-detail-section">
                <Eyebrow>{t('icpRadar.sourceUrls')}</Eyebrow>
                <SourceUrlList candidate={detailCandidate} />
              </section>
            </div>
          </Card>

          <Card>
            <div className="icp-detail-card">
              <section className="icp-detail-section">
                <Eyebrow>{t('icpRadar.criteria')}</Eyebrow>
                <CriteriaBreakdown artifact={artifact} candidate={detailCandidate} />
              </section>
            </div>
          </Card>
        </div>
      </section>
    );
  }

  return (
    <section className="screen icp-radar-screen" aria-label={t('icpRadar.aria')}>
      <header className="icp-radar-header">
        <span className="section-icon">
          <Radar aria-hidden="true" />
        </span>
        <div>
          <Eyebrow>{t('icpRadar.eyebrow')}</Eyebrow>
          <h1>{t('icpRadar.title')}</h1>
          <p>
            {t('icpRadar.summary', {
              count: artifact.candidates.length,
              holding: artifact.radar.profile.holding,
              product: artifact.radar.profile.product,
            })}
          </p>
        </div>
        <div className="icp-profile-meta">
          <Badge tone="cobalt">{artifact.radar.profile.run_mode}</Badge>
          <Mono>{artifact.radar.profile.source_workbook}</Mono>
        </div>
      </header>

      <Card>
        <div className="icp-radar-table-wrap" aria-label={t('icpRadar.tableAria')}>
          <div className="icp-radar-table">
            <div className="icp-radar-table-head">
              <span className="icp-sticky-cell">{t('icpRadar.columns.company')}</span>
              <span>{t('icpRadar.columns.total')}</span>
              <span>{t('icpRadar.columns.fit')}</span>
              <span>{t('icpRadar.columns.intent')}</span>
              <span>{t('icpRadar.columns.trigger')}</span>
              <span>{t('icpRadar.columns.tier')}</span>
              <span>{t('icpRadar.columns.evidence')}</span>
              <span>{t('icpRadar.columns.action')}</span>
            </div>
            {artifact.candidates.map((candidate) => {
              const expanded = expandedCandidateId === candidate.account_id;
              return (
                <div className="icp-candidate-record" key={candidate.account_id}>
                  <button
                    aria-expanded={expanded}
                    className={`icp-candidate-row${expanded ? ' icp-candidate-row-selected' : ''}`}
                    type="button"
                    onClick={() => setExpandedCandidateId(expanded ? null : candidate.account_id)}
                  >
                    <span className="icp-company-cell icp-sticky-cell">
                      <span className="account-initials">{candidate.rank}</span>
                      <span>
                        <strong>{candidate.legal_name}</strong>
                        <small>{candidate.description}</small>
                      </span>
                    </span>
                    <span className="score-cell">
                      <span className="score-track">
                        <span className="score-fill" style={{ width: `${Math.min(100, candidate.score.total_score * 2)}%` }} />
                      </span>
                      <Mono>{candidate.score.total_score}</Mono>
                    </span>
                    <Mono>{candidate.score.fit_score}</Mono>
                    <Mono>{candidate.score.intent_score}</Mono>
                    <Mono>{candidate.score.trigger_score}</Mono>
                    <span>
                      <Badge tone={candidate.score.tier === 'Tier 1' ? 'ally' : 'neutral'}>{candidate.score.tier}</Badge>
                    </span>
                    <Mono>{candidate.evidence_refs.length}</Mono>
                    <span className="row-action">
                      <span className="planned-action">{t('icpRadar.takeIntoWorkPlanned')}</span>
                      {expanded ? <ChevronDown aria-hidden="true" /> : <ChevronRight aria-hidden="true" />}
                    </span>
                  </button>
                  {expanded && (
                    <CandidatePreview
                      artifact={artifact}
                      candidate={candidate}
                      onOpenDetails={() => setDetailCandidateId(candidate.account_id)}
                      sourcesById={sourcesById}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </Card>
    </section>
  );
}

function CandidatePreview({
  artifact,
  candidate,
  onOpenDetails,
  sourcesById,
}: {
  artifact: ICPRadarArtifact;
  candidate: ICPRadarCandidate;
  onOpenDetails: () => void;
  sourcesById: Map<string, EvidenceSource>;
}) {
  const { t } = useTranslation();
  const criteria = topCriteria(artifact, candidate, 5);
  return (
    <div className="icp-candidate-preview">
      <div className="icp-preview-sticky-cell icp-sticky-cell">
        <Eyebrow>{t('icpRadar.previewEyebrow')}</Eyebrow>
        <strong>{candidate.legal_name}</strong>
        <Button icon={<ArrowRight aria-hidden="true" />} variant="default" onClick={onOpenDetails}>
          {t('icpRadar.openDetails')}
        </Button>
      </div>
      <div className="icp-preview-body">
        <div className="icp-preview-main">
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.mainSignal')}</Eyebrow>
            <p>{candidate.main_signal}</p>
          </section>
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.signalSummary')}</Eyebrow>
            <p>{candidate.comment || candidate.signal_summary}</p>
          </section>
        </div>
        <div className="icp-preview-lists">
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.evidence')}</Eyebrow>
            <EvidenceList candidate={candidate} sourcesById={sourcesById} compact />
          </section>
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.topCriteria')}</Eyebrow>
            <div className="criteria-list criteria-list-compact">
              {criteria.map(({ criterion, value }) => (
                <div className="criterion-row" key={criterion.code}>
                  <Mono>{criterion.code}</Mono>
                  <span>
                    <strong>{criterion.name}</strong>
                  </span>
                  <Mono>{value}</Mono>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function CandidateScoreGrid({ candidate }: { candidate: ICPRadarCandidate }) {
  const { t } = useTranslation();
  return (
    <div className="icp-score-grid">
      <ScoreBox label={t('icpRadar.fit')} value={candidate.score.fit_score} />
      <ScoreBox label={t('icpRadar.intent')} value={candidate.score.intent_score} />
      <ScoreBox label={t('icpRadar.trigger')} value={candidate.score.trigger_score} />
      <ScoreBox label={t('icpRadar.total')} value={candidate.score.total_score} />
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
  sourcesById: Map<string, EvidenceSource>;
  compact?: boolean;
}) {
  const refs = compact ? candidate.evidence_refs.slice(0, 5) : candidate.evidence_refs;
  return (
    <div className={`icp-evidence-list${compact ? ' icp-evidence-list-compact' : ''}`}>
      {refs.map((ref) => {
        const source = sourcesById.get(ref);
        return (
          <a href={source?.url ?? ref} key={ref} target="_blank" rel="noreferrer">
            <ShieldCheck aria-hidden="true" />
            <span>
              <strong>{ref}</strong>
              <small>{source?.usage ?? ref}</small>
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

function ScoreBox({ label, value }: { label: string; value: number }) {
  return (
    <div className="icp-score-box">
      <Mono>{label}</Mono>
      <strong>{value}</strong>
    </div>
  );
}

function topCriteria(artifact: ICPRadarArtifact, candidate: ICPRadarCandidate, count: number) {
  return artifact.radar.criteria
    .map((criterion) => ({
      criterion,
      value: candidate.criteria_scores[criterion.code] ?? 0,
    }))
    .filter((item): item is { criterion: SignalCriterion; value: number } => item.value > 0)
    .sort((left, right) => right.value - left.value || left.criterion.code.localeCompare(right.criterion.code))
    .slice(0, count);
}

function CriteriaBreakdown({
  artifact,
  candidate,
}: {
  artifact: ICPRadarArtifact;
  candidate: ICPRadarCandidate;
}) {
  return (
    <div className="criteria-list">
      {artifact.radar.criteria.map((criterion) => {
        const value = candidate.criteria_scores[criterion.code] ?? 0;
        return (
          <div className="criterion-row" key={criterion.code}>
            <Mono>{criterion.code}</Mono>
            <span>
              <strong>{criterion.name}</strong>
              <small>{criterion.description}</small>
            </span>
            <Mono>{value}</Mono>
          </div>
        );
      })}
    </div>
  );
}
