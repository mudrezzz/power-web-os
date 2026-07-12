import { ExternalLink, History } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Badge, Mono } from '../../../components/primitives';
import type { SignalMonitoringCandidateSurface, SignalMonitoringPresentationStatus } from '../../../types';

export function SignalMonitoringCandidateDetail({
  candidate,
}: {
  candidate: SignalMonitoringCandidateSurface;
}) {
  const { t } = useTranslation();
  if (!candidate.monitored) {
    return <p>{t('icpRadar.live.pipeline.signal.notMonitoredCopy')}</p>;
  }
  return (
    <div className="signal-monitoring-candidate-detail">
      {candidate.outcomes.map((outcome) => (
        <article key={outcome.signal_code}>
          <header>
            <div>
              <Mono>{outcome.signal_code}</Mono>
              <strong>{outcome.signal_label}</strong>
            </div>
            <Badge tone={statusTone(outcome.cumulative.presentation_status)}>
              {t(`icpRadar.live.pipeline.signal.presentationStatus.${outcome.cumulative.presentation_status}`)}
            </Badge>
          </header>
          <p>{outcome.current.summary || t(`icpRadar.live.pipeline.signal.presentationStatus.${outcome.current.presentation_status}`)}</p>
          {outcome.cumulative.origin_run_id && (
            <div className="radar-signal-origin">
              <History aria-hidden="true" />
              <span>{outcome.new_in_selected_run
                ? t('icpRadar.live.pipeline.signal.foundInSelectedRun')
                : t('icpRadar.live.pipeline.signal.retainedFromRun')}</span>
              <Mono>{outcome.cumulative.origin_run_id}</Mono>
            </div>
          )}
          <div className="signal-monitoring-detail-evidence">
            {outcome.cumulative.evidence.map((evidence, index) => (
              <div key={`${evidence.source_ref}:${index}`}>
                <span>
                  <strong>{evidence.title || evidence.source_ref}</strong>
                  <small>{evidence.fact || evidence.snippet || evidence.resolution_reason}</small>
                </span>
                <span>
                  <Mono>{evidence.event_at || evidence.published_at || t('icpRadar.live.pipeline.signal.dateUnknown')}</Mono>
                  {evidence.url && (
                    <a href={evidence.url} rel="noreferrer" target="_blank" title={t('icpRadar.live.pipeline.signal.openSource')}>
                      <ExternalLink aria-hidden="true" />
                    </a>
                  )}
                </span>
              </div>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}

function statusTone(status: SignalMonitoringPresentationStatus) {
  if (status === 'found_fresh') return 'ally';
  if (status === 'found_relevant_date_unknown' || status === 'coverage_incomplete') return 'unsurfaced';
  return 'neutral';
}
