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
import logoUrl from '../../../ui-design-system/assets/logo.svg';
import { Avatar, Badge, Button, HealthBar, IconButton, Mono } from '../components/primitives';
import type { AccessPlanArtifact } from '../types';

export type ScreenId = 'accounts' | 'map' | 'plans' | 'signals' | 'playbook' | 'tasks' | 'inbox';

const workspaceNav = [
  { id: 'accounts', label: 'Accounts', icon: LayoutGrid },
  { id: 'map', label: 'Account Map', icon: Share2 },
  { id: 'plans', label: 'Access Plans', icon: Route },
  { id: 'signals', label: 'Signals', icon: Activity },
  { id: 'playbook', label: 'Playbook', icon: Settings2 },
] satisfies Array<{ id: ScreenId; label: string; icon: typeof LayoutGrid }>;

const queueNav = [
  { id: 'tasks', label: 'My Tasks', icon: CheckCircle2 },
  { id: 'inbox', label: 'Signals Inbox', icon: Bell },
] satisfies Array<{ id: ScreenId; label: string; icon: typeof LayoutGrid }>;

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
  return (
    <aside className="sidebar">
      <div className="brand">
        <img src={logoUrl} alt="" className="brand-mark" />
        <div>
          <span className="brand-name">Power Web OS</span>
          <span className="brand-meta">Access workspace</span>
        </div>
      </div>

      <nav className="nav-stack" aria-label="Workspace">
        <span className="nav-group">Workspace</span>
        {workspaceNav.map((item) => (
          <NavItem
            key={item.id}
            {...item}
            active={activeScreen === item.id}
            onClick={() => onNavigate(item.id)}
          />
        ))}

        <span className="nav-group nav-group-spaced">Queue</span>
        {queueNav.map((item) => (
          <NavItem
            key={item.id}
            {...item}
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
  const routeCount = artifact?.access_plan.routes.length ?? 0;
  const health = artifact ? Math.round(artifact.account.icp_fit * 100) : 0;

  return (
    <header className="topbar">
      <div className="account-context">
        <div className="account-mark">{artifact ? initials(artifact.account.name) : 'PW'}</div>
        <div className="account-copy">
          <span className="account-title">{topBarTitle(activeScreen, artifact)}</span>
          <span className="account-meta">
            {artifact ? (
              <>
                <span>{artifact.playbook.name}</span>
                <span> / </span>
                <span>{routeCount} ranked routes</span>
              </>
            ) : (
              'Generated Access Plan artifact'
            )}
          </span>
        </div>
        <Badge tone="cobalt">Access loop</Badge>
        <HealthBar value={health} label="ICP fit health" />
        {artifact && <Mono>{artifact.workflow_metadata.runtime_mode}</Mono>}
      </div>

      <div className="topbar-actions">
        <label className="search-field">
          <Search aria-hidden="true" />
          <input aria-label="Search accounts and people" placeholder="Search accounts, people" />
        </label>
        <IconButton aria-label="Filters">
          <Filter aria-hidden="true" />
        </IconButton>
        <IconButton aria-label="Notifications">
          <Bell aria-hidden="true" />
        </IconButton>
        <Button variant="primary" icon={<Plus aria-hidden="true" />}>
          Add account
        </Button>
      </div>
    </header>
  );
}

function topBarTitle(activeScreen: ScreenId, artifact: AccessPlanArtifact | null) {
  if (artifact && activeScreen === 'plans') {
    return `Access Plans / ${artifact.account.name}`;
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
