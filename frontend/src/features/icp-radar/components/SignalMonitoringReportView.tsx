import { ExternalLink, History } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Badge, Eyebrow, Mono } from '../../../components/primitives';
import type {
  SignalMonitoringCandidateSurfaceArtifact,
  SignalMonitoringPresentationStatus,
  SignalMonitoringReportArtifact,
  SignalMonitoringSurfaceEvidence,
  SignalMonitoringSurfaceOutcome,
} from '../../../types';

export function SignalMonitoringReportView({
  report,
  surface,
}: {
  report: SignalMonitoringReportArtifact | null;
  surface: SignalMonitoringCandidateSurfaceArtifact | null;
}) {
  const { t } = useTranslation();
  if (!report || !surface) {
    return (
      <section className="radar-signal-report" aria-label={t('icpRadar.live.pipeline.signal.reportAria')}>
        <p>{t('icpRadar.live.pipeline.signal.emptyReportCopy')}</p>
      </section>
    );
  }
  const monitored = surface.candidates.filter((candidate) => candidate.monitored);
  return (
    <section className="radar-signal-report" aria-label={t('icpRadar.live.pipeline.signal.reportAria')}>
      <header>
        <div>
          <Eyebrow>{t('icpRadar.live.pipeline.signal.reportEyebrow')}</Eyebrow>
          <h3>{t('icpRadar.live.pipeline.signal.reportTitle')}</h3>
          <p data-testid="signal-check-summary">{t('icpRadar.live.pipeline.signal.checkSummary', {
            candidates: surface.summary.monitored_candidate_count,
            criteria: surface.summary.criterion_count,
            pairs: surface.summary.pair_count,
          })}</p>
          <p className="radar-signal-report-lineage">
            {t('icpRadar.live.pipeline.signal.sourceRun')} <Mono>{report.source_candidate_run_id}</Mono>
          </p>
        </div>
        <div className="radar-signal-report-meta">
          <Mono>{report.artifact_version}</Mono>
          <Mono>{report.model_profile_id}</Mono>
          <Badge tone={report.provider_runtime === 'recorded' || report.recorded_provider ? 'neutral' : 'ally'}>
            {report.provider_runtime || (report.recorded_provider
              ? t('icpRadar.live.pipeline.signal.recordedStatus')
              : t('icpRadar.notAvailable'))}
          </Badge>
        </div>
      </header>
      <div className="radar-signal-surface-summary">
        <SurfaceMetric label={t('icpRadar.live.pipeline.signal.newFound')} value={surface.summary.new_confirmed_count} />
        <SurfaceMetric label={t('icpRadar.live.pipeline.signal.previouslyFound')} value={surface.summary.cumulative_confirmed_count - surface.summary.new_confirmed_count} />
        <SurfaceMetric label={t('icpRadar.live.pipeline.signal.reviewFound')} value={surface.summary.current_review_count} />
        <SurfaceMetric label={t('icpRadar.live.pipeline.signal.searchedNegative')} value={surface.summary.current_searched_negative_count} />
      </div>
      <div className="radar-signal-candidate-groups">
        {monitored.map((candidate) => (
          <section className="radar-signal-candidate-group" data-candidate-id={candidate.candidate_id} key={candidate.candidate_id}>
            <header>
              <div>
                <strong>{candidate.candidate_name}</strong>
                <Mono>{candidate.candidate_id}</Mono>
              </div>
              <Badge tone={candidateTone(candidate.monitoring_status)}>
                {t(`icpRadar.live.pipeline.signal.candidateStatus.${candidate.monitoring_status}`)}
              </Badge>
            </header>
            <div className="radar-signal-outcomes">
              {candidate.outcomes.map((outcome) => <SignalOutcomeRow key={outcome.signal_code} outcome={outcome} />)}
            </div>
          </section>
        ))}
      </div>
    </section>
  );
}

function SignalOutcomeRow({ outcome }: { outcome: SignalMonitoringSurfaceOutcome }) {
  const { t } = useTranslation();
  const cumulativeEvidence = outcome.cumulative.evidence;
  const searchedCount = outcome.current.searched_sources?.length ?? 0;
  return (
    <article
      className="radar-signal-outcome-row"
      data-current-status={outcome.current.presentation_status}
      data-cumulative-status={outcome.cumulative.presentation_status}
      data-signal-code={outcome.signal_code}
    >
      <div className="radar-signal-outcome-heading">
        <Mono>{outcome.signal_code}</Mono>
        <strong>{outcome.signal_label}</strong>
        <Badge tone={statusTone(outcome.cumulative.presentation_status)}>
          {t(`icpRadar.live.pipeline.signal.presentationStatus.${outcome.cumulative.presentation_status}`)}
        </Badge>
      </div>
      <div className="radar-signal-outcome-state">
        <span>{t('icpRadar.live.pipeline.signal.currentRun')}</span>
        <strong>{t(`icpRadar.live.pipeline.signal.presentationStatus.${outcome.current.presentation_status}`)}</strong>
        {outcome.current.summary && <small>{outcome.current.summary}</small>}
      </div>
      {outcome.cumulative.origin_run_id && (
        <div className="radar-signal-origin">
          <History aria-hidden="true" />
          <span>{outcome.new_in_selected_run
            ? t('icpRadar.live.pipeline.signal.foundInSelectedRun')
            : t('icpRadar.live.pipeline.signal.retainedFromRun')}</span>
          <Mono>{outcome.cumulative.origin_run_id}</Mono>
        </div>
      )}
      {cumulativeEvidence.length > 0 ? (
        <div className="radar-signal-evidence-list">
          {cumulativeEvidence.map((item, index) => (
            <EvidenceLink evidence={item} key={`${item.source_ref}:${item.temporal_status}:${index}`} />
          ))}
        </div>
      ) : (
        <p className="radar-signal-source-count">
          {t('icpRadar.live.pipeline.signal.sourcesChecked', { count: searchedCount })}
        </p>
      )}
    </article>
  );
}

function EvidenceLink({ evidence }: { evidence: SignalMonitoringSurfaceEvidence }) {
  const { t } = useTranslation();
  const body = (
    <>
      <span>
        <strong>{evidence.title || evidence.source_ref}</strong>
        <small>{evidence.fact || evidence.snippet || evidence.resolution_reason}</small>
      </span>
      <span className="radar-signal-evidence-meta">
        <Mono>{evidence.event_at || evidence.published_at || t('icpRadar.live.pipeline.signal.dateUnknown')}</Mono>
        {evidence.url && <ExternalLink aria-hidden="true" />}
      </span>
    </>
  );
  return evidence.url ? (
    <a href={evidence.url} rel="noreferrer" target="_blank">{body}</a>
  ) : (
    <div className="radar-signal-evidence-unresolved">{body}</div>
  );
}

function SurfaceMetric({ label, value }: { label: string; value: number }) {
  return <div data-value={value}><span>{label}</span><Mono>{value}</Mono></div>;
}

function candidateTone(status: string) {
  if (status === 'found_fresh') return 'ally';
  if (status === 'review_needed') return 'unsurfaced';
  return 'neutral';
}

function statusTone(status: SignalMonitoringPresentationStatus) {
  if (status === 'found_fresh') return 'ally';
  if (status === 'found_relevant_date_unknown' || status === 'coverage_incomplete') return 'unsurfaced';
  return 'neutral';
}
