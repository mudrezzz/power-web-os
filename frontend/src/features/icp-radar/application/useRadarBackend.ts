import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { RadarApiClient, RadarApiError, type RadarPreflightDto, type RadarRunConfigurationDto, type RadarRunSummaryDto } from '../../../api/radarApi';
import type {
  ICPRadarCatalogArtifact,
  ICPRadarCatalogItem,
  LiveICPRadarRunArtifact,
  QualificationReviewDecision,
  RadarDefinition,
  SignalValidationDecision,
} from '../../../types';
import {
  apiDetailToCatalogItem,
  apiDetailsToCatalogArtifact,
  apiRunToLiveArtifact,
  catalogWithLiveRunArtifacts,
} from '../adapters/apiRadarAdapter';
import {
  useSignalMonitoringBackend,
  type SignalMonitoringBackendController,
} from './useSignalMonitoringBackend';

const terminalStatuses = new Set(['completed', 'failed']);
const pollingIntervalMs = 2000;
const pollingDeadlineMs = 15 * 60 * 1000;

export type RadarBackendMode = 'loading' | 'api' | 'fallback';

export type RadarRunControlState = {
  mode: RadarBackendMode;
  apiBaseUrl: string;
  busy: boolean;
  runId: string | null;
  status: string | null;
  error: string | null;
  outputPending: boolean;
};

export type RadarPreflightControlState = {
  busy: boolean;
  report: RadarPreflightDto | null;
  error: string | null;
};

export type RadarResourceState = {
  status: 'idle' | 'loading' | 'loaded' | 'empty' | 'failed';
  error: string | null;
};

export type RadarBackendController = {
  catalog: ICPRadarCatalogArtifact | null;
  liveRunArtifact: LiveICPRadarRunArtifact | null;
  liveRunArtifacts: Record<string, LiveICPRadarRunArtifact>;
  runHistoryByRadarId: Record<string, RadarRunSummaryDto[]>;
  selectedRunByRadarId: Record<string, RadarRunSummaryDto>;
  runState: RadarRunControlState;
  preflightState: RadarPreflightControlState;
  definitionStateByRadarId: Record<string, RadarResourceState>;
  runResourceStateByKey: Record<string, RadarResourceState>;
  configurationByRunId: Record<string, RadarRunConfigurationDto>;
  loadRadarDefinition: (radarId: string) => Promise<ICPRadarCatalogItem | null>;
  loadRadarRunResource: (radarId: string, resource: 'journal' | 'dossier' | 'trace') => Promise<void>;
  loadRadarRunConfiguration: (runId: string) => Promise<RadarRunConfigurationDto | null>;
  loadRadarRunArtifact: (radarId: string) => Promise<void>;
  loadRadarRunHistory: (radarId: string) => Promise<RadarRunSummaryDto[]>;
  selectRadarRun: (radarId: string, runId: string) => Promise<boolean>;
  selectRadarRunById: (runId: string) => Promise<string | null>;
  saveRadarDefinition: (radarId: string, definition: RadarDefinition) => Promise<ICPRadarCatalogItem | null>;
  checkRadarSetup: (radarId: string) => Promise<void>;
  runRadar: (radarId: string) => void;
  saveQualificationReview: (
    radarId: string,
    candidateId: string,
    ruleId: string,
    decision: QualificationReviewDecision | null,
  ) => Promise<boolean>;
  saveSignalReview: (decision: SignalValidationDecision | null) => Promise<boolean>;
  resetSignalReview: (radarId: string, candidateId: string, signalCode: string) => Promise<boolean>;
} & SignalMonitoringBackendController;

export function useRadarBackend({
  fallbackCatalog,
  fallbackLiveRunArtifact,
}: {
  fallbackCatalog: ICPRadarCatalogArtifact | null;
  fallbackLiveRunArtifact: LiveICPRadarRunArtifact | null;
}): RadarBackendController {
  // The backend mode boundary decides when API state owns Radar data and when demo fallback remains active.
  const api = useMemo(() => new RadarApiClient(), []);
  const [apiCatalog, setApiCatalog] = useState<ICPRadarCatalogArtifact | null>(null);
  const [apiLiveArtifacts, setApiLiveArtifacts] = useState<Record<string, LiveICPRadarRunArtifact>>({});
  const [runHistoryByRadarId, setRunHistoryByRadarId] = useState<Record<string, RadarRunSummaryDto[]>>({});
  const [selectedRunByRadarId, setSelectedRunByRadarId] = useState<Record<string, RadarRunSummaryDto>>({});
  const [definitionStateByRadarId, setDefinitionStateByRadarId] = useState<Record<string, RadarResourceState>>({});
  const [runResourceStateByKey, setRunResourceStateByKey] = useState<Record<string, RadarResourceState>>({});
  const [configurationByRunId, setConfigurationByRunId] = useState<Record<string, RadarRunConfigurationDto>>({});
  const [runState, setRunState] = useState<RadarRunControlState>({
    mode: 'loading',
    apiBaseUrl: api.baseUrl,
    busy: false,
    runId: null,
    status: null,
    error: null,
    outputPending: false,
  });
  const [preflightState, setPreflightState] = useState<RadarPreflightControlState>({
    busy: false,
    report: null,
    error: null,
  });
  const activeRunByRadarId = useRef<Record<string, string>>({});
  const latestRunByRadarId = useRef<Record<string, RadarRunSummaryDto>>({});
  const detailsByRadarId = useRef<Record<string, ICPRadarCatalogItem>>({});
  const definitionRequestByRadarId = useRef<Record<string, number>>({});
  const loadedDefinitionByRadarId = useRef<Record<string, boolean>>({});
  const runResources = useRef<Record<string, {
    journal?: Awaited<ReturnType<RadarApiClient['getRunJournal']>>;
    dossier?: Awaited<ReturnType<RadarApiClient['getRunDossier']>>;
    trace?: Awaited<ReturnType<RadarApiClient['getRunTechnicalTrace']>>;
  }>>({});
  const explicitRunSelectionByRadarId = useRef<Record<string, boolean>>({});
  const pollCancel = useRef(false);

  const loadRunArtifact = useCallback(async (run: RadarRunSummaryDto, radar: ICPRadarCatalogItem) => {
    const candidates = await api.getRunCandidates(run.run_id);
    return apiRunToLiveArtifact(run, candidates, radar);
  }, [api]);

  useEffect(() => {
    let cancelled = false;
    async function loadCatalog() {
      let summaryCatalog: ICPRadarCatalogArtifact;
      let summaries: Awaited<ReturnType<typeof api.listRadars>>;
      try {
        summaries = await api.listRadars();
        if (cancelled) {
          return;
        }
        summaryCatalog = apiDetailsToCatalogArtifact(summaries, fallbackCatalog);
        detailsByRadarId.current = Object.fromEntries(summaryCatalog.radars.map((radar) => [radar.radar_id, radar]));
        const summarySelectedRuns: Record<string, RadarRunSummaryDto> = {};
        for (const summary of summaries) {
          if (summary.latest_run?.status === 'completed' && !explicitRunSelectionByRadarId.current[summary.radar_id]) {
            activeRunByRadarId.current[summary.radar_id] = summary.latest_run.run_id;
            latestRunByRadarId.current[summary.radar_id] = summary.latest_run;
            summarySelectedRuns[summary.radar_id] = summary.latest_run;
          }
        }
        setSelectedRunByRadarId(summarySelectedRuns);
        setApiCatalog(summaryCatalog);
        setRunState((current) => ({
          ...current,
          mode: 'api',
          error: null,
        }));
      } catch (error) {
        if (cancelled) {
          return;
        }
        setRunState((current) => ({
          ...current,
          mode: 'fallback',
          error: errorMessage(error),
        }));
        return;
      }

    }
    loadCatalog();
    return () => {
      cancelled = true;
      pollCancel.current = true;
    };
  }, [api, fallbackCatalog]);

  const loadRadarDefinition = useCallback(async (radarId: string) => {
    if (loadedDefinitionByRadarId.current[radarId]) {
      return detailsByRadarId.current[radarId];
    }
    const requestId = (definitionRequestByRadarId.current[radarId] ?? 0) + 1;
    definitionRequestByRadarId.current[radarId] = requestId;
    setDefinitionStateByRadarId((current) => ({
      ...current,
      [radarId]: { status: 'loading', error: null },
    }));
    try {
      const detail = await api.getRadar(radarId);
      if (definitionRequestByRadarId.current[radarId] !== requestId) {
        return null;
      }
      const radar = apiDetailToCatalogItem(detail);
      detailsByRadarId.current[radarId] = radar;
      loadedDefinitionByRadarId.current[radarId] = Boolean(detail.active_definition);
      setApiCatalog((current) => current ? {
        ...current,
        radars: current.radars.map((item) => item.radar_id === radarId ? radar : item),
      } : current);
      setDefinitionStateByRadarId((current) => ({
        ...current,
        [radarId]: { status: detail.active_definition ? 'loaded' : 'empty', error: null },
      }));
      return radar;
    } catch (error) {
      if (definitionRequestByRadarId.current[radarId] === requestId) {
        setDefinitionStateByRadarId((current) => ({
          ...current,
          [radarId]: { status: 'failed', error: errorMessage(error) },
        }));
      }
      return null;
    }
  }, [api]);

  const loadRadarRunResource = useCallback(async (
    radarId: string,
    resource: 'journal' | 'dossier' | 'trace',
  ) => {
    const run = selectedRunByRadarId[radarId] ?? latestRunByRadarId.current[radarId];
    const radar = detailsByRadarId.current[radarId];
    if (!run || !radar || run.status !== 'completed') {
      return;
    }
    const key = `${run.run_id}:${resource}`;
    if (runResourceStateByKey[key]?.status === 'loaded') {
      return;
    }
    setRunResourceStateByKey((current) => ({ ...current, [key]: { status: 'loading', error: null } }));
    try {
      const candidates = await api.getRunCandidates(run.run_id);
      const cache = runResources.current[run.run_id] ?? {};
      if (resource === 'journal') cache.journal = await api.getRunJournal(run.run_id);
      if (resource === 'dossier') cache.dossier = await api.getRunDossier(run.run_id);
      if (resource === 'trace') cache.trace = await api.getRunTechnicalTrace(run.run_id);
      runResources.current[run.run_id] = cache;
      if ((selectedRunByRadarId[radarId] ?? latestRunByRadarId.current[radarId])?.run_id !== run.run_id) {
        return;
      }
      const artifact = apiRunToLiveArtifact(run, candidates, radar, cache.journal, cache.dossier, cache.trace);
      setApiLiveArtifacts((current) => ({ ...current, [radarId]: artifact }));
      setRunResourceStateByKey((current) => ({ ...current, [key]: { status: 'loaded', error: null } }));
    } catch (error) {
      setRunResourceStateByKey((current) => ({
        ...current,
        [key]: { status: 'failed', error: errorMessage(error) },
      }));
    }
  }, [api, runResourceStateByKey, selectedRunByRadarId]);

  const loadRadarRunConfiguration = useCallback(async (runId: string) => {
    if (configurationByRunId[runId]) {
      return configurationByRunId[runId];
    }
    try {
      const configuration = await api.getRunConfiguration(runId);
      setConfigurationByRunId((current) => ({ ...current, [runId]: configuration }));
      return configuration;
    } catch (error) {
      setRunState((current) => ({ ...current, error: errorMessage(error) }));
      return null;
    }
  }, [api, configurationByRunId]);

  const refreshRunOutput = useCallback(async (run: RadarRunSummaryDto, radar: ICPRadarCatalogItem | null) => {
    if (!radar) {
      return;
    }
    try {
      const artifact = await loadRunArtifact(run, radar);
      if (isSameOrNewerRun(run, latestRunByRadarId.current[radar.radar_id])) {
        latestRunByRadarId.current[radar.radar_id] = run;
      }
      activeRunByRadarId.current[radar.radar_id] = run.run_id;
      setSelectedRunByRadarId((current) => ({ ...current, [radar.radar_id]: run }));
      setApiLiveArtifacts((current) => ({ ...current, [radar.radar_id]: artifact }));
      setApiCatalog((current) => (current ? catalogWithLiveRunArtifacts(current, { [radar.radar_id]: artifact }) : current));
      setRunState((current) => ({
        ...current,
        busy: false,
        runId: run.run_id,
        status: run.status,
        error: null,
        outputPending: false,
      }));
    } catch (error) {
      if (error instanceof RadarApiError && error.kind === 'conflict') {
        activeRunByRadarId.current[radar.radar_id] = run.run_id;
        setSelectedRunByRadarId((current) => ({ ...current, [radar.radar_id]: run }));
        setApiLiveArtifacts((current) => {
          const next = { ...current };
          delete next[radar.radar_id];
          return next;
        });
        setRunState((current) => ({
          ...current,
          busy: false,
          runId: run.run_id,
          status: run.status,
          error: null,
          outputPending: true,
        }));
        return;
      }
      setRunState((current) => ({
        ...current,
        busy: false,
        runId: run.run_id,
        status: run.status,
        error: errorMessage(error),
        outputPending: false,
      }));
    }
  }, [loadRunArtifact]);

  const loadRadarRunArtifact = useCallback(async (radarId: string) => {
    const selectedRun = selectedRunByRadarId[radarId] ?? latestRunByRadarId.current[radarId];
    const currentArtifact = apiLiveArtifacts[radarId];
    if (
      runState.mode !== 'api'
      || (currentArtifact && artifactRunId(currentArtifact) === selectedRun?.run_id)
    ) {
      return;
    }
    const radar = detailsByRadarId.current[radarId];
    if (!radar || selectedRun?.status !== 'completed' || !selectedRun.output) {
      return;
    }
    await refreshRunOutput(selectedRun, radar);
  }, [apiLiveArtifacts, refreshRunOutput, runState.mode, selectedRunByRadarId]);

  const loadRadarRunHistory = useCallback(async (radarId: string) => {
    try {
      const runs = await api.listRadarRuns(radarId);
      setRunHistoryByRadarId((current) => ({ ...current, [radarId]: runsNewestFirst(runs) }));
      return runs;
    } catch (error) {
      setRunState((current) => ({
        ...current,
        mode: current.mode === 'loading' ? 'fallback' : current.mode,
        error: errorMessage(error),
      }));
      return [];
    }
  }, [api]);

  const selectRadarRun = useCallback(async (radarId: string, runId: string) => {
    try {
      const run = await api.getRun(runId);
      if (run.radar_id !== radarId) {
        setRunState((current) => ({
          ...current,
          mode: 'api',
          busy: false,
          error: `Radar run ${runId} belongs to ${run.radar_id}, not ${radarId}.`,
        }));
        return false;
      }
      let radar = detailsByRadarId.current[radarId] ?? null;
      if (!radar) {
        const detail = await api.getRadar(radarId);
        radar = apiDetailToCatalogItem(detail);
        detailsByRadarId.current[radarId] = radar;
        setRunHistoryByRadarId((current) => ({ ...current, [radarId]: runsNewestFirst(detail.runs) }));
      }
      explicitRunSelectionByRadarId.current[radarId] = true;
      activeRunByRadarId.current[radarId] = run.run_id;
      setSelectedRunByRadarId((current) => ({ ...current, [radarId]: run }));
      setRunHistoryByRadarId((current) => ({ ...current, [radarId]: mergeRunIntoHistory(current[radarId], run) }));
      setRunState((current) => ({
        ...current,
        mode: 'api',
        busy: !terminalStatuses.has(run.status),
        runId: run.run_id,
        status: run.status,
        error: run.error_message,
        outputPending: run.status === 'completed' && !run.output,
      }));
      if (run.status === 'completed' && run.output) {
        await refreshRunOutput(run, radar);
        return true;
      }
      setApiLiveArtifacts((current) => {
        const next = { ...current };
        delete next[radarId];
        return next;
      });
      return true;
    } catch (error) {
      setRunState((current) => ({
        ...current,
        mode: current.mode === 'loading' ? 'fallback' : current.mode,
        busy: false,
        error: errorMessage(error),
      }));
      return false;
    }
  }, [api, refreshRunOutput]);

  const selectRadarRunById = useCallback(async (runId: string) => {
    try {
      const run = await api.getRun(runId);
      const selected = await selectRadarRun(run.radar_id, run.run_id);
      return selected ? run.radar_id : null;
    } catch (error) {
      setRunState((current) => ({
        ...current,
        mode: current.mode === 'loading' ? 'fallback' : current.mode,
        busy: false,
        error: errorMessage(error),
      }));
      return null;
    }
  }, [api, selectRadarRun]);

  const signalMonitoring = useSignalMonitoringBackend({
    api,
    mode: runState.mode,
    selectedCandidateRunByRadarId: selectedRunByRadarId,
    selectCandidateRun: selectRadarRun,
  });

  const pollRun = useCallback(async (radarId: string, runId: string, startedAt: number) => {
    if (pollCancel.current) {
      return;
    }
    try {
      const run = await api.getRun(runId);
      const radar = detailsByRadarId.current[radarId] ?? null;
      setRunState((current) => ({
        ...current,
        mode: 'api',
        busy: !terminalStatuses.has(run.status),
        runId: run.run_id,
        status: run.status,
        error: run.error_message,
        outputPending: run.status === 'completed' && !run.output,
      }));
      if (run.status === 'completed') {
        await refreshRunOutput(run, radar);
        return;
      }
      if (run.status === 'failed' || Date.now() - startedAt > pollingDeadlineMs) {
        setRunState((current) => ({
          ...current,
          busy: false,
          error: run.error_message ?? current.error,
        }));
        return;
      }
      window.setTimeout(() => pollRun(radarId, runId, startedAt), pollingIntervalMs);
    } catch (error) {
      setRunState((current) => ({
        ...current,
        busy: false,
        error: errorMessage(error),
      }));
    }
  }, [api, refreshRunOutput]);

  const runRadar = useCallback((radarId: string) => {
    if (runState.busy) {
      return;
    }
    pollCancel.current = false;
    explicitRunSelectionByRadarId.current[radarId] = true;
    const idempotencyKey = `frontend:${radarId}:${Date.now()}:${Math.random().toString(36).slice(2)}`;
    setRunState((current) => ({
      ...current,
      mode: 'api',
      busy: true,
      runId: null,
      status: 'queued',
      error: null,
      outputPending: false,
    }));
    api.queueCandidateDiscoveryRun(radarId, {
      live: true,
      idempotency_key: idempotencyKey,
      requester: 'frontend',
      task_context: { source: 'manual_run' },
    })
      .then((run) => {
        activeRunByRadarId.current[radarId] = run.run_id;
        latestRunByRadarId.current[radarId] = run;
        setSelectedRunByRadarId((current) => ({ ...current, [radarId]: run }));
        setRunHistoryByRadarId((current) => ({ ...current, [radarId]: mergeRunIntoHistory(current[radarId], run) }));
        setRunState((current) => ({
          ...current,
          runId: run.run_id,
          status: run.status,
          busy: !terminalStatuses.has(run.status),
          error: run.error_message,
        }));
        if (run.status === 'completed') {
          return refreshRunOutput(run, detailsByRadarId.current[radarId] ?? null);
        }
        return pollRun(radarId, run.run_id, Date.now());
      })
      .catch((error) => {
        setRunState((current) => ({
          ...current,
          mode: 'fallback',
          busy: false,
          error: errorMessage(error),
        }));
      });
  }, [api, pollRun, refreshRunOutput, runState.busy]);

  const checkRadarSetup = useCallback(async (radarId: string) => {
    setPreflightState((current) => ({ ...current, busy: true, error: null }));
    try {
      const report = await api.getRadarPreflight(radarId);
      setPreflightState({ busy: false, report, error: null });
    } catch (error) {
      setPreflightState((current) => ({
        ...current,
        busy: false,
        error: errorMessage(error),
      }));
    }
  }, [api]);

  const saveRadarDefinition = useCallback(async (radarId: string, definition: RadarDefinition) => {
    if (runState.mode !== 'api') {
      return null;
    }
    const detail = await api.updateRadarDefinition(radarId, {
      definition_payload: definition as unknown as Record<string, unknown>,
      definition_version: undefined,
      is_active: true,
    });
    const saved = apiDetailToCatalogItem(detail);
    detailsByRadarId.current[radarId] = saved;
    setApiCatalog((current) => {
      if (!current) {
        return current;
      }
      return {
        ...current,
        radars: current.radars.map((item) => (item.radar_id === radarId ? saved : item)),
      };
    });
    return saved;
  }, [api, runState.mode]);

  const saveQualificationReview = useCallback(async (
    radarId: string,
    candidateId: string,
    ruleId: string,
    decision: QualificationReviewDecision | null,
  ) => {
    const runId = activeRunByRadarId.current[radarId];
    if (!runId || runState.mode !== 'api') {
      return false;
    }
    if (decision) {
      await api.saveQualificationReview(runId, candidateId, ruleId, {
        status: decision.status,
        reviewer: 'frontend',
        comment: decision.comment,
        corrected_assessment: decision.corrected_assessment,
        reviewed_at: decision.reviewed_at,
      });
    } else {
      await api.deleteQualificationReview(runId, candidateId, ruleId);
    }
    await refreshRunOutput(await api.getRun(runId), detailsByRadarId.current[radarId] ?? null);
    return true;
  }, [api, refreshRunOutput, runState.mode]);

  const saveSignalReview = useCallback(async (decision: SignalValidationDecision | null) => {
    if (!decision) {
      return false;
    }
    const runId = activeRunByRadarId.current[decision.radar_id];
    if (!runId || runState.mode !== 'api') {
      return false;
    }
    if (decision.status === 'unreviewed') {
      await api.deleteSignalReview(runId, decision.account_id, decision.signal_code);
    } else {
      await api.saveSignalReview(runId, decision.account_id, decision.signal_code, {
        status: decision.status,
        reviewer: 'frontend',
        comment: decision.comment,
        adjusted_score: decision.adjusted_score,
        confidence: decision.confidence,
        corrected_summary: decision.corrected_summary,
        evidence_refs: decision.evidence_refs,
        reviewed_at: decision.reviewed_at,
      });
    }
    await refreshRunOutput(await api.getRun(runId), detailsByRadarId.current[decision.radar_id] ?? null);
    return true;
  }, [api, refreshRunOutput, runState.mode]);

  const resetSignalReview = useCallback(async (radarId: string, candidateId: string, signalCode: string) => {
    const runId = activeRunByRadarId.current[radarId];
    if (!runId || runState.mode !== 'api') {
      return false;
    }
    await api.deleteSignalReview(runId, candidateId, signalCode);
    await refreshRunOutput(await api.getRun(runId), detailsByRadarId.current[radarId] ?? null);
    return true;
  }, [api, refreshRunOutput, runState.mode]);

  return {
    catalog: apiCatalog ?? (runState.mode === 'fallback' ? fallbackCatalog : null),
    liveRunArtifact: apiLiveArtifacts['toir-quick-live']
      ?? (runState.mode === 'fallback' ? fallbackLiveRunArtifact : null),
    liveRunArtifacts: apiLiveArtifacts,
    runHistoryByRadarId,
    selectedRunByRadarId,
    runState,
    preflightState,
    definitionStateByRadarId,
    runResourceStateByKey,
    configurationByRunId,
    loadRadarDefinition,
    loadRadarRunResource,
    loadRadarRunConfiguration,
    loadRadarRunArtifact,
    loadRadarRunHistory,
    selectRadarRun,
    selectRadarRunById,
    saveRadarDefinition,
    checkRadarSetup,
    runRadar,
    saveQualificationReview,
    saveSignalReview,
    resetSignalReview,
    ...signalMonitoring,
  };
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'Radar API request failed';
}

function artifactRunId(artifact: LiveICPRadarRunArtifact | undefined) {
  return artifact?.dossier?.run_context.run_id ?? null;
}

function mergeRunIntoHistory(
  current: RadarRunSummaryDto[] | undefined,
  run: RadarRunSummaryDto,
) {
  const byId = new Map((current ?? []).map((item) => [item.run_id, item]));
  byId.set(run.run_id, run);
  return runsNewestFirst(Array.from(byId.values()));
}

function runsNewestFirst(runs: RadarRunSummaryDto[]) {
  return [...runs].sort((left, right) => runTimestamp(right) - runTimestamp(left));
}

function isSameOrNewerRun(run: RadarRunSummaryDto, current: RadarRunSummaryDto | undefined) {
  if (!current) {
    return true;
  }
  return runTimestamp(run) >= runTimestamp(current);
}

function runTimestamp(run: RadarRunSummaryDto) {
  const value = run.queued_at ?? run.started_at ?? run.completed_at;
  const timestamp = value ? Date.parse(value) : Number.NaN;
  return Number.isFinite(timestamp) ? timestamp : 0;
}
