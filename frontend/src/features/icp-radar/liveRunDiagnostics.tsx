import { Eye, ListChecks, ListTree, Radar, ScrollText } from 'lucide-react';
import type { ReactNode } from 'react';
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, Card, Eyebrow, Mono } from '../../components/primitives';
import type { LiveICPRadarRunArtifact, LiveRadarRunDossier } from '../../types';
import type { RadarRunControlState } from './application/useRadarBackend';
import { LiveRunDossierPanel, LiveRunJournalFallback } from './liveDossier';
import { LiveRunTechnicalTracePanel } from './liveTrace';

type DiagnosticsTab = 'overview' | 'universe' | 'sources' | 'journal' | 'trace';

// Run diagnostics is intentionally run-scoped: candidate detail remains candidate-specific evidence/review.
export function LiveRadarRunDiagnosticsView({
  artifact,
  runState,
}: {
  artifact: LiveICPRadarRunArtifact | null;
  runState: RadarRunControlState;
}) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<DiagnosticsTab>('overview');
  const dossier = artifact?.dossier;
  const diagnostics = useMemo(() => buildRunDiagnostics(artifact, dossier), [artifact, dossier]);
  const tabs: DiagnosticsTab[] = artifact?.technical_trace ? ['overview', 'universe', 'sources', 'journal', 'trace'] : ['overview', 'universe', 'sources', 'journal'];

  return (
    <Card>
      <section className="run-diagnostics" aria-label={t('icpRadar.live.diagnostics.aria')}>
        <header className="run-diagnostics-head">
          <span className="section-icon">
            <Radar aria-hidden="true" />
          </span>
          <div>
            <Eyebrow>{t('icpRadar.live.diagnostics.eyebrow')}</Eyebrow>
            <h2>{t('icpRadar.live.diagnostics.title')}</h2>
            <p>{t('icpRadar.live.diagnostics.copy')}</p>
          </div>
          <RunDiagnosticsStatus artifact={artifact} runState={runState} />
        </header>

        <div className="icp-candidate-detail-tabs" aria-label={t('icpRadar.live.diagnostics.tabsAria')}>
          {tabs.map((tab) => (
            <button
              aria-pressed={activeTab === tab}
              className={`criteria-chip${activeTab === tab ? ' criteria-chip-active' : ''}`}
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab)}
            >
              {t(`icpRadar.live.diagnostics.tabs.${tab}`)}
            </button>
          ))}
        </div>

        {activeTab === 'overview' && <RunDiagnosticsOverview diagnostics={diagnostics} runState={runState} />}
        {activeTab === 'universe' && <CandidateUniverseDiagnostics diagnostics={diagnostics} />}
        {activeTab === 'sources' && <SourceLifecycleDiagnostics diagnostics={diagnostics} />}
        {activeTab === 'journal' && (
          <div className="run-diagnostics-panel">
            {artifact?.dossier ? (
              <LiveRunDossierPanel artifact={artifact} dossier={artifact.dossier} />
            ) : artifact ? (
              <LiveRunJournalFallback
                artifact={artifact}
                events={(artifact.journal_events ?? []).filter((event) => event.visibility !== 'debug')}
              />
            ) : (
              <RunDiagnosticsEmpty
                icon={<ScrollText aria-hidden="true" />}
                title={t('icpRadar.live.diagnostics.noDossier')}
                copy={t('icpRadar.live.diagnostics.noDossierCopy')}
              />
            )}
            <p className="journal-policy-copy">{t('icpRadar.live.journal.hiddenCotPolicy')}</p>
          </div>
        )}
        {activeTab === 'trace' && (
          <div className="run-diagnostics-panel">
            <LiveRunTechnicalTracePanel trace={artifact?.technical_trace} />
          </div>
        )}
      </section>
    </Card>
  );
}

function RunDiagnosticsStatus({
  artifact,
  runState,
}: {
  artifact: LiveICPRadarRunArtifact | null;
  runState: RadarRunControlState;
}) {
  const { t } = useTranslation();
  const status = artifact?.dossier?.run_context.status ?? runState.status ?? (runState.mode === 'api' ? 'ready' : runState.mode);
  return (
    <div className="run-diagnostics-status">
      <Badge tone={runState.error || status === 'failed' ? 'blocker' : runState.busy || runState.outputPending ? 'unsurfaced' : 'neutral'}>
        {t(`icpRadar.live.runStatus.${status}`, { defaultValue: status })}
      </Badge>
      {(artifact?.dossier?.run_context.run_id || runState.runId) && <Mono>{artifact?.dossier?.run_context.run_id ?? runState.runId}</Mono>}
      {runState.outputPending && <span>{t('icpRadar.live.outputPending')}</span>}
    </div>
  );
}

function RunDiagnosticsOverview({
  diagnostics,
  runState,
}: {
  diagnostics: RunDiagnosticsViewModel;
  runState: RadarRunControlState;
}) {
  const { t } = useTranslation();
  return (
    <div className="run-diagnostics-panel">
      <div className="run-diagnostics-metric-grid">
        {diagnostics.metrics.map((metric) => (
          <div className="run-diagnostics-metric" key={metric.key}>
            <span>{t(`icpRadar.live.diagnostics.metrics.${metric.key}`)}</span>
            <Mono>{metric.value}</Mono>
          </div>
        ))}
      </div>
      {runState.error && (
        <div className="run-diagnostics-warning">
          <Badge tone="blocker">{t('icpRadar.live.diagnostics.runError')}</Badge>
          <p>{runState.error}</p>
        </div>
      )}
      {diagnostics.coverageWarnings.length > 0 ? (
        <div className="run-diagnostics-warning-list">
          {diagnostics.coverageWarnings.map((warning) => (
            <div className="run-diagnostics-warning" key={warning}>
              <Badge tone="unsurfaced">{t('icpRadar.live.diagnostics.coverageWarning')}</Badge>
              <p>{warning}</p>
            </div>
          ))}
        </div>
      ) : (
        <RunDiagnosticsEmpty
          icon={<ListChecks aria-hidden="true" />}
          title={t('icpRadar.live.diagnostics.noWarnings')}
          copy={t('icpRadar.live.diagnostics.noWarningsCopy')}
        />
      )}
    </div>
  );
}

function CandidateUniverseDiagnostics({ diagnostics }: { diagnostics: RunDiagnosticsViewModel }) {
  const { t } = useTranslation();
  if (!diagnostics.candidateUniverse.length) {
    return (
      <RunDiagnosticsEmpty
        icon={<ListTree aria-hidden="true" />}
        title={t('icpRadar.live.diagnostics.noCandidateUniverse')}
        copy={t('icpRadar.live.diagnostics.noCandidateUniverseCopy')}
      />
    );
  }
  return (
    <div className="run-diagnostics-panel">
      <div className="run-diagnostics-table run-diagnostics-table--candidates">
        <div className="run-diagnostics-table-head">
          <span>{t('icpRadar.live.diagnostics.candidateColumns.candidate')}</span>
          <span>{t('icpRadar.live.diagnostics.candidateColumns.status')}</span>
          <span>{t('icpRadar.live.diagnostics.candidateColumns.origin')}</span>
          <span>{t('icpRadar.live.diagnostics.candidateColumns.signal')}</span>
          <span>{t('icpRadar.live.diagnostics.candidateColumns.reasons')}</span>
        </div>
        {diagnostics.candidateUniverse.map((candidate) => (
          <div className="run-diagnostics-table-row" key={candidate.candidateId}>
            <span>
              <strong>{candidate.legalName}</strong>
              <small><Mono>{candidate.candidateId}</Mono></small>
            </span>
            <span>
              <Badge tone={candidate.statusTone}>
                {t(`icpRadar.live.dossier.candidateUniverseStatus.${candidate.status}`, { defaultValue: candidate.status })}
              </Badge>
            </span>
            <span><Mono>{candidate.originTaskId || t('icpRadar.unknown')}</Mono></span>
            <span>
              <Badge tone={candidate.signalSearched ? 'ally' : 'unsurfaced'}>
                {candidate.signalSearched
                  ? t('icpRadar.live.diagnostics.signalStatus.searched')
                  : t(`icpRadar.live.diagnostics.signalStatus.${candidate.signalReason}`)}
              </Badge>
            </span>
            <span className="run-diagnostics-reasons">
              {candidate.reasons.length ? candidate.reasons.map((reason) => <Mono key={reason}>{reason}</Mono>) : <small>{t('icpRadar.live.diagnostics.noReasons')}</small>}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function SourceLifecycleDiagnostics({ diagnostics }: { diagnostics: RunDiagnosticsViewModel }) {
  const { t } = useTranslation();
  if (!diagnostics.sources.length) {
    return (
      <RunDiagnosticsEmpty
        icon={<Eye aria-hidden="true" />}
        title={t('icpRadar.live.diagnostics.noSourceLifecycle')}
        copy={t('icpRadar.live.diagnostics.noSourceLifecycleCopy')}
      />
    );
  }
  return (
    <div className="run-diagnostics-panel">
      <div className="run-diagnostics-source-list">
        {diagnostics.sources.map((source) => (
          <article className="run-diagnostics-source" key={`${source.ref}-${source.state}-${source.reason}`}>
            <header>
              <Mono>{source.ref}</Mono>
              <Badge tone={source.stateTone}>{t(`icpRadar.live.dossier.sourceLifecycleState.${source.state}`, { defaultValue: source.state })}</Badge>
              {source.verificationState && (
                <Badge tone={source.verificationTone}>
                  {t(`icpRadar.live.dossier.sourceVerificationState.${source.verificationState}`, { defaultValue: source.verificationState })}
                </Badge>
              )}
            </header>
            <strong>{source.title}</strong>
            <p>{t(`icpRadar.live.dossier.sourceLifecycleReason.${source.reason}`, { defaultValue: source.reason })}</p>
            {source.url && <a href={source.url} rel="noreferrer" target="_blank">{source.url}</a>}
            <div className="run-diagnostics-source-meta">
              <Mono>{source.queryId || t('icpRadar.unknown')}</Mono>
              <Mono>{source.origin || t('icpRadar.unknown')}</Mono>
              <Mono>{source.usageCount}</Mono>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function RunDiagnosticsEmpty({ copy, icon, title }: { copy: string; icon: ReactNode; title: string }) {
  return (
    <div className="run-diagnostics-empty">
      <span className="section-icon">{icon}</span>
      <span>
        <strong>{title}</strong>
        <p>{copy}</p>
      </span>
    </div>
  );
}

type RunDiagnosticsViewModel = {
  metrics: Array<{ key: string; value: number | string }>;
  coverageWarnings: string[];
  candidateUniverse: Array<{
    candidateId: string;
    legalName: string;
    status: string;
    statusTone: 'ally' | 'blocker' | 'unsurfaced' | 'neutral';
    originTaskId: string;
    signalSearched: boolean;
    signalReason: string;
    reasons: string[];
  }>;
  sources: Array<{
    ref: string;
    title: string;
    url: string;
    state: string;
    stateTone: 'ally' | 'blocker' | 'unsurfaced' | 'neutral';
    reason: string;
    verificationState: string | null;
    verificationTone: 'ally' | 'blocker' | 'unsurfaced' | 'neutral';
    queryId: string | null;
    origin: string;
    usageCount: number;
  }>;
};

function buildRunDiagnostics(artifact: LiveICPRadarRunArtifact | null, dossier: LiveRadarRunDossier | undefined): RunDiagnosticsViewModel {
  const signalTasks = dossier?.search_plan.filter((query) => query.stage === 'signal_search' || query.subject_type === 'signal') ?? [];
  const searchedSignals = new Set<string>();
  for (const task of signalTasks) {
    for (const ref of task.candidate_refs ?? []) {
      searchedSignals.add(ref);
    }
    for (const ref of task.candidate_scope ?? []) {
      searchedSignals.add(ref);
    }
  }
  for (const candidate of artifact?.candidates ?? []) {
    if (candidate.signals.length > 0) {
      searchedSignals.add(candidate.candidate_id);
      searchedSignals.add(candidate.legal_name);
    }
  }
  const warnings = [
    ...(dossier?.coverage_warnings ?? []),
    ...(dossier?.coverage_summary.warnings ?? []),
    ...(dossier?.discovery_plan.warnings ?? []),
  ].filter(Boolean);
  const budgetLimited = warnings.some((warning) => warning.toLowerCase().includes('budget'));
  const candidateUniverse = (dossier?.candidate_universe ?? []).map((candidate) => {
    const signalSearched = searchedSignals.has(candidate.candidate_id) || searchedSignals.has(candidate.legal_name);
    const signalReason = signalSearched ? 'searched' : signalNotSearchedReason(candidate.status, signalTasks.length, budgetLimited);
    return {
      candidateId: candidate.candidate_id,
      legalName: candidate.legal_name,
      status: candidate.status,
      statusTone: candidateUniverseTone(candidate.status),
      originTaskId: candidate.origin_task_id,
      signalSearched,
      signalReason,
      reasons: [...candidate.rejection_reasons, ...candidate.coverage_flags, ...candidate.source_refs].filter(Boolean).slice(0, 8),
    };
  });
  return {
    metrics: [
      { key: 'tasks', value: dossier?.search_plan.length ?? artifact?.search_plan.queries.length ?? 0 },
      { key: 'candidates', value: dossier?.summary.candidate_count ?? artifact?.candidates.length ?? 0 },
      { key: 'universe', value: dossier?.candidate_universe.length ?? 0 },
      { key: 'usedSources', value: dossier?.summary.used_source_count ?? artifact?.sources.length ?? 0 },
      { key: 'analyzedSources', value: dossier?.summary.analyzed_source_count ?? 0 },
      { key: 'trace', value: artifact?.technical_trace?.traces.length ?? 0 },
    ],
    coverageWarnings: warnings,
    candidateUniverse,
    sources: (dossier?.source_lifecycle ?? []).map((source) => ({
      ref: source.evidence_ref,
      title: source.title || source.url || source.evidence_ref,
      url: source.url,
      state: source.state,
      stateTone: sourceLifecycleTone(source.state),
      reason: source.reason,
      verificationState: source.verification_state,
      verificationTone: sourceVerificationTone(source.verification_state ?? ''),
      queryId: source.query_id,
      origin: source.origin,
      usageCount: source.usages.length,
    })),
  };
}

function signalNotSearchedReason(status: string, signalTaskCount: number, budgetLimited: boolean) {
  if (status === 'rejected') {
    return 'rejected';
  }
  if (status === 'gap') {
    return 'gap';
  }
  if (signalTaskCount === 0) {
    return 'no_signal_tasks';
  }
  if (budgetLimited) {
    return 'budget_limited';
  }
  return 'not_selected';
}

function candidateUniverseTone(status: string): 'ally' | 'blocker' | 'unsurfaced' | 'neutral' {
  if (status === 'qualified') {
    return 'ally';
  }
  if (status === 'rejected') {
    return 'blocker';
  }
  if (status === 'gap' || status === 'unknown_review_needed') {
    return 'unsurfaced';
  }
  return 'neutral';
}

function sourceLifecycleTone(state: string): 'ally' | 'blocker' | 'unsurfaced' | 'neutral' {
  if (state === 'used' || state === 'used_in_product' || state === 'linked' || state === 'verified') {
    return 'ally';
  }
  if (state === 'schema_rejected' || state === 'verification_failed') {
    return 'blocker';
  }
  if (state === 'discarded' || state === 'analyzed_only' || state === 'skipped' || state === 'linking_failed' || state === 'budget_limited') {
    return 'unsurfaced';
  }
  return 'neutral';
}

function sourceVerificationTone(state: string): 'ally' | 'blocker' | 'unsurfaced' | 'neutral' {
  if (state === 'reachable') {
    return 'ally';
  }
  if (state === 'invalid_url') {
    return 'blocker';
  }
  if (state === 'blocked' || state === 'timeout' || state === 'unverified_url') {
    return 'unsurfaced';
  }
  return 'neutral';
}
