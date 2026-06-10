import { ArrowRight, ExternalLink, Radar, ShieldCheck, Target } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, Card, Eyebrow, Mono } from '../components/primitives';
import type { EvidenceSource, ICPRadarArtifact, ICPRadarCandidate } from '../types';

export function ICPRadarScreen({
  artifact,
  error,
}: {
  artifact: ICPRadarArtifact | null;
  error: string | null;
}) {
  const { t } = useTranslation();
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const selectedCandidate =
    artifact?.candidates.find((item) => item.account_id === selectedCandidateId) ?? artifact?.candidates[0] ?? null;
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

      <div className="icp-radar-layout">
        <Card>
          <div className="icp-radar-table-wrap">
            <div className="icp-radar-table">
              <div className="icp-radar-table-head">
                <span>{t('icpRadar.columns.company')}</span>
                <span>{t('icpRadar.columns.total')}</span>
                <span>{t('icpRadar.columns.fit')}</span>
                <span>{t('icpRadar.columns.intent')}</span>
                <span>{t('icpRadar.columns.trigger')}</span>
                <span>{t('icpRadar.columns.tier')}</span>
                <span>{t('icpRadar.columns.evidence')}</span>
                <span>{t('icpRadar.columns.action')}</span>
              </div>
              {artifact.candidates.map((candidate) => (
                <button
                  className={`icp-candidate-row${
                    selectedCandidate?.account_id === candidate.account_id ? ' icp-candidate-row-selected' : ''
                  }`}
                  key={candidate.account_id}
                  type="button"
                  onClick={() => setSelectedCandidateId(candidate.account_id)}
                >
                  <span className="icp-company-cell">
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
                    <span className="planned-action">{t('icpRadar.takeIntoWork')}</span>
                    <ArrowRight aria-hidden="true" />
                  </span>
                </button>
              ))}
            </div>
          </div>
        </Card>

        {selectedCandidate && (
          <aside className="icp-radar-detail">
            <Card>
              <div className="icp-detail-heading">
                <span className="section-icon">
                  <Target aria-hidden="true" />
                </span>
                <div>
                  <Eyebrow>{t('icpRadar.detailEyebrow')}</Eyebrow>
                  <h2>{selectedCandidate.legal_name}</h2>
                  <p>{selectedCandidate.main_signal}</p>
                </div>
              </div>

              <div className="icp-score-grid">
                <ScoreBox label={t('icpRadar.fit')} value={selectedCandidate.score.fit_score} />
                <ScoreBox label={t('icpRadar.intent')} value={selectedCandidate.score.intent_score} />
                <ScoreBox label={t('icpRadar.trigger')} value={selectedCandidate.score.trigger_score} />
                <ScoreBox label={t('icpRadar.total')} value={selectedCandidate.score.total_score} />
              </div>

              <section className="icp-detail-section">
                <Eyebrow>{t('icpRadar.companyContext')}</Eyebrow>
                <dl className="icp-definition-list">
                  <div>
                    <dt>{t('icpRadar.revenue')}</dt>
                    <dd>{selectedCandidate.revenue || t('icpRadar.unknown')}</dd>
                  </div>
                  <div>
                    <dt>{t('icpRadar.inn')}</dt>
                    <dd>{selectedCandidate.inn || t('icpRadar.unknown')}</dd>
                  </div>
                  <div>
                    <dt>{t('icpRadar.site')}</dt>
                    <dd>{selectedCandidate.site || t('icpRadar.unknown')}</dd>
                  </div>
                  <div>
                    <dt>{t('icpRadar.confidence')}</dt>
                    <dd>{selectedCandidate.confidence || t('icpRadar.unknown')}</dd>
                  </div>
                </dl>
              </section>

              <section className="icp-detail-section">
                <Eyebrow>{t('icpRadar.evidence')}</Eyebrow>
                <div className="icp-evidence-list">
                  {selectedCandidate.evidence_refs.map((ref) => {
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
              </section>

              <section className="icp-detail-section">
                <Eyebrow>{t('icpRadar.criteria')}</Eyebrow>
                <CriteriaBreakdown artifact={artifact} candidate={selectedCandidate} />
              </section>
            </Card>
          </aside>
        )}
      </div>
    </section>
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
