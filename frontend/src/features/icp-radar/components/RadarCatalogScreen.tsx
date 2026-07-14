import { ChevronRight, LoaderCircle, Plus, Radar, RefreshCw, RotateCcw } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Card, Eyebrow, Mono } from '../../../components/primitives';
import type { ICPRadarCatalogItem } from '../../../types';
import type { RadarBackendMode, RadarCatalogConnectionState } from '../application/useRadarBackend';
import { cadenceKey, isLocalRadarStatus, lastRunKey, runModeKey } from '../domain/catalogMeta';
import { radarStatusKey } from '../domain/radarStatus';

export function RadarCatalogScreen({
  backendError,
  backendMode,
  catalogState,
  hasLocalChanges,
  onCreateRadar,
  onOpenRadar,
  onReconnect,
  onResetDemoChanges,
  radars,
}: {
  backendError: string | null;
  backendMode: RadarBackendMode;
  catalogState: RadarCatalogConnectionState;
  hasLocalChanges: boolean;
  onCreateRadar: () => void;
  onOpenRadar: (radar: ICPRadarCatalogItem) => void;
  onReconnect: () => void;
  onResetDemoChanges: () => void;
  radars: ICPRadarCatalogItem[];
}) {
  const { t } = useTranslation();
  const totals = radars.reduce(
    (acc, radar) => ({
      candidates: acc.candidates + radar.summary.candidate_count,
      review: acc.review + radar.summary.needs_review_count,
      accepted: acc.accepted + radar.summary.accepted_count,
    }),
    { candidates: 0, review: 0, accepted: 0 },
  );

  return (
    <section className="screen icp-radar-screen" aria-label={t('icpRadar.catalogAria')}>
      <header className="icp-radar-header">
        <span className="section-icon">
          <Radar aria-hidden="true" />
        </span>
        <div>
          <Eyebrow>{t('icpRadar.catalogEyebrow')}</Eyebrow>
          <h1>{t('icpRadar.catalogTitle')}</h1>
          <p>{t('icpRadar.catalogSummary', { count: radars.length })}</p>
        </div>
        <div className="icp-profile-meta">
          <Badge tone={backendMode === 'api' ? 'ally' : backendMode === 'fallback' ? 'unsurfaced' : 'neutral'}>
            {t(`icpRadar.live.backendMode.${backendMode}`)}
          </Badge>
          {backendMode !== 'api' && (
            <Button
              icon={catalogState.status === 'loading' || catalogState.status === 'retrying'
                ? <LoaderCircle aria-hidden="true" className="spin" />
                : <RefreshCw aria-hidden="true" />}
              variant="default"
              onClick={onReconnect}
              disabled={catalogState.status === 'loading'}
            >
              {t(catalogState.status === 'retrying'
                ? 'icpRadar.catalogRecovery.retrying'
                : 'icpRadar.catalogRecovery.reconnect')}
            </Button>
          )}
          <Badge tone="cobalt">{t('icpRadar.catalogTotals.candidates', { count: totals.candidates })}</Badge>
          <Badge tone="neutral">{t('icpRadar.catalogTotals.review', { count: totals.review })}</Badge>
          <Button icon={<Plus aria-hidden="true" />} variant="default" onClick={onCreateRadar}>
            {t('icpRadar.createRadar')}
          </Button>
          {hasLocalChanges && (
            <Button icon={<RotateCcw aria-hidden="true" />} variant="default" onClick={onResetDemoChanges}>
              {t('icpRadar.resetDemoChanges')}
            </Button>
          )}
          {backendError && (
            <span className="icp-radar-backend-error">
              <Mono>{backendError}</Mono>
            </span>
          )}
        </div>
      </header>

      <div className="icp-radar-catalog-list">
        {radars.map((radar) => (
          <Card interactive key={radar.radar_id} onClick={() => onOpenRadar(radar)}>
            <div className="icp-radar-list-row">
              <div className="icp-radar-list-main">
                <span className="section-icon">
                  <Radar aria-hidden="true" />
                </span>
                <div>
                  <Eyebrow>{t('icpRadar.radarCardEyebrow')}</Eyebrow>
                  <h2>{radar.name}</h2>
                  <p>{radar.profile.icp_profile}</p>
                  <small>{radar.profile.scope}</small>
                </div>
              </div>
              <span className="icp-radar-list-status">
                <Badge tone={radar.status === 'active' ? 'ally' : 'neutral'}>
                  {t(radarStatusKey(radar.status))}
                </Badge>
                {isLocalRadarStatus(radar.status) && (
                  <Badge tone="unsurfaced">{t('icpRadar.localDraft')}</Badge>
                )}
                {radar.local_override_status === 'protected_from_delete' && (
                  <Badge tone="unsurfaced">{t('icpRadar.localOverrideProtected')}</Badge>
                )}
              </span>
              <dl className="icp-radar-list-metrics">
                <Metric label={t('icpRadar.cardFields.cadence')} value={t(cadenceKey(radar.summary.cadence))} />
                <Metric label={t('icpRadar.cardFields.lastRun')} value={t(lastRunKey(radar.summary.last_run))} />
                <Metric label={t('icpRadar.cardFields.candidates')} value={String(radar.summary.candidate_count)} />
                <Metric label={t('icpRadar.cardFields.needsReview')} value={String(radar.summary.needs_review_count)} />
                <Metric label={t('icpRadar.cardFields.accepted')} value={String(radar.summary.accepted_count)} />
                <Metric label={t('icpRadar.cardFields.owner')} value={radar.owner} />
              </dl>
              <span className="icp-radar-run-mode">
                <Mono>{t(runModeKey(radar.summary.run_mode))}</Mono>
                {radar.summary.candidate_count_run_id && (
                  <small title={t('icpRadar.catalogRecovery.countBasis')}>
                    <Mono>{radar.summary.candidate_count_run_id}</Mono>
                  </small>
                )}
              </span>
              <div className="icp-radar-list-action">
                <span className="row-action">
                  {t('icpRadar.openRadar')}
                  <ChevronRight aria-hidden="true" />
                </span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}
