import {
  Activity,
  Bell,
  CheckCircle2,
  ChevronDown,
  Filter,
  LayoutGrid,
  Plus,
  Route,
  Search,
  Settings2,
  Share2,
} from 'lucide-react';
import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import type { TFunction } from 'i18next';
import logoUrl from '../../../ui-design-system/assets/logo.svg';
import { Avatar, Badge, Button, HealthBar, IconButton, Mono } from '../components/primitives';
import { localeStorageKey, supportedLocales, type SupportedLocale } from '../i18n';
import type { AccessPlanArtifact } from '../types';

export type ScreenId = 'accounts' | 'map' | 'plans' | 'signals' | 'playbook' | 'tasks' | 'inbox';

const workspaceNav = [
  { id: 'accounts', labelKey: 'nav.accounts', icon: LayoutGrid },
  { id: 'map', labelKey: 'nav.map', icon: Share2 },
  { id: 'plans', labelKey: 'nav.plans', icon: Route },
  { id: 'signals', labelKey: 'nav.signals', icon: Activity },
  { id: 'playbook', labelKey: 'nav.playbook', icon: Settings2 },
] satisfies Array<{ id: ScreenId; labelKey: string; icon: typeof LayoutGrid }>;

const queueNav = [
  { id: 'tasks', labelKey: 'nav.tasks', icon: CheckCircle2 },
  { id: 'inbox', labelKey: 'nav.inbox', icon: Bell },
] satisfies Array<{ id: ScreenId; labelKey: string; icon: typeof LayoutGrid }>;

export function AppShell({
  activeScreen,
  artifact,
  children,
  onNavigate,
}: {
  activeScreen: ScreenId;
  artifact: AccessPlanArtifact | null;
  children: ReactNode;
  onNavigate: (screen: ScreenId) => void;
}) {
  return (
    <main className="app-shell">
      <Sidebar activeScreen={activeScreen} onNavigate={onNavigate} />
      <section className="workspace">
        <TopBar activeScreen={activeScreen} artifact={artifact} />
        <div className="workspace-body">{children}</div>
      </section>
    </main>
  );
}

function Sidebar({
  activeScreen,
  onNavigate,
}: {
  activeScreen: ScreenId;
  onNavigate: (screen: ScreenId) => void;
}) {
  const { t } = useTranslation();

  return (
    <aside className="sidebar">
      <div className="brand">
        <img src={logoUrl} alt="" className="brand-mark" />
        <div>
          <span className="brand-name">Power Web OS</span>
          <span className="brand-meta">{t('app.brandMeta')}</span>
        </div>
      </div>

      <nav className="nav-stack" aria-label={t('nav.workspace')}>
        <span className="nav-group">{t('nav.workspace')}</span>
        {workspaceNav.map((item) => (
          <NavItem
            key={item.id}
            icon={item.icon}
            label={t(item.labelKey)}
            active={activeScreen === item.id}
            onClick={() => onNavigate(item.id)}
          />
        ))}

        <span className="nav-group nav-group-spaced">{t('nav.queue')}</span>
        {queueNav.map((item) => (
          <NavItem
            key={item.id}
            icon={item.icon}
            label={t(item.labelKey)}
            active={activeScreen === item.id}
            onClick={() => onNavigate(item.id)}
          />
        ))}
      </nav>

      <div className="profile-card">
        <Avatar label="Alex Rivera" />
        <div className="profile-copy">
          <span className="profile-name">Alex Rivera</span>
          <span className="profile-role">Enterprise AE</span>
        </div>
        <ChevronDown aria-hidden="true" />
      </div>
    </aside>
  );
}

function NavItem({
  active,
  badge,
  icon: Icon,
  label,
  onClick,
}: {
  active: boolean;
  badge?: string;
  icon: typeof LayoutGrid;
  label: string;
  onClick: () => void;
}) {
  return (
    <button className={`nav-item${active ? ' nav-item-active' : ''}`} type="button" onClick={onClick}>
      <Icon aria-hidden="true" />
      <span>{label}</span>
      {badge && <span className="nav-badge">{badge}</span>}
    </button>
  );
}

function TopBar({
  activeScreen,
  artifact,
}: {
  activeScreen: ScreenId;
  artifact: AccessPlanArtifact | null;
}) {
  const { i18n, t } = useTranslation();
  const routeCount = artifact?.access_plan.routes.length ?? 0;
  const health = artifact ? Math.round(artifact.account.icp_fit * 100) : 0;
  const activeLocale = supportedLocales.includes(i18n.language as SupportedLocale)
    ? (i18n.language as SupportedLocale)
    : 'en';

  function changeLocale(locale: SupportedLocale) {
    window.localStorage.setItem(localeStorageKey, locale);
    void i18n.changeLanguage(locale);
  }

  return (
    <header className="topbar">
      <div className="account-context">
        <div className="account-mark">{artifact ? initials(artifact.account.name) : 'PW'}</div>
        <div className="account-copy">
          <span className="account-title">{topBarTitle(activeScreen, artifact, t)}</span>
          <span className="account-meta">
            {artifact ? (
              <>
                <span>{artifact.playbook.name}</span>
                <span> / </span>
                <span>{t('topbar.routeCount', { count: routeCount })}</span>
              </>
            ) : (
              t('topbar.fallbackMeta')
            )}
          </span>
        </div>
        <Badge tone="cobalt">{t('app.workflowBadge')}</Badge>
        <HealthBar value={health} label={t('topbar.icpFitHealth')} />
        {artifact && <Mono>{artifact.workflow_metadata.runtime_mode}</Mono>}
      </div>

      <div className="topbar-actions">
        <label className="search-field">
          <Search aria-hidden="true" />
          <input aria-label={t('topbar.searchLabel')} placeholder={t('topbar.searchPlaceholder')} />
        </label>
        <IconButton aria-label={t('topbar.filters')}>
          <Filter aria-hidden="true" />
        </IconButton>
        <IconButton aria-label={t('topbar.notifications')}>
          <Bell aria-hidden="true" />
        </IconButton>
        <LanguageSwitch activeLocale={activeLocale} onChange={changeLocale} label={t('topbar.language')} />
        <Button variant="primary" icon={<Plus aria-hidden="true" />}>
          {t('topbar.addAccount')}
        </Button>
      </div>
    </header>
  );
}

function LanguageSwitch({
  activeLocale,
  label,
  onChange,
}: {
  activeLocale: SupportedLocale;
  label: string;
  onChange: (locale: SupportedLocale) => void;
}) {
  return (
    <div className="language-switch" aria-label={label} role="group">
      {supportedLocales.map((locale) => (
        <button
          aria-pressed={activeLocale === locale}
          className={`language-option${activeLocale === locale ? ' language-option-active' : ''}`}
          key={locale}
          type="button"
          onClick={() => onChange(locale)}
        >
          {locale.toUpperCase()}
        </button>
      ))}
    </div>
  );
}

function topBarTitle(activeScreen: ScreenId, artifact: AccessPlanArtifact | null, t: TFunction) {
  if (artifact && activeScreen === 'plans') {
    return t('topbar.accessPlansFor', { accountName: artifact.account.name });
  }

  if (artifact) {
    return artifact.account.name;
  }

  return 'Power Web OS';
}

function initials(value: string) {
  return value
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}
