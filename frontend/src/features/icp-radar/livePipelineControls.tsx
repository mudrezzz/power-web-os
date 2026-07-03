import type { ReactNode } from 'react';
import { Activity, BellRing, Clock, Eye, ListChecks, Play, Radar } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Card, Eyebrow, Mono } from '../../components/primitives';
import type { ICPRadarCatalogItem, SignalMonitoringReportArtifact, SignalMonitoringReportSignal } from '../../types';
import type { RadarRunControlState } from './application/useRadarBackend';

// Radar pipeline controls make candidate discovery and signal monitoring visibly separate without owning API transport.
export function RadarPipelineControlPanel({
  diagnosticsOpen,
  onCheckSetup,
  onRunCandidateDiscovery,
  onToggleDiagnostics,
  onTogglePreflight,
  onToggleSignalReport,
  preflightOpen,
  radar,
  runState,
  signalMonitoringReport,
  signalReportOpen,
}: {
  diagnosticsOpen: boolean;
  onCheckSetup: () => void;
  onRunCandidateDiscovery: () => void;
  onToggleDiagnostics: () => void;
  onTogglePreflight: () => void;
  onToggleSignalReport: () => void;
  preflightOpen: boolean;
  radar: ICPRadarCatalogItem | null;
  runState: RadarRunControlState;
  signalMonitoringReport: SignalMonitoringReportArtifact | null;
  signalReportOpen: boolean;
}) {
  const { t } = useTranslation();
  const monitoring = radar?.definition.monitoring_policy;
  const signalSummary = signalMonitoringReport?.summary;
  const signalRows = signalMonitoringReport?.signals.slice(0, 6) ?? [];
  return (
    <Card>
      <section className="radar-pipeline-controls" aria-label={t('icpRadar.live.pipeline.aria')}>
        <div className="radar-pipeline-card radar-pipeline-card-active">
          <header>
            <span className="section-icon">
              <Radar aria-hidden="true" />
            </span>
            <div>
              <Eyebrow>{t('icpRadar.live.pipeline.candidate.eyebrow')}</Eyebrow>
              <h2>{t('icpRadar.live.pipeline.candidate.title')}</h2>
              <p>{t('icpRadar.live.pipeline.candidate.copy')}</p>
            </div>
          </header>
          <dl className="radar-pipeline-facts">
            <div>
              <dt>{t('icpRadar.live.pipeline.status')}</dt>
              <dd><PipelineRunStatus state={runState} /></dd>
            </div>
            <div>
              <dt>{t('icpRadar.live.pipeline.cadence')}</dt>
              <dd>{radar?.summary.cadence || t('icpRadar.live.pipeline.notConfigured')}</dd>
            </div>
            <div>
              <dt>{t('icpRadar.live.pipeline.lastRun')}</dt>
              <dd>{runState.runId ? <Mono>{runState.runId}</Mono> : radar?.summary.last_run || t('icpRadar.live.pipeline.notConfigured')}</dd>
            </div>
            <div>
              <dt>{t('icpRadar.live.pipeline.nextRun')}</dt>
              <dd>{t('icpRadar.live.pipeline.notConfigured')}</dd>
            </div>
          </dl>
          <div className="radar-pipeline-actions">
            <Button disabled={runState.busy || runState.mode === 'loading'} icon={<Play aria-hidden="true" />} variant="primary" onClick={onRunCandidateDiscovery}>
              {runState.busy ? t('icpRadar.live.runInProgress') : t('icpRadar.live.pipeline.candidate.run')}
            </Button>
            {runState.runId && (
              <Button icon={<Eye aria-hidden="true" />} variant="default" onClick={onToggleDiagnostics}>
                {diagnosticsOpen ? t('icpRadar.live.diagnostics.hideRun') : t('icpRadar.live.diagnostics.inspectRun')}
              </Button>
            )}
            <Button icon={<ListChecks aria-hidden="true" />} variant="default" onClick={preflightOpen ? onTogglePreflight : onCheckSetup}>
              {preflightOpen ? t('icpRadar.live.preflight.hide') : t('icpRadar.live.preflight.checkSetup')}
            </Button>
          </div>
        </div>

        <div className="radar-pipeline-card">
          <header>
            <span className="section-icon">
              <BellRing aria-hidden="true" />
            </span>
            <div>
              <Eyebrow>{t('icpRadar.live.pipeline.signal.eyebrow')}</Eyebrow>
              <h2>{t('icpRadar.live.pipeline.signal.title')}</h2>
              <p>{t('icpRadar.live.pipeline.signal.copy')}</p>
            </div>
          </header>
          <dl className="radar-pipeline-facts">
            <div>
              <dt>{t('icpRadar.live.pipeline.status')}</dt>
              <dd>
                <Badge tone={signalMonitoringReport ? 'ally' : 'neutral'}>
                  {signalMonitoringReport ? t('icpRadar.live.pipeline.signal.recordedStatus') : t('icpRadar.live.pipeline.signal.noReport')}
                </Badge>
              </dd>
            </div>
            <div>
              <dt>{t('icpRadar.live.pipeline.cadence')}</dt>
              <dd>{monitoring?.cadence || t('icpRadar.live.pipeline.notConfigured')}</dd>
            </div>
            <div>
              <dt>{t('icpRadar.live.pipeline.lookback')}</dt>
              <dd>{signalMonitoringReport ? t('icpRadar.live.pipeline.signal.lookbackDays', { count: signalMonitoringReport.lookback_days }) : monitoring?.lookback_window || t('icpRadar.live.pipeline.notConfigured')}</dd>
            </div>
            <div>
              <dt>{t('icpRadar.live.pipeline.lastRun')}</dt>
              <dd>{signalMonitoringReport ? <Mono>{signalMonitoringReport.run_id}</Mono> : t('icpRadar.live.pipeline.notConfigured')}</dd>
            </div>
          </dl>
          <div className="radar-pipeline-metrics">
            <PipelineMetric icon={<Activity aria-hidden="true" />} label={t('icpRadar.live.pipeline.signal.newSignals')} value={signalSummary?.new_signal_count ?? 0} />
            <PipelineMetric icon={<Clock aria-hidden="true" />} label={t('icpRadar.live.pipeline.signal.repeatedSignals')} value={signalSummary?.repeated_signal_count ?? 0} />
            <PipelineMetric label={t('icpRadar.live.pipeline.signal.notObserved')} value={signalSummary?.searched_negative_count ?? 0} />
            <PipelineMetric label={t('icpRadar.live.pipeline.signal.budgetLimited')} value={signalSummary?.not_searched_budget_limited_count ?? 0} />
          </div>
          <div className="radar-pipeline-actions">
            <Button disabled icon={<Play aria-hidden="true" />} variant="default">
              {t('icpRadar.live.pipeline.signal.run')}
            </Button>
            <span className="radar-pipeline-disabled-copy">{t('icpRadar.live.pipeline.signal.disabledCopy')}</span>
            {signalMonitoringReport && (
              <Button icon={<Eye aria-hidden="true" />} variant="default" onClick={onToggleSignalReport}>
                {signalReportOpen ? t('icpRadar.live.pipeline.signal.hideReport') : t('icpRadar.live.pipeline.signal.showReport')}
              </Button>
            )}
          </div>
        </div>
      </section>
      {signalReportOpen && <SignalMonitoringRecordedReport report={signalMonitoringReport} rows={signalRows} />}
    </Card>
  );
}

function PipelineRunStatus({ state }: { state: RadarRunControlState }) {
  const { t } = useTranslation();
  const status = state.status ?? (state.mode === 'api' ? 'ready' : state.mode);
  return (
    <div className="live-radar-run-status">
      <Badge tone={state.error ? 'blocker' : state.busy || state.outputPending ? 'unsurfaced' : state.mode === 'api' ? 'ally' : 'neutral'}>
        {t(`icpRadar.live.runStatus.${status}`, { defaultValue: status })}
      </Badge>
      <span>{t(`icpRadar.live.backendMode.${state.mode}`)}</span>
      {state.runId && <Mono>{state.runId}</Mono>}
      {state.outputPending && <span>{t('icpRadar.live.outputPending')}</span>}
      {state.error && <span className="live-radar-run-error">{state.error}</span>}
    </div>
  );
}

function PipelineMetric({ icon, label, value }: { icon?: ReactNode; label: string; value: number }) {
  return (
    <div className="radar-pipeline-metric">
      {icon}
      <span>{label}</span>
      <Mono>{value}</Mono>
    </div>
  );
}

function SignalMonitoringRecordedReport({
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
        </div>
        <div className="radar-signal-report-meta">
          <Mono>{report.artifact_version}</Mono>
          <Mono>{report.model_profile_id}</Mono>
          <Badge tone={report.live_provider_calls === 0 ? 'ally' : 'unsurfaced'}>
            {report.live_provider_calls === 0 ? t('icpRadar.live.pipeline.signal.noLiveCalls') : t('icpRadar.live.pipeline.signal.liveCalls', { count: report.live_provider_calls })}
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
              <span>
                <Badge tone={signalStatusTone(row)}>{signalStatusLabel(row, t)}</Badge>
              </span>
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
  if (row.search_status === 'duplicate_existing_signal') {
    return 'neutral' as const;
  }
  if (row.search_status.includes('budget')) {
    return 'unsurfaced' as const;
  }
  if (row.observation_status === 'observed') {
    return 'ally' as const;
  }
  return 'neutral' as const;
}

function signalStatusLabel(row: SignalMonitoringReportSignal, t: (key: string, options?: Record<string, unknown>) => string) {
  if (row.search_status === 'duplicate_existing_signal') {
    return t('icpRadar.live.pipeline.signal.status.duplicate');
  }
  if (row.search_status.includes('budget')) {
    return t('icpRadar.live.pipeline.signal.status.budget');
  }
  if (row.observation_status === 'observed') {
    return t('icpRadar.live.pipeline.signal.status.observed');
  }
  if (row.observation_status === 'not_observed') {
    return t('icpRadar.live.pipeline.signal.status.notObserved');
  }
  return row.search_status || row.observation_status || t('icpRadar.notAvailable');
}
