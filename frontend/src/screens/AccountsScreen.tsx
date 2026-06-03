import { CheckCircle2, ChevronRight, EyeOff, Route, ShieldCheck } from 'lucide-react';
import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, Card, Eyebrow, HealthBar, Mono } from '../components/primitives';
import { useDemoLocalization } from '../demoLocalization';
import type { AccountRadarArtifact, AccountRadarItem } from '../types';

export function AccountsScreen({
  artifact,
  error,
  selectedAccountId,
  onOpenAccount,
}: {
  artifact: AccountRadarArtifact | null;
  error: string | null;
  selectedAccountId: string | null;
  onOpenAccount: (item: AccountRadarItem) => void;
}) {
  const { t } = useTranslation();
  const demo = useDemoLocalization();

  if (error) {
    return (
      <StatusCard title={t('accounts.status.notReadyTitle')}>
        <p>{t('accounts.status.notReadyCopy')}</p>
        <code>python -m power_web_os.demo generate-account-radar</code>
      </StatusCard>
    );
  }

  if (!artifact) {
    return (
      <StatusCard title={t('accounts.status.loadingTitle')}>
        <p>{t('accounts.status.loadingCopy')}</p>
      </StatusCard>
    );
  }

  const topAccount = artifact.accounts[0];

  return (
    <section className="screen accounts-screen" aria-label={t('accounts.aria')}>
      <div className="accounts-header">
        <div>
          <Eyebrow>{t('accounts.eyebrow')}</Eyebrow>
          <h1>{t('accounts.title')}</h1>
          <p>{t('accounts.summary', { count: artifact.accounts.length })}</p>
        </div>
        {topAccount && (
          <div className="radar-highlight">
            <span>{t('accounts.topAccount')}</span>
            <strong>{topAccount.account_name}</strong>
            <Mono>{t('accounts.radarScoreValue', { score: topAccount.radar_score })}</Mono>
          </div>
        )}
      </div>

      <div className="filter-row" aria-label={t('accounts.filters.aria')}>
        <Badge tone="cobalt">{t('accounts.filters.all')}</Badge>
        <Badge tone="neutral">{t('accounts.filters.myBook')}</Badge>
        <Badge tone="neutral">{t('accounts.filters.needsRoute')}</Badge>
        <Badge tone="neutral">{t('accounts.filters.reviewRequired')}</Badge>
      </div>

      <Card>
        <div className="accounts-table">
          <div className="accounts-table-head">
            <span>{t('accounts.columns.account')}</span>
            <span>{t('accounts.columns.stage')}</span>
            <span>{t('accounts.columns.radarScore')}</span>
            <span>{t('accounts.columns.signals')}</span>
            <span>{t('accounts.columns.missing')}</span>
            <span>{t('accounts.columns.bestRoute')}</span>
            <span>{t('accounts.columns.owner')}</span>
            <span>{t('accounts.columns.review')}</span>
          </div>
          {artifact.accounts.map((item) => (
            <button
              className={`account-row${selectedAccountId === item.account_id ? ' account-row-selected' : ''}`}
              key={item.account_id}
              type="button"
              onClick={() => onOpenAccount(item)}
            >
              <span className="account-cell">
                <span className="account-initials">{initials(item.account_name)}</span>
                <span>
                  <strong>{item.account_name}</strong>
                  <small>{demo.text(item.top_reason)}</small>
                </span>
              </span>
              <span>
                <StageBadge stage={item.stage} label={demo.stage(item.stage)} />
              </span>
              <span>
                <HealthBar value={item.radar_score} label={t('accounts.scoreLabel', { accountName: item.account_name })} />
              </span>
              <span className="metric-cell">
                <ShieldCheck aria-hidden="true" />
                <Mono>{item.signal_count}</Mono>
              </span>
              <span className="metric-cell">
                {item.missing_role_count > 0 ? <EyeOff aria-hidden="true" /> : <CheckCircle2 aria-hidden="true" />}
                <Mono>{item.missing_role_count}</Mono>
              </span>
              <span className="route-cell">
                <Route aria-hidden="true" />
                <span>
                  {item.best_route_title
                    ? demo.routeTitle(item.best_route_type ?? '', item.best_route_title)
                    : t('accounts.noRoute')}
                </span>
                <Mono>{item.best_route_score}</Mono>
              </span>
              <span className="text-cell">{item.owner ? demo.owner(item.owner) : t('accounts.unassigned')}</span>
              <span>
                <Badge tone={item.review_required ? 'unsurfaced' : 'ally'}>
                  {item.review_required ? t('accounts.reviewRequired') : t('accounts.ready')}
                </Badge>
              </span>
              <ChevronRight aria-hidden="true" className="row-chevron" />
            </button>
          ))}
        </div>
      </Card>
    </section>
  );
}

function StatusCard({ children, title }: { children: ReactNode; title: string }) {
  const { t } = useTranslation();

  return (
    <section className="screen status-screen">
      <Card>
        <Eyebrow>{t('accounts.status.eyebrow')}</Eyebrow>
        <h1>{title}</h1>
        {children}
      </Card>
    </section>
  );
}

function StageBadge({ label, stage }: { label: string; stage: string }) {
  if (stage === 'Access') {
    return <Badge tone="ally">{label}</Badge>;
  }
  if (stage === 'Mapping') {
    return <Badge tone="cobalt">{label}</Badge>;
  }
  return <Badge tone="neutral">{label}</Badge>;
}

function initials(value: string) {
  return value
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}
