import { useTranslation } from 'react-i18next';
import { Badge, Eyebrow, Mono } from '../../../components/primitives';
import type { SignalMonitoringReportArtifact, SignalMonitoringReportSignal } from '../../../types';

export function SignalMonitoringReportView({
  report,
  rows,
}: {
  report: SignalMonitoringReportArtifact | null;
  rows: SignalMonitoringReportSignal[];
}) {
  const { t } = useTranslation();
  if (!report) {
    return (
      <section className="radar-signal-report" aria-label={t('icpRadar.live.pipeline.signal.reportAria')}>
        <p>{t('icpRadar.live.pipeline.signal.emptyReportCopy')}</p>
      </section>
    );
  }
  return (
    <section className="radar-signal-report" aria-label={t('icpRadar.live.pipeline.signal.reportAria')}>
      <header>
        <div>
          <Eyebrow>{t('icpRadar.live.pipeline.signal.reportEyebrow')}</Eyebrow>
          <h3>{t('icpRadar.live.pipeline.signal.reportTitle')}</h3>
          <p className="radar-signal-report-lineage">
            {t('icpRadar.live.pipeline.signal.sourceRun')} <Mono>{report.source_candidate_run_id || t('icpRadar.notAvailable')}</Mono>
          </p>
        </div>
        <div className="radar-signal-report-meta">
          <Mono>{report.artifact_version}</Mono>
          <Mono>{report.model_profile_id}</Mono>
          <Badge tone={report.provider_runtime === 'recorded' || report.recorded_provider ? 'neutral' : 'ally'}>
            {report.provider_runtime || (report.recorded_provider ? t('icpRadar.live.pipeline.signal.recordedStatus') : t('icpRadar.notAvailable'))}
          </Badge>
        </div>
      </header>
      {rows.length === 0 ? (
        <p>{t('icpRadar.live.pipeline.signal.emptyReportCopy')}</p>
      ) : (
        <div className="radar-signal-report-table">
          <div className="radar-signal-report-head">
            <span>{t('icpRadar.live.pipeline.signal.columns.candidate')}</span>
            <span>{t('icpRadar.live.pipeline.signal.columns.signal')}</span>
            <span>{t('icpRadar.live.pipeline.signal.columns.status')}</span>
            <span>{t('icpRadar.live.pipeline.signal.columns.source')}</span>
            <span>{t('icpRadar.live.pipeline.signal.columns.evidence')}</span>
          </div>
          {rows.map((row) => (
            <div className="radar-signal-report-row" key={`${row.candidate_id}-${row.signal_code}-${row.source_lane}`}>
              <span>
                <strong>{row.candidate_name || row.candidate_id}</strong>
                <small>{row.candidate_id}</small>
              </span>
              <span>
                <strong>{row.signal_label || row.signal_code}</strong>
                <small>{row.summary}</small>
              </span>
              <span><Badge tone={signalStatusTone(row)}>{signalStatusLabel(row, t)}</Badge></span>
              <Mono>{row.source_lane || t('icpRadar.notAvailable')}</Mono>
              <Mono>{row.evidence_refs.length}</Mono>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function signalStatusTone(row: SignalMonitoringReportSignal) {
  if (row.search_status === 'duplicate_existing_signal') return 'neutral' as const;
  if (row.search_status.includes('budget')) return 'unsurfaced' as const;
  if (row.observation_status === 'observed') return 'ally' as const;
  return 'neutral' as const;
}

function signalStatusLabel(
  row: SignalMonitoringReportSignal,
  t: (key: string, options?: Record<string, unknown>) => string,
) {
  if (row.search_status === 'duplicate_existing_signal') return t('icpRadar.live.pipeline.signal.status.duplicate');
  if (row.search_status.includes('budget')) return t('icpRadar.live.pipeline.signal.status.budget');
  if (row.observation_status === 'observed') return t('icpRadar.live.pipeline.signal.status.observed');
  if (row.observation_status === 'not_observed') return t('icpRadar.live.pipeline.signal.status.notObserved');
  return row.search_status || row.observation_status || t('icpRadar.notAvailable');
}
