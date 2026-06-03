import { Activity, AlertTriangle, Compass, GitBranch, Route, ShieldCheck, Users } from 'lucide-react';
import { useEffect, useState } from 'react';
import type { AccessPlanArtifact, Role as PowerRole, Route as AccessRoute, Signal } from './types';

const artifactUrl = '/demo/access_plan.json';

export function App() {
  const [artifact, setArtifact] = useState<AccessPlanArtifact | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(artifactUrl)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Artifact request failed with ${response.status}`);
        }
        return response.json() as Promise<AccessPlanArtifact>;
      })
      .then(setArtifact)
      .catch((requestError: Error) => setError(requestError.message));
  }, []);

  if (error) {
    return (
      <main className="page-shell">
        <section className="status-card">
          <p className="eyebrow">DEMO STATUS</p>
          <h1>Artifact is not ready</h1>
          <p>Run the access plan generator, then restart the local demo server.</p>
          <code>python -m power_web_os.demo generate-access-plan</code>
        </section>
      </main>
    );
  }

  if (!artifact) {
    return (
      <main className="page-shell">
        <section className="status-card">
          <p className="eyebrow">DEMO STATUS</p>
          <h1>Loading Access Plan</h1>
          <p>Reading the generated artifact from the local Vite server.</p>
        </section>
      </main>
    );
  }

  const primaryRoute = artifact.access_plan.routes[0];

  return (
    <main className="page-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">FIRST CLOSED LOOP</p>
          <h1>{artifact.account.name}</h1>
          <p className="lede">
            Synthetic account data was processed by {artifact.workflow_metadata.workflow_name} and rendered as an
            explainable Access Plan.
          </p>
        </div>
        <div className="hero-metrics" aria-label="Account context">
          <Metric label="ICP fit" value={score(artifact.account.icp_fit)} detail="Account profile match" />
          <Metric label="Runtime" value={artifact.workflow_metadata.runtime_mode} detail={artifact.workflow_metadata.runtime} />
          <Metric label="Routes" value={String(artifact.access_plan.routes.length)} detail="Ranked next moves" />
        </div>
      </section>

      <section className="layout-grid">
        <div className="stack">
          <Panel title="Signal evidence" icon={<Activity aria-hidden="true" />}>
            <div className="card-list">
              {artifact.account.signals.map((signal) => (
                <SignalCard key={signal.kind} signal={signal} />
              ))}
            </div>
          </Panel>

          <Panel title="Power Web Lite" icon={<Users aria-hidden="true" />}>
            <div className="role-grid">
              {artifact.account.roles.map((role) => (
                <RoleCard key={`${role.role}-${role.person_name ?? 'unknown'}`} role={role} />
              ))}
            </div>
          </Panel>

          <Panel title="Unresolved gaps" icon={<AlertTriangle aria-hidden="true" />}>
            <div className="gap-list">
              {artifact.access_plan.unresolved_gaps.map((gap) => (
                <span className="badge badge-unsurfaced" key={gap}>
                  {humanize(gap)}
                </span>
              ))}
            </div>
            <p className="muted">These roles must be surfaced before the account is treated as fully mapped.</p>
          </Panel>
        </div>

        <div className="stack">
          <Panel title="Access Plan" icon={<Compass aria-hidden="true" />}>
            <div className="route-list">
              {artifact.access_plan.routes.map((route, index) => (
                <RouteCard key={route.route_type} route={route} active={route.route_type === primaryRoute.route_type} index={index} />
              ))}
            </div>
          </Panel>

          <Panel title="Human review" icon={<ShieldCheck aria-hidden="true" />}>
            <div className="review-card">
              <div>
                <p className="eyebrow">REVIEW POLICY</p>
                <h2>Human approval required</h2>
              </div>
              <p>
                Playbook rule <span className="mono">required_review_for: all</span> marks every route as pending review before
                it becomes a task.
              </p>
              <div className="metadata-row">
                <span className="badge badge-cobalt">{artifact.playbook.name}</span>
                <span className="badge badge-neutral">{artifact.workflow_metadata.planner}</span>
              </div>
            </div>
          </Panel>
        </div>
      </section>
    </main>
  );
}

function Panel({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="panel">
      <header className="panel-header">
        <span className="icon-tile">{icon}</span>
        <h2>{title}</h2>
      </header>
      {children}
    </section>
  );
}

function Metric({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="metric-card">
      <p className="eyebrow">{label}</p>
      <p className="metric-value">{value}</p>
      <p className="muted">{detail}</p>
    </div>
  );
}

function SignalCard({ signal }: { signal: Signal }) {
  return (
    <article className="inner-card">
      <div className="split-row">
        <div>
          <p className="eyebrow">{signal.kind}</p>
          <h3>{signal.summary}</h3>
        </div>
        <span className="score">{score(signal.strength)}</span>
      </div>
      {signal.evidence.map((item) => (
        <p className="evidence-line" key={item.source}>
          <span className="mono">{item.source}</span> · {item.summary}
        </p>
      ))}
    </article>
  );
}

function RoleCard({ role }: { role: PowerRole }) {
  const stance = role.relation === 'partner' ? 'cobalt' : 'ally';
  return (
    <article className="inner-card role-card">
      <div className="avatar" aria-hidden="true">
        {initials(role.person_name ?? role.role)}
      </div>
      <div>
        <h3>{role.person_name ?? role.role}</h3>
        <p className="muted">{role.role}</p>
        <div className="metadata-row">
          <span className={`badge badge-${stance}`}>{role.relation ?? role.state}</span>
          <span className="mono">{score(role.influence)} influence</span>
        </div>
      </div>
    </article>
  );
}

function RouteCard({ route, active, index }: { route: AccessRoute; active: boolean; index: number }) {
  return (
    <article className={`route-card${active ? ' route-card-active' : ''}`}>
      <div className="route-rank">
        <Route aria-hidden="true" />
        <span>{index + 1}</span>
      </div>
      <div className="route-body">
        <div className="split-row">
          <div>
            <p className="eyebrow">WHY THIS ROUTE</p>
            <h3>{route.title}</h3>
          </div>
          <span className="score">{route.score}</span>
        </div>
        <p>{route.reason}</p>
        <div className="route-detail">
          <GitBranch aria-hidden="true" />
          <span>{route.expected_state_change}</span>
        </div>
        <p className="risk">{route.risk}</p>
        <div className="metadata-row">
          <span className="badge badge-neutral">{route.owner}</span>
          <span className="badge badge-cobalt">{route.requires_human_review ? 'Review required' : 'Ready'}</span>
        </div>
      </div>
    </article>
  );
}

function score(value: number) {
  return String(Math.round(value * 100));
}

function humanize(value: string) {
  return value.replaceAll('_', ' ');
}

function initials(value: string) {
  return value
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}
