import { Clock3, History } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { RadarRunSummaryDto } from '../../../api/radarApi';
import { Badge, Eyebrow, Mono } from '../../../components/primitives';

export function RadarRunSelector({
  runs,
  selectedRun,
  onSelectRun,
}: {
  runs: RadarRunSummaryDto[];
  selectedRun: RadarRunSummaryDto | null;
  onSelectRun: (runId: string) => void;
}) {
  const { i18n, t } = useTranslation();
  const options = runs.length ? runs : selectedRun ? [selectedRun] : [];
  const selectedMode = selectedRun ? runMode(selectedRun) : '';
  const selectedAt = selectedRun ? runTimestampLabel(selectedRun, i18n.language) : '';
  const selectedCount = selectedRun?.output?.candidate_count;

  return (
    <section className="radar-run-selector" aria-label={t('icpRadar.runHistory.aria')}>
      <div className="radar-run-selector-head">
        <span className="section-icon section-icon-sm">
          <History aria-hidden="true" />
        </span>
        <div>
          <Eyebrow>{t('icpRadar.runHistory.eyebrow')}</Eyebrow>
          <label htmlFor="radar-run-selector">{t('icpRadar.runHistory.label')}</label>
        </div>
      </div>
      <div className="radar-run-selector-control">
        <select
          id="radar-run-selector"
          disabled={!options.length}
          value={selectedRun?.run_id ?? ''}
          onChange={(event) => onSelectRun(event.target.value)}
        >
          {!options.length && <option value="">{t('icpRadar.runHistory.noRuns')}</option>}
          {options.map((run, index) => (
            <option key={run.run_id} value={run.run_id}>
              {index === 0 ? `${t('icpRadar.runHistory.latest')} - ` : ''}
              {runOptionLabel(run, i18n.language)}
            </option>
          ))}
        </select>
      </div>
      {selectedRun ? (
        <div className="radar-run-selector-meta">
          <Badge tone={statusTone(selectedRun.status)}>{selectedRun.status}</Badge>
          {selectedMode && <span>{selectedMode}</span>}
          {typeof selectedCount === 'number' && (
            <span>{t('icpRadar.runHistory.candidates', { count: selectedCount })}</span>
          )}
          {selectedAt && (
            <span className="radar-run-selector-date">
              <Clock3 aria-hidden="true" />
              {selectedAt}
            </span>
          )}
          <Mono>{selectedRun.run_id}</Mono>
        </div>
      ) : (
        <p className="radar-run-selector-empty">{t('icpRadar.runHistory.noRunsCopy')}</p>
      )}
    </section>
  );
}

function runOptionLabel(run: RadarRunSummaryDto, locale: string) {
  const timestamp = runTimestampLabel(run, locale);
  const mode = runMode(run);
  const count = typeof run.output?.candidate_count === 'number' ? `${run.output.candidate_count}` : 'no output';
  return [shortRunId(run.run_id), run.status, mode, count, timestamp].filter(Boolean).join(' - ');
}

function runTimestampLabel(run: RadarRunSummaryDto, locale: string) {
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

function runMode(run: RadarRunSummaryDto) {
  return stringMetadata(run, 'benchmark_mode')
    || stringMetadata(run, 'run_kind')
    || stringMetadata(run, 'pipeline_id')
    || stringMetadata(run, 'runtime_mode');
}

function stringMetadata(run: RadarRunSummaryDto, key: string) {
  const value = run.display_metadata?.[key] ?? run.run_metadata[key];
  return typeof value === 'string' && value.trim() ? value.trim() : '';
}

function statusTone(status: string) {
  if (status === 'completed') {
    return 'ally';
  }
  if (status === 'failed' || status === 'cancelled') {
    return 'blocker';
  }
  if (status === 'running' || status === 'queued') {
    return 'unsurfaced';
  }
  return 'neutral';
}

function shortRunId(runId: string) {
  return runId.length > 18 ? `${runId.slice(0, 18)}...` : runId;
}
