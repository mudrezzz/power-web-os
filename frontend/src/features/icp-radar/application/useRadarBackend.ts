import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { RadarApiClient, RadarApiError, type RadarPreflightDto, type RadarRunSummaryDto } from '../../../api/radarApi';
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

export type RadarBackendController = {
  catalog: ICPRadarCatalogArtifact | null;
  liveRunArtifact: LiveICPRadarRunArtifact | null;
  liveRunArtifacts: Record<string, LiveICPRadarRunArtifact>;
  runState: RadarRunControlState;
  preflightState: RadarPreflightControlState;
  loadRadarRunArtifact: (radarId: string) => Promise<void>;
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
};

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
  const pollCancel = useRef(false);

  const loadRunArtifact = useCallback(async (run: RadarRunSummaryDto, radar: ICPRadarCatalogItem) => {
    const [candidates, journal, dossier, technicalTrace] = await Promise.all([
      api.getRunCandidates(run.run_id),
      api.getRunJournal(run.run_id),
      api.getRunDossier(run.run_id),
      api.getRunTechnicalTrace(run.run_id),
    ]);
    return apiRunToLiveArtifact(run, candidates, radar, journal, dossier, technicalTrace);
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
        for (const summary of summaries) {
          if (summary.latest_run?.status === 'completed') {
            activeRunByRadarId.current[summary.radar_id] = summary.latest_run.run_id;
            latestRunByRadarId.current[summary.radar_id] = summary.latest_run;
          }
        }
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

      const detailResults = await Promise.allSettled(summaries.map((item) => api.getRadar(item.radar_id)));
      if (cancelled) {
        return;
      }
      const details = detailResults.flatMap((entry) => (entry.status === 'fulfilled' ? [entry.value] : []));
      const detailCatalog = apiDetailsToCatalogArtifact(details, fallbackCatalog);
      const detailItemsById = new Map(detailCatalog.radars.map((radar) => [radar.radar_id, radar]));
      const mergedRadars = summaryCatalog.radars.map((radar) => detailItemsById.get(radar.radar_id) ?? radar);
      for (const detailRadar of detailCatalog.radars) {
        if (!mergedRadars.some((radar) => radar.radar_id === detailRadar.radar_id)) {
          mergedRadars.push(detailRadar);
        }
      }
      const baseCatalog = { ...summaryCatalog, radars: mergedRadars };
      detailsByRadarId.current = Object.fromEntries(baseCatalog.radars.map((radar) => [radar.radar_id, radar]));
      for (const detail of details) {
        if (detail.latest_run?.status === 'completed') {
          activeRunByRadarId.current[detail.radar_id] = detail.latest_run.run_id;
          latestRunByRadarId.current[detail.radar_id] = detail.latest_run;
        }
      }
      setApiCatalog(baseCatalog);
    }
    loadCatalog();
    return () => {
      cancelled = true;
      pollCancel.current = true;
    };
  }, [api, fallbackCatalog]);

  const refreshRunOutput = useCallback(async (run: RadarRunSummaryDto, radar: ICPRadarCatalogItem | null) => {
    if (!radar) {
      return;
    }
    try {
      const artifact = await loadRunArtifact(run, radar);
      latestRunByRadarId.current[radar.radar_id] = run;
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
    if (runState.mode !== 'api' || apiLiveArtifacts[radarId]) {
      return;
    }
    const radar = detailsByRadarId.current[radarId];
    const latestRun = latestRunByRadarId.current[radarId];
    if (!radar || latestRun?.status !== 'completed' || !latestRun.output) {
      return;
    }
    await refreshRunOutput(latestRun, radar);
  }, [apiLiveArtifacts, refreshRunOutput, runState.mode]);

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
    catalog: apiCatalog ?? fallbackCatalog,
    liveRunArtifact: apiLiveArtifacts['toir-quick-live'] ?? fallbackLiveRunArtifact,
    liveRunArtifacts: apiLiveArtifacts,
    runState,
    preflightState,
    loadRadarRunArtifact,
    saveRadarDefinition,
    checkRadarSetup,
    runRadar,
    saveQualificationReview,
    saveSignalReview,
    resetSignalReview,
  };
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'Radar API request failed';
}
