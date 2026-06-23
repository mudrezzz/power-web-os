import { AlertTriangle, CircleHelp, ServerCog } from 'lucide-react';
import type { ReactNode } from 'react';
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import type { RadarPreflightCheckDto, RadarPreflightDto } from '../../api/radarApi';
import { Badge, Card, Eyebrow, Mono } from '../../components/primitives';
import type { LiveICPRadarRunArtifact } from '../../types';
import type { RadarPreflightControlState, RadarRunControlState } from './application/useRadarBackend';

type PreflightReadiness = 'ready' | 'warning' | 'failed' | 'unavailable';
type BadgeTone = 'ally' | 'blocker' | 'unsurfaced' | 'cobalt' | 'neutral';

// Preflight stays run-scoped and product-readable: provider probes remain CLI-only.

export function LiveRadarPreflightPanel({
  artifact,
  preflightState,
  runState,
}: {
  artifact: LiveICPRadarRunArtifact | null;
  preflightState: RadarPreflightControlState;
  runState: RadarRunControlState;
}) {
  const { t } = useTranslation();
  const model = useMemo(
    () => buildPreflightViewModel(preflightState.report, artifact, runState),
    [artifact, preflightState.report, runState],
  );

  return (
    <Card>
      <section className="run-preflight" aria-label={t('icpRadar.live.preflight.aria')}>
        <header className="run-diagnostics-head">
          <span className="section-icon">
            <ServerCog aria-hidden="true" />
          </span>
          <div>
            <Eyebrow>{t('icpRadar.live.preflight.eyebrow')}</Eyebrow>
            <h2>{t('icpRadar.live.preflight.title')}</h2>
            <p>{t('icpRadar.live.preflight.copy')}</p>
          </div>
          <Badge tone={readinessTone(model.readiness)}>
            {t(`icpRadar.live.preflight.readiness.${model.readiness}`)}
          </Badge>
        </header>

        {preflightState.busy && (
          <PreflightNotice icon={<CircleHelp aria-hidden="true" />} tone="neutral" title={t('icpRadar.live.preflight.loading')} />
        )}
        {preflightState.error && (
          <PreflightNotice icon={<AlertTriangle aria-hidden="true" />} tone="blocker" title={t('icpRadar.live.preflight.error')} copy={preflightState.error} />
        )}
        {!preflightState.busy && !preflightState.error && !preflightState.report && (
          <PreflightNotice icon={<CircleHelp aria-hidden="true" />} tone="neutral" title={t('icpRadar.live.preflight.notRun')} copy={t('icpRadar.live.preflight.notRunCopy')} />
        )}

        {preflightState.report && (
          <>
            <div className="run-diagnostics-metric-grid">
              {model.metrics.map((metric) => (
                <div className="run-diagnostics-metric" key={metric.key}>
                  <span>{t(`icpRadar.live.preflight.metrics.${metric.key}`)}</span>
                  <Mono>{metric.value}</Mono>
                </div>
              ))}
            </div>

            <section className="run-preflight-section">
              <h3>{t('icpRadar.live.preflight.runtime')}</h3>
              <div className="run-preflight-runtime-grid">
                {model.runtimeCards.map((card) => (
                  <div className="run-diagnostics-metric" key={card.key}>
                    <span>{t(`icpRadar.live.preflight.runtimeCards.${card.key}`)}</span>
                    <Mono>{card.value || t('icpRadar.unknown')}</Mono>
                  </div>
                ))}
              </div>
            </section>

            <section className="run-preflight-section">
              <h3>{t('icpRadar.live.preflight.parity')}</h3>
              <div className="run-diagnostics-warning">
                <Badge tone={parityTone(model.parity)}>
                  {t(`icpRadar.live.preflight.parityState.${model.parity}`)}
                </Badge>
                <p>{t(`icpRadar.live.preflight.parityCopy.${model.parity}`)}</p>
                <div className="run-diagnostics-reasons">
                  {model.apiFingerprint && <Mono>{t('icpRadar.live.preflight.apiFingerprint', { fingerprint: model.apiFingerprint })}</Mono>}
                  {model.workerFingerprint && <Mono>{t('icpRadar.live.preflight.workerFingerprint', { fingerprint: model.workerFingerprint })}</Mono>}
                </div>
                {model.runtimeWarnings.map((warning) => (
                  <p key={warning}>{warning}</p>
                ))}
              </div>
            </section>

            <section className="run-preflight-section">
              <h3>{t('icpRadar.live.preflight.checks')}</h3>
              <div className="run-preflight-check-list">
                {model.checks.map((check) => (
                  <article className="run-preflight-check" key={`${check.code}-${check.message}`}>
                    <header>
                      <Badge tone={checkTone(check)}>{t(`icpRadar.live.preflight.checkStatus.${check.status}`, { defaultValue: check.status })}</Badge>
                      <Mono>{check.code}</Mono>
                    </header>
                    <strong>{check.message}</strong>
                    {check.remediation && <p>{check.remediation}</p>}
                  </article>
                ))}
              </div>
            </section>
          </>
        )}
      </section>
    </Card>
  );
}

function PreflightNotice({
  copy,
  icon,
  title,
  tone,
}: {
  copy?: string;
  icon: ReactNode;
  title: string;
  tone: 'blocker' | 'neutral';
}) {
  return (
    <div className="run-diagnostics-empty">
      <span className="section-icon">{icon}</span>
      <span>
        <Badge tone={tone}>{title}</Badge>
        {copy && <p>{copy}</p>}
      </span>
    </div>
  );
}

function buildPreflightViewModel(
  report: RadarPreflightDto | null,
  artifact: LiveICPRadarRunArtifact | null,
  runState: RadarRunControlState,
) {
  const summary = objectField(report?.summary);
  const runtime = objectField(report?.runtime_config?.config);
  const apiFingerprint = report?.runtime_config?.fingerprint ?? '';
  const workerRuntime = objectField(artifact?.dossier?.runtime_config);
  const workerFingerprint = stringField(workerRuntime.fingerprint);
  const runtimeWarnings = (artifact?.dossier?.runtime_config_warnings ?? []).map((item) => {
    const path = stringField(item.path);
    const code = stringField(item.code, 'runtime_config_mismatch');
    return path ? `${code}: ${path}` : code;
  });
  const parity = runtimeWarnings.length
    ? 'mismatch'
    : apiFingerprint && workerFingerprint
      ? apiFingerprint === workerFingerprint ? 'match' : 'mismatch'
      : runState.runId ? 'no_worker_snapshot' : 'not_started';
  const failedCount = numberField(summary.error_count);
  const warningCount = numberField(summary.warning_count);
  const readiness: PreflightReadiness = !report
    ? 'unavailable'
    : report.ready_for_live_run && warningCount === 0
      ? 'ready'
      : report.ready_for_live_run
        ? 'warning'
        : 'failed';
  return {
    apiFingerprint,
    checks: [...(report?.checks ?? [])].sort(checkSort),
    metrics: [
      { key: 'passed', value: numberField(summary.passed_count) },
      { key: 'failed', value: failedCount },
      { key: 'warnings', value: warningCount },
      { key: 'checks', value: numberField(summary.check_count, report?.checks.length ?? 0) },
    ],
    parity,
    readiness,
    runtimeCards: [
      { key: 'model', value: stringField(nested(runtime, 'openrouter', 'model')) },
      { key: 'planner', value: stringField(nested(runtime, 'openrouter', 'planner_model')) },
      { key: 'extractor', value: stringField(nested(runtime, 'openrouter', 'extractor_model')) },
      { key: 'webMode', value: stringField(nested(runtime, 'openrouter', 'web_mode')) },
      { key: 'retrieval', value: `${stringField(nested(runtime, 'retrieval', 'provider'))}/${stringField(nested(runtime, 'retrieval', 'openrouter_web_search_engine'))}` },
      { key: 'dadata', value: stringField(nested(runtime, 'dadata', 'mode')) },
      { key: 'verification', value: stringField(nested(runtime, 'radar', 'source_verification_mode')) },
      { key: 'budget', value: String(nested(runtime, 'radar', 'max_total_web_tasks_per_run') ?? nested(runtime, 'radar', 'max_web_tasks_per_subject') ?? '') },
      { key: 'db', value: stringField(nested(runtime, 'persistence', 'database_kind')) },
      { key: 'queue', value: stringField(nested(runtime, 'celery', 'broker_kind')) },
      { key: 'fingerprint', value: apiFingerprint },
    ],
    runtimeWarnings,
    workerFingerprint,
  };
}

function checkSort(left: RadarPreflightCheckDto, right: RadarPreflightCheckDto) {
  const weight = (status: string) => ({ failed: 0, warning: 1, skipped: 2, passed: 3 }[status] ?? 4);
  return weight(left.status) - weight(right.status) || left.code.localeCompare(right.code);
}

function checkTone(check: RadarPreflightCheckDto): BadgeTone {
  if (check.status === 'failed' || check.severity === 'error') {
    return 'blocker';
  }
  if (check.status === 'warning' || check.severity === 'warning') {
    return 'unsurfaced';
  }
  return check.status === 'passed' ? 'ally' : 'neutral';
}

function readinessTone(readiness: PreflightReadiness): BadgeTone {
  if (readiness === 'ready') {
    return 'ally';
  }
  if (readiness === 'failed') {
    return 'blocker';
  }
  return readiness === 'warning' ? 'unsurfaced' : 'neutral';
}

function parityTone(parity: string): BadgeTone {
  if (parity === 'match') {
    return 'ally';
  }
  if (parity === 'mismatch') {
    return 'blocker';
  }
  return 'neutral';
}

function nested(payload: Record<string, unknown>, ...path: string[]) {
  let value: unknown = payload;
  for (const item of path) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
      return undefined;
    }
    value = (value as Record<string, unknown>)[item];
  }
  return value;
}

function objectField(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function numberField(value: unknown, fallback = 0): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function stringField(value: unknown, fallback = ''): string {
  return typeof value === 'string' && value ? value : fallback;
}
