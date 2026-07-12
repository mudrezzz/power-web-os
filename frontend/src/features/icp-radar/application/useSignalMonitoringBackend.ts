import { useCallback, useEffect, useRef, useState } from 'react';
import {
  RadarApiClient,
  RadarApiError,
  type RadarRunSummaryDto,
  type SignalMonitoringPreflightDto,
  type SignalMonitoringRunRequestDto,
  type SignalMonitoringRunSummaryDto,
} from '../../../api/radarApi';
import type { SignalMonitoringCandidateSurfaceArtifact, SignalMonitoringReportArtifact } from '../../../types';
import { signalMonitoringReportFromJson } from '../signalMonitoringReport';
import { signalMonitoringCandidateSurfaceFromJson } from '../signalMonitoringSurface';

const terminalStatuses = new Set(['completed', 'failed']);
const pollingIntervalMs = 2000;
const pollingDeadlineMs = 15 * 60 * 1000;

type BackendMode = 'loading' | 'api' | 'fallback';

export type SignalMonitoringRunControlState = {
  busy: boolean;
  runId: string | null;
  status: string | null;
  error: string | null;
  outputPending: boolean;
};

export type SignalMonitoringPreflightControlState = {
  busy: boolean;
  report: SignalMonitoringPreflightDto | null;
  error: string | null;
};

export type SignalMonitoringBackendController = {
  signalRunHistoryByRadarId: Record<string, SignalMonitoringRunSummaryDto[]>;
  selectedSignalRunByRadarId: Record<string, SignalMonitoringRunSummaryDto>;
  signalReportByRunId: Record<string, SignalMonitoringReportArtifact>;
  signalSurfaceByRunId: Record<string, SignalMonitoringCandidateSurfaceArtifact>;
  signalRunState: SignalMonitoringRunControlState;
  signalPreflightState: SignalMonitoringPreflightControlState;
  loadSignalRunHistory: (radarId: string) => Promise<SignalMonitoringRunSummaryDto[]>;
  selectSignalRun: (radarId: string, runId: string) => Promise<boolean>;
  selectSignalRunById: (runId: string) => Promise<string | null>;
  checkSignalMonitoringSetup: (radarId: string) => Promise<void>;
  runSignalMonitoring: (radarId: string) => Promise<void>;
};

export function useSignalMonitoringBackend({
  api,
  mode,
  selectedCandidateRunByRadarId,
  selectCandidateRun,
}: {
  api: RadarApiClient;
  mode: BackendMode;
  selectedCandidateRunByRadarId: Record<string, RadarRunSummaryDto>;
  selectCandidateRun: (radarId: string, runId: string) => Promise<boolean>;
}): SignalMonitoringBackendController {
  const [signalRunHistoryByRadarId, setSignalRunHistoryByRadarId] = useState<
    Record<string, SignalMonitoringRunSummaryDto[]>
  >({});
  const [selectedSignalRunByRadarId, setSelectedSignalRunByRadarId] = useState<
    Record<string, SignalMonitoringRunSummaryDto>
  >({});
  const selectedSignalRunRef = useRef<Record<string, SignalMonitoringRunSummaryDto>>({});
  const [signalReportByRunId, setSignalReportByRunId] = useState<Record<string, SignalMonitoringReportArtifact>>({});
  const [signalSurfaceByRunId, setSignalSurfaceByRunId] = useState<
    Record<string, SignalMonitoringCandidateSurfaceArtifact>
  >({});
  const [signalRunState, setSignalRunState] = useState<SignalMonitoringRunControlState>({
    busy: false,
    runId: null,
    status: null,
    error: null,
    outputPending: false,
  });
  const [signalPreflightState, setSignalPreflightState] = useState<SignalMonitoringPreflightControlState>({
    busy: false,
    report: null,
    error: null,
  });
  const pollCancelled = useRef(false);

  useEffect(() => () => {
    pollCancelled.current = true;
  }, []);

  useEffect(() => {
    selectedSignalRunRef.current = selectedSignalRunByRadarId;
  }, [selectedSignalRunByRadarId]);

  const loadSignalReport = useCallback(async (run: SignalMonitoringRunSummaryDto) => {
    try {
      const [payload, surfacePayload] = await Promise.all([
        api.getSignalMonitoringReport(run.run_id),
        api.getSignalMonitoringCandidateSurface(run.run_id),
      ]);
      const report = signalMonitoringReportFromJson(payload);
      const surface = signalMonitoringCandidateSurfaceFromJson(surfacePayload);
      if (!report || report.run_id !== run.run_id || report.source_candidate_run_id !== run.source_run_id) {
        throw new Error(`Signal monitoring report ${run.run_id} has invalid pipeline lineage.`);
      }
      if (!surface || surface.selected_run_id !== run.run_id || surface.source_candidate_run_id !== run.source_run_id) {
        throw new Error(`Signal monitoring surface ${run.run_id} has invalid pipeline lineage.`);
      }
      setSignalReportByRunId((current) => ({ ...current, [run.run_id]: report }));
      setSignalSurfaceByRunId((current) => ({ ...current, [run.run_id]: surface }));
      setSignalRunState((current) => ({
        ...current,
        busy: false,
        runId: run.run_id,
        status: run.status,
        error: null,
        outputPending: false,
      }));
      return report;
    } catch (error) {
      const outputPending = error instanceof RadarApiError && error.kind === 'conflict';
      setSignalRunState((current) => ({
        ...current,
        busy: false,
        runId: run.run_id,
        status: run.status,
        error: outputPending ? null : errorMessage(error),
        outputPending,
      }));
      return null;
    }
  }, [api]);

  const selectSignalRun = useCallback(async (radarId: string, runId: string) => {
    try {
      const run = await api.getSignalMonitoringRun(runId);
      if (run.radar_id !== radarId) {
        throw new Error(`Signal monitoring run ${runId} belongs to ${run.radar_id}, not ${radarId}.`);
      }
      const selectedCandidate = selectedCandidateRunByRadarId[radarId];
      if (selectedCandidate?.run_id !== run.source_run_id) {
        const selected = await selectCandidateRun(radarId, run.source_run_id);
        if (!selected) {
          throw new Error(`Cannot select source candidate run ${run.source_run_id} for ${run.run_id}.`);
        }
      }
      setSelectedSignalRunByRadarId((current) => ({ ...current, [radarId]: run }));
      setSignalRunHistoryByRadarId((current) => ({
        ...current,
        [radarId]: mergeSignalRunIntoHistory(current[radarId], run),
      }));
      setSignalRunState({
        busy: !terminalStatuses.has(run.status),
        runId: run.run_id,
        status: run.status,
        error: run.error_message,
        outputPending: run.status === 'completed' && !run.output,
      });
      if (run.status === 'completed') {
        await loadSignalReport(run);
      }
      return true;
    } catch (error) {
      setSignalRunState((current) => ({ ...current, busy: false, error: errorMessage(error) }));
      return false;
    }
  }, [api, loadSignalReport, selectCandidateRun, selectedCandidateRunByRadarId]);

  const loadSignalRunHistory = useCallback(async (radarId: string) => {
    if (mode !== 'api') {
      return [];
    }
    try {
      const runs = signalRunsNewestFirst(await api.listSignalMonitoringRuns(radarId));
      setSignalRunHistoryByRadarId((current) => ({ ...current, [radarId]: runs }));
      const candidateRunId = selectedCandidateRunByRadarId[radarId]?.run_id;
      const current = selectedSignalRunRef.current[radarId];
      if (candidateRunId && current?.source_run_id !== candidateRunId) {
        const linked = runs.find((run) => run.source_run_id === candidateRunId);
        if (linked) {
          await selectSignalRun(radarId, linked.run_id);
        } else if (current) {
          setSelectedSignalRunByRadarId((items) => withoutKey(items, radarId));
          setSignalRunState((state) => ({
            ...state,
            busy: false,
            runId: null,
            status: null,
            error: null,
            outputPending: false,
          }));
        }
      }
      return runs;
    } catch (error) {
      setSignalRunState((current) => ({ ...current, busy: false, error: errorMessage(error) }));
      return [];
    }
  }, [api, mode, selectSignalRun, selectedCandidateRunByRadarId]);

  const selectSignalRunById = useCallback(async (runId: string) => {
    try {
      const run = await api.getSignalMonitoringRun(runId);
      const selected = await selectSignalRun(run.radar_id, run.run_id);
      return selected ? run.radar_id : null;
    } catch (error) {
      setSignalRunState((current) => ({ ...current, busy: false, error: errorMessage(error) }));
      return null;
    }
  }, [api, selectSignalRun]);

  const requestForRadar = useCallback((radarId: string): SignalMonitoringRunRequestDto | null => {
    const sourceRun = selectedCandidateRunByRadarId[radarId];
    if (!sourceRun || sourceRun.status !== 'completed' || !sourceRun.output) {
      return null;
    }
    return {
      source_candidate_run_id: sourceRun.run_id,
      candidate_scope_mode: 'accepted_and_review_needed',
      candidate_ids: [],
      signal_codes: [],
      lookback_days: null,
      run_profile: 'signal_monitoring_smoke',
      requester: 'frontend',
    };
  }, [selectedCandidateRunByRadarId]);

  const checkSignalMonitoringSetup = useCallback(async (radarId: string) => {
    const request = requestForRadar(radarId);
    if (!request) {
      setSignalPreflightState({
        busy: false,
        report: null,
        error: 'Select a completed candidate-discovery run with output before monitoring signals.',
      });
      return;
    }
    setSignalPreflightState((current) => ({ ...current, busy: true, error: null }));
    try {
      const report = await api.getSignalMonitoringPreflight(radarId, request);
      setSignalPreflightState({ busy: false, report, error: null });
    } catch (error) {
      setSignalPreflightState((current) => ({ ...current, busy: false, error: errorMessage(error) }));
    }
  }, [api, requestForRadar]);

  const pollSignalRun = useCallback(async function poll(
    radarId: string,
    runId: string,
    startedAt: number,
  ): Promise<void> {
    if (pollCancelled.current) {
      return;
    }
    try {
      const run = await api.getSignalMonitoringRun(runId);
      setSelectedSignalRunByRadarId((current) => ({ ...current, [radarId]: run }));
      setSignalRunHistoryByRadarId((current) => ({
        ...current,
        [radarId]: mergeSignalRunIntoHistory(current[radarId], run),
      }));
      setSignalRunState({
        busy: !terminalStatuses.has(run.status),
        runId: run.run_id,
        status: run.status,
        error: run.error_message,
        outputPending: run.status === 'completed' && !run.output,
      });
      if (run.status === 'completed') {
        await loadSignalReport(run);
        return;
      }
      if (run.status === 'failed' || Date.now() - startedAt > pollingDeadlineMs) {
        return;
      }
      window.setTimeout(() => {
        void poll(radarId, runId, startedAt);
      }, pollingIntervalMs);
    } catch (error) {
      setSignalRunState((current) => ({ ...current, busy: false, error: errorMessage(error) }));
    }
  }, [api, loadSignalReport]);

  const runSignalMonitoring = useCallback(async (radarId: string) => {
    if (mode !== 'api' || signalRunState.busy) {
      return;
    }
    const request = requestForRadar(radarId);
    if (!request) {
      setSignalRunState((current) => ({
        ...current,
        error: 'Select a completed candidate-discovery run with output before monitoring signals.',
      }));
      return;
    }
    pollCancelled.current = false;
    setSignalRunState({ busy: true, runId: null, status: 'preflight', error: null, outputPending: false });
    try {
      const preflight = await api.getSignalMonitoringPreflight(radarId, request);
      setSignalPreflightState({ busy: false, report: preflight, error: null });
      if (!preflight.ready_for_live_run) {
        setSignalRunState({
          busy: false,
          runId: null,
          status: 'preflight_failed',
          error: preflight.issues.join(' ') || 'Signal monitoring preflight failed.',
          outputPending: false,
        });
        return;
      }
      const run = await api.queueSignalMonitoringRun(radarId, {
        ...request,
        idempotency_key: `frontend:signal:${radarId}:${Date.now()}:${Math.random().toString(36).slice(2)}`,
      });
      setSelectedSignalRunByRadarId((current) => ({ ...current, [radarId]: run }));
      setSignalRunHistoryByRadarId((current) => ({
        ...current,
        [radarId]: mergeSignalRunIntoHistory(current[radarId], run),
      }));
      setSignalRunState({
        busy: !terminalStatuses.has(run.status),
        runId: run.run_id,
        status: run.status,
        error: run.error_message,
        outputPending: false,
      });
      if (run.status === 'completed') {
        await loadSignalReport(run);
      } else {
        await pollSignalRun(radarId, run.run_id, Date.now());
      }
    } catch (error) {
      setSignalRunState((current) => ({ ...current, busy: false, error: errorMessage(error) }));
    }
  }, [api, loadSignalReport, mode, pollSignalRun, requestForRadar, signalRunState.busy]);

  return {
    signalRunHistoryByRadarId,
    selectedSignalRunByRadarId,
    signalReportByRunId,
    signalSurfaceByRunId,
    signalRunState,
    signalPreflightState,
    loadSignalRunHistory,
    selectSignalRun,
    selectSignalRunById,
    checkSignalMonitoringSetup,
    runSignalMonitoring,
  };
}

function mergeSignalRunIntoHistory(
  current: SignalMonitoringRunSummaryDto[] | undefined,
  run: SignalMonitoringRunSummaryDto,
) {
  const byId = new Map((current ?? []).map((item) => [item.run_id, item]));
  byId.set(run.run_id, run);
  return signalRunsNewestFirst(Array.from(byId.values()));
}

function signalRunsNewestFirst(runs: SignalMonitoringRunSummaryDto[]) {
  return [...runs].sort((left, right) => runTimestamp(right) - runTimestamp(left));
}

function runTimestamp(run: SignalMonitoringRunSummaryDto) {
  const value = run.completed_at ?? run.started_at ?? run.queued_at;
  const timestamp = value ? Date.parse(value) : Number.NaN;
  return Number.isFinite(timestamp) ? timestamp : 0;
}

function withoutKey<T>(items: Record<string, T>, key: string) {
  const next = { ...items };
  delete next[key];
  return next;
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'Signal monitoring API request failed';
}
