import { Ban, CheckCircle2, FileText, Lock, Route, ShieldCheck, SlidersHorizontal } from 'lucide-react';
import type { ReactNode } from 'react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, Card, Eyebrow, Mono } from '../components/primitives';
import { useDemoLocalization } from '../demoLocalization';
import type { AccessPlanArtifact, PlaybookVariantAnalysis, RoutePolicyDecision } from '../types';

export function PlaybookScreen({
  artifact,
  error,
}: {
  artifact: AccessPlanArtifact | null;
  error: string | null;
}) {
  const { t } = useTranslation();
  const [selectedVariantId, setSelectedVariantId] = useState('current');

  if (error || !artifact?.playbook_analysis) {
    return (
      <section className="screen status-screen">
        <Card>
          <Eyebrow>{t('playbook.statusEyebrow')}</Eyebrow>
          <h1>{t('playbook.notReadyTitle')}</h1>
          <p>{t('playbook.notReadyCopy')}</p>
          <code>python demo/run_demo.py generate-account-radar</code>
        </Card>
      </section>
    );
  }

  const variants = [artifact.playbook_analysis.current, ...artifact.playbook_analysis.variants];
  const selectedVariant = variants.find((variant) => variant.variant_id === selectedVariantId) ?? variants[0];

  return (
    <section className="screen playbook-screen" aria-label={t('playbook.aria')}>
      <div className="playbook-header">
        <div className="objective-icon">
          <SlidersHorizontal aria-hidden="true" />
        </div>
        <div>
          <Eyebrow>{t('playbook.eyebrow')}</Eyebrow>
          <h1>{t('playbook.title')}</h1>
          <p>{t('playbook.summary', { accountName: artifact.account.name })}</p>
        </div>
        <Badge tone="neutral">{artifact.playbook_analysis.contract_version}</Badge>
      </div>

      <div className="variant-switch" aria-label={t('playbook.variantSwitch')}>
        {variants.map((variant) => (
          <button
            className={`variant-option${variant.variant_id === selectedVariant.variant_id ? ' variant-option-active' : ''}`}
            key={variant.variant_id}
            type="button"
            onClick={() => setSelectedVariantId(variant.variant_id)}
          >
            {t(`playbook.variants.${variant.variant_id}.label`)}
          </button>
        ))}
      </div>

      <div className="playbook-layout">
        <div className="playbook-main">
          <PolicySummary variant={selectedVariant} />
          <RouteDecisions decisions={selectedVariant.route_decisions} />
        </div>
        <aside className="playbook-inspector">
          <RoutePreview variant={selectedVariant} />
        </aside>
      </div>
    </section>
  );
}

function PolicySummary({ variant }: { variant: PlaybookVariantAnalysis }) {
  const { t } = useTranslation();
  const demo = useDemoLocalization();

  return (
    <Card>
      <div className="playbook-section-heading">
        <div className="section-icon">
          <ShieldCheck aria-hidden="true" />
        </div>
        <div>
          <Eyebrow>{t('playbook.policyEyebrow')}</Eyebrow>
          <h2>{t(`playbook.variants.${variant.variant_id}.title`)}</h2>
          <p>{t(`playbook.variants.${variant.variant_id}.description`)}</p>
        </div>
      </div>

      <div className="playbook-policy-grid">
        <PolicyList
          icon={<CheckCircle2 aria-hidden="true" />}
          title={t('playbook.allowedRoutes')}
          items={variant.playbook.allowed_routes.map((route) => demo.routeType(route))}
          tone="ally"
        />
        <PolicyList
          icon={<Lock aria-hidden="true" />}
          title={t('playbook.blockedChannels')}
          items={variant.blocked_channels.map((channel) => demo.playbookToken(channel))}
          tone="blocker"
        />
        <PolicyList
          icon={<FileText aria-hidden="true" />}
          title={t('playbook.assets')}
          items={variant.assets.map((asset) => demo.playbookToken(asset))}
          tone="neutral"
        />
        <PolicyList
          icon={<ShieldCheck aria-hidden="true" />}
          title={t('playbook.reviewRules')}
          items={variant.review_policy.required_review_for.map((rule) => demo.playbookToken(rule))}
          tone="unsurfaced"
        />
      </div>
    </Card>
  );
}

function PolicyList({
  icon,
  items,
  title,
  tone,
}: {
  icon: ReactNode;
  items: string[];
  title: string;
  tone: 'ally' | 'blocker' | 'neutral' | 'unsurfaced';
}) {
  const { t } = useTranslation();

  return (
    <div className="policy-list">
      <div className="policy-list-title">
        {icon}
        <span>{title}</span>
      </div>
      <div className="badge-list">
        {items.length > 0 ? (
          items.map((item) => (
            <Badge key={item} tone={tone}>
              {item}
            </Badge>
          ))
        ) : (
          <span className="muted">{t('playbook.none')}</span>
        )}
      </div>
    </div>
  );
}

function RouteDecisions({ decisions }: { decisions: RoutePolicyDecision[] }) {
  const { t } = useTranslation();
  const demo = useDemoLocalization();

  return (
    <Card>
      <div className="playbook-section-heading">
        <div className="section-icon">
          <Route aria-hidden="true" />
        </div>
        <div>
          <Eyebrow>{t('playbook.decisionsEyebrow')}</Eyebrow>
          <h2>{t('playbook.decisionsTitle')}</h2>
          <p>{t('playbook.decisionsCopy')}</p>
        </div>
      </div>

      <div className="decision-list">
        {decisions.map((decision) => (
          <div className="decision-row" key={decision.route_type}>
            <DecisionIcon status={decision.status} />
            <div>
              <strong>{demo.routeType(decision.route_type)}</strong>
              <p>{demo.text(decision.reason)}</p>
            </div>
            <Badge tone={decisionTone(decision.status)}>{t(`playbook.decisionStatus.${decision.status}`)}</Badge>
            <Mono>{decision.route_score ?? t('playbook.notRanked')}</Mono>
          </div>
        ))}
      </div>
    </Card>
  );
}

function RoutePreview({ variant }: { variant: PlaybookVariantAnalysis }) {
  const { t } = useTranslation();
  const demo = useDemoLocalization();

  return (
    <Card>
      <div className="playbook-inspector-content">
        <Eyebrow>{t('playbook.previewEyebrow')}</Eyebrow>
        <h2>{t('playbook.previewTitle')}</h2>
        <p className="muted">{t('playbook.previewCopy')}</p>

        <div className="preview-route-list">
          {variant.route_preview.routes.length > 0 ? (
            variant.route_preview.routes.map((route, index) => (
              <div className="preview-route" key={route.route_type}>
                <div className="preview-route-rank">
                  <Mono>{index + 1}</Mono>
                </div>
                <div>
                  <strong>{demo.routeTitle(route.route_type, route.title)}</strong>
                  <p>{demo.text(route.reason)}</p>
                  <div className="metadata-row">
                    <Badge tone="neutral">{demo.owner(route.owner)}</Badge>
                    <Badge tone={route.requires_human_review ? 'unsurfaced' : 'ally'}>
                      {route.requires_human_review ? t('accounts.reviewRequired') : t('accounts.ready')}
                    </Badge>
                  </div>
                </div>
                <Mono>{route.score}</Mono>
              </div>
            ))
          ) : (
            <p className="muted">{t('playbook.noRoutes')}</p>
          )}
        </div>
      </div>
    </Card>
  );
}

function DecisionIcon({ status }: { status: RoutePolicyDecision['status'] }) {
  if (status === 'blocked') {
    return (
      <span className="decision-icon decision-icon-blocked">
        <Ban aria-hidden="true" />
      </span>
    );
  }
  return (
    <span className={`decision-icon${status === 'recommended' ? ' decision-icon-recommended' : ''}`}>
      <CheckCircle2 aria-hidden="true" />
    </span>
  );
}

function decisionTone(status: RoutePolicyDecision['status']): 'ally' | 'blocker' | 'neutral' {
  if (status === 'recommended') {
    return 'ally';
  }
  if (status === 'blocked') {
    return 'blocker';
  }
  return 'neutral';
}
