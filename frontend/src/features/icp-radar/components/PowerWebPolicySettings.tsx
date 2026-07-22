import { ExternalLink, LoaderCircle, Pencil, Save, X } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Card, Eyebrow, Mono } from '../../../components/primitives';
import type { PowerWebHandoffBackendController } from '../application/usePowerWebHandoffBackend';

export function PowerWebPolicySettings({
  backend,
  radarId,
}: {
  backend: PowerWebHandoffBackendController;
  radarId: string;
}) {
  const { t } = useTranslation();
  const policy = backend.powerWebPolicyByRadarId[radarId] ?? null;
  const state = backend.powerWebPolicyStateByRadarId[radarId] ?? { status: 'idle' as const, error: null };
  const bound = useMemo(() => policy?.product_bindings.map((item) => item.product_id) ?? [], [policy]);
  const [editing, setEditing] = useState(false);
  const [selected, setSelected] = useState<string[]>(bound);

  useEffect(() => { void backend.loadPowerWebPolicy(radarId); }, [backend.loadPowerWebPolicy, radarId]);
  useEffect(() => { if (!editing) setSelected(bound); }, [bound, editing]);

  const toggle = (productId: string) => setSelected((current) => (
    current.includes(productId) ? current.filter((item) => item !== productId) : [...current, productId]
  ));
  return (
    <div className="power-web-policy-settings" data-testid="radar-power-web-policy"><Card>
      <div className="power-web-section-header">
        <div>
          <Eyebrow>{t('icpRadar.powerWeb.settingsEyebrow')}</Eyebrow>
          <h2>{t('icpRadar.powerWeb.settingsTitle')}</h2>
          <p>{t('icpRadar.powerWeb.settingsCopy')}</p>
        </div>
        {state.status === 'loading' ? <LoaderCircle className="spin" aria-hidden="true" /> : editing ? (
          <div className="inline-actions">
            <Button icon={<X aria-hidden="true" />} variant="quiet" onClick={() => setEditing(false)}>{t('common.cancel')}</Button>
            <Button icon={<Save aria-hidden="true" />} variant="default" onClick={async () => {
              if (await backend.savePowerWebPolicy(radarId, selected)) setEditing(false);
            }}>{t('icpRadar.powerWeb.savePolicy')}</Button>
          </div>
        ) : (
          <Button icon={<Pencil aria-hidden="true" />} variant="quiet" onClick={() => setEditing(true)}>{t('icpRadar.editSettings')}</Button>
        )}
      </div>
      {state.status === 'failed' && <p role="alert">{state.error}</p>}
      {!editing && bound.length === 0 && <p>{t('icpRadar.powerWeb.notConfigured')}</p>}
      <div className="power-web-product-list">
        {backend.powerWebProducts.map((product) => {
          const version = backend.powerWebProductVersions[product.product_id];
          const checked = editing ? selected.includes(product.product_id) : bound.includes(product.product_id);
          if (!editing && !checked) return null;
          const required = version?.buying_roles.filter((role) => role.required).length ?? 0;
          const optional = (version?.buying_roles.length ?? 0) - required;
          return (
            <label key={product.product_id} className="power-web-product-row">
              {editing && <input type="checkbox" checked={checked} onChange={() => toggle(product.product_id)} />}
              <span>
                <strong>{product.name}</strong>
                <Mono>v{product.active_version_number ?? '-'}</Mono>
              </span>
              <span className="badge-list">
                <Badge tone="neutral">{t('icpRadar.powerWeb.requiredCount', { count: required })}</Badge>
                <Badge tone="neutral">{t('icpRadar.powerWeb.optionalCount', { count: optional })}</Badge>
              </span>
              <a href={`/?screen=playbook&productId=${encodeURIComponent(product.product_id)}`} aria-label={t('icpRadar.powerWeb.openProduct')}>
                <ExternalLink aria-hidden="true" />
              </a>
            </label>
          );
        })}
      </div>
      {policy && <Mono>{policy.policy_version_id}</Mono>}
    </Card></div>
  );
}
