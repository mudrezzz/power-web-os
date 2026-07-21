import {
  Archive,
  ArrowLeft,
  ChevronDown,
  Eye,
  History,
  LoaderCircle,
  Package,
  Plus,
  RefreshCw,
  Save,
  Upload,
  X,
} from 'lucide-react';
import { Fragment, useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { salesPlaybookApi, SalesPlaybookApiError } from '../api/salesPlaybookApi';
import { Badge, Button, Eyebrow, IconButton, Mono } from '../components/primitives';
import { WorkspaceTabPanel, WorkspaceTabs } from '../components/WorkspaceTabs';
import '../features/sales-playbook/salesPlaybook.css';
import type { ProductSummary, SalesPlaybookDraft, SalesPlaybookVersion, SemanticBuyingRole } from '../types';

type WorkspaceTab = 'product' | 'roles' | 'versions';
type LoadState = 'loading' | 'loaded' | 'failed';

const workspaceTabs: WorkspaceTab[] = ['product', 'roles', 'versions'];

export function SalesPlaybookScreen() {
  const { t } = useTranslation();
  const initialQuery = useMemo(() => new URLSearchParams(window.location.search), []);
  const requestedTab = initialQuery.get('playbookTab') as WorkspaceTab | null;
  const [tab, setTab] = useState<WorkspaceTab>(requestedTab && workspaceTabs.includes(requestedTab) ? requestedTab : 'product');
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<string | null>(initialQuery.get('productId'));
  const [draft, setDraft] = useState<SalesPlaybookDraft | null>(null);
  const [versions, setVersions] = useState<SalesPlaybookVersion[]>([]);
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conflict, setConflict] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedRoleCode, setSelectedRoleCode] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [archiveOpen, setArchiveOpen] = useState(false);
  const [newProductName, setNewProductName] = useState('');
  const [newProductCode, setNewProductCode] = useState('');

  const refreshProducts = useCallback(async () => {
    setLoadState('loading');
    setError(null);
    try {
      const items = await salesPlaybookApi.listProducts();
      setProducts(items);
      setSelectedProductId((current) => current && items.some((item) => item.product_id === current) ? current : null);
      setLoadState('loaded');
    } catch (requestError) {
      setError(messageOf(requestError));
      setLoadState('failed');
    }
  }, []);

  const loadProduct = useCallback(async (productId: string) => {
    setBusy(true);
    setDraft(null);
    setError(null);
    try {
      const [nextDraft, nextVersions] = await Promise.all([
        salesPlaybookApi.getDraft(productId),
        salesPlaybookApi.listVersions(productId),
      ]);
      setDraft(nextDraft);
      setVersions(nextVersions);
      setDirty(false);
      setConflict(false);
      setSelectedRoleCode(null);
    } catch (requestError) {
      setError(messageOf(requestError));
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => { void refreshProducts(); }, [refreshProducts]);
  useEffect(() => { if (selectedProductId) void loadProduct(selectedProductId); }, [loadProduct, selectedProductId]);
  useEffect(() => {
    const handlePopState = () => {
      const query = new URLSearchParams(window.location.search);
      const nextTab = query.get('playbookTab') as WorkspaceTab | null;
      setSelectedProductId(query.get('productId'));
      setTab(nextTab && workspaceTabs.includes(nextTab) ? nextTab : 'product');
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);
  useEffect(() => {
    const url = new URL(window.location.href);
    if (selectedProductId) {
      url.searchParams.set('productId', selectedProductId);
      url.searchParams.set('playbookTab', tab);
    } else {
      url.searchParams.delete('productId');
      url.searchParams.delete('playbookTab');
    }
    window.history.replaceState({}, '', url);
  }, [selectedProductId, tab]);

  function openProduct(productId: string) {
    const url = new URL(window.location.href);
    url.searchParams.set('productId', productId);
    url.searchParams.set('playbookTab', 'product');
    window.history.pushState({}, '', url);
    setTab('product');
    setSelectedProductId(productId);
  }

  function closeProduct() {
    const url = new URL(window.location.href);
    url.searchParams.delete('productId');
    url.searchParams.delete('playbookTab');
    window.history.pushState({}, '', url);
    setSelectedProductId(null);
    setDraft(null);
    setVersions([]);
    setTab('product');
  }

  function updateDraft(mutator: (current: SalesPlaybookDraft) => SalesPlaybookDraft) {
    setDraft((current) => current ? mutator(current) : current);
    setDirty(true);
    setConflict(false);
  }

  async function saveDraft(): Promise<SalesPlaybookDraft | null> {
    if (!draft) return null;
    setBusy(true);
    setError(null);
    try {
      const saved = await salesPlaybookApi.saveDraft(draft.product_id, draft.draft_revision, draft.product, draft.buying_roles);
      setDraft(saved);
      setDirty(false);
      setConflict(false);
      await refreshProducts();
      return saved;
    } catch (requestError) {
      if (requestError instanceof SalesPlaybookApiError && requestError.status === 409) setConflict(true);
      setError(messageOf(requestError));
      return null;
    } finally {
      setBusy(false);
    }
  }

  async function publish() {
    if (!draft) return;
    const saved = dirty ? await saveDraft() : draft;
    if (!saved) return;
    setBusy(true);
    setError(null);
    try {
      await salesPlaybookApi.publish(saved.product_id);
      await Promise.all([refreshProducts(), loadProduct(saved.product_id)]);
    } catch (requestError) {
      setError(messageOf(requestError));
    } finally {
      setBusy(false);
    }
  }

  async function createProduct() {
    if (!newProductName.trim() || !newProductCode.trim()) return;
    setBusy(true);
    try {
      const created = await salesPlaybookApi.createProduct(newProductCode.trim(), newProductName.trim());
      setCreateOpen(false);
      setNewProductCode('');
      setNewProductName('');
      await refreshProducts();
      openProduct(created.product_id);
    } catch (requestError) {
      setError(messageOf(requestError));
    } finally {
      setBusy(false);
    }
  }

  const visibleProducts = products.filter((item) =>
    `${item.name} ${item.product_code}`.toLocaleLowerCase().includes(search.toLocaleLowerCase()),
  );
  const selectedProduct = products.find((item) => item.product_id === selectedProductId) ?? null;

  return (
    <section className="screen sales-playbook-screen" aria-label={t('salesPlaybook.aria')} data-testid="sales-playbook-workspace">
      {error && <div className="sales-alert sales-alert-error" role="alert">{error}</div>}
      {conflict && (
        <div className="sales-alert sales-alert-conflict" role="alert">
          <span>{t('salesPlaybook.conflict')}</span>
          <Button onClick={() => selectedProductId && void loadProduct(selectedProductId)}>{t('salesPlaybook.loadServerVersion')}</Button>
          <Button onClick={() => setConflict(false)}>{t('salesPlaybook.keepLocalDraft')}</Button>
        </div>
      )}

      {!selectedProductId ? (
        <ProductCatalog
          products={visibleProducts}
          loadState={loadState}
          search={search}
          onSearch={setSearch}
          onOpen={openProduct}
          onCreate={() => setCreateOpen(true)}
          onRetry={() => void refreshProducts()}
        />
      ) : busy && !draft ? (
        <Loading label={t('salesPlaybook.loadingProduct')} />
      ) : draft && selectedProduct ? (
        <div className="sales-playbook-detail" data-testid="sales-playbook-detail">
          <header className="sales-playbook-header">
            <div className="sales-playbook-identity">
              <Button icon={<ArrowLeft />} variant="quiet" onClick={closeProduct}>{t('salesPlaybook.backToProducts')}</Button>
              <Package aria-hidden="true" />
              <div>
                <Eyebrow>{t('salesPlaybook.eyebrow')}</Eyebrow>
                <h1>{draft.product.name}</h1>
                <div className="sales-meta"><Mono>{draft.product.product_code}</Mono><Mono>{`revision ${draft.draft_revision}`}</Mono><Badge tone={selectedProduct.lifecycle === 'active' ? 'ally' : 'neutral'}>{t(`salesPlaybook.lifecycle.${selectedProduct.lifecycle}`)}</Badge></div>
              </div>
            </div>
            <div className="sales-playbook-actions">
              <label className="product-switcher"><span>{t('salesPlaybook.switchProduct')}</span><select value={draft.product_id} onChange={(event) => openProduct(event.target.value)}>{products.map((product) => <option key={product.product_id} value={product.product_id}>{product.name}</option>)}</select></label>
              <Button data-testid="save-draft-header" icon={<Save />} disabled={!dirty || busy} onClick={() => void saveDraft()}>{t('salesPlaybook.saveDraft')}</Button>
              <Button variant="primary" icon={<Upload />} disabled={busy} onClick={() => void publish()}>{t('salesPlaybook.publish')}</Button>
              <IconButton aria-label={t('salesPlaybook.archive')} onClick={() => setArchiveOpen(true)}><Archive /></IconButton>
            </div>
          </header>

          <WorkspaceTabs
            id="sales-playbook"
            activeId={tab}
            ariaLabel={t('salesPlaybook.tabsAria')}
            items={workspaceTabs.map((item) => ({ id: item, label: t(`salesPlaybook.tabs.${item}`) }))}
            onChange={setTab}
          />

          <WorkspaceTabPanel groupId="sales-playbook" tabId={tab} className="sales-tab-content">
            {tab === 'product' && <ProductEditor draft={draft} lockedCode={versions.length > 0} onChange={updateDraft} />}
            {tab === 'roles' && <RolesEditor draft={draft} selectedCode={selectedRoleCode} onSelect={setSelectedRoleCode} onChange={updateDraft} />}
            {tab === 'versions' && <VersionsView versions={versions} onActivate={async (id) => { await salesPlaybookApi.activate(draft.product_id, id); await Promise.all([refreshProducts(), loadProduct(draft.product_id)]); }} onRestore={async (id) => { await salesPlaybookApi.restore(draft.product_id, id); await loadProduct(draft.product_id); setTab('product'); }} />}
          </WorkspaceTabPanel>

          {dirty && <div className="draft-bar"><span>{t('salesPlaybook.unsaved')}</span><Button onClick={() => void loadProduct(draft.product_id)}>{t('salesPlaybook.discard')}</Button><Button data-testid="save-draft-footer" icon={<Save />} onClick={() => void saveDraft()}>{t('salesPlaybook.saveDraft')}</Button><Button variant="primary" icon={<Upload />} onClick={() => void publish()}>{t('salesPlaybook.publish')}</Button></div>}
        </div>
      ) : (
        <div className="sales-empty"><Package /><h2>{t('salesPlaybook.emptyTitle')}</h2><p>{t('salesPlaybook.emptyCopy')}</p>{selectedProductId && <Button icon={<RefreshCw />} onClick={() => void loadProduct(selectedProductId)}>{t('common.retry')}</Button>}<Button icon={<ArrowLeft />} onClick={closeProduct}>{t('salesPlaybook.backToProducts')}</Button></div>
      )}

      {createOpen && <Dialog title={t('salesPlaybook.createProduct')} onClose={() => setCreateOpen(false)}><label className="sales-field"><span>{t('salesPlaybook.productName')}</span><input autoFocus value={newProductName} onChange={(event) => { setNewProductName(event.target.value); if (!newProductCode) setNewProductCode(slug(event.target.value)); }} /></label><label className="sales-field"><span>{t('salesPlaybook.productCode')}</span><input value={newProductCode} onChange={(event) => setNewProductCode(slug(event.target.value))} /></label><div className="dialog-actions"><Button onClick={() => setCreateOpen(false)}>{t('common.cancel')}</Button><Button variant="primary" onClick={() => void createProduct()}>{t('common.create')}</Button></div></Dialog>}
      {archiveOpen && selectedProductId && <Dialog title={t('salesPlaybook.archive')} onClose={() => setArchiveOpen(false)}><p>{t('salesPlaybook.archiveConfirm')}</p><div className="dialog-actions"><Button onClick={() => setArchiveOpen(false)}>{t('common.cancel')}</Button><Button variant="primary" icon={<Archive />} onClick={async () => { await salesPlaybookApi.archive(selectedProductId); setArchiveOpen(false); await refreshProducts(); }}>{t('salesPlaybook.archive')}</Button></div></Dialog>}
    </section>
  );
}

function ProductCatalog({ products, loadState, search, onSearch, onOpen, onCreate, onRetry }: { products: ProductSummary[]; loadState: LoadState; search: string; onSearch: (value: string) => void; onOpen: (id: string) => void; onCreate: () => void; onRetry: () => void }) {
  const { t } = useTranslation();
  return <div className="product-catalog" data-testid="product-catalog">
    <header className="product-catalog-header"><div><Eyebrow>{t('salesPlaybook.catalogEyebrow')}</Eyebrow><h1>{t('salesPlaybook.catalogTitle')}</h1></div><Button variant="primary" icon={<Plus />} onClick={onCreate}>{t('salesPlaybook.createProduct')}</Button></header>
    <label className="sales-field product-search"><span>{t('salesPlaybook.searchProducts')}</span><input value={search} onChange={(event) => onSearch(event.target.value)} /></label>
    {loadState === 'loading' && <Loading label={t('salesPlaybook.loadingProducts')} />}
    {loadState === 'failed' && <Button icon={<RefreshCw />} onClick={onRetry}>{t('common.retry')}</Button>}
    {loadState === 'loaded' && <div className="product-catalog-table"><div className="product-catalog-row product-catalog-head"><span>{t('salesPlaybook.productName')}</span><span>{t('salesPlaybook.version')}</span><span>{t('salesPlaybook.status')}</span><span>{t('salesPlaybook.updated')}</span></div>{products.map((product) => <button className="product-catalog-row" data-testid={`product-${product.product_code}`} key={product.product_id} type="button" onClick={() => onOpen(product.product_id)}><span><strong>{product.name}</strong><Mono>{product.product_code}</Mono></span><Mono>{`v${product.active_version_number ?? 'draft'}`}</Mono><Badge tone={product.lifecycle === 'active' ? 'ally' : 'neutral'}>{t(`salesPlaybook.lifecycle.${product.lifecycle}`)}</Badge><span>{new Date(product.updated_at).toLocaleString()}</span></button>)}</div>}
  </div>;
}

function ProductEditor({ draft, lockedCode, onChange }: { draft: SalesPlaybookDraft; lockedCode: boolean; onChange: (mutator: (value: SalesPlaybookDraft) => SalesPlaybookDraft) => void }) {
  const { t } = useTranslation();
  const update = (key: keyof SalesPlaybookDraft['product'], value: string | string[]) => onChange((current) => ({ ...current, product: { ...current.product, [key]: value } }));
  return <div className="sales-form-grid" data-testid="product-editor">
    <label className="sales-field"><span>{t('salesPlaybook.productName')}</span><input value={draft.product.name} onChange={(e) => update('name', e.target.value)} /></label>
    <label className="sales-field"><span>{t('salesPlaybook.productCode')}</span><input disabled={lockedCode} value={draft.product.product_code} onChange={(e) => update('product_code', slug(e.target.value))} /></label>
    <label className="sales-field sales-field-wide"><span>{t('salesPlaybook.shortDescription')}</span><textarea data-testid="product-short-description" value={draft.product.short_description} onChange={(e) => update('short_description', e.target.value)} /></label>
    <label className="sales-field"><span>{t('salesPlaybook.customerProblem')}</span><textarea value={draft.product.customer_problem} onChange={(e) => update('customer_problem', e.target.value)} /></label>
    <label className="sales-field"><span>{t('salesPlaybook.valueProposition')}</span><textarea value={draft.product.value_proposition} onChange={(e) => update('value_proposition', e.target.value)} /></label>
    <label className="sales-field sales-field-wide"><span>{t('salesPlaybook.useContexts')}</span><input value={draft.product.use_contexts.join(', ')} onChange={(e) => update('use_contexts', splitList(e.target.value))} /></label>
  </div>;
}

function RolesEditor({ draft, selectedCode, onSelect, onChange }: { draft: SalesPlaybookDraft; selectedCode: string | null; onSelect: (value: string | null) => void; onChange: (mutator: (value: SalesPlaybookDraft) => SalesPlaybookDraft) => void }) {
  const { t } = useTranslation();
  const replace = (role: SemanticBuyingRole) => onChange((current) => ({ ...current, buying_roles: current.buying_roles.map((item) => item.role_code === role.role_code ? role : item) }));
  const add = () => {
    const code = nextRoleCode(draft.buying_roles);
    const role: SemanticBuyingRole = { role_code: code, display_name: t('salesPlaybook.newRole'), business_responsibility: '', decision_rights: [], required: true, priority: 'high', scope: 'account', reason: '', expected_evidence: [], exclusions: [] };
    onChange((current) => ({ ...current, buying_roles: [...current.buying_roles, role] }));
    onSelect(code);
  };
  const remove = (code: string) => { onChange((current) => ({ ...current, buying_roles: current.buying_roles.filter((role) => role.role_code !== code) })); onSelect(null); };

  return <div className="editor-main"><div className="editor-heading"><div><Eyebrow>{t('salesPlaybook.rolesEyebrow')}</Eyebrow><h2>{t('salesPlaybook.rolesTitle')}</h2><p>{t('salesPlaybook.rolesCopy')}</p></div><Button icon={<Plus />} onClick={add}>{t('salesPlaybook.addRole')}</Button></div><div className="sales-table roles-table" data-testid="roles-table"><div className="sales-table-head"><span>{t('salesPlaybook.role')}</span><span>{t('salesPlaybook.requirement')}</span><span>{t('salesPlaybook.priority')}</span><span>{t('salesPlaybook.scope')}</span><span>{t('salesPlaybook.responsibility')}</span></div>{draft.buying_roles.map((role) => <Fragment key={role.role_code}><button className={role.role_code === selectedCode ? 'sales-table-row sales-table-row-active' : 'sales-table-row'} type="button" onClick={() => onSelect(role.role_code === selectedCode ? null : role.role_code)}><span><strong>{role.display_name}</strong><Mono>{role.role_code}</Mono></span><span>{t(`salesPlaybook.required.${role.required}`)}</span><span>{t(`salesPlaybook.priorities.${role.priority}`)}</span><span>{t(`salesPlaybook.scopes.${role.scope}`)}</span><span>{role.business_responsibility || t('salesPlaybook.needsCompletion')}</span></button>{role.role_code === selectedCode && <div className="role-inline-editor" data-testid="role-inline-editor"><div className="inspector-heading"><div><h2>{t('salesPlaybook.editRole')}</h2><Mono>{role.role_code}</Mono></div><IconButton aria-label={t('common.close')} onClick={() => onSelect(null)}><X /></IconButton></div><RoleFields role={role} onChange={replace} /><Button onClick={() => remove(role.role_code)}>{t('common.delete')}</Button></div>}</Fragment>)}</div></div>;
}

function RoleFields({ role, onChange }: { role: SemanticBuyingRole; onChange: (role: SemanticBuyingRole) => void }) {
  const { t } = useTranslation();
  const set = <K extends keyof SemanticBuyingRole>(key: K, value: SemanticBuyingRole[K]) => onChange({ ...role, [key]: value });
  return <div className="role-fields"><div className="role-basic-fields">
    <label className="sales-field" data-basic-role-field="true"><span>{t('salesPlaybook.roleName')}</span><input value={role.display_name} onChange={(e) => set('display_name', e.target.value)} /></label>
    <label className="sales-field role-responsibility" data-basic-role-field="true"><span>{t('salesPlaybook.responsibility')}</span><textarea value={role.business_responsibility} onChange={(e) => set('business_responsibility', e.target.value)} /></label>
    <label className="sales-check" data-basic-role-field="true"><input type="checkbox" checked={role.required} onChange={(e) => onChange({ ...role, required: e.target.checked, priority: e.target.checked ? 'high' : 'normal' })} /><span>{t('salesPlaybook.requiredRole')}</span></label>
    <label className="sales-field" data-basic-role-field="true"><span>{t('salesPlaybook.scope')}</span><select value={role.scope} onChange={(e) => set('scope', e.target.value as SemanticBuyingRole['scope'])}>{['holding','account','site','external'].map((scope) => <option value={scope} key={scope}>{t(`salesPlaybook.scopes.${scope}`)}</option>)}</select></label>
  </div><details className="role-advanced" data-testid="role-advanced"><summary><ChevronDown aria-hidden="true" />{t('salesPlaybook.advanced')}</summary><div className="role-advanced-fields"><label className="sales-field"><span>{t('salesPlaybook.decisionRights')}</span><textarea value={role.decision_rights.join('\n')} onChange={(e) => set('decision_rights', splitLines(e.target.value))} /></label><label className="sales-field"><span>{t('salesPlaybook.priority')}</span><select value={role.priority} onChange={(e) => set('priority', e.target.value as SemanticBuyingRole['priority'])}><option value="critical">{t('salesPlaybook.priorities.critical')}</option><option value="high">{t('salesPlaybook.priorities.high')}</option><option value="normal">{t('salesPlaybook.priorities.normal')}</option></select></label><label className="sales-field"><span>{t('salesPlaybook.exclusions')}</span><textarea value={role.exclusions.join('\n')} onChange={(e) => set('exclusions', splitLines(e.target.value))} /></label></div></details><div className="sales-note">{t('salesPlaybook.titleHypothesisNote')}</div></div>;
}

function VersionsView({ versions, onActivate, onRestore }: { versions: SalesPlaybookVersion[]; onActivate: (id: string) => Promise<void>; onRestore: (id: string) => Promise<void> }) {
  const { t } = useTranslation();
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const selected = versions.find((version) => version.version_id === selectedVersionId) ?? null;
  return <div className="versions-workspace"><div className="editor-heading"><div><Eyebrow>{t('salesPlaybook.versionsEyebrow')}</Eyebrow><h2>{t('salesPlaybook.versionsTitle')}</h2></div></div><div className="sales-table version-table"><div className="sales-table-head"><span>{t('salesPlaybook.version')}</span><span>{t('salesPlaybook.publishedAt')}</span><span>{t('salesPlaybook.author')}</span><span>{t('salesPlaybook.contents')}</span><span>{t('salesPlaybook.actions')}</span></div>{versions.map((version) => <div className="sales-table-row" data-testid={`version-${version.version_id}`} key={version.version_id}><span><Mono>{`v${version.version_number}`}</Mono>{version.is_active && <Badge tone="ally">{t('salesPlaybook.active')}</Badge>}</span><span>{new Date(version.published_at).toLocaleString()}</span><span>{version.published_by}</span><span>{t('salesPlaybook.versionContents', { roles: version.buying_roles.length })}</span><span className="version-actions"><IconButton aria-label={t('salesPlaybook.openVersion')} onClick={() => setSelectedVersionId(version.version_id)}><Eye /></IconButton><Button disabled={version.is_active} onClick={() => void onActivate(version.version_id)}>{t('salesPlaybook.activate')}</Button><Button icon={<History />} onClick={() => void onRestore(version.version_id)}>{t('salesPlaybook.restore')}</Button></span></div>)}</div>{selected && <section className="version-snapshot" aria-label={t('salesPlaybook.versionReadOnly')}><div className="inspector-heading"><div><Eyebrow>{t('salesPlaybook.versionReadOnly')}</Eyebrow><h2>{`${selected.product.name} · v${selected.version_number}`}</h2></div><IconButton aria-label={t('common.close')} onClick={() => setSelectedVersionId(null)}><X /></IconButton></div><p>{selected.product.short_description}</p><div className="version-snapshot-grid"><div><strong>{t('salesPlaybook.tabs.roles')}</strong>{selected.buying_roles.map((role) => <span key={role.role_code}>{role.display_name}<Mono>{role.role_code}</Mono></span>)}</div>{selected.access_playbook && <div className="legacy-access-snapshot" data-testid="legacy-access-snapshot"><strong>{t('salesPlaybook.legacyAccessTitle')}</strong><p>{t('salesPlaybook.legacyAccessCopy')}</p>{selected.access_playbook.route_rules.map((route) => <span key={route.route_code}>{route.name}<Mono>{route.route_code}</Mono></span>)}</div>}</div></section>}</div>;
}

function Dialog({ title, children, onClose }: { title: string; children: React.ReactNode; onClose: () => void }) { const { t } = useTranslation(); return <div className="dialog-backdrop" role="presentation"><section className="sales-dialog" role="dialog" aria-modal="true" aria-label={title}><div className="inspector-heading"><h2>{title}</h2><IconButton aria-label={t('common.close')} onClick={onClose}><X /></IconButton></div>{children}</section></div>; }
function Loading({ label }: { label: string }) { return <div className="sales-loading"><LoaderCircle aria-hidden="true" /><span>{label}</span></div>; }
function splitList(value: string) { return value.split(',').map((item) => item.trim()).filter(Boolean); }
function splitLines(value: string) { return value.split('\n').map((item) => item.trim()).filter(Boolean); }
function nextRoleCode(roles: SemanticBuyingRole[]) { let index = roles.length + 1; while (roles.some((role) => role.role_code === `semantic_role_${index}`)) index += 1; return `semantic_role_${index}`; }
function slug(value: string) { return value.toLocaleLowerCase().trim().replace(/[^a-z0-9а-яё]+/gi, '-').replace(/^-|-$/g, '').replace(/[а-яё]/gi, 'x'); }
function messageOf(error: unknown) { return error instanceof Error ? error.message : 'Unknown error'; }
