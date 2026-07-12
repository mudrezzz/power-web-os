import type { ReactNode } from 'react';
import { Activity, BellRing, Clock, Eye, ListChecks, Play, Radar } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Card, Eyebrow, Mono } from '../../components/primitives';
import type { SignalMonitoringRunSummaryDto } from '../../api/radarApi';
import type { ICPRadarCatalogItem, LiveICPRadarRunArtifact, SignalMonitoringReportArtifact } from '../../types';
import type { RadarRunControlState } from './application/useRadarBackend';
import type {
  SignalMonitoringPreflightControlState,
  SignalMonitoringRunControlState,
} from './application/useSignalMonitoringBackend';
import { SignalMonitoringRunSelector } from './components/SignalMonitoringRunSelector';
import { SignalMonitoringReportView } from './components/SignalMonitoringReportView';

// Radar pipeline controls make candidate discovery and signal monitoring visibly separate without owning API transport.
export function RadarPipelineControlPanel({
  artifact,
  diagnosticsOpen,
  onCheckSetup,
  onRunCandidateDiscovery,
  onRunSignalMonitoring,
  onCheckSignalMonitoringSetup,
  onSelectSignalRun,
  onToggleDiagnostics,
  onTogglePreflight,
  onToggleSignalReport,
  preflightOpen,
  radar,
  runState,
  signalMonitoringReport,
  signalPreflightState,
  signalRunHistory,
  signalRunState,
  selectedSignalRun,
  signalReportOpen,
}: {
  artifact: LiveICPRadarRunArtifact | null;
  diagnosticsOpen: boolean;
  onCheckSetup: () => void;
  onRunCandidateDiscovery: () => void;
  onRunSignalMonitoring: () => void;
  onCheckSignalMonitoringSetup: () => void;
  onSelectSignalRun: (runId: string) => void;
  onToggleDiagnostics: () => void;
  onTogglePreflight: () => void;
  onToggleSignalReport: () => void;
  preflightOpen: boolean;
  radar: ICPRadarCatalogItem | null;
  runState: RadarRunControlState;
  signalMonitoringReport: SignalMonitoringReportArtifact | null;
  signalPreflightState: SignalMonitoringPreflightControlState;
  signalRunHistory: SignalMonitoringRunSummaryDto[];
  signalRunState: SignalMonitoringRunControlState;
  selectedSignalRun: SignalMonitoringRunSummaryDto | null;
  signalReportOpen: boolean;
}) {
  const { t } = useTranslation();
  const monitoring = radar?.definition.monitoring_policy;
  const signalSummary = signalMonitoringReport?.summary;
  const signalRows = signalMonitoringReport?.signals.slice(0, 6) ?? [];
  const lastCandidateRun = candidateDiscoveryLastRunLabel(runState, radar, artifact, t);
  const candidateBudget = candidateBudgetSummary(artifact);
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
              <dd>{lastCandidateRun.kind === 'id' ? <Mono>{lastCandidateRun.label}</Mono> : lastCandidateRun.label}</dd>
            </div>
            <div>
              <dt>{t('icpRadar.live.pipeline.nextRun')}</dt>
              <dd>{t('icpRadar.live.pipeline.notConfigured')}</dd>
            </div>
          </dl>
          <div className="radar-pipeline-budget-heading"><Eyebrow>{t('icpRadar.live.pipeline.candidate.budgetAria')}</Eyebrow></div>
          <div className="radar-pipeline-metrics radar-pipeline-budget" aria-label={t('icpRadar.live.pipeline.candidate.budgetAria')}>
            <PipelineMetric label={t('icpRadar.live.pipeline.candidate.taskBudget')} value={candidateBudget.tasksUsed} />
            <PipelineMetric label={t('icpRadar.live.pipeline.candidate.taskLimit')} value={candidateBudget.taskLimit} />
            <PipelineMetric label={t('icpRadar.live.pipeline.candidate.providerCalls')} value={candidateBudget.providerCalls} />
            <PipelineMetric label={t('icpRadar.live.pipeline.candidate.exhausted')} value={candidateBudget.exhausted} />
          </div>
          <div className="radar-pipeline-actions">
            <Button disabled={runState.busy || runState.mode === 'loading'} icon={<Play aria-hidden="true" />} variant="primary" onClick={onRunCandidateDiscovery}>
              {runState.busy ? t('icpRadar.live.runInProgress') : t('icpRadar.live.pipeline.candidate.run')}
            </Button>
            {(runState.runId || artifact) && (
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
              <dd><SignalPipelineRunStatus state={signalRunState} report={signalMonitoringReport} /></dd>
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
              <dd>{selectedSignalRun ? <Mono>{selectedSignalRun.run_id}</Mono> : signalMonitoringReport ? <Mono>{signalMonitoringReport.run_id}</Mono> : t('icpRadar.live.pipeline.notConfigured')}</dd>
            </div>
          </dl>
          {selectedSignalRun && (
            <div className="radar-pipeline-lineage">
              <span>{t('icpRadar.live.pipeline.signal.sourceRun')}</span>
              <Mono>{selectedSignalRun.source_run_id}</Mono>
            </div>
          )}
          {runState.mode === 'api' && (
            <SignalMonitoringRunSelector
              runs={signalRunHistory}
              selectedRun={selectedSignalRun}
              onSelectRun={onSelectSignalRun}
            />
          )}
          <div className="radar-pipeline-budget-heading"><Eyebrow>{t('icpRadar.live.pipeline.signal.budgetAria')}</Eyebrow></div>
          <div className="radar-pipeline-metrics" aria-label={t('icpRadar.live.pipeline.signal.budgetAria')}>
            <PipelineMetric icon={<Activity aria-hidden="true" />} label={t('icpRadar.live.pipeline.signal.observations')} value={signalSummary?.observation_count ?? 0} />
            <PipelineMetric icon={<Clock aria-hidden="true" />} label={t('icpRadar.live.pipeline.signal.tasks')} value={signalSummary?.task_count ?? 0} />
            <PipelineMetric label={t('icpRadar.live.pipeline.signal.providerCalls')} value={signalSummary?.provider_call_count ?? 0} />
            <PipelineMetric label={t('icpRadar.live.pipeline.signal.retries')} value={signalSummary?.retry_count ?? 0} />
          </div>
          <div className="radar-pipeline-actions">
            <Button
              disabled={runState.mode !== 'api' || !artifact || signalRunState.busy}
              icon={<Play aria-hidden="true" />}
              variant="default"
              onClick={onRunSignalMonitoring}
            >
              {signalRunState.busy ? t('icpRadar.live.pipeline.signal.running') : t('icpRadar.live.pipeline.signal.run')}
            </Button>
            <Button
              disabled={runState.mode !== 'api' || !artifact || signalPreflightState.busy}
              icon={<ListChecks aria-hidden="true" />}
              variant="default"
              onClick={onCheckSignalMonitoringSetup}
            >
              {signalPreflightState.busy ? t('icpRadar.live.pipeline.signal.checking') : t('icpRadar.live.pipeline.signal.checkSetup')}
            </Button>
            {signalMonitoringReport && (
              <Button icon={<Eye aria-hidden="true" />} variant="default" onClick={onToggleSignalReport}>
                {signalReportOpen ? t('icpRadar.live.pipeline.signal.hideReport') : t('icpRadar.live.pipeline.signal.showReport')}
              </Button>
            )}
          </div>
          {runState.mode !== 'api' && (
            <p className="radar-pipeline-disabled-copy">{t('icpRadar.live.pipeline.signal.offlineCopy')}</p>
          )}
          <SignalMonitoringPreflightSummary state={signalPreflightState} />
          {signalRunState.error && <p className="live-radar-run-error">{signalRunState.error}</p>}
        </div>
      </section>
      {signalReportOpen && <SignalMonitoringReportView report={signalMonitoringReport} rows={signalRows} />}
    </Card>
  );
}

function candidateDiscoveryLastRunLabel(
  runState: RadarRunControlState,
  radar: ICPRadarCatalogItem | null,
  artifact: LiveICPRadarRunArtifact | null,
  t: (key: string, options?: Record<string, unknown>) => string,
) {
  const summaryLastRun = radar?.summary.last_run;
  const artifactRunId = artifact?.dossier?.run_context.run_id || artifact?.run_metadata.task_id;
  const artifactRunAt = artifact?.run_metadata.run_at;
  const fallback = t('icpRadar.live.pipeline.notConfigured');
  if (runState.runId) {
    return { kind: 'id' as const, label: runState.runId };
  }
  if (artifactRunId) {
    return { kind: 'id' as const, label: artifactRunId };
  }
  if (summaryLastRun && summaryLastRun !== 'not_run') {
    return { kind: 'text' as const, label: summaryLastRun };
  }
  if (artifactRunAt) {
    return { kind: 'text' as const, label: artifactRunAt };
  }
  return { kind: 'text' as const, label: fallback };
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

function SignalPipelineRunStatus({
  state,
  report,
}: {
  state: SignalMonitoringRunControlState;
  report: SignalMonitoringReportArtifact | null;
}) {
  const { t } = useTranslation();
  const status = state.status ?? (report ? report.completion_state : 'not_run');
  return (
    <div className="live-radar-run-status">
      <Badge tone={state.error ? 'blocker' : state.busy || state.outputPending ? 'unsurfaced' : report ? 'ally' : 'neutral'}>
        {t(`icpRadar.live.runStatus.${status}`, { defaultValue: status })}
      </Badge>
      {state.outputPending && <span>{t('icpRadar.live.outputPending')}</span>}
    </div>
  );
}

function SignalMonitoringPreflightSummary({ state }: { state: SignalMonitoringPreflightControlState }) {
  const { t } = useTranslation();
  if (state.error) {
    return <p className="live-radar-run-error">{state.error}</p>;
  }
  if (!state.report) {
    return null;
  }
  return (
    <div className="radar-signal-preflight">
      <Badge tone={state.report.ready_for_live_run ? 'ally' : 'blocker'}>
        {state.report.ready_for_live_run
          ? t('icpRadar.live.pipeline.signal.preflightReady')
          : t('icpRadar.live.pipeline.signal.preflightBlocked')}
      </Badge>
      <span>{t('icpRadar.live.pipeline.signal.preflightScope', {
        candidates: state.report.candidate_count,
        signals: state.report.signal_rule_count,
      })}</span>
      {state.report.issues.map((issue) => <span key={issue}>{issue}</span>)}
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

function candidateBudgetSummary(artifact: LiveICPRadarRunArtifact | null) {
  const dossier = artifact?.dossier;
  const semanticCounters = recordValue(dossier?.budget_summary, 'counters');
  const semanticSettings = recordValue(dossier?.budget_summary, 'settings');
  const externalCounters = dossier?.external_call_budget_counters ?? {};
  return {
    tasksUsed: numberValue(semanticCounters.total),
    taskLimit: numberValue(semanticSettings.max_total_web_tasks_per_run),
    providerCalls: numberValue(externalCounters['openrouter:run']),
    exhausted: (dossier?.budget_exhaustion_events.length ?? 0)
      + (dossier?.external_call_budget_exhaustion_events.length ?? 0),
  };
}

function recordValue(value: Record<string, unknown> | undefined, key: string): Record<string, unknown> {
  const nested = value?.[key];
  return nested && typeof nested === 'object' && !Array.isArray(nested)
    ? nested as Record<string, unknown>
    : {};
}

function numberValue(value: unknown) {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0;
}
