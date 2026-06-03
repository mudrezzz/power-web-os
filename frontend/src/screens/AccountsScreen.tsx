import { CheckCircle2, ChevronRight, EyeOff, Route, ShieldCheck } from 'lucide-react';
import type { ReactNode } from 'react';
import { Badge, Card, Eyebrow, HealthBar, Mono } from '../components/primitives';
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
  if (error) {
    return (
      <StatusCard title="Account Radar is not ready">
        <p>Run the portfolio generator, then restart or refresh the local demo server.</p>
        <code>python -m power_web_os.demo generate-account-radar</code>
      </StatusCard>
    );
  }

  if (!artifact) {
    return (
      <StatusCard title="Loading Account Radar">
        <p>Reading the generated portfolio artifact from the local Vite server.</p>
      </StatusCard>
    );
  }

  const topAccount = artifact.accounts[0];

  return (
    <section className="screen accounts-screen" aria-label="Accounts portfolio">
      <div className="accounts-header">
        <div>
          <Eyebrow>Account Radar</Eyebrow>
          <h1>Accounts</h1>
          <p>
            {artifact.accounts.length} target accounts ranked by ICP fit, signal strength, access route, and missing-role risk.
          </p>
        </div>
        {topAccount && (
          <div className="radar-highlight">
            <span>Top account</span>
            <strong>{topAccount.account_name}</strong>
            <Mono>{topAccount.radar_score} radar score</Mono>
          </div>
        )}
      </div>

      <div className="filter-row" aria-label="Portfolio filters">
        <Badge tone="cobalt">All accounts</Badge>
        <Badge tone="neutral">My book</Badge>
        <Badge tone="neutral">Needs route</Badge>
        <Badge tone="neutral">Review required</Badge>
      </div>

      <Card>
        <div className="accounts-table">
          <div className="accounts-table-head">
            <span>Account</span>
            <span>Stage</span>
            <span>Radar score</span>
            <span>Signals</span>
            <span>Missing</span>
            <span>Best route</span>
            <span>Owner</span>
            <span>Review</span>
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
                  <small>{item.top_reason}</small>
                </span>
              </span>
              <span>
                <StageBadge stage={item.stage} />
              </span>
              <span>
                <HealthBar value={item.radar_score} label={`${item.account_name} radar score`} />
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
                <span>{item.best_route_title ?? 'No route yet'}</span>
                <Mono>{item.best_route_score}</Mono>
              </span>
              <span>{item.owner ?? 'Unassigned'}</span>
              <span>
                <Badge tone={item.review_required ? 'unsurfaced' : 'ally'}>
                  {item.review_required ? 'Review required' : 'Ready'}
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
  return (
    <section className="screen status-screen">
      <Card>
        <Eyebrow>RADAR STATUS</Eyebrow>
        <h1>{title}</h1>
        {children}
      </Card>
    </section>
  );
}

function StageBadge({ stage }: { stage: string }) {
  if (stage === 'Access') {
    return <Badge tone="ally">{stage}</Badge>;
  }
  if (stage === 'Mapping') {
    return <Badge tone="cobalt">{stage}</Badge>;
  }
  return <Badge tone="neutral">{stage}</Badge>;
}

function initials(value: string) {
  return value
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}
