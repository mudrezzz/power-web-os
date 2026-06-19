import { AlertTriangle, CheckCircle2, Clipboard, Filter, Search, ShieldCheck } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Mono } from '../../components/primitives';
import type { LiveRadarTechnicalTrace } from '../../types';
import {
  filterReadableTraceGroups,
  readableTraceGroups,
  stringifyTraceValue,
  type ReadableTraceStep,
  type TraceFilterKey,
} from './liveTraceModel';

const TRACE_FILTERS: TraceFilterKey[] = ['all', 'errors', 'provider', 'planning', 'validation'];

export function LiveRunTechnicalTracePanel({ trace }: { trace: LiveRadarTechnicalTrace | undefined }) {
  const { t } = useTranslation();
  const [filter, setFilter] = useState<TraceFilterKey>('all');
  const [query, setQuery] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const groups = useMemo(() => readableTraceGroups(trace), [trace]);
  const filteredGroups = useMemo(() => filterReadableTraceGroups(groups, filter, query), [filter, groups, query]);
  const visibleSteps = filteredGroups.flatMap((group) => group.steps);
  const selectedStep = visibleSteps.find((step) => step.item.trace_id === selectedId) ?? visibleSteps[0] ?? null;

  if (!groups.length) {
    return (
      <div className="technical-trace-empty">
        <strong>{t('icpRadar.live.trace.empty')}</strong>
        <p>{t('icpRadar.live.trace.emptyCopy')}</p>
      </div>
    );
  }

  return (
    <div className="technical-trace">
      <header className="technical-trace-header">
        <span className="section-icon">
          <ShieldCheck aria-hidden="true" />
        </span>
        <div>
          <strong>{t('icpRadar.live.trace.viewerTitle')}</strong>
          <p>{t('icpRadar.live.trace.policy')}</p>
        </div>
      </header>

      <div className="technical-trace-toolbar">
        <label className="technical-trace-search">
          <Search aria-hidden="true" />
          <input
            value={query}
            aria-label={t('icpRadar.live.trace.searchLabel')}
            placeholder={t('icpRadar.live.trace.searchPlaceholder')}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
        <div className="technical-trace-filters" aria-label={t('icpRadar.live.trace.filtersAria')}>
          {TRACE_FILTERS.map((key) => (
            <button
              className={`criteria-chip${filter === key ? ' criteria-chip-active' : ''}`}
              key={key}
              type="button"
              onClick={() => setFilter(key)}
            >
              {t(`icpRadar.live.trace.filters.${key}`)}
            </button>
          ))}
        </div>
      </div>

      {selectedStep ? (
        <div className="technical-trace-viewer">
          <TraceStepList groups={filteredGroups} selectedId={selectedStep.item.trace_id} onSelect={setSelectedId} />
          <TraceStepDetail step={selectedStep} />
        </div>
      ) : (
        <div className="technical-trace-empty">
          <strong>{t('icpRadar.live.trace.noMatches')}</strong>
          <p>{t('icpRadar.live.trace.noMatchesCopy')}</p>
        </div>
      )}
    </div>
  );
}

function TraceStepList({
  groups,
  onSelect,
  selectedId,
}: {
  groups: ReturnType<typeof filterReadableTraceGroups>;
  onSelect: (traceId: string) => void;
  selectedId: string;
}) {
  const { t } = useTranslation();
  return (
    <aside className="technical-trace-sidebar" aria-label={t('icpRadar.live.trace.stepList')}>
      {groups.map((group) => (
        <section className="technical-trace-group" key={group.key}>
          <h4>{t(`icpRadar.live.trace.group.${group.key}`)}</h4>
          {group.steps.map((step) => (
            <button
              className={`technical-trace-step${selectedId === step.item.trace_id ? ' technical-trace-step-active' : ''}`}
              key={step.item.trace_id}
              type="button"
              onClick={() => onSelect(step.item.trace_id)}
            >
              <TraceStatusIcon status={step.status} />
              <span>
                <strong>{step.title}</strong>
                <small>{step.summary || t('icpRadar.live.trace.noSummary')}</small>
              </span>
              <Mono>{step.item.sequence}</Mono>
            </button>
          ))}
        </section>
      ))}
    </aside>
  );
}

function TraceStepDetail({ step }: { step: ReadableTraceStep }) {
  const { t } = useTranslation();
  return (
    <article className="technical-trace-detail">
      <header>
        <div>
          <Badge tone={traceStatusTone(step.status)}>{t(`icpRadar.live.trace.status.${step.status}`)}</Badge>
          <Badge tone="neutral">{t(`icpRadar.live.trace.group.${step.groupKey}`)}</Badge>
          <Badge tone="neutral">{t(`icpRadar.live.trace.type.${step.item.trace_type}`, { defaultValue: step.item.trace_type })}</Badge>
        </div>
        <h3>{step.title}</h3>
        <p>{step.summary || t('icpRadar.live.trace.noSummary')}</p>
      </header>

      <dl className="technical-trace-meta">
        <TraceMeta label={t('icpRadar.live.trace.node')} value={step.item.node_name} />
        <TraceMeta label={t('icpRadar.live.trace.createdAt')} value={step.item.created_at ?? t('icpRadar.unknown')} />
        <TraceMeta
          label={t('icpRadar.live.trace.duration')}
          value={step.item.duration_ms == null ? t('icpRadar.unknown') : t('icpRadar.live.trace.durationMs', { count: step.item.duration_ms })}
        />
        {step.hints.map((hint) => <TraceMeta key={hint} label={t('icpRadar.live.trace.hint')} value={hint} />)}
      </dl>

      <div className="technical-trace-section-list">
        {step.sections.map((section) => (
          <section className="technical-trace-section" key={section.key}>
            <header>
              <h4>{t(`icpRadar.live.trace.section.${section.key}`)}</h4>
              {section.key !== 'raw' && (
                <Button icon={<Clipboard aria-hidden="true" />} variant="quiet" onClick={() => copyTraceValue(section.value)}>
                  {t('icpRadar.live.trace.copy')}
                </Button>
              )}
            </header>
            {section.key === 'raw' ? (
              <details>
                <summary>{t('icpRadar.live.trace.showRaw')}</summary>
                <TraceCode value={section.value} />
              </details>
            ) : (
              <TraceCode value={section.value} />
            )}
          </section>
        ))}
      </div>
    </article>
  );
}

function TraceMeta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd><Mono>{value}</Mono></dd>
    </div>
  );
}

function TraceCode({ value }: { value: Record<string, unknown> }) {
  return <pre>{stringifyTraceValue(value)}</pre>;
}

function TraceStatusIcon({ status }: { status: ReadableTraceStep['status'] }) {
  if (status === 'error') return <AlertTriangle aria-hidden="true" />;
  if (status === 'warning') return <Filter aria-hidden="true" />;
  return <CheckCircle2 aria-hidden="true" />;
}

function traceStatusTone(status: ReadableTraceStep['status']) {
  if (status === 'error') return 'blocker';
  if (status === 'warning') return 'unsurfaced';
  return 'ally';
}

function copyTraceValue(value: Record<string, unknown>) {
  void navigator.clipboard?.writeText(stringifyTraceValue(value));
}
