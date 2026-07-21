import { AlertTriangle, CheckCircle2, ChevronDown, GitBranch, Lightbulb, Route, ShieldCheck, Target } from 'lucide-react';
import type { ReactNode } from 'react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, Card, Eyebrow, Mono } from '../components/primitives';
import { WorkspaceTabs } from '../components/WorkspaceTabs';
import { useDemoLocalization } from '../demoLocalization';
import type { AccessPlanArtifact, Evidence, Route as AccessRoute, Signal } from '../types';
import { AccountPlaybookAnalysis } from './PlaybookScreen';

export function AccessPlansScreen({
  artifact,
  error,
}: {
  artifact: AccessPlanArtifact | null;
  error: string | null;
}) {
  const { t } = useTranslation();
  const [openRouteType, setOpenRouteType] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<'routes' | 'analysis'>('routes');

  if (error) {
    return (
      <StatusPanel title={t('plans.artifactNotReadyTitle')} eyebrow={t('plans.statusEyebrow')}>
        <p>{t('plans.artifactNotReadyCopy')}</p>
        <code>python -m power_web_os.demo generate-access-plan</code>
      </StatusPanel>
    );
  }

  if (!artifact) {
    return (
      <StatusPanel title={t('plans.loadingTitle')} eyebrow={t('plans.statusEyebrow')}>
        <p>{t('plans.loadingCopy')}</p>
      </StatusPanel>
    );
  }

  const routes = artifact.access_plan.routes;
  const activeRouteType = openRouteType ?? routes[0]?.route_type;

  return (
    <section className="screen access-plans-screen" aria-label={t('plans.aria')}>
      <div className="objective-banner">
        <div className="objective-icon">
          <Target aria-hidden="true" />
        </div>
        <div className="objective-copy">
          <Eyebrow>{t('plans.objectiveEyebrow')}</Eyebrow>
          <h1>{t('plans.objectiveTitle')}</h1>
          <p>{t('plans.objectiveCopy', {
            accountName: artifact.account.name,
            gapCount: artifact.access_plan.unresolved_gaps.length,
            routeCount: routes.length,
            workflowName: artifact.workflow_metadata.workflow_name,
          })}</p>
        </div>
        <Badge tone="cobalt">{artifact.workflow_metadata.runtime}</Badge>
      </div>

      <WorkspaceTabs
        id="access-plans"
        activeId={activeView}
        ariaLabel={t('plans.viewsAria')}
        items={[
          { id: 'routes', label: t('plans.routesView') },
          { id: 'analysis', label: t('plans.ruleAnalysisView'), testId: 'access-plan-rule-analysis-tab' },
        ]}
        onChange={setActiveView}
      />

      {activeView === 'routes' ? <div className="plans-layout">
        <div className="plans-main">
          <div className="route-list">
            {routes.map((route, index) => (
              <PlanCard
                key={route.route_type}
                artifact={artifact}
                index={index}
                open={route.route_type === activeRouteType}
                route={route}
                onToggle={() => setOpenRouteType(route.route_type === activeRouteType ? null : route.route_type)}
              />
            ))}
          </div>
        </div>

        <aside className="plans-inspector">
          <BoardSummary artifact={artifact} />
          <EvidenceSummary signals={artifact.account.signals} />
        </aside>
      </div> : <AccountPlaybookAnalysis artifact={artifact} error={error} embedded />}
    </section>
  );
}

function PlanCard({
  artifact,
  index,
  open,
  route,
  onToggle,
}: {
  artifact: AccessPlanArtifact;
  index: number;
  open: boolean;
  route: AccessRoute;
  onToggle: () => void;
}) {
  const { t } = useTranslation();
  const demo = useDemoLocalization();
  const evidence = evidenceForRoute(artifact.account.signals, route.evidence_refs);
  const routeTitle = demo.routeTitle(route.route_type, route.title);
  const reviewRules = artifact.playbook_analysis.current.review_policy.required_review_for;

  return (
    <Card interactive selected={index === 0} onClick={onToggle}>
      <div className="plan-card-header">
        <div className="rank-block">
          <span className="rank-label">{t('plans.rank')}</span>
          <span className="rank-value">{index + 1}</span>
        </div>
        <div className="plan-heading">
          <div className="plan-title-row">
            <h2>{routeTitle}</h2>
            {index === 0 && <Badge tone="cobalt">{t('plans.recommended')}</Badge>}
          </div>
          <p>{t('plans.target', { target: demo.routeType(route.route_type) })}</p>
        </div>
        <div className="score-block">
          <span className="rank-label">{t('plans.score')}</span>
          <span className="score-row">
            <span className="score-track">
              <span className="score-fill" style={{ width: `${route.score}%` }} />
            </span>
            <Mono>{route.score}</Mono>
          </span>
        </div>
        <ChevronDown aria-hidden="true" className={`chevron${open ? ' chevron-open' : ''}`} />
      </div>

      {open && (
        <div className="plan-card-detail">
          <div className="route-explanation">
            <Eyebrow>{t('plans.routeEyebrow')}</Eyebrow>
            <div className="route-path">
              <span>{demo.owner(route.owner)}</span>
              <Route aria-hidden="true" />
              <span>{routeTitle}</span>
            </div>

            <div className="why-box">
              <Lightbulb aria-hidden="true" />
              <div>
                <span className="why-title">{t('plans.whyThisRoute')}</span>
                <p>{demo.text(route.reason)}</p>
              </div>
            </div>

            <Eyebrow>{t('plans.expectedStateChange')}</Eyebrow>
            <div className="state-change">
              <GitBranch aria-hidden="true" />
              <span>{demo.text(route.expected_state_change ?? '')}</span>
            </div>

            <p className="risk-line">
              <AlertTriangle aria-hidden="true" />
              <span>{demo.text(route.risk)}</span>
            </p>
          </div>

          <div className="route-meta">
            <div className="hook-card">
              <Eyebrow>{t('plans.reviewStatus')}</Eyebrow>
              <h3>{route.requires_human_review ? t('plans.humanApprovalRequired') : t('plans.readyForTasking')}</h3>
              <p>
                {t('plans.reviewRule')}{' '}
                <Mono>{`required_review_for: ${reviewRules.map((rule) => demo.playbookToken(rule)).join(', ')}`}</Mono>{' '}
                {t('plans.reviewRuleCopy')}
              </p>
            </div>

            <div>
              <Eyebrow>{t('plans.evidence')}</Eyebrow>
              <div className="evidence-list">
                {evidence.map((item) => (
                  <span className="evidence-item" key={item.source}>
                    <CheckCircle2 aria-hidden="true" />
                    <span>{demo.text(item.summary)}</span>
                    <Mono>{item.source}</Mono>
                  </span>
                ))}
              </div>
            </div>

            <div className="metadata-row">
              <Badge tone="neutral">{demo.owner(route.owner)}</Badge>
              <Badge tone={route.requires_human_review ? 'unsurfaced' : 'ally'}>
                {route.requires_human_review ? t('accounts.reviewRequired') : t('accounts.ready')}
              </Badge>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}

function BoardSummary({ artifact }: { artifact: AccessPlanArtifact }) {
  const { t } = useTranslation();
  const demo = useDemoLocalization();

  return (
    <Card>
      <div className="inspector-section">
        <Eyebrow>{t('plans.boardCoverage')}</Eyebrow>
        <div className="coverage-number">
          <span>{artifact.account.roles.length}</span>
          <span>/{artifact.account.roles.length + artifact.access_plan.unresolved_gaps.length}</span>
        </div>
        <p className="muted">{t('plans.boardCoverageCopy')}</p>
        <div className="badge-list">
          {artifact.account.roles.map((role) => (
            <Badge key={role.role} tone={role.relation === 'partner' ? 'cobalt' : 'ally'}>
              {role.person_name ?? demo.role(role.role)}
            </Badge>
          ))}
          {artifact.access_plan.unresolved_gaps.map((gap) => (
            <Badge key={gap} tone="unsurfaced">
              {demo.role(gap)}
            </Badge>
          ))}
        </div>
      </div>
    </Card>
  );
}

function EvidenceSummary({ signals }: { signals: Signal[] }) {
  const { t } = useTranslation();
  const demo = useDemoLocalization();

  return (
    <Card>
      <div className="inspector-section">
        <Eyebrow>{t('plans.signalEvidence')}</Eyebrow>
        <div className="signal-stack">
          {signals.map((signal) => (
            <div className="signal-row" key={signal.kind}>
              <ShieldCheck aria-hidden="true" />
              <div>
                <h3>{demo.signalKind(signal.kind)}</h3>
                <p>{demo.text(signal.summary)}</p>
                <Mono>{t('plans.strength', { score: score(signal.strength) })}</Mono>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}

function StatusPanel({
  children,
  eyebrow,
  title,
}: {
  children: ReactNode;
  eyebrow: string;
  title: string;
}) {
  return (
    <section className="screen status-screen">
      <Card>
        <Eyebrow>{eyebrow}</Eyebrow>
        <h1>{title}</h1>
        {children}
      </Card>
    </section>
  );
}

function evidenceForRoute(signals: Signal[], refs: string[]): Evidence[] {
  const evidence = signals.flatMap((signal) => signal.evidence);
  return evidence.filter((item) => refs.includes(item.source));
}

function score(value: number) {
  return String(Math.round(value * 100));
}
