import { useTranslation } from 'react-i18next';
import { Badge, Mono } from '../../components/primitives';
import type { LiveRadarTechnicalTrace } from '../../types';

export function LiveRunTechnicalTracePanel({ trace }: { trace: LiveRadarTechnicalTrace | undefined }) {
  const { t } = useTranslation();
  const traces = trace?.traces ?? [];
  if (!traces.length) {
    return (
      <div className="technical-trace-empty">
        <strong>{t('icpRadar.live.trace.empty')}</strong>
        <p>{t('icpRadar.live.trace.emptyCopy')}</p>
      </div>
    );
  }
  return (
    <div className="technical-trace">
      <p className="journal-policy-copy">{t('icpRadar.live.trace.policy')}</p>
      {traces.map((item) => (
        <details className="technical-trace-row" key={item.trace_id}>
          <summary>
            <Mono>{item.sequence}</Mono>
            <span>
              <strong>{item.title || t(`icpRadar.live.trace.type.${item.trace_type}`, { defaultValue: item.trace_type })}</strong>
              <small>{item.summary || t('icpRadar.live.trace.noSummary')}</small>
            </span>
            <Badge tone="neutral">{t(`icpRadar.live.trace.phase.${item.phase}`, { defaultValue: item.phase })}</Badge>
            <Badge tone="neutral">{t(`icpRadar.live.trace.type.${item.trace_type}`, { defaultValue: item.trace_type })}</Badge>
          </summary>
          <dl className="technical-trace-meta">
            <div>
              <dt>{t('icpRadar.live.trace.node')}</dt>
              <dd><Mono>{item.node_name}</Mono></dd>
            </div>
            <div>
              <dt>{t('icpRadar.live.trace.createdAt')}</dt>
              <dd>{item.created_at ?? t('icpRadar.unknown')}</dd>
            </div>
            <div>
              <dt>{t('icpRadar.live.trace.duration')}</dt>
              <dd>{item.duration_ms == null ? t('icpRadar.unknown') : t('icpRadar.live.trace.durationMs', { count: item.duration_ms })}</dd>
            </div>
          </dl>
          <section className="technical-trace-payload">
            <h4>{t('icpRadar.live.trace.payload')}</h4>
            <pre>{formatTracePayload(item.payload)}</pre>
          </section>
          <section className="technical-trace-payload">
            <h4>{t('icpRadar.live.trace.redaction')}</h4>
            <pre>{formatTracePayload(item.redaction_report)}</pre>
          </section>
        </details>
      ))}
    </div>
  );
}

function formatTracePayload(value: Record<string, unknown>) {
  return JSON.stringify(value, null, 2);
}
