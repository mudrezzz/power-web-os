import { BellRing, Clock3, History } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { SignalMonitoringRunSummaryDto } from '../../../api/radarApi';
import { Badge, Eyebrow, Mono } from '../../../components/primitives';

export function SignalMonitoringRunSelector({
  runs,
  selectedRun,
  onSelectRun,
}: {
  runs: SignalMonitoringRunSummaryDto[];
  selectedRun: SignalMonitoringRunSummaryDto | null;
  onSelectRun: (runId: string) => void;
}) {
  const { i18n, t } = useTranslation();
  const options = runs.length ? runs : selectedRun ? [selectedRun] : [];
  const selectedAt = selectedRun ? runTimestampLabel(selectedRun, i18n.language) : '';

  return (
    <section className="radar-run-selector radar-run-selector-signal" aria-label={t('icpRadar.signalRunHistory.aria')}>
      <div className="radar-run-selector-head">
        <span className="section-icon section-icon-sm">
          <History aria-hidden="true" />
        </span>
        <div>
          <Eyebrow>{t('icpRadar.signalRunHistory.eyebrow')}</Eyebrow>
          <label htmlFor="signal-monitoring-run-selector">{t('icpRadar.signalRunHistory.label')}</label>
        </div>
      </div>
      <div className="radar-run-selector-control">
        <select
          id="signal-monitoring-run-selector"
          disabled={!options.length}
          value={selectedRun?.run_id ?? ''}
          onChange={(event) => onSelectRun(event.target.value)}
        >
          {!options.length && <option value="">{t('icpRadar.signalRunHistory.noRuns')}</option>}
          {options.map((run, index) => (
            <option key={run.run_id} value={run.run_id}>
              {index === 0 ? `${t('icpRadar.signalRunHistory.latest')} - ` : ''}
              {runOptionLabel(run, i18n.language)}
            </option>
          ))}
        </select>
      </div>
      {selectedRun ? (
        <div className="radar-run-selector-meta">
          <Badge tone={statusTone(selectedRun.status)}>{selectedRun.status}</Badge>
          {selectedRun.output?.completion_state && <span>{selectedRun.output.completion_state}</span>}
          {typeof selectedRun.output?.candidate_count === 'number' && (
            <span>{t('icpRadar.signalRunHistory.candidates', { count: selectedRun.output.candidate_count })}</span>
          )}
          {typeof selectedRun.output?.observation_count === 'number' && (
            <span>{t('icpRadar.signalRunHistory.observations', { count: selectedRun.output.observation_count })}</span>
          )}
          {selectedAt && (
            <span className="radar-run-selector-date">
              <Clock3 aria-hidden="true" />
              {selectedAt}
            </span>
          )}
          <span className="radar-run-selector-lineage">
            <BellRing aria-hidden="true" />
            {t('icpRadar.signalRunHistory.sourceRun')}
            <Mono>{selectedRun.source_run_id}</Mono>
          </span>
          <Mono>{selectedRun.run_id}</Mono>
        </div>
      ) : (
        <p className="radar-run-selector-empty">{t('icpRadar.signalRunHistory.noRunsCopy')}</p>
      )}
    </section>
  );
}

function runOptionLabel(run: SignalMonitoringRunSummaryDto, locale: string) {
  const timestamp = runTimestampLabel(run, locale);
  const count = typeof run.output?.candidate_count === 'number' ? `${run.output.candidate_count}` : 'no output';
  return [shortRunId(run.run_id), run.status, run.output?.completion_state, count, timestamp].filter(Boolean).join(' - ');
}

function runTimestampLabel(run: SignalMonitoringRunSummaryDto, locale: string) {
  const value = run.completed_at ?? run.started_at ?? run.queued_at;
  if (!value) {
    return '';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(locale, {
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function statusTone(status: string) {
  if (status === 'completed') {
    return 'ally' as const;
  }
  if (status === 'failed' || status === 'cancelled') {
    return 'blocker' as const;
  }
  if (status === 'running' || status === 'queued') {
    return 'unsurfaced' as const;
  }
  return 'neutral' as const;
}

function shortRunId(runId: string) {
  return runId.length > 18 ? `${runId.slice(0, 18)}...` : runId;
}
