import { Check, LoaderCircle, Search } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Card, Eyebrow, Mono } from '../../../components/primitives';
import type { LiveRadarCandidate } from '../../../types';
import {
  powerWebCandidateKey,
  type PowerWebHandoffBackendController,
} from '../application/usePowerWebHandoffBackend';

export function PowerWebHandoffPanel({
  backend,
  candidate,
  radarId,
  runId,
}: {
  backend: PowerWebHandoffBackendController;
  candidate: LiveRadarCandidate;
  radarId: string;
  runId: string;
}) {
  const { t } = useTranslation();
  const policy = backend.powerWebPolicyByRadarId[radarId] ?? null;
  const defaultProducts = useMemo(() => policy?.product_bindings.map((item) => item.product_id) ?? [], [policy]);
  const [selected, setSelected] = useState<string[]>(defaultProducts);
  const reviewNeeded = candidate.candidate_surface_status !== 'accepted_product_candidate';
  const [acknowledged, setAcknowledged] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const key = powerWebCandidateKey(radarId, runId, candidate.candidate_id);
  const preflight = backend.powerWebPreflightByKey[key];
  const requestedHandoffId = new URLSearchParams(window.location.search).get('handoffId');
  const handoffs = backend.powerWebHandoffsByKey[key] ?? [];
  const handoff = handoffs.find((item) => item.handoff_id === requestedHandoffId) ?? handoffs[0] ?? null;

  useEffect(() => { void backend.loadPowerWebPolicy(radarId); }, [backend.loadPowerWebPolicy, radarId]);
  useEffect(() => { setSelected(defaultProducts); }, [defaultProducts]);
  useEffect(() => {
    if (selected.length) {
      void backend.loadPowerWebCandidateBrief(radarId, runId, candidate.candidate_id, selected, acknowledged);
    }
  }, [acknowledged, backend.loadPowerWebCandidateBrief, candidate.candidate_id, radarId, runId, selected.join('|')]);
  useEffect(() => {
    if (!handoff || requestedHandoffId) return;
    const url = new URL(window.location.href);
    url.searchParams.set('candidateId', candidate.candidate_id);
    url.searchParams.set('handoffId', handoff.handoff_id);
    window.history.replaceState(window.history.state, '', `${url.pathname}${url.search}${url.hash}`);
  }, [candidate.candidate_id, handoff, requestedHandoffId]);

  const toggle = (productId: string) => setSelected((current) => (
    current.includes(productId) ? current.filter((item) => item !== productId) : [...current, productId]
  ));
  if (handoff) {
    return (
      <div className="power-web-handoff-panel" data-testid="power-web-handoff-ready"><Card>
        <div className="power-web-ready-title">
          <Check aria-hidden="true" />
          <div><Eyebrow>{t('icpRadar.powerWeb.readyEyebrow')}</Eyebrow><h2>{t('icpRadar.powerWeb.readyTitle')}</h2></div>
        </div>
        <dl className="icp-definition-list">
          <div><dt>{t('icpRadar.powerWeb.handoffId')}</dt><dd><Mono>{handoff.handoff_id}</Mono></dd></div>
          <div><dt>{t('icpRadar.powerWeb.accountIdentity')}</dt><dd>{handoff.account.identity_basis} / {handoff.account.identity_status}</dd></div>
          <div><dt>{t('icpRadar.powerWeb.candidateRun')}</dt><dd><Mono>{handoff.source_candidate_run_id}</Mono></dd></div>
          <div><dt>{t('icpRadar.powerWeb.signalRun')}</dt><dd><Mono>{handoff.source_signal_run_id ?? t('icpRadar.powerWeb.noSignalContext')}</Mono></dd></div>
        </dl>
        {handoff.product_role_demand_sets.map((group) => (
          <section key={group.product.product_id} className="power-web-role-group">
            <h3>{group.product.name}</h3>
            <Mono>{group.product.sales_playbook_version_id}</Mono>
            <div className="power-web-role-list">
              {group.role_demands.map((role) => (
                <div key={role.demand_id}><strong>{role.display_name}</strong><span>{role.responsibility}</span><Badge tone="neutral">{role.required ? t('icpRadar.powerWeb.required') : t('icpRadar.powerWeb.optional')}</Badge></div>
              ))}
            </div>
          </section>
        ))}
      </Card></div>
    );
  }
  return (
    <div className="power-web-handoff-panel" data-testid="power-web-handoff-preflight"><Card>
      <Eyebrow>{t('icpRadar.powerWeb.prepareEyebrow')}</Eyebrow>
      <h2>{t('icpRadar.powerWeb.prepareTitle')}</h2>
      <p>{t('icpRadar.powerWeb.prepareCopy')}</p>
      <div className="power-web-product-list">
        {backend.powerWebProducts.filter((product) => defaultProducts.includes(product.product_id)).map((product) => {
          const version = backend.powerWebProductVersions[product.product_id];
          return (
            <label key={product.product_id} className="power-web-product-row">
              <input type="checkbox" checked={selected.includes(product.product_id)} onChange={() => toggle(product.product_id)} />
              <span><strong>{product.name}</strong><Mono>v{product.active_version_number ?? '-'}</Mono></span>
              <Badge tone="neutral">{t('icpRadar.powerWeb.roleCount', { count: version?.buying_roles.length ?? 0 })}</Badge>
            </label>
          );
        })}
      </div>
      {reviewNeeded && (
        <label className="power-web-review-ack">
          <input type="checkbox" checked={acknowledged} onChange={(event) => setAcknowledged(event.target.checked)} />
          <span>{t('icpRadar.powerWeb.reviewAcknowledgement')}</span>
        </label>
      )}
      {preflight && (
        <div className="power-web-preflight-summary">
          <Badge tone={preflight.ready ? 'ally' : 'unsurfaced'}>{preflight.ready ? t('icpRadar.powerWeb.preflightReady') : t('icpRadar.powerWeb.preflightBlocked')}</Badge>
          <span>{t('icpRadar.powerWeb.roleCount', { count: preflight.role_demand_count })}</span>
          <span>{preflight.linked_signal_run_id ?? t('icpRadar.powerWeb.noSignalContext')}</span>
          {preflight.blockers.map((item) => <Mono key={item}>{item}</Mono>)}
        </div>
      )}
      {error && <p role="alert">{error}</p>}
      <Button
        data-testid="prepare-power-web"
        icon={busy ? <LoaderCircle className="spin" aria-hidden="true" /> : <Search aria-hidden="true" />}
        disabled={busy || selected.length === 0 || (reviewNeeded && !acknowledged) || Boolean(preflight && !preflight.ready)}
        onClick={async () => {
          setBusy(true); setError('');
          try {
            const created = await backend.preparePowerWebHandoff({ radarId, runId, candidateId: candidate.candidate_id, productIds: selected, reviewNeeded, acknowledged });
            if (created) {
              const url = new URL(window.location.href);
              url.searchParams.set('candidateId', candidate.candidate_id);
              url.searchParams.set('handoffId', created.handoff_id);
              window.history.replaceState(window.history.state, '', `${url.pathname}${url.search}${url.hash}`);
            }
          } catch (failure) {
            setError(failure instanceof Error ? failure.message : t('icpRadar.powerWeb.prepareFailed'));
          } finally { setBusy(false); }
        }}
        variant="default"
      >{t('icpRadar.powerWeb.prepareAction')}</Button>
    </Card></div>
  );
}
