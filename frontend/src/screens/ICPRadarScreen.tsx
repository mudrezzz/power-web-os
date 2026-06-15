import {
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronDown,
  ChevronRight,
  Copy,
  ExternalLink,
  Plus,
  Radar,
  RotateCcw,
  Save,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Target,
  Trash2,
  X,
} from 'lucide-react';
import type { ReactNode } from 'react';
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Card, Eyebrow, Mono } from '../components/primitives';
import type {
  AtomicRule,
  CriterionEvidenceExplanation,
  EditableRadarDefinitionDraft,
  ICPRadarArtifact,
  ICPRadarCatalogArtifact,
  ICPRadarCatalogItem,
  ICPRadarCandidate,
  IntentSignalDefinition,
  GlobalSearchPolicy,
  LiveICPRadarRunArtifact,
  LiveRadarCandidate,
  LiveRadarQualificationResult,
  LiveRadarSignalResult,
  LiveRadarSourceEvidence,
  MonitoringPolicy,
  RadarConfigOverride,
  RadarDefinition,
  RadarEditorState,
  RadarMetadata,
  RadarScoringModel,
  RadarValidationReport,
  RuleGroup,
  SignalValidationDecision,
  SignalValidationOverlay,
  SignalValidationStatus,
  SourceDefinition,
  SourcePolicy,
  ValidatedCandidateScore,
} from '../types';

type RadarDetailTab = 'shortlist' | 'settings';
type CandidateDetailTab = 'overview' | 'qualification' | 'signals' | 'sources' | 'journal';
type RadarOperationalStatus = 'draft' | 'active' | 'stopped';

const radarConfigStorageKey = 'power-web-os-icp-radar-config-overrides';
const signalValidationStorageKey = 'power-web-os-icp-radar-signal-validation';
const signalCodes = Array.from({ length: 20 }, (_, index) => `C${index + 1}`);
const fitSignalCodes = ['C13', 'C14', 'C15', 'C16', 'C17'];
const intentSignalCodes = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C18', 'C19'];
const triggerSignalCodes = ['C10', 'C11', 'C12', 'C20'];

export function ICPRadarScreen({
  artifact,
  catalog,
  error,
  liveRunArtifact,
}: {
  artifact: ICPRadarArtifact | null;
  catalog: ICPRadarCatalogArtifact | null;
  error: string | null;
  liveRunArtifact: LiveICPRadarRunArtifact | null;
}) {
  const { t } = useTranslation();
  const [selectedRadarId, setSelectedRadarId] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<RadarDetailTab>('shortlist');
  const [expandedCandidateId, setExpandedCandidateId] = useState<string | null>(null);
  const [detailCandidateId, setDetailCandidateId] = useState<string | null>(null);
  const [expandedLiveCandidateId, setExpandedLiveCandidateId] = useState<string | null>(null);
  const [detailLiveCandidateId, setDetailLiveCandidateId] = useState<string | null>(null);
  const [candidateDetailTab, setCandidateDetailTab] = useState<CandidateDetailTab>('overview');
  const [signalValidation, setSignalValidation] = useState<SignalValidationOverlay>(() => loadSignalValidationOverlay());
  const [radarOverrides, setRadarOverrides] = useState<Record<string, RadarConfigOverride>>(() => loadRadarConfigOverrides());
  const mergedRadars = useMemo(() => mergeRadarCatalog(catalog, radarOverrides), [catalog, radarOverrides]);
  const selectedRadar = mergedRadars.find((item) => item.radar_id === selectedRadarId) ?? null;
  const selectedRadarOverride = selectedRadar ? radarOverrides[selectedRadar.radar_id] : undefined;
  const activeFixtureRadarId = catalog?.workflow_metadata.active_fixture_radar_id ?? 'toir-sibur';
  const selectedRadarArtifact = selectedRadar?.radar_id === activeFixtureRadarId ? artifact : null;
  const selectedLiveRunArtifact = selectedRadar?.radar_id === 'toir-quick-live' ? liveRunArtifact : null;
  const detailCandidate = artifact?.candidates.find((item) => item.account_id === detailCandidateId) ?? null;
  const detailLiveCandidate = selectedLiveRunArtifact?.candidates.find((item) => item.candidate_id === detailLiveCandidateId) ?? null;
  const [settingsDraft, setSettingsDraft] = useState<EditableRadarDefinitionDraft | null>(null);
  const [savedSettingsDraftSnapshot, setSavedSettingsDraftSnapshot] = useState('');
  const [editingBlock, setEditingBlock] = useState<SettingsBlockId | null>(null);
  const sourcesById = useMemo(() => {
    const entries = selectedRadarArtifact?.radar.definition.global_search_policy.sources.map((source) => [source.source_id, source]) ?? [];
    return new Map(entries as Array<[string, SourceDefinition]>);
  }, [selectedRadarArtifact]);
  const validationErrors = settingsDraft ? validateRadarDraft(settingsDraft, t) : [];
  const settingsDirty = settingsDraft ? JSON.stringify(settingsDraft) !== savedSettingsDraftSnapshot : false;

  useEffect(() => {
    if (Object.keys(radarOverrides).length) {
      window.localStorage.setItem(radarConfigStorageKey, JSON.stringify(radarOverrides));
      return;
    }
    window.localStorage.removeItem(radarConfigStorageKey);
  }, [radarOverrides]);

  useEffect(() => {
    if (Object.keys(signalValidation).length) {
      window.localStorage.setItem(signalValidationStorageKey, JSON.stringify(signalValidation));
      return;
    }
    window.localStorage.removeItem(signalValidationStorageKey);
  }, [signalValidation]);

  useEffect(() => {
    if (!selectedRadar) {
      setSettingsDraft(null);
      setSavedSettingsDraftSnapshot('');
      setEditingBlock(null);
      return;
    }
    const nextDraft = draftFromRadar(selectedRadar);
    setSettingsDraft(nextDraft);
    setSavedSettingsDraftSnapshot(JSON.stringify(nextDraft));
    setEditingBlock(null);
  }, [selectedRadar?.radar_id]);

  useEffect(() => {
    if (detailCandidateId || detailLiveCandidateId) {
      document.querySelector('.workspace-body')?.scrollTo({ top: 0 });
      setCandidateDetailTab('overview');
    }
  }, [detailCandidateId, detailLiveCandidateId]);

  if (error || !catalog) {
    return (
      <section className="screen status-screen" aria-label={t('icpRadar.aria')}>
        <Card>
          <Eyebrow>{t('icpRadar.statusEyebrow')}</Eyebrow>
          <h1>{error ? t('icpRadar.notReadyTitle') : t('icpRadar.loadingTitle')}</h1>
          <p>{error ? t('icpRadar.notReadyCopy') : t('icpRadar.loadingCopy')}</p>
          {error && <code>{error}</code>}
        </Card>
      </section>
    );
  }

  function openRadar(radar: ICPRadarCatalogItem) {
    setSelectedRadarId(radar.radar_id);
    setSelectedTab('shortlist');
    setExpandedCandidateId(null);
    setDetailCandidateId(null);
    setExpandedLiveCandidateId(null);
    setDetailLiveCandidateId(null);
  }

  function backToCatalog() {
    setSelectedRadarId(null);
    setDetailCandidateId(null);
    setExpandedCandidateId(null);
    setDetailLiveCandidateId(null);
    setExpandedLiveCandidateId(null);
  }

  function createRadar() {
    const template = artifact?.radar.definition ?? catalog?.radars[0]?.definition;
    if (!template) {
      return;
    }
    const created = createLocalRadarFromTemplate(
      template,
      t('icpRadar.newRadarName'),
      t('icpRadar.newRadarOwner'),
      t('icpRadar.settings.localDraftLimitation'),
    );
    setRadarOverrides((current) => ({
      ...current,
      [created.radar_id]: {
        override_type: 'created',
        radar: created,
        saved_at: new Date().toISOString(),
      },
    }));
    setSelectedRadarId(created.radar_id);
    setSelectedTab('settings');
    setEditingBlock('overview');
    setExpandedCandidateId(null);
    setDetailCandidateId(null);
    setExpandedLiveCandidateId(null);
    setDetailLiveCandidateId(null);
  }

  function saveRadarDraft(radar: ICPRadarCatalogItem, overrideType: RadarConfigOverride['override_type']) {
    const normalizedRadar = normalizeRadarCatalogItem(radar);
    setRadarOverrides((current) => ({
      ...current,
      [normalizedRadar.radar_id]: {
        override_type: overrideType === 'deleted' ? 'edited' : overrideType,
        radar: normalizedRadar,
        saved_at: new Date().toISOString(),
      },
    }));
    setSelectedRadarId(normalizedRadar.radar_id);
  }

  function deleteRadar(radar: ICPRadarCatalogItem) {
    setRadarOverrides((current) => {
      const next = { ...current };
      if (current[radar.radar_id]?.override_type === 'created') {
        delete next[radar.radar_id];
      } else {
        next[radar.radar_id] = {
          override_type: 'deleted',
          radar,
          saved_at: new Date().toISOString(),
        };
      }
      return next;
    });
    setSelectedRadarId(null);
    setSelectedTab('shortlist');
    setDetailCandidateId(null);
    setDetailLiveCandidateId(null);
  }

  function resetRadarToArtifact(radarId: string) {
    setRadarOverrides((current) => {
      const next = { ...current };
      delete next[radarId];
      return next;
    });
    if (!catalog?.radars.some((radar) => radar.radar_id === radarId)) {
      setSelectedRadarId(null);
      setSelectedTab('shortlist');
    }
    setEditingBlock(null);
  }

  function resetDemoChanges() {
    setRadarOverrides({});
    setSelectedRadarId(null);
    setSelectedTab('shortlist');
    setEditingBlock(null);
  }

  function saveSignalValidationDecision(decision: SignalValidationDecision) {
    setSignalValidation((current) => ({
      ...current,
      [signalValidationKey(decision.radar_id, decision.account_id, decision.signal_code)]: decision,
    }));
  }

  function resetCandidateSignalValidation(radarId: string, accountId: string) {
    setSignalValidation((current) => Object.fromEntries(
      Object.entries(current).filter(([, decision]) => (
        decision.radar_id !== radarId || decision.account_id !== accountId
      )),
    ));
  }

  function duplicateRadar(radar: ICPRadarCatalogItem) {
    const duplicate = duplicateLocalRadar(radar, t('icpRadar.duplicateName', { name: radar.name }));
    setRadarOverrides((current) => ({
      ...current,
      [duplicate.radar_id]: {
        override_type: 'created',
        radar: duplicate,
        saved_at: new Date().toISOString(),
      },
    }));
    setSelectedRadarId(duplicate.radar_id);
    setSelectedTab('settings');
    setEditingBlock('overview');
  }

  function startHeaderEdit() {
    setSelectedTab('settings');
    setEditingBlock('overview');
  }

  function saveSettingsDraft() {
    if (!selectedRadar || !settingsDraft || validationErrors.length) {
      return;
    }
    const nextRadar = radarFromDraft(selectedRadar, settingsDraft);
    saveRadarDraft(
      nextRadar,
      selectedRadarOverride?.override_type === 'created' ? 'created' : 'edited',
    );
    setSavedSettingsDraftSnapshot(JSON.stringify(settingsDraft));
    setEditingBlock(null);
  }

  function discardSettingsDraft() {
    if (!selectedRadar) {
      return;
    }
    const nextDraft = draftFromRadar(selectedRadar);
    setSettingsDraft(nextDraft);
    setSavedSettingsDraftSnapshot(JSON.stringify(nextDraft));
    setEditingBlock(null);
  }

  if (!selectedRadar) {
    return (
      <RadarCatalogScreen
        hasLocalChanges={Object.keys(radarOverrides).length > 0}
        radars={mergedRadars}
        onCreateRadar={createRadar}
        onOpenRadar={openRadar}
        onResetDemoChanges={resetDemoChanges}
      />
    );
  }

  const detailValidatedScore = detailCandidate && selectedRadar
    ? buildValidatedCandidateScore(detailCandidate, validationForCandidate(signalValidation, selectedRadar.radar_id, detailCandidate.account_id))
    : null;

  if (detailCandidate && selectedRadarArtifact && detailValidatedScore) {
    return (
      <FixtureRadarCandidateDetailView
        activeTab={candidateDetailTab}
        artifact={selectedRadarArtifact}
        candidate={detailCandidate}
        onBack={() => setDetailCandidateId(null)}
        onDecisionChange={saveSignalValidationDecision}
        onResetValidation={() => resetCandidateSignalValidation(selectedRadar.radar_id, detailCandidate.account_id)}
        onTabChange={setCandidateDetailTab}
        radarId={selectedRadar.radar_id}
        radarName={selectedRadar.name}
        signalValidation={signalValidation}
        sourcesById={sourcesById}
        validatedScore={detailValidatedScore}
      />
    );
  }

  if (detailLiveCandidate && selectedLiveRunArtifact && selectedRadar) {
    return (
      <LiveRadarCandidateDetailView
        activeTab={candidateDetailTab}
        artifact={selectedLiveRunArtifact}
        candidate={detailLiveCandidate}
        onBack={() => setDetailLiveCandidateId(null)}
        onTabChange={setCandidateDetailTab}
        radarName={selectedRadar.name}
      />
    );
  }

  return (
    <section className="screen icp-radar-screen" aria-label={t('icpRadar.aria')}>
      <RadarDetailHeader
        activeTab={selectedTab}
        artifact={selectedRadarArtifact}
        draft={settingsDraft}
        dirty={settingsDirty}
        editingBlock={editingBlock}
        isLocalDraft={selectedRadarOverride !== undefined}
        onBack={backToCatalog}
        onDelete={() => deleteRadar(selectedRadar)}
        onDiscard={discardSettingsDraft}
        onDraftChange={setSettingsDraft}
        onDuplicate={() => duplicateRadar(selectedRadar)}
        onEditHeader={startHeaderEdit}
        onReset={() => resetRadarToArtifact(selectedRadar.radar_id)}
        onSave={saveSettingsDraft}
        onTabChange={setSelectedTab}
        overrideType={selectedRadarOverride?.override_type}
        radar={selectedRadar}
        validationErrors={validationErrors}
      />

      {selectedTab === 'settings' ? (
        <RadarSettings
          dirty={settingsDirty}
          draft={settingsDraft ?? draftFromRadar(selectedRadar)}
          editingBlock={editingBlock}
          onCancel={discardSettingsDraft}
          onDraftChange={setSettingsDraft}
          onEdit={(blockId) => {
            setEditingBlock(blockId);
          }}
          onSave={saveSettingsDraft}
          validationErrors={validationErrors}
        />
      ) : selectedRadarArtifact ? (
        <CandidateTable
          artifact={selectedRadarArtifact}
          expandedCandidateId={expandedCandidateId}
          onOpenDetails={setDetailCandidateId}
          onToggleCandidate={(candidateId) => setExpandedCandidateId(
            expandedCandidateId === candidateId ? null : candidateId,
          )}
          radarId={selectedRadar.radar_id}
          signalValidation={signalValidation}
        />
      ) : selectedRadar?.radar_id === 'toir-quick-live' ? (
        <LiveRadarShortlistTable
          artifact={selectedLiveRunArtifact}
          expandedCandidateId={expandedLiveCandidateId}
          onOpenDetails={setDetailLiveCandidateId}
          onOpenSettings={() => setSelectedTab('settings')}
          onToggleCandidate={(candidateId) => setExpandedLiveCandidateId(
            expandedLiveCandidateId === candidateId ? null : candidateId,
          )}
        />
      ) : (
        <EmptyShortlist radar={selectedRadar} onOpenSettings={() => setSelectedTab('settings')} />
      )}
    </section>
  );
}

function RadarCatalogScreen({
  hasLocalChanges,
  onCreateRadar,
  onOpenRadar,
  onResetDemoChanges,
  radars,
}: {
  hasLocalChanges: boolean;
  onCreateRadar: () => void;
  onOpenRadar: (radar: ICPRadarCatalogItem) => void;
  onResetDemoChanges: () => void;
  radars: ICPRadarCatalogItem[];
}) {
  const { t } = useTranslation();
  const totals = radars.reduce(
    (acc, radar) => ({
      candidates: acc.candidates + radar.summary.candidate_count,
      review: acc.review + radar.summary.needs_review_count,
      accepted: acc.accepted + radar.summary.accepted_count,
    }),
    { candidates: 0, review: 0, accepted: 0 },
  );

  return (
    <section className="screen icp-radar-screen" aria-label={t('icpRadar.catalogAria')}>
      <header className="icp-radar-header">
        <span className="section-icon">
          <Radar aria-hidden="true" />
        </span>
        <div>
          <Eyebrow>{t('icpRadar.catalogEyebrow')}</Eyebrow>
          <h1>{t('icpRadar.catalogTitle')}</h1>
          <p>{t('icpRadar.catalogSummary', { count: radars.length })}</p>
        </div>
        <div className="icp-profile-meta">
          <Badge tone="cobalt">{t('icpRadar.catalogTotals.candidates', { count: totals.candidates })}</Badge>
          <Badge tone="neutral">{t('icpRadar.catalogTotals.review', { count: totals.review })}</Badge>
          <Button icon={<Plus aria-hidden="true" />} variant="default" onClick={onCreateRadar}>
            {t('icpRadar.createRadar')}
          </Button>
          {hasLocalChanges && (
            <Button icon={<RotateCcw aria-hidden="true" />} variant="default" onClick={onResetDemoChanges}>
              {t('icpRadar.resetDemoChanges')}
            </Button>
          )}
        </div>
      </header>

      <div className="icp-radar-catalog-list">
        {radars.map((radar) => (
          <Card interactive key={radar.radar_id} onClick={() => onOpenRadar(radar)}>
            <div className="icp-radar-list-row">
              <div className="icp-radar-list-main">
                <span className="section-icon">
                  <Radar aria-hidden="true" />
                </span>
                <div>
                  <Eyebrow>{t('icpRadar.radarCardEyebrow')}</Eyebrow>
                  <h2>{radar.name}</h2>
                  <p>{radar.profile.icp_profile}</p>
                  <small>{radar.profile.scope}</small>
                </div>
              </div>
              <span className="icp-radar-list-status">
                <Badge tone={radar.status === 'active' ? 'ally' : 'neutral'}>
                  {t(radarStatusKey(radar.status))}
                </Badge>
                {isLocalRadarStatus(radar.status) && (
                  <Badge tone="unsurfaced">{t('icpRadar.localDraft')}</Badge>
                )}
              </span>
              <dl className="icp-radar-list-metrics">
                <Metric label={t('icpRadar.cardFields.cadence')} value={t(cadenceKey(radar.summary.cadence))} />
                <Metric label={t('icpRadar.cardFields.lastRun')} value={t(lastRunKey(radar.summary.last_run))} />
                <Metric label={t('icpRadar.cardFields.candidates')} value={String(radar.summary.candidate_count)} />
                <Metric label={t('icpRadar.cardFields.needsReview')} value={String(radar.summary.needs_review_count)} />
                <Metric label={t('icpRadar.cardFields.accepted')} value={String(radar.summary.accepted_count)} />
                <Metric label={t('icpRadar.cardFields.owner')} value={radar.owner} />
              </dl>
              <span className="icp-radar-run-mode">
                <Mono>{t(runModeKey(radar.summary.run_mode))}</Mono>
              </span>
              <div className="icp-radar-list-action">
                <span className="row-action">
                  {t('icpRadar.openRadar')}
                  <ChevronRight aria-hidden="true" />
                </span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </section>
  );
}

function RadarDetailHeader({
  activeTab,
  artifact,
  dirty,
  draft,
  editingBlock,
  isLocalDraft,
  onBack,
  onDelete,
  onDiscard,
  onDraftChange,
  onDuplicate,
  onEditHeader,
  onReset,
  onSave,
  onTabChange,
  overrideType,
  radar,
  validationErrors,
}: {
  activeTab: RadarDetailTab;
  artifact: ICPRadarArtifact | null;
  dirty: boolean;
  draft: EditableRadarDefinitionDraft | null;
  editingBlock: SettingsBlockId | null;
  isLocalDraft: boolean;
  onBack: () => void;
  onDelete: () => void;
  onDiscard: () => void;
  onDraftChange: (draft: EditableRadarDefinitionDraft) => void;
  onDuplicate: () => void;
  onEditHeader: () => void;
  onReset: () => void;
  onSave: () => void;
  onTabChange: (tab: RadarDetailTab) => void;
  overrideType: RadarConfigOverride['override_type'] | undefined;
  radar: ICPRadarCatalogItem;
  validationErrors: string[];
}) {
  const { t } = useTranslation();
  const headerDraft = draft ?? radar.definition;
  const headerDescription = headerDraft.metadata.description || radar.profile.scope || (
    artifact
      ? t('icpRadar.summary', {
        count: artifact.candidates.length,
        holding: artifact.radar.profile.holding,
        product: artifact.radar.profile.product,
      })
      : t('icpRadar.emptyShortlistSummary', { product: radar.profile.product })
  );
  const editingHeader = activeTab === 'settings' && editingBlock === 'overview';
  const effectiveHeaderStatus = radarOperationalStatus(headerDraft.metadata.status || radar.status);
  const statusTone = effectiveHeaderStatus === 'active' ? 'ally' : 'neutral';
  return (
    <div className="icp-radar-selected-shell">
      <div className="icp-detail-breadcrumbs" aria-label={t('icpRadar.radarBreadcrumbs')}>
        <Button icon={<ArrowLeft aria-hidden="true" />} variant="quiet" onClick={onBack}>
          {t('icpRadar.backToCatalog')}
        </Button>
        <span>{t('icpRadar.aria')}</span>
        <ChevronRight aria-hidden="true" />
        <strong>{radar.name}</strong>
      </div>
      <header className="icp-radar-header">
        <span className="section-icon">
          <Radar aria-hidden="true" />
        </span>
        <div className="icp-radar-header-main">
          {editingHeader ? (
            <RadarHeaderEditor draft={headerDraft} onDraftChange={onDraftChange} />
          ) : (
            <>
              <Eyebrow>{t('icpRadar.eyebrow')}</Eyebrow>
              <h1>{headerDraft.metadata.name || radar.name}</h1>
              <p>{headerDescription}</p>
              <div className="icp-radar-header-meta-row">
                <Badge tone={statusTone}>{t(radarStatusKey(effectiveHeaderStatus))}</Badge>
                {isLocalDraft && <Badge tone="unsurfaced">{t('icpRadar.localDraft')}</Badge>}
                {dirty && <Badge tone="unsurfaced">{t('icpRadar.unsavedChanges')}</Badge>}
                <span>{t('icpRadar.cardFields.owner')}: {headerDraft.metadata.owner || radar.owner}</span>
              </div>
            </>
          )}
        </div>
        <div className="icp-radar-header-actions">
          {activeTab === 'settings' && (
            <div className="icp-editor-actions">
              {editingHeader ? (
                <>
                  <Button disabled={validationErrors.length > 0} icon={<Save aria-hidden="true" />} variant="default" onClick={onSave}>
                    {t('icpRadar.saveDraft')}
                  </Button>
                  <Button icon={<X aria-hidden="true" />} variant="default" onClick={onDiscard}>
                    {t('icpRadar.discardChanges')}
                  </Button>
                </>
              ) : (
                <>
                  <Button icon={<SlidersHorizontal aria-hidden="true" />} variant="default" onClick={onEditHeader}>
                    {t('icpRadar.editSettings')}
                  </Button>
                  <Button icon={<Copy aria-hidden="true" />} variant="default" onClick={onDuplicate}>
                    {t('icpRadar.duplicateRadar')}
                  </Button>
                  <Button icon={<Trash2 aria-hidden="true" />} variant="default" onClick={onDelete}>
                    {t('icpRadar.deleteRadar')}
                  </Button>
                  {overrideType && (
                    <Button icon={<RotateCcw aria-hidden="true" />} variant="default" onClick={onReset}>
                      {t('icpRadar.resetToArtifact')}
                    </Button>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </header>
      <div className="icp-radar-tabs" aria-label={t('icpRadar.radarTabs')}>
        <button
          aria-pressed={activeTab === 'shortlist'}
          className={`criteria-chip${activeTab === 'shortlist' ? ' criteria-chip-active' : ''}`}
          type="button"
          onClick={() => onTabChange('shortlist')}
        >
          {t('icpRadar.shortlistTab')}
        </button>
        <button
          aria-pressed={activeTab === 'settings'}
          className={`criteria-chip${activeTab === 'settings' ? ' criteria-chip-active' : ''}`}
          type="button"
          onClick={() => onTabChange('settings')}
        >
          {t('icpRadar.settingsTab')}
        </button>
      </div>
    </div>
  );
}

function CandidateTable({
  artifact,
  expandedCandidateId,
  onOpenDetails,
  onToggleCandidate,
  radarId,
  signalValidation,
}: {
  artifact: ICPRadarArtifact;
  expandedCandidateId: string | null;
  onOpenDetails: (candidateId: string) => void;
  onToggleCandidate: (candidateId: string) => void;
  radarId: string;
  signalValidation: SignalValidationOverlay;
}) {
  const { t } = useTranslation();
  const candidates = useMemo(() => validatedCandidatesForArtifact(artifact, radarId, signalValidation), [artifact, radarId, signalValidation]);
  return (
    <Card>
      <div className="icp-radar-table-wrap" aria-label={t('icpRadar.tableAria')}>
        <div className="icp-radar-table">
          <div className="icp-radar-table-head">
            <span className="icp-sticky-cell">{t('icpRadar.columns.company')}</span>
            <span>{t('icpRadar.columns.total')}</span>
            <span>{t('icpRadar.columns.fit')}</span>
            <span>{t('icpRadar.columns.intent')}</span>
            <span>{t('icpRadar.columns.trigger')}</span>
            <span>{t('icpRadar.columns.tier')}</span>
            <span>{t('icpRadar.columns.evidence')}</span>
            <span>{t('icpRadar.columns.action')}</span>
          </div>
          {candidates.map(({ candidate, score }) => {
            const expanded = expandedCandidateId === candidate.account_id;
            const scoreDelta = score.effective_score.total_score - score.original_score.total_score;
            return (
              <div className="icp-candidate-record" key={candidate.account_id}>
                <button
                  aria-expanded={expanded}
                  className={`icp-candidate-row${expanded ? ' icp-candidate-row-selected' : ''}`}
                  type="button"
                  onClick={() => onToggleCandidate(candidate.account_id)}
                >
                  <span className="icp-company-cell icp-sticky-cell">
                    <span className="account-initials">{candidate.rank}</span>
                    <span>
                      <strong>{candidate.legal_name}</strong>
                      <small>{candidate.description}</small>
                    </span>
                  </span>
                  <span className="score-cell">
                    <span className="score-track">
                      <span className="score-fill" style={{ width: `${Math.min(100, score.effective_score.total_score * 2)}%` }} />
                    </span>
                    <Mono>{score.effective_score.total_score}</Mono>
                    {scoreDelta !== 0 && <span className="score-delta">{formatDelta(scoreDelta)}</span>}
                  </span>
                  <Mono>{score.effective_score.fit_score}</Mono>
                  <Mono>{score.effective_score.intent_score}</Mono>
                  <Mono>{score.effective_score.trigger_score}</Mono>
                  <span>
                    <Badge tone={score.effective_score.tier === 'Tier 1' ? 'ally' : 'neutral'}>{score.effective_score.tier}</Badge>
                  </span>
                  <Mono>{candidate.evidence_refs.length}</Mono>
                  <span className="row-action">
                    <span className="planned-action">{t('icpRadar.takeIntoWorkPlanned')}</span>
                    {expanded ? <ChevronDown aria-hidden="true" /> : <ChevronRight aria-hidden="true" />}
                  </span>
                </button>
                {expanded && (
                  <CandidatePreview
                    artifact={artifact}
                    candidate={candidate}
                    onOpenDetails={() => onOpenDetails(candidate.account_id)}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}

function EmptyShortlist({
  radar,
  onOpenSettings,
}: {
  radar: ICPRadarCatalogItem;
  onOpenSettings: () => void;
}) {
  const { t } = useTranslation();
  return (
    <Card>
      <div className="icp-empty-shortlist">
        <span className="section-icon">
          <Settings aria-hidden="true" />
        </span>
        <div>
          <Eyebrow>{t('icpRadar.emptyShortlistEyebrow')}</Eyebrow>
          <h2>{t('icpRadar.emptyShortlistTitle')}</h2>
          <p>{t('icpRadar.emptyShortlistCopy', { radarName: radar.name })}</p>
        </div>
        <Button icon={<Settings aria-hidden="true" />} variant="default" onClick={onOpenSettings}>
          {t('icpRadar.openSettings')}
        </Button>
      </div>
    </Card>
  );
}

function FixtureRadarCandidateDetailView({
  activeTab,
  artifact,
  candidate,
  onBack,
  onDecisionChange,
  onResetValidation,
  onTabChange,
  radarId,
  radarName,
  signalValidation,
  sourcesById,
  validatedScore,
}: {
  activeTab: CandidateDetailTab;
  artifact: ICPRadarArtifact;
  candidate: ICPRadarCandidate;
  onBack: () => void;
  onDecisionChange: (decision: SignalValidationDecision) => void;
  onResetValidation: () => void;
  onTabChange: (tab: CandidateDetailTab) => void;
  radarId: string;
  radarName: string;
  signalValidation: SignalValidationOverlay;
  sourcesById: Map<string, SourceDefinition>;
  validatedScore: ValidatedCandidateScore;
}) {
  const { t } = useTranslation();
  return (
    <section className="screen icp-radar-screen icp-detail-screen" aria-label={t('icpRadar.aria')}>
      <div className="icp-detail-sticky-header">
        <div className="icp-detail-breadcrumbs" aria-label={t('icpRadar.breadcrumbs')}>
          <Button icon={<ArrowLeft aria-hidden="true" />} variant="quiet" onClick={onBack}>
            {t('icpRadar.backToTable')}
          </Button>
          <span>{t('icpRadar.aria')}</span>
          <ChevronRight aria-hidden="true" />
          <span>{radarName}</span>
          <ChevronRight aria-hidden="true" />
          <strong>{candidate.legal_name}</strong>
        </div>

        <header className="icp-radar-header icp-detail-header">
          <span className="section-icon">
            <Target aria-hidden="true" />
          </span>
          <div>
            <Eyebrow>{t('icpRadar.detailEyebrow')}</Eyebrow>
            <h1>{candidate.legal_name}</h1>
            <p>{candidate.main_signal}</p>
          </div>
          <div className="icp-profile-meta">
            <Badge tone={validatedScore.effective_score.tier === 'Tier 1' ? 'ally' : 'neutral'}>{validatedScore.effective_score.tier}</Badge>
            <Mono>{t('icpRadar.total')} {validatedScore.effective_score.total_score}</Mono>
          </div>
        </header>
        <CandidateDetailTabs activeTab={activeTab} onTabChange={onTabChange} />
      </div>

      <div className="icp-candidate-detail-panel">
        {activeTab === 'overview' && (
          <Card>
            <CandidateScoreGrid candidate={candidate} validatedScore={validatedScore} />
            <CompanyContext candidate={candidate} />
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.canonicalDetail.mainInsight')}</Eyebrow>
              <p>{candidate.signal_summary || candidate.comment || candidate.main_signal}</p>
            </section>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.signalValidation')}</Eyebrow>
              <ValidationSummary score={validatedScore} />
              <Button icon={<RotateCcw aria-hidden="true" />} variant="default" onClick={onResetValidation}>
                {t('icpRadar.resetLocalValidation')}
              </Button>
            </section>
          </Card>
        )}

        {activeTab === 'qualification' && (
          <Card>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.canonicalDetail.qualification')}</Eyebrow>
              <div className="canonical-detail-table">
                {topCriteriaByCodes(artifact, candidate, fitSignalCodes, 10).map(({ criterion, value }) => (
                  <details className="canonical-detail-record" key={criterion.code}>
                    <summary>
                      <Mono>{criterion.code}</Mono>
                      <strong>{criterion.name}</strong>
                      <Mono>{value}</Mono>
                    </summary>
                    <p>{criterion.description}</p>
                    {candidate.criteria_evidence[criterion.code]?.facts.slice(0, 3).map((fact) => (
                      <div className="canonical-journal-row" key={`${criterion.code}-${fact.evidence_ref}`}>
                        <Mono>{fact.evidence_ref}</Mono>
                        <strong>{fact.fact}</strong>
                        <small>{fact.why_it_matters}</small>
                      </div>
                    ))}
                  </details>
                ))}
              </div>
            </section>
          </Card>
        )}

        {activeTab === 'signals' && (
          <Card>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.canonicalDetail.signals')}</Eyebrow>
              <CriteriaBreakdown
                artifact={artifact}
                candidate={candidate}
                radarId={radarId}
                signalValidation={signalValidation}
                validatedScore={validatedScore}
                onDecisionChange={onDecisionChange}
              />
            </section>
          </Card>
        )}

        {activeTab === 'sources' && (
          <Card>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.canonicalDetail.sources')}</Eyebrow>
              <EvidenceList candidate={candidate} sourcesById={sourcesById} />
              <SourceUrlList candidate={candidate} />
            </section>
          </Card>
        )}

        {activeTab === 'journal' && (
          <Card>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.canonicalDetail.journal')}</Eyebrow>
              <dl className="icp-definition-list">
                <div>
                  <dt>{t('icpRadar.live.runtime')}</dt>
                  <dd>{artifact.workflow_metadata.workflow_name}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.live.sources')}</dt>
                  <dd>{artifact.workflow_metadata.source_count}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.criteria')}</dt>
                  <dd>{artifact.workflow_metadata.criteria_count}</dd>
                </div>
              </dl>
              <p>{t('icpRadar.canonicalDetail.fixtureJournalCopy')}</p>
            </section>
          </Card>
        )}
      </div>
    </section>
  );
}

function LiveRadarShortlistTable({
  artifact,
  expandedCandidateId,
  onOpenDetails,
  onOpenSettings,
  onToggleCandidate,
}: {
  artifact: LiveICPRadarRunArtifact | null;
  expandedCandidateId: string | null;
  onOpenDetails: (candidateId: string) => void;
  onOpenSettings: () => void;
  onToggleCandidate: (candidateId: string) => void;
}) {
  const { t } = useTranslation();

  if (!artifact) {
    return (
      <Card>
        <div className="icp-empty-shortlist live-radar-empty">
          <span className="section-icon">
            <Radar aria-hidden="true" />
          </span>
          <div>
            <Eyebrow>{t('icpRadar.live.emptyEyebrow')}</Eyebrow>
            <h2>{t('icpRadar.live.emptyTitle')}</h2>
            <p>{t('icpRadar.live.emptyCopy')}</p>
            <code>python -m power_web_os.demo run-live-mini-icp-radar --live</code>
          </div>
          <Button icon={<Settings aria-hidden="true" />} variant="default" onClick={onOpenSettings}>
            {t('icpRadar.openSettings')}
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <>
      {artifact.candidates.length === 0 ? (
        <Card>
          <div className="icp-empty-shortlist">
            <span className="section-icon">
              <ShieldCheck aria-hidden="true" />
            </span>
            <div>
              <Eyebrow>{t('icpRadar.live.noCandidatesEyebrow')}</Eyebrow>
              <h2>{t('icpRadar.live.noCandidatesTitle')}</h2>
              <p>{t('icpRadar.live.noCandidatesCopy')}</p>
            </div>
          </div>
        </Card>
      ) : (
        <Card>
          <div className="icp-radar-table-wrap" aria-label={t('icpRadar.live.tableAria')}>
            <div className="icp-radar-table icp-radar-table-live">
              <div className="icp-radar-table-head">
                <span className="icp-sticky-cell">{t('icpRadar.columns.company')}</span>
                <span>{t('icpRadar.columns.total')}</span>
                <span>{t('icpRadar.columns.fit')}</span>
                <span>{t('icpRadar.columns.intent')}</span>
                <span>{t('icpRadar.columns.trigger')}</span>
                <span>{t('icpRadar.columns.tier')}</span>
                <span>{t('icpRadar.columns.evidence')}</span>
                <span>{t('icpRadar.columns.action')}</span>
              </div>
              {artifact.candidates.map((candidate, index) => {
                const expanded = expandedCandidateId === candidate.candidate_id;
                return (
                  <div className="icp-candidate-record" key={candidate.candidate_id}>
                    <button
                      aria-expanded={expanded}
                      className={`icp-candidate-row${expanded ? ' icp-candidate-row-selected' : ''}`}
                      type="button"
                      onClick={() => onToggleCandidate(candidate.candidate_id)}
                    >
                      <span className="icp-company-cell icp-sticky-cell">
                        <span className="account-initials">{index + 1}</span>
                        <span>
                          <strong>{candidate.legal_name}</strong>
                          <small>{candidate.description || t('icpRadar.live.noDescription')}</small>
                        </span>
                      </span>
                      <span className="score-cell">
                        <span className="score-track">
                          <span className="score-fill" style={{ width: `${Math.min(100, liveTotalScore(candidate) * 10)}%` }} />
                        </span>
                        <Mono>{liveTotalScore(candidate)}</Mono>
                      </span>
                      <Mono>{candidate.score.fit_score}</Mono>
                      <Mono>{candidate.score.intent_score}</Mono>
                      <Mono>{t('icpRadar.notAvailable')}</Mono>
                      <span>
                        <Badge tone={candidate.score.tier === 'Tier 1' ? 'ally' : 'neutral'}>{candidate.score.tier}</Badge>
                      </span>
                      <Mono>{candidate.evidence_refs.length}</Mono>
                      <span className="row-action">
                        <span className="planned-action">{t('icpRadar.takeIntoWorkPlanned')}</span>
                        {expanded ? <ChevronDown aria-hidden="true" /> : <ChevronRight aria-hidden="true" />}
                      </span>
                    </button>
                    {expanded && (
                      <LiveRadarCandidatePreview
                        candidate={candidate}
                        onOpenDetails={() => onOpenDetails(candidate.candidate_id)}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </Card>
      )}
    </>
  );
}

function LiveRadarCandidatePreview({
  candidate,
  onOpenDetails,
}: {
  candidate: LiveRadarCandidate;
  onOpenDetails: () => void;
}) {
  const { t } = useTranslation();
  const topSignals = candidate.signals.filter((item) => item.status !== 'not_observed').slice(0, 5);
  return (
    <div className="icp-candidate-preview">
      <div className="icp-preview-body">
        <header className="icp-preview-heading">
          <div>
            <Eyebrow>{t('icpRadar.previewEyebrow')}</Eyebrow>
            <strong>{candidate.legal_name}</strong>
          </div>
        </header>
        <div className="icp-preview-main">
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.canonicalPreview.summary')}</Eyebrow>
            <p>{candidate.description || t('icpRadar.live.noDescription')}</p>
          </section>
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.canonicalPreview.tier')}</Eyebrow>
            <p>{t('icpRadar.live.tierExplanation', {
              fit: candidate.score.fit_score,
              intent: candidate.score.intent_score,
              tier: candidate.score.tier,
            })}</p>
          </section>
        </div>
        <div className="icp-preview-lists">
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.canonicalPreview.qualification')}</Eyebrow>
            <div className="criteria-list criteria-list-compact">
              {candidate.qualification.slice(0, 5).map((item) => (
                <div className="criterion-row" key={item.criterion_code}>
                  <Mono>{item.criterion_code}</Mono>
                  <span>
                    <strong>{item.criterion}</strong>
                  </span>
                  <Badge tone={liveQualificationTone(item.status)}>{t(`icpRadar.live.qualificationStatus.${item.status}`)}</Badge>
                </div>
              ))}
            </div>
          </section>
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.canonicalPreview.signals')}</Eyebrow>
            <div className="criteria-list criteria-list-compact">
              {(topSignals.length ? topSignals : candidate.signals.slice(0, 5)).map((item) => (
                <div className="criterion-row" key={item.signal_code}>
                  <Mono>{item.signal_code}</Mono>
                  <span>
                    <strong>{item.signal}</strong>
                    <small>{item.summary}</small>
                  </span>
                  <Mono>{item.score}</Mono>
                </div>
              ))}
            </div>
          </section>
        </div>
        <div className="icp-preview-actions">
          <Button icon={<ArrowRight aria-hidden="true" />} variant="default" onClick={onOpenDetails}>
            {t('icpRadar.openDetails')}
          </Button>
        </div>
      </div>
    </div>
  );
}

function LiveRadarCandidateDetailView({
  activeTab,
  artifact,
  candidate,
  onBack,
  onTabChange,
  radarName,
}: {
  activeTab: CandidateDetailTab;
  artifact: LiveICPRadarRunArtifact;
  candidate: LiveRadarCandidate;
  onBack: () => void;
  onTabChange: (tab: CandidateDetailTab) => void;
  radarName: string;
}) {
  const { t } = useTranslation();
  const sourcesByRef = useMemo(() => new Map(artifact.sources.map((source) => [source.evidence_ref, source])), [artifact.sources]);
  const usedSources = candidate.evidence_refs.map((ref) => sourcesByRef.get(ref)).filter((source): source is LiveRadarSourceEvidence => Boolean(source));
  return (
    <section className="screen icp-radar-screen icp-detail-screen" aria-label={t('icpRadar.aria')}>
      <div className="icp-detail-sticky-header">
        <div className="icp-detail-breadcrumbs" aria-label={t('icpRadar.breadcrumbs')}>
          <Button icon={<ArrowLeft aria-hidden="true" />} variant="quiet" onClick={onBack}>
            {t('icpRadar.backToTable')}
          </Button>
          <span>{t('icpRadar.aria')}</span>
          <ChevronRight aria-hidden="true" />
          <span>{radarName}</span>
          <ChevronRight aria-hidden="true" />
          <strong>{candidate.legal_name}</strong>
        </div>

        <header className="icp-radar-header icp-detail-header">
          <span className="section-icon">
            <Radar aria-hidden="true" />
          </span>
          <div>
            <Eyebrow>{t('icpRadar.live.detailEyebrow')}</Eyebrow>
            <h1>{candidate.legal_name}</h1>
            <p>{candidate.description || t('icpRadar.live.noDescription')}</p>
          </div>
          <div className="icp-profile-meta">
            <Badge tone={candidate.score.tier === 'Tier 1' ? 'ally' : 'neutral'}>{candidate.score.tier}</Badge>
            <Mono>{t('icpRadar.fit')} {candidate.score.fit_score}</Mono>
            <Mono>{t('icpRadar.intent')} {candidate.score.intent_score}</Mono>
          </div>
        </header>
        <CandidateDetailTabs activeTab={activeTab} onTabChange={onTabChange} />
      </div>

      <div className="icp-candidate-detail-panel">
        {activeTab === 'overview' && (
          <Card>
            <div className="icp-score-grid">
              <ScoreBox label={t('icpRadar.total')} value={liveTotalScore(candidate)} />
              <ScoreBox label={t('icpRadar.fit')} value={candidate.score.fit_score} />
              <ScoreBox label={t('icpRadar.intent')} value={candidate.score.intent_score} />
              <ScoreBox label={t('icpRadar.live.sources')} value={candidate.evidence_refs.length} />
            </div>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.canonicalDetail.mainInsight')}</Eyebrow>
              <p>{candidate.description || t('icpRadar.live.noDescription')}</p>
            </section>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.companyContext')}</Eyebrow>
              <dl className="icp-definition-list">
                <div>
                  <dt>{t('icpRadar.canonicalDetail.legalName')}</dt>
                  <dd>{candidate.legal_name}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.inn')}</dt>
                  <dd>{t('icpRadar.unknown')}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.revenue')}</dt>
                  <dd>{t('icpRadar.unknown')}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.canonicalDetail.affiliation')}</dt>
                  <dd>{candidate.qualification.find((item) => item.criterion_code === 'Q1')?.status === 'confirmed'
                    ? t('icpRadar.live.siburAffiliation')
                    : t('icpRadar.unknown')}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.canonicalDetail.foundAt')}</dt>
                  <dd>{artifact.run_metadata.run_at}</dd>
                </div>
              </dl>
            </section>
          </Card>
        )}

        {activeTab === 'qualification' && (
          <Card>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.live.qualification')}</Eyebrow>
              <div className="canonical-detail-table">
                {candidate.qualification.map((item) => (
                  <details className="canonical-detail-record" key={item.criterion_code}>
                    <summary>
                      <Mono>{item.criterion_code}</Mono>
                      <strong>{item.criterion}</strong>
                      <Badge tone={liveQualificationTone(item.status)}>
                        {t(`icpRadar.live.qualificationStatus.${item.status}`)}
                      </Badge>
                    </summary>
                    <span>
                      <p>{item.rationale}</p>
                      <LiveEvidenceList refs={item.evidence_refs} sourcesByRef={sourcesByRef} compact />
                    </span>
                  </details>
                ))}
              </div>
            </section>
          </Card>
        )}

        {activeTab === 'signals' && (
          <Card>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.live.signals')}</Eyebrow>
              <div className="canonical-detail-table">
                {candidate.signals.map((item) => (
                  <details className="canonical-detail-record" key={item.signal_code}>
                    <summary>
                      <Mono>{item.signal_code}</Mono>
                      <strong>{item.signal}</strong>
                      <span className="live-radar-score">
                        <Mono>{item.score}</Mono>
                        <Badge tone={liveSignalTone(item.status)}>
                          {t(`icpRadar.live.signalStatus.${item.status}`)}
                        </Badge>
                      </span>
                    </summary>
                    <span>
                      <p>{item.summary}</p>
                      <LiveEvidenceList refs={item.evidence_refs} sourcesByRef={sourcesByRef} compact />
                    </span>
                  </details>
                ))}
              </div>
            </section>
          </Card>
        )}

        {activeTab === 'sources' && (
          <Card>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.live.evidence')}</Eyebrow>
              <LiveSourceSummary sources={usedSources} />
            </section>
          </Card>
        )}

        {activeTab === 'journal' && (
          <Card>
            <section className="icp-detail-section">
              <Eyebrow>{t('icpRadar.canonicalDetail.journal')}</Eyebrow>
              <dl className="icp-definition-list">
                <div>
                  <dt>{t('icpRadar.live.runtime')}</dt>
                  <dd>{t(liveRuntimeKey(artifact.run_metadata.runtime))}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.live.model')}</dt>
                  <dd>{artifact.run_metadata.model ?? t('icpRadar.unknown')}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.live.webMode')}</dt>
                  <dd>{artifact.run_metadata.web_mode ?? t('icpRadar.unknown')}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.live.queries')}</dt>
                  <dd>{artifact.run_metadata.query_count}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.live.sources')}</dt>
                  <dd>{artifact.run_metadata.source_count}</dd>
                </div>
                <div>
                  <dt>{t('icpRadar.canonicalDetail.runAt')}</dt>
                  <dd>{artifact.run_metadata.run_at}</dd>
                </div>
              </dl>
              <div className="canonical-journal-list">
                {artifact.search_plan.queries.map((query) => (
                  <div className="canonical-journal-row" key={query.query_id}>
                    <Mono>{query.query_id}</Mono>
                    <strong>{query.query}</strong>
                    <small>{query.purpose}</small>
                  </div>
                ))}
              </div>
              {candidate.review_flags.length > 0 && (
                <div className="badge-list">
                  {candidate.review_flags.map((flag) => (
                    <Badge key={flag} tone="unsurfaced">{flag}</Badge>
                  ))}
                </div>
              )}
            </section>
          </Card>
        )}
      </div>
    </section>
  );
}

function LiveEvidenceList({
  compact = false,
  refs,
  sourcesByRef,
}: {
  compact?: boolean;
  refs: string[];
  sourcesByRef: Map<string, LiveRadarSourceEvidence>;
}) {
  return (
    <div className={`live-radar-source-list${compact ? ' icp-evidence-list-compact' : ''}`}>
      {refs.map((ref) => {
        const source = sourcesByRef.get(ref);
        return (
          <a href={source?.url ?? '#'} key={ref} rel="noreferrer" target="_blank">
            <ShieldCheck aria-hidden="true" />
            <span>
              <strong>{source?.title ?? ref}</strong>
              <small>{source?.snippet ?? ref}</small>
            </span>
            {source?.url && <ExternalLink aria-hidden="true" />}
          </a>
        );
      })}
    </div>
  );
}

function LiveSourceSummary({ sources }: { sources: LiveRadarSourceEvidence[] }) {
  const { t } = useTranslation();
  if (!sources.length) {
    return <p>{t('icpRadar.unknown')}</p>;
  }
  return (
    <div className="source-table-wrap">
      <table className="source-table">
        <thead>
          <tr>
            <th>{t('icpRadar.settings.sourceNumber')}</th>
            <th>{t('icpRadar.settings.sourceLabel')}</th>
            <th>{t('icpRadar.settings.sourceType')}</th>
            <th>{t('icpRadar.settings.sourceReference')}</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((source, index) => (
            <tr key={source.evidence_ref}>
              <td><Mono>{index + 1}</Mono></td>
              <td>
                <strong>{source.title}</strong>
                <small>{source.snippet}</small>
              </td>
              <td>{source.source_type}</td>
              <td>
                <a href={source.url} rel="noreferrer" target="_blank">{source.url}</a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RadarSettings({
  dirty,
  draft,
  editingBlock,
  onCancel,
  onDraftChange,
  onEdit,
  onSave,
  validationErrors,
}: {
  dirty: boolean;
  draft: EditableRadarDefinitionDraft;
  editingBlock: SettingsBlockId | null;
  onCancel: () => void;
  onDraftChange: (draft: EditableRadarDefinitionDraft) => void;
  onEdit: (block: SettingsBlockId | null) => void;
  onSave: () => void;
  validationErrors: string[];
}) {
  const { t } = useTranslation();
  const editorState: RadarEditorState = {
    mode: editingBlock ? 'edit' : 'view',
    dirty,
    errors: validationErrors,
  };

  return (
    <div className="icp-settings-stack">
      {editorState.dirty && (
        <div className="icp-editor-errors" role="status">
          <span>{t('icpRadar.unsavedChanges')}</span>
        </div>
      )}
      {editorState.errors.length > 0 && (
        <div className="icp-editor-errors" role="alert">
          {editorState.errors.map((error) => <span key={error}>{error}</span>)}
        </div>
      )}

      <div className="icp-settings-grid">
        <SettingsBlockCard
          blockId="global_search"
          editingBlock={editingBlock}
          headerAction={<AiSuggestButton />}
          onCancel={onCancel}
          onEdit={onEdit}
          onSave={onSave}
          title={t('icpRadar.settings.globalSearch')}
        >
          {editingBlock === 'global_search' ? (
            <GlobalSearchEditor draft={draft} onDraftChange={onDraftChange} />
          ) : (
            <GlobalSearchSummary definition={draft} />
          )}
        </SettingsBlockCard>

        <SettingsBlockCard
          blockId="qualification"
          editingBlock={editingBlock}
          headerAction={<AiSuggestButton />}
          onCancel={onCancel}
          onEdit={onEdit}
          onSave={onSave}
          title={t('icpRadar.settings.qualificationRules')}
        >
          {editingBlock === 'qualification' ? (
            <QualificationRulesEditor
              group={draft.account_qualification.rule_group}
              globalSources={draft.global_search_policy.sources}
              onChange={(rule_group) => onDraftChange({ ...draft, account_qualification: { rule_group } })}
            />
          ) : (
            <RuleGroupSummary group={draft.account_qualification.rule_group} />
          )}
        </SettingsBlockCard>

        <SettingsBlockCard
          blockId="monitoring"
          editingBlock={editingBlock}
          onCancel={onCancel}
          onEdit={onEdit}
          onSave={onSave}
          title={t('icpRadar.settings.monitoring')}
        >
          {editingBlock === 'monitoring' ? (
            <MonitoringEditor draft={draft} onDraftChange={onDraftChange} />
          ) : (
            <MonitoringSummary definition={draft} />
          )}
        </SettingsBlockCard>

        <SettingsBlockCard
          blockId="signal_scale"
          editingBlock={editingBlock}
          onCancel={onCancel}
          onEdit={onEdit}
          onSave={onSave}
          title={t('icpRadar.settings.signalScale')}
        >
          {editingBlock === 'signal_scale' ? (
            <SignalScaleEditor draft={draft} onDraftChange={onDraftChange} />
          ) : (
            <SignalScaleSummary definition={draft} />
          )}
        </SettingsBlockCard>

        <SettingsBlockCard
          blockId="intent_signals"
          editingBlock={editingBlock}
          onCancel={onCancel}
          onEdit={onEdit}
          onSave={onSave}
          title={t('icpRadar.settings.intentSignals')}
        >
          {editingBlock === 'intent_signals' ? (
            <IntentSignalsEditor draft={draft} onDraftChange={onDraftChange} />
          ) : (
            <IntentSignalsSummary definition={draft} />
          )}
        </SettingsBlockCard>

        <SettingsBlockCard
          blockId="scoring"
          editingBlock={editingBlock}
          onCancel={onCancel}
          onEdit={onEdit}
          onSave={onSave}
          title={t('icpRadar.settings.scoring')}
        >
          {editingBlock === 'scoring' ? (
            <ScoringModelEditor draft={draft} onDraftChange={onDraftChange} />
          ) : (
            <ScoringModelSummary definition={draft} />
          )}
        </SettingsBlockCard>

        <SettingsBlockCard
          blockId="validation"
          editingBlock={editingBlock}
          onCancel={onCancel}
          onEdit={onEdit}
          onSave={onSave}
          title={t('icpRadar.settings.validation')}
        >
          <ValidationReportView report={draft.validation_report} />
        </SettingsBlockCard>
      </div>
    </div>
  );
}

type SettingsBlockId = 'overview' | 'global_search' | 'qualification' | 'monitoring' | 'signal_scale' | 'intent_signals' | 'scoring' | 'validation';

function SettingsBlockCard({
  blockId,
  children,
  editingBlock,
  headerAction,
  onCancel,
  onEdit,
  onSave,
  title,
}: {
  blockId: SettingsBlockId;
  children: ReactNode;
  editingBlock: SettingsBlockId | null;
  headerAction?: ReactNode;
  onCancel: () => void;
  onEdit: (block: SettingsBlockId | null) => void;
  onSave: () => void;
  title: string;
}) {
  const { t } = useTranslation();
  const editing = editingBlock === blockId;
  return (
    <Card>
      <div className="icp-settings-section">
        <div className="icp-settings-section-head">
          <Eyebrow>{title}</Eyebrow>
          {blockId !== 'validation' && (
            <div className="icp-editor-actions">
              {headerAction}
              {editing ? (
                <>
                  <Button icon={<Save aria-hidden="true" />} variant="default" onClick={onSave}>
                    {t('icpRadar.saveDraft')}
                  </Button>
                  <Button icon={<X aria-hidden="true" />} variant="default" onClick={onCancel}>
                    {t('icpRadar.discardChanges')}
                  </Button>
                </>
              ) : (
                <Button icon={<SlidersHorizontal aria-hidden="true" />} variant="default" onClick={() => onEdit(blockId)}>
                  {t('icpRadar.editSettings')}
                </Button>
              )}
            </div>
          )}
        </div>
        {children}
      </div>
    </Card>
  );
}

function AiSuggestButton() {
  const { t } = useTranslation();
  return (
    <Button disabled icon={<Sparkles aria-hidden="true" />} variant="default">
      {t('icpRadar.settings.aiSuggest')}
    </Button>
  );
}

function RadarHeaderEditor({
  draft,
  onDraftChange,
}: {
  draft: EditableRadarDefinitionDraft;
  onDraftChange: (draft: EditableRadarDefinitionDraft) => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="icp-settings-header-editor">
      <TextField label={t('icpRadar.settings.radarName')} value={draft.metadata.name} onChange={(name) => onDraftChange({ ...draft, metadata: { ...draft.metadata, name } })} />
      <TextAreaField label={t('icpRadar.settings.description')} value={draft.metadata.description} onChange={(description) => onDraftChange({ ...draft, metadata: { ...draft.metadata, description } })} />
      <div className="icp-radar-header-meta-row">
        <ToggleField
          checked={draft.metadata.status === 'active'}
          label={t('icpRadar.settings.activeStatus')}
          onChange={(active) => onDraftChange({ ...draft, metadata: { ...draft.metadata, status: active ? 'active' : 'configured' } })}
        />
        <span>{t('icpRadar.cardFields.owner')}: {draft.metadata.owner}</span>
      </div>
    </div>
  );
}

function GlobalSearchSummary({ definition }: { definition: RadarDefinition }) {
  const { t } = useTranslation();
  return (
    <>
      <div className="icp-search-policy-grid">
        <ListSection bounded title={t('icpRadar.settings.keywords')} items={definition.global_search_policy.keywords} />
        <ListSection bounded title={t('icpRadar.settings.exclusions')} items={definition.global_search_policy.exclusions} />
      </div>
      <SourceTable sources={definition.global_search_policy.sources} />
      <div className="policy-switch-strip policy-switch-strip-end">
        <ToggleField
          checked={definition.global_search_policy.allow_system_sources}
          disabled
          label={t('icpRadar.settings.systemSources')}
          onChange={() => undefined}
        />
      </div>
    </>
  );
}

function GlobalSearchEditor({
  draft,
  onDraftChange,
}: {
  draft: EditableRadarDefinitionDraft;
  onDraftChange: (draft: EditableRadarDefinitionDraft) => void;
}) {
  const { t } = useTranslation();
  const policy = draft.global_search_policy;
  function updatePolicy(patch: Partial<EditableRadarDefinitionDraft['global_search_policy']>) {
    onDraftChange({ ...draft, global_search_policy: { ...policy, ...patch } });
  }
  return (
    <div className="criteria-editor-list">
      <ArrayTextAreaField label={t('icpRadar.settings.keywords')} value={policy.keywords} onChange={(keywords) => updatePolicy({ keywords })} />
      <ArrayTextAreaField label={t('icpRadar.settings.exclusions')} value={policy.exclusions} onChange={(exclusions) => updatePolicy({ exclusions })} />
      <SourceListEditor
        sources={policy.sources}
        onChange={(sources) => updatePolicy({ sources })}
      />
      <div className="policy-switch-strip policy-switch-strip-end">
        <ToggleField
          checked={policy.allow_system_sources}
          label={t('icpRadar.settings.systemSources')}
          onChange={(allow_system_sources) => updatePolicy({ allow_system_sources })}
        />
      </div>
    </div>
  );
}

function SourceTable({ sources }: { sources: SourceDefinition[] }) {
  const { t } = useTranslation();
  return (
    <div className="source-table-wrap">
      <table className="source-table">
        <thead>
          <tr>
            <th>{t('icpRadar.settings.sourceNumber')}</th>
            <th>{t('icpRadar.settings.sourceLabel')}</th>
            <th>{t('icpRadar.settings.sourceType')}</th>
            <th>{t('icpRadar.settings.trustLevel')}</th>
            <th>{t('icpRadar.settings.sourceReference')}</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((source, index) => (
            <tr key={source.source_id}>
              <td><Mono>{index + 1}</Mono></td>
              <td><strong>{source.label}</strong></td>
              <td>{t(sourceTypeKey(source.source_type))}</td>
              <td><Badge tone={trustPolicyTone(source.trust_level)}>{t(trustPolicyKey(source.trust_level))}</Badge></td>
              <td><span className="source-reference-cell">{source.reference}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SourceListEditor({
  onChange,
  sources,
}: {
  onChange: (sources: SourceDefinition[]) => void;
  sources: SourceDefinition[];
}) {
  const { t } = useTranslation();
  return (
    <div className="source-list-editor">
      {sources.map((source, index) => (
        <div className="source-editor-row" key={`${source.source_id || 'source'}-${index}`}>
          <SelectField label={t('icpRadar.settings.sourceType')} options={['url', 'search_engine', 'api', 'mcp', 'manual_dataset']} value={source.source_type} onChange={(source_type) => onChange(replaceAt(sources, index, { ...source, source_type }))} optionLabel={(option) => t(sourceTypeKey(option))} />
          <TextField label={t('icpRadar.settings.sourceLabel')} value={source.label} onChange={(label) => onChange(replaceAt(sources, index, { ...source, label }))} />
          <TextField label={t('icpRadar.settings.sourceReference')} value={source.reference} onChange={(reference) => onChange(replaceAt(sources, index, { ...source, reference }))} />
          <SelectField label={t('icpRadar.settings.trustLevel')} options={['trusted', 'cross_check', 'hitl_required']} value={trustPolicyValue(source.trust_level)} onChange={(trust_level) => onChange(replaceAt(sources, index, { ...source, trust_level }))} optionLabel={(option) => t(trustPolicyKey(option))} />
          <Button icon={<X aria-hidden="true" />} variant="default" onClick={() => onChange(sources.filter((_, currentIndex) => currentIndex !== index))}>
            {t('icpRadar.settings.remove')}
          </Button>
        </div>
      ))}
      <Button icon={<Plus aria-hidden="true" />} variant="default" onClick={() => onChange([...sources, newSourceDefinition()])}>
        {t('icpRadar.settings.addSource')}
      </Button>
    </div>
  );
}

function RuleGroupSummary({ group }: { group: RuleGroup }) {
  const { t } = useTranslation();
  return (
    <div className="settings-table qualification-table">
      <div className="settings-table-head">
        <span>{t('icpRadar.settings.operator')}</span>
        <span>{t('icpRadar.settings.rule')}</span>
        <span>{t('icpRadar.settings.sources')}</span>
        <span>{t('icpRadar.settings.crossValidationShort')}</span>
        <span>{t('icpRadar.settings.additionalSourcesShort')}</span>
        <span>{t('icpRadar.settings.requirement')}</span>
      </div>
      {group.rules.map((rule) => (
        <div className="settings-table-row simple-rule-row" key={rule.rule_id}>
          <Mono>{ruleOperatorLabel(group.operator, rule)}</Mono>
          <span>
            <strong>{rule.description || t('icpRadar.settings.rule')}</strong>
            <small>{rule.rule_id}</small>
          </span>
          <span>{sourcePolicySummary(rule.source_policy, t)}</span>
          <BooleanPill active={rule.source_policy.source_logic === 'AND'} />
          <BooleanPill active={rule.source_policy.allow_additional_sources} />
          <Badge tone={rule.requirement_level === 'required' ? 'ally' : 'neutral'}>{t(requirementKey(rule.requirement_level))}</Badge>
        </div>
      ))}
    </div>
  );
}

function QualificationRulesEditor({
  globalSources,
  group,
  onChange,
}: {
  globalSources: SourceDefinition[];
  group: RuleGroup;
  onChange: (group: RuleGroup) => void;
}) {
  const { t } = useTranslation();
  function updateRule(index: number, nextRule: AtomicRule) {
    onChange({ ...group, rules: replaceAt(group.rules, index, nextRule), groups: [] });
  }
  return (
    <div className="criteria-editor-list">
      <div className="icp-section-toolbar">
        <SelectField
          label={t('icpRadar.settings.logicalOperator')}
          options={['AND', 'OR']}
          value={group.operator === 'OR' ? 'OR' : 'AND'}
          onChange={(operator) => onChange({ ...group, operator, groups: [] })}
          optionLabel={(option) => t(logicalOperatorKey(option))}
        />
      </div>
      {group.rules.map((rule, index) => (
        <SimpleRuleEditor
          globalSources={globalSources}
          key={`${rule.rule_id || 'rule'}-${index}`}
          rule={rule}
          onChange={(nextRule) => updateRule(index, nextRule)}
          onRemove={() => onChange({ ...group, rules: group.rules.filter((_, currentIndex) => currentIndex !== index) })}
        />
      ))}
      <Button icon={<Plus aria-hidden="true" />} variant="default" onClick={() => onChange({ ...group, rules: [...group.rules, newAtomicRule()] })}>
        {t('icpRadar.settings.addRule')}
      </Button>
    </div>
  );
}

function SimpleRuleEditor({
  globalSources,
  onChange,
  onRemove,
  rule,
}: {
  globalSources: SourceDefinition[];
  onChange: (rule: AtomicRule) => void;
  onRemove: () => void;
  rule: AtomicRule;
}) {
  const { t } = useTranslation();
  return (
    <div className="criteria-editor-row">
      <div className="generated-code-row">
        <Mono>{rule.rule_id || t('icpRadar.settings.rule')}</Mono>
        <small>{t('icpRadar.settings.generatedIdReadonly')}</small>
      </div>
      <div className="simple-rule-editor-main">
        <ToggleField
          checked={isNotRule(rule)}
          label={t('icpRadar.settings.notRule')}
          onChange={(checked) => onChange({ ...rule, generated_comparison_operator: checked ? 'not_equals' : '' })}
        />
        <TextAreaField label={t('icpRadar.settings.ruleDescription')} value={rule.description} onChange={(description) => onChange({ ...rule, description })} />
        <SelectField label={t('icpRadar.settings.requirement')} options={['required', 'recommended']} value={rule.requirement_level} onChange={(requirement_level) => onChange({ ...rule, requirement_level })} optionLabel={(option) => t(requirementKey(option))} />
      </div>
      <SimpleSourcePolicyEditor globalSources={globalSources} policy={rule.source_policy} onChange={(source_policy) => onChange({ ...rule, source_policy })} />
      <Button icon={<X aria-hidden="true" />} variant="default" onClick={onRemove}>
        {t('icpRadar.settings.remove')}
      </Button>
    </div>
  );
}

function SimpleSourcePolicyEditor({
  globalSources,
  onChange,
  policy,
}: {
  globalSources: SourceDefinition[];
  onChange: (policy: SourcePolicy) => void;
  policy: SourcePolicy;
}) {
  const { t } = useTranslation();
  return (
    <div className="source-policy-editor">
      <div className="policy-switch-strip">
        <ToggleField checked={policy.use_global_search_policy} label={t('icpRadar.settings.useGlobalSearchPolicy')} onChange={(use_global_search_policy) => onChange({ ...policy, use_global_search_policy })} />
        <ToggleField
          checked={policy.source_logic === 'AND'}
          label={t('icpRadar.settings.crossValidation')}
          onChange={(checked) => onChange({ ...policy, source_logic: checked ? 'AND' : 'OR' })}
        />
        <ToggleField
          checked={policy.allow_additional_sources}
          label={t('icpRadar.settings.hitlAdditionalSources')}
          onChange={(allow_additional_sources) => onChange({ ...policy, allow_additional_sources, fallback_confidence: allow_additional_sources ? 'hitl_required' : 'trusted' })}
        />
      </div>
      {policy.use_global_search_policy && (
        <small>{t('icpRadar.settings.globalSearchPolicyCopy', { count: globalSources.length })}</small>
      )}
      <SourceListEditor
        sources={policy.local_sources ?? []}
        onChange={(local_sources) => onChange({ ...policy, local_sources })}
      />
    </div>
  );
}

function MonitoringSummary({ definition }: { definition: RadarDefinition }) {
  const { t } = useTranslation();
  return (
    <dl className="icp-definition-list">
      <Metric label={t('icpRadar.cardFields.cadence')} value={t(cadenceKey(definition.monitoring_policy.cadence))} />
      <Metric label={t('icpRadar.settings.lookbackWindow')} value={definition.monitoring_policy.lookback_window} />
      <Metric label={t('icpRadar.cardFields.runMode')} value={t(runModeKey(definition.monitoring_policy.run_mode))} />
      <Metric label={t('icpRadar.settings.deduplication')} value={definition.monitoring_policy.deduplication} />
      <Metric label={t('icpRadar.settings.staleAfter')} value={definition.monitoring_policy.stale_after} />
    </dl>
  );
}

function MonitoringEditor({
  draft,
  onDraftChange,
}: {
  draft: EditableRadarDefinitionDraft;
  onDraftChange: (draft: EditableRadarDefinitionDraft) => void;
}) {
  const { t } = useTranslation();
  const policy = draft.monitoring_policy;
  function updatePolicy(patch: Partial<EditableRadarDefinitionDraft['monitoring_policy']>) {
    onDraftChange({ ...draft, monitoring_policy: { ...policy, ...patch } });
  }
  return (
    <div className="criteria-editor-list">
      <SelectField label={t('icpRadar.cardFields.cadence')} options={['weekly', 'monthly']} value={policy.cadence} onChange={(cadence) => updatePolicy({ cadence })} optionLabel={(option) => t(cadenceKey(option))} />
      <DurationField label={t('icpRadar.settings.lookbackWindow')} value={policy.lookback_window} onChange={(lookback_window) => updatePolicy({ lookback_window })} />
      <SelectField label={t('icpRadar.cardFields.runMode')} options={['incremental_signal_monitoring', 'configured_not_generated', 'fixture_import']} value={policy.run_mode} onChange={(run_mode) => updatePolicy({ run_mode })} optionLabel={(option) => t(runModeKey(option))} />
      <SelectField label={t('icpRadar.settings.deduplication')} options={['source_url', 'source_url_and_signal', 'normalized_fact', 'none']} value={deduplicationValue(policy.deduplication)} onChange={(deduplication) => updatePolicy({ deduplication })} optionLabel={(option) => t(deduplicationKey(option))} />
      <DurationField label={t('icpRadar.settings.staleAfter')} value={policy.stale_after} onChange={(stale_after) => updatePolicy({ stale_after })} />
    </div>
  );
}

function IntentSignalsSummary({ definition }: { definition: RadarDefinition }) {
  const { t } = useTranslation();
  const globalRubric = globalSignalRubric(definition);
  return (
    <div className="settings-table intent-signal-table">
      <div className="settings-table-head">
        <span>{t('icpRadar.settings.signalCode')}</span>
        <span>{t('icpRadar.settings.signalDetection')}</span>
        <span>{t('icpRadar.settings.sources')}</span>
        <span>{t('icpRadar.settings.crossValidationShort')}</span>
        <span>{t('icpRadar.settings.additionalSourcesShort')}</span>
        <span>{t('icpRadar.settings.scaleOverrideShort')}</span>
      </div>
      {definition.intent_signals.map((signal) => (
        <div className="settings-table-row criterion-row" key={signal.signal_id}>
          <Mono>{signal.code}</Mono>
          <span>
            <strong>{signalRuleText(signal)}</strong>
            <small>{signal.signal_id}</small>
          </span>
          <span>{sourcePolicySummary(signal.source_policy, t)}</span>
          <BooleanPill active={signal.source_policy.source_logic === 'AND'} />
          <BooleanPill active={signal.source_policy.allow_additional_sources} />
          <BooleanPill active={!sameRubric(signal.scoring_rubric, globalRubric)} />
        </div>
      ))}
    </div>
  );
}

function SignalScaleSummary({ definition }: { definition: RadarDefinition }) {
  return <SignalRubricSummary rubric={globalSignalRubric(definition)} />;
}

function SignalScaleEditor({
  draft,
  onDraftChange,
}: {
  draft: EditableRadarDefinitionDraft;
  onDraftChange: (draft: EditableRadarDefinitionDraft) => void;
}) {
  const { t } = useTranslation();
  const globalRubric = globalSignalRubric(draft);
  function updateAllRubrics(scoring_rubric: IntentSignalDefinition['scoring_rubric']) {
    onDraftChange({
      ...draft,
      intent_signals: draft.intent_signals.map((signal) => (
        sameRubric(signal.scoring_rubric, globalRubric)
          ? { ...signal, scoring_rubric }
          : signal
      )),
    });
  }
  return (
    <div className="signal-scale-editor">
      <div className="generated-code-row">
        <Mono>{globalRubric.scale.join(' / ')}</Mono>
        <small>{t('icpRadar.settings.signalScaleLocked')}</small>
      </div>
      <SignalRubricTable rubric={globalRubric} onChange={updateAllRubrics} />
    </div>
  );
}

function IntentSignalsEditor({
  draft,
  onDraftChange,
}: {
  draft: EditableRadarDefinitionDraft;
  onDraftChange: (draft: EditableRadarDefinitionDraft) => void;
}) {
  const { t } = useTranslation();
  const globalSources = draft.global_search_policy.sources;
  const globalRubric = globalSignalRubric(draft);

  return (
    <div className="criteria-editor-list">
      {draft.intent_signals.map((signal, index) => (
        <div className="criteria-editor-row" key={`${signal.signal_id}-${index}`}>
          <div className="generated-code-row">
            <Mono>{signal.code}</Mono>
            <small>{t('icpRadar.settings.generatedCode')}</small>
          </div>
          <TextAreaField
            label={t('icpRadar.settings.signalDetection')}
            value={primaryRuleDescription(signal.trigger_rule_group)}
            onChange={(description) => onDraftChange({ ...draft, intent_signals: replaceAt(draft.intent_signals, index, { ...signal, trigger_rule_group: setPrimaryRuleDescription(signal.trigger_rule_group, description) }) })}
          />
          <SimpleSourcePolicyEditor globalSources={globalSources} policy={signal.source_policy} onChange={(source_policy) => onDraftChange({ ...draft, intent_signals: replaceAt(draft.intent_signals, index, { ...signal, source_policy }) })} />
          <SignalRubricOverride
            globalRubric={globalRubric}
            signal={signal}
            onChange={(nextSignal) => onDraftChange({ ...draft, intent_signals: replaceAt(draft.intent_signals, index, nextSignal) })}
          />
          <Button icon={<X aria-hidden="true" />} variant="default" onClick={() => onDraftChange({ ...draft, intent_signals: draft.intent_signals.filter((_, currentIndex) => currentIndex !== index) })}>
            {t('icpRadar.settings.remove')}
          </Button>
        </div>
      ))}
      <Button icon={<Plus aria-hidden="true" />} variant="default" onClick={() => onDraftChange({ ...draft, intent_signals: [...draft.intent_signals, newIntentSignal(globalSources.map((source) => source.source_id))] })}>
        {t('icpRadar.settings.addSignal')}
      </Button>
    </div>
  );
}

function SignalRubricOverride({
  globalRubric,
  onChange,
  signal,
}: {
  globalRubric: IntentSignalDefinition['scoring_rubric'];
  onChange: (signal: IntentSignalDefinition) => void;
  signal: IntentSignalDefinition;
}) {
  const { t } = useTranslation();
  const [override, setOverride] = useState(!sameRubric(signal.scoring_rubric, globalRubric));
  return (
    <div className="scoring-rubric-editor">
      <ToggleField
        checked={override}
        label={t('icpRadar.settings.overrideSignalScoring')}
        onChange={(checked) => {
          setOverride(checked);
          if (!checked) {
            onChange({ ...signal, scoring_rubric: globalRubric });
          }
        }}
      />
      {override && (
        <SignalRubricTable
          rubric={signal.scoring_rubric}
          onChange={(scoring_rubric) => onChange({ ...signal, scoring_rubric })}
        />
      )}
    </div>
  );
}

function SignalRubricSummary({ rubric }: { rubric: IntentSignalDefinition['scoring_rubric'] }) {
  const { t } = useTranslation();
  return (
    <table className="rubric-table rubric-table-compact">
      <thead>
        <tr>
          <th>{t('icpRadar.settings.scoreValue')}</th>
          <th>{t('icpRadar.settings.whenToScore')}</th>
        </tr>
      </thead>
      <tbody>
        {rubric.rules.map((rule) => (
          <tr key={rule.score}>
            <td><Mono>{rule.score}</Mono></td>
            <td>{rule.description}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function SignalRubricTable({
  onChange,
  rubric,
}: {
  onChange: (rubric: IntentSignalDefinition['scoring_rubric']) => void;
  rubric: IntentSignalDefinition['scoring_rubric'];
}) {
  const { t } = useTranslation();
  return (
      <table className="rubric-table">
        <thead>
          <tr>
            <th>{t('icpRadar.settings.scoreValue')}</th>
            <th>{t('icpRadar.settings.whenToScore')}</th>
          </tr>
        </thead>
        <tbody>
      {rubric.rules.map((rule, index) => (
        <tr key={rule.score}>
          <td><Mono>{rule.score}</Mono></td>
          <td>
            <TextAreaField
              label={`${rule.score}`}
              value={rule.description}
              onChange={(description) => onChange({ ...rubric, rules: replaceAt(rubric.rules, index, { ...rule, description }) })}
            />
          </td>
        </tr>
      ))}
        </tbody>
      </table>
  );
}

function ScoringModelSummary({ definition }: { definition: RadarDefinition }) {
  const { t } = useTranslation();
  return (
    <>
      <div className="icp-settings-formula-grid">
        {[
          [t('icpRadar.fit'), presetLabel(definition.scoring_model.fit_model.formula_preset, t)],
          [t('icpRadar.intent'), presetLabel(definition.scoring_model.intent_model.formula_preset, t)],
          [t('icpRadar.columns.tier'), definition.scoring_model.tier_model.basis],
        ].map(([name, value]) => (
          <div key={name}>
            <Mono>{name}</Mono>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <div className="icp-settings-thresholds">
        {Object.entries(definition.scoring_model.tier_thresholds).map(([tier, value]) => (
          <Badge key={tier} tone={tier === 'Tier 1' ? 'ally' : 'neutral'}>{tier} {value}</Badge>
        ))}
      </div>
    </>
  );
}

function ScoringModelEditor({
  draft,
  onDraftChange,
}: {
  draft: EditableRadarDefinitionDraft;
  onDraftChange: (draft: EditableRadarDefinitionDraft) => void;
}) {
  const { t } = useTranslation();
  const model = draft.scoring_model;
  function updateModel(patch: Partial<EditableRadarDefinitionDraft['scoring_model']>) {
    onDraftChange({ ...draft, scoring_model: { ...model, ...patch } });
  }
  return (
    <div className="criteria-editor-list">
      <FormulaModelEditor
        codes={draft.account_qualification.rule_group.rules.map((rule) => rule.rule_id)}
        label={t('icpRadar.fit')}
        model={model.fit_model}
        onChange={(fit_model) => updateModel({ fit_model })}
      />
      <FormulaModelEditor
        codes={draft.intent_signals.map((signal) => signal.code)}
        label={t('icpRadar.intent')}
        model={model.intent_model}
        onChange={(intent_model) => updateModel({ intent_model })}
      />
      <TextAreaField
        label={t('icpRadar.settings.tierModel')}
        value={model.tier_model.description}
        onChange={(description) => updateModel({ tier_model: { ...model.tier_model, description } })}
      />
      <div className="icp-threshold-editor">
        {Object.entries(model.tier_thresholds).map(([tier, value]) => (
          <TextField
            key={tier}
            label={tier}
            value={value}
            onChange={(nextValue) => updateModel({ tier_thresholds: { ...model.tier_thresholds, [tier]: nextValue } })}
          />
        ))}
      </div>
    </div>
  );
}

function FormulaModelEditor({
  codes,
  label,
  model,
  onChange,
}: {
  codes: string[];
  label: string;
  model: RadarScoringModel['fit_model'];
  onChange: (model: RadarScoringModel['fit_model']) => void;
}) {
  const { t } = useTranslation();
  const presetOptions = ['arithmetic_mean', 'weighted_average', 'maximum_signal', 'capped_sum', 'custom'];
  return (
    <div className="formula-model-editor">
      <SelectField label={label} options={presetOptions} value={model.formula_preset} onChange={(formula_preset) => onChange({ ...model, formula_preset })} />
      <TextAreaField label={t('icpRadar.settings.description')} value={model.description} onChange={(description) => onChange({ ...model, description })} />
      {model.formula_preset === 'custom' && (
        <>
          <div className="formula-code-reference">
            <Mono>{t('icpRadar.settings.availableCodes')}</Mono>
            <span>{codes.join(', ')}</span>
          </div>
          <TextAreaField label={t('icpRadar.settings.customFormula')} value={model.custom_formula} onChange={(custom_formula) => onChange({ ...model, custom_formula })} />
        </>
      )}
    </div>
  );
}

function presetLabel(preset: string, t: (key: string) => string): string {
  const key = `icpRadar.settings.formulaPresets.${preset}`;
  const translated = t(key);
  return translated === key ? preset : translated;
}

function ValidationReportView({ report }: { report: RadarDefinition['validation_report'] }) {
  const { t } = useTranslation();
  const actionableIssues = [...report.errors, ...report.warnings];
  const groupedIssues = groupValidationIssues(actionableIssues);
  if (actionableIssues.length === 0) {
    return (
      <div className="validation-summary valid">
        <Badge tone="ally">{t('icpRadar.settings.validConfiguration')}</Badge>
        <span>{t('icpRadar.settings.validConfigurationCopy')}</span>
      </div>
    );
  }
  return (
    <div className="validation-summary">
      {Object.entries(groupedIssues).map(([block, issues]) => (
        <div className="validation-group" key={block}>
          <Badge tone={issues.some((issue) => issue.level === 'error') ? 'blocker' : 'unsurfaced'}>{t(validationBlockKey(block))}</Badge>
          <span>{issues.length}</span>
          <ul>
            {issues.slice(0, 4).map((issue) => (
              <li key={`${issue.code}-${issue.path}`}>{issue.message}</li>
            ))}
          </ul>
        </div>
      ))}
      <details>
        <summary>{t('icpRadar.settings.validationDetails')}</summary>
        <div className="criteria-list">
          {actionableIssues.map((issue) => (
            <div className="criterion-row" key={`${issue.code}-${issue.path}`}>
              <Mono>{issue.code}</Mono>
              <span>
                <strong>{issue.message}</strong>
                <small>{issue.path}</small>
              </span>
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}

function groupValidationIssues(issues: RadarDefinition['validation_report']['errors']): Record<string, typeof issues> {
  return issues.reduce<Record<string, typeof issues>>((result, issue) => {
    const block = issue.path.includes('metadata')
      ? 'overview'
      : issue.path.includes('global_search_policy')
        ? 'globalSearch'
        : issue.path.includes('account_qualification')
          ? 'qualification'
          : issue.path.includes('intent_signals')
            ? 'intentSignals'
            : issue.path.includes('scoring_model')
              ? 'scoring'
              : 'validation';
    result[block] = [...(result[block] ?? []), issue];
    return result;
  }, {});
}

function validationBlockKey(block: string): string {
  return `icpRadar.settings.validationBlocks.${block}`;
}

function TextField({ label, onChange, value }: { label: string; onChange: (value: string) => void; value: string }) {
  return (
    <label className="icp-editor-field">
      <span>{label}</span>
      <input value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function TextAreaField({ label, onChange, value }: { label: string; onChange: (value: string) => void; value: string }) {
  return (
    <label className="icp-editor-field">
      <span>{label}</span>
      <textarea value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function ArrayTextAreaField({ label, onChange, value }: { label: string; onChange: (value: string[]) => void; value: string[] }) {
  return (
    <TextAreaField
      label={label}
      value={value.join('\n')}
      onChange={(nextValue) => onChange(nextValue.split('\n').map((item) => item.trim()).filter(Boolean))}
    />
  );
}

function SelectField({
  label,
  onChange,
  optionLabel,
  options,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  optionLabel?: (value: string) => string;
  options: string[];
  value: string;
}) {
  return (
    <label className="icp-editor-field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option} value={option}>
            {optionLabel ? optionLabel(option) : option}
          </option>
        ))}
      </select>
    </label>
  );
}

function ToggleField({
  checked,
  disabled = false,
  label,
  onChange,
}: {
  checked: boolean;
  disabled?: boolean;
  label: string;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className={`toggle-field${disabled ? ' toggle-field-disabled' : ''}`}>
      <input
        checked={checked}
        disabled={disabled}
        type="checkbox"
        onChange={(event) => {
          if (!disabled) {
            onChange(event.target.checked);
          }
        }}
      />
      <span aria-hidden="true" />
      <strong>{label}</strong>
    </label>
  );
}

function DurationField({ label, onChange, value }: { label: string; onChange: (value: string) => void; value: string }) {
  const { t } = useTranslation();
  const duration = parseDuration(value);
  return (
    <div className="duration-field">
      <span>{label}</span>
      <TextField
        label={t('icpRadar.settings.durationValue')}
        value={String(duration.amount)}
        onChange={(amount) => onChange(formatDuration(amount, duration.unit))}
      />
      <SelectField
        label={t('icpRadar.settings.durationUnit')}
        options={['days', 'weeks', 'months']}
        value={duration.unit}
        onChange={(unit) => onChange(formatDuration(duration.amount, unit))}
        optionLabel={(option) => t(durationUnitKey(option))}
      />
    </div>
  );
}

function ListSection({ bounded = false, title, items }: { bounded?: boolean; title: string; items: string[] }) {
  return (
    <section className="icp-detail-section">
      <Eyebrow>{title}</Eyebrow>
      <ul className={`icp-settings-list${bounded ? ' icp-settings-list-bounded' : ''}`}>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function CandidateDetailTabs({ activeTab, onTabChange }: { activeTab: CandidateDetailTab; onTabChange: (tab: CandidateDetailTab) => void }) {
  const { t } = useTranslation();
  const tabs: CandidateDetailTab[] = ['overview', 'qualification', 'signals', 'sources', 'journal'];
  return (
    <div className="icp-candidate-detail-tabs" aria-label={t('icpRadar.canonicalDetail.tabsAria')}>
      {tabs.map((tab) => (
        <button
          aria-pressed={activeTab === tab}
          className={`criteria-chip${activeTab === tab ? ' criteria-chip-active' : ''}`}
          key={tab}
          type="button"
          onClick={() => onTabChange(tab)}
        >
          {t(`icpRadar.canonicalDetail.tabs.${tab}`)}
        </button>
      ))}
    </div>
  );
}

function CandidatePreview({
  artifact,
  candidate,
  onOpenDetails,
}: {
  artifact: ICPRadarArtifact;
  candidate: ICPRadarCandidate;
  onOpenDetails: () => void;
}) {
  const { t } = useTranslation();
  const qualificationRows = topCriteriaByCodes(artifact, candidate, fitSignalCodes, 5);
  const signalRows = topCriteriaByCodes(
    artifact,
    candidate,
    [...intentSignalCodes, ...triggerSignalCodes],
    5,
  );
  return (
    <div className="icp-candidate-preview">
      <div className="icp-preview-body">
        <header className="icp-preview-heading">
          <div>
            <Eyebrow>{t('icpRadar.previewEyebrow')}</Eyebrow>
            <strong>{candidate.legal_name}</strong>
          </div>
        </header>
        <div className="icp-preview-main">
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.canonicalPreview.summary')}</Eyebrow>
            <p>{candidate.main_signal}</p>
          </section>
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.canonicalPreview.tier')}</Eyebrow>
            <p>{candidate.comment || candidate.signal_summary}</p>
          </section>
        </div>
        <div className="icp-preview-lists">
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.canonicalPreview.qualification')}</Eyebrow>
            <div className="criteria-list criteria-list-compact">
              {(qualificationRows.length ? qualificationRows : topCriteria(artifact, candidate, 5)).map(({ criterion, value }) => (
                <div className="criterion-row" key={criterion.code}>
                  <Mono>{criterion.code}</Mono>
                  <span>
                    <strong>{criterion.name}</strong>
                  </span>
                  <Mono>{value}</Mono>
                </div>
              ))}
            </div>
          </section>
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.canonicalPreview.signals')}</Eyebrow>
            <div className="criteria-list criteria-list-compact">
              {(signalRows.length ? signalRows : topCriteria(artifact, candidate, 5)).map(({ criterion, value }) => (
                <div className="criterion-row" key={criterion.code}>
                  <Mono>{criterion.code}</Mono>
                  <span>
                    <strong>{criterion.name}</strong>
                  </span>
                  <Mono>{value}</Mono>
                </div>
              ))}
            </div>
          </section>
        </div>
        <div className="icp-preview-actions">
          <Button icon={<ArrowRight aria-hidden="true" />} variant="default" onClick={onOpenDetails}>
            {t('icpRadar.openDetails')}
          </Button>
        </div>
      </div>
    </div>
  );
}

function CandidateScoreGrid({ candidate, validatedScore }: { candidate: ICPRadarCandidate; validatedScore: ValidatedCandidateScore }) {
  const { t } = useTranslation();
  const delta = validatedScore.effective_score.total_score - validatedScore.original_score.total_score;
  return (
    <div className="icp-score-grid">
      <ScoreBox label={t('icpRadar.fit')} value={validatedScore.effective_score.fit_score} />
      <ScoreBox label={t('icpRadar.intent')} value={validatedScore.effective_score.intent_score} />
      <ScoreBox label={t('icpRadar.trigger')} value={validatedScore.effective_score.trigger_score} />
      <ScoreBox delta={delta} label={t('icpRadar.total')} value={validatedScore.effective_score.total_score} />
    </div>
  );
}

function CompanyContext({ candidate }: { candidate: ICPRadarCandidate }) {
  const { t } = useTranslation();
  return (
    <section className="icp-detail-section">
      <Eyebrow>{t('icpRadar.companyContext')}</Eyebrow>
      <dl className="icp-definition-list">
        <div>
          <dt>{t('icpRadar.revenue')}</dt>
          <dd>{candidate.revenue || t('icpRadar.unknown')}</dd>
        </div>
        <div>
          <dt>{t('icpRadar.inn')}</dt>
          <dd>{candidate.inn || t('icpRadar.unknown')}</dd>
        </div>
        <div>
          <dt>{t('icpRadar.site')}</dt>
          <dd>{candidate.site || t('icpRadar.unknown')}</dd>
        </div>
        <div>
          <dt>{t('icpRadar.confidence')}</dt>
          <dd>{candidate.confidence || t('icpRadar.unknown')}</dd>
        </div>
      </dl>
    </section>
  );
}

function EvidenceList({
  candidate,
  sourcesById,
  compact = false,
}: {
  candidate: ICPRadarCandidate;
  sourcesById: Map<string, SourceDefinition>;
  compact?: boolean;
}) {
  const refs = compact ? candidate.evidence_refs.slice(0, 5) : candidate.evidence_refs;
  return (
    <div className={`icp-evidence-list${compact ? ' icp-evidence-list-compact' : ''}`}>
      {refs.map((ref) => {
        const source = sourcesById.get(ref);
        return (
          <a href={source?.reference ?? ref} key={ref} target="_blank" rel="noreferrer">
            <ShieldCheck aria-hidden="true" />
            <span>
              <strong>{ref}</strong>
              <small>{source?.label ?? ref}</small>
            </span>
            <ExternalLink aria-hidden="true" />
          </a>
        );
      })}
    </div>
  );
}

function SourceUrlList({ candidate }: { candidate: ICPRadarCandidate }) {
  const { t } = useTranslation();
  if (!candidate.source_urls.length) {
    return <p>{t('icpRadar.unknown')}</p>;
  }

  return (
    <div className="icp-evidence-list">
      {candidate.source_urls.map((url) => (
        <a href={url} key={url} target="_blank" rel="noreferrer">
          <ExternalLink aria-hidden="true" />
          <span>
            <strong>{url}</strong>
          </span>
        </a>
      ))}
    </div>
  );
}

function ScoreBox({ delta = 0, label, value }: { delta?: number; label: string; value: number }) {
  return (
    <div className="icp-score-box">
      <Mono>{label}</Mono>
      <strong>{value}</strong>
      {delta !== 0 && <small className="score-delta">{formatDelta(delta)}</small>}
    </div>
  );
}

function ValidationSummary({ score }: { score: ValidatedCandidateScore }) {
  const { t } = useTranslation();
  const reviewedCount = score.status_counts.confirmed
    + score.status_counts.corrected
    + score.status_counts.rejected
    + score.status_counts.stale;
  const needsReviewCount = signalCodes.length - reviewedCount;
  return (
    <div className="validation-summary-grid">
      <span>
        <Mono>{t('icpRadar.reviewStatus.confirmed')}</Mono>
        <strong>{score.status_counts.confirmed}</strong>
      </span>
      <span>
        <Mono>{t('icpRadar.reviewStatus.corrected')}</Mono>
        <strong>{score.status_counts.corrected}</strong>
      </span>
      <span>
        <Mono>{t('icpRadar.reviewStatus.rejected')}</Mono>
        <strong>{score.status_counts.rejected}</strong>
      </span>
      <span>
        <Mono>{t('icpRadar.reviewStatus.stale')}</Mono>
        <strong>{score.status_counts.stale}</strong>
      </span>
      <span>
        <Mono>{t('icpRadar.criteriaFilters.needs_review')}</Mono>
        <strong>{needsReviewCount}</strong>
      </span>
    </div>
  );
}

function topCriteria(artifact: ICPRadarArtifact, candidate: ICPRadarCandidate, count: number) {
  return artifact.radar.definition.intent_signals
    .map((signal) => ({
      criterion: signal,
      value: candidate.criteria_scores[signal.code] ?? 0,
    }))
    .filter((item): item is { criterion: IntentSignalDefinition; value: number } => item.value > 0)
    .sort((left, right) => right.value - left.value || left.criterion.code.localeCompare(right.criterion.code))
    .slice(0, count);
}

function topCriteriaByCodes(artifact: ICPRadarArtifact, candidate: ICPRadarCandidate, codes: string[], count: number) {
  const codeSet = new Set(codes);
  return topCriteria(artifact, candidate, artifact.radar.definition.intent_signals.length)
    .filter((item) => codeSet.has(item.criterion.code))
    .slice(0, count);
}

type CriterionFilter = 'all' | 'needs_review' | 'confirmed' | 'corrected' | 'rejected' | 'stale';
type CriterionSort = 'score_desc' | 'status' | 'confidence';

function CriteriaBreakdown({
  artifact,
  candidate,
  onDecisionChange,
  radarId,
  signalValidation,
  validatedScore,
}: {
  artifact: ICPRadarArtifact;
  candidate: ICPRadarCandidate;
  onDecisionChange: (decision: SignalValidationDecision) => void;
  radarId: string;
  signalValidation: SignalValidationOverlay;
  validatedScore: ValidatedCandidateScore;
}) {
  const { t } = useTranslation();
  const [expandedCriterionCode, setExpandedCriterionCode] = useState<string | null>(null);
  const [filter, setFilter] = useState<CriterionFilter>('all');
  const [sort, setSort] = useState<CriterionSort>('score_desc');
  const rows = useMemo(() => (
    artifact.radar.definition.intent_signals
      .map((criterion) => {
        const evidence = candidate.criteria_evidence[criterion.code];
        const decision = signalValidation[signalValidationKey(radarId, candidate.account_id, criterion.code)];
        const signalScore = validatedScore.signal_scores[criterion.code];
        return {
          criterion,
          decision,
          evidence,
          signalScore,
          score: signalScore?.original_score ?? evidence?.score ?? candidate.criteria_scores[criterion.code] ?? 0,
        };
      })
      .filter((row) => matchesCriterionFilter(row.evidence, row.decision, filter))
      .sort((left, right) => compareCriterionRows(left, right, sort))
  ), [
    artifact.radar.definition.intent_signals,
    candidate.account_id,
    candidate.criteria_evidence,
    candidate.criteria_scores,
    filter,
    radarId,
    signalValidation,
    sort,
    validatedScore.signal_scores,
  ]);

  const filterOptions: CriterionFilter[] = ['all', 'needs_review', 'confirmed', 'corrected', 'rejected', 'stale'];
  const sortOptions: CriterionSort[] = ['score_desc', 'status', 'confidence'];

  return (
    <div className="criteria-evidence-list" aria-label={t('icpRadar.criterionEvidence')}>
      <div className="criteria-review-toolbar" aria-label={t('icpRadar.criteriaReviewToolbar')}>
        <div className="criteria-review-control">
          <Mono>{t('icpRadar.filter')}</Mono>
          <div className="criteria-review-segmented">
            {filterOptions.map((option) => (
              <button
                aria-pressed={filter === option}
                className={`criteria-chip${filter === option ? ' criteria-chip-active' : ''}`}
                key={option}
                type="button"
                onClick={() => setFilter(option)}
              >
                {t(criterionFilterKey(option))}
              </button>
            ))}
          </div>
        </div>

        <label className="criteria-sort-field">
          <SlidersHorizontal aria-hidden="true" />
          <span>{t('icpRadar.sort')}</span>
          <select value={sort} onChange={(event) => setSort(event.target.value as CriterionSort)}>
            {sortOptions.map((option) => (
              <option key={option} value={option}>
                {t(criterionSortKey(option))}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="criteria-review-table">
        <div className="criteria-review-head">
          <span>{t('icpRadar.criteriaColumns.code')}</span>
          <span>{t('icpRadar.criteriaColumns.criterion')}</span>
          <span>{t('icpRadar.criteriaColumns.score')}</span>
          <span>{t('icpRadar.criteriaColumns.status')}</span>
          <span>{t('icpRadar.criteriaColumns.confidence')}</span>
          <span>{t('icpRadar.criteriaColumns.facts')}</span>
          <span>{t('icpRadar.criteriaColumns.review')}</span>
          <span className="criteria-action-head" aria-label={t('icpRadar.criteriaColumns.action')} />
        </div>

        {rows.map(({ criterion, decision, evidence, score, signalScore }) => {
          const expanded = expandedCriterionCode === criterion.code;
          const effectiveScore = signalScore?.effective_score ?? score;
          const adjusted = effectiveScore !== score;
          const statusLabel = evidence ? t(evidenceStatusKey(evidence.evidence_status)) : t('icpRadar.notObserved');
          const confidenceLabel = evidence ? t(confidenceKey(evidence.confidence)) : t('icpRadar.confidenceValues.none');
          const validationStatus = decision?.status ?? 'unreviewed';

          return (
            <div className={`criteria-review-record${expanded ? ' criteria-review-record-expanded' : ''}`} key={criterion.code}>
              <button
                aria-expanded={expanded}
                className="criteria-review-row"
                type="button"
                onClick={() => setExpandedCriterionCode(expanded ? null : criterion.code)}
              >
                <Mono>{criterion.code}</Mono>
                <span className="criteria-review-name">
                  <strong>{criterion.name}</strong>
                  <small>{criterion.description}</small>
                </span>
                <span className="criteria-score-inline">
                  <Mono>{score}</Mono>
                  {adjusted && (
                    <>
                      <span aria-hidden="true">-&gt;</span>
                      <Mono>{effectiveScore}</Mono>
                      <small className="score-delta">{formatDelta(effectiveScore - score)}</small>
                    </>
                  )}
                </span>
                <span>
                  <Badge tone={evidenceBadgeTone(evidence?.evidence_status ?? 'not_observed')}>{statusLabel}</Badge>
                </span>
                <span>
                  <Badge tone={confidenceTone(evidence?.confidence)}>{confidenceLabel}</Badge>
                </span>
                <Mono>{evidence?.facts.length ?? 0}</Mono>
                <span>
                  <Badge tone={validationTone(validationStatus)}>{t(validationStatusKey(validationStatus))}</Badge>
                </span>
                <span className="row-action">
                  {expanded ? <ChevronDown aria-hidden="true" /> : <ChevronRight aria-hidden="true" />}
                </span>
              </button>

              {expanded && evidence && (
                <CriterionEvidenceDetail
                  candidate={candidate}
                  criterion={criterion}
                  decision={decision}
                  evidence={evidence}
                  radarId={radarId}
                  signalScore={signalScore}
                  onDecision={onDecisionChange}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CriterionEvidenceDetail({
  candidate,
  criterion,
  decision,
  evidence,
  onDecision,
  radarId,
  signalScore,
}: {
  candidate: ICPRadarCandidate;
  criterion: IntentSignalDefinition;
  decision: SignalValidationDecision | undefined;
  evidence: CriterionEvidenceExplanation;
  onDecision: (decision: SignalValidationDecision) => void;
  radarId: string;
  signalScore: ValidatedCandidateScore['signal_scores'][string] | undefined;
}) {
  const { t } = useTranslation();
  const [draftScore, setDraftScore] = useState(decision?.adjusted_score ?? signalScore?.effective_score ?? evidence.score);
  const [confidence, setConfidence] = useState(decision?.confidence ?? evidence.confidence);
  const [correctedSummary, setCorrectedSummary] = useState(decision?.corrected_summary ?? '');
  const [selectedEvidenceRefs, setSelectedEvidenceRefs] = useState<string[]>(
    decision?.evidence_refs?.length ? decision.evidence_refs : evidence.evidence_refs,
  );
  const [comment, setComment] = useState(decision?.comment ?? '');
  const commentRequired = !comment.trim();

  function submitDecision(status: SignalValidationStatus) {
    const needsComment = status === 'corrected' || status === 'rejected' || status === 'stale';
    if (needsComment && commentRequired) {
      return;
    }
    onDecision({
      radar_id: radarId,
      account_id: candidate.account_id,
      signal_code: criterion.code,
      status,
      original_score: evidence.score,
      adjusted_score: status === 'corrected' ? draftScore : null,
      confidence: status === 'corrected' ? confidence : null,
      corrected_summary: status === 'corrected' ? correctedSummary : null,
      evidence_refs: status === 'corrected' ? selectedEvidenceRefs : evidence.evidence_refs,
      comment,
      reviewed_at: new Date().toISOString(),
    });
  }

  function toggleEvidenceRef(ref: string) {
    setSelectedEvidenceRefs((current) => (
      current.includes(ref) ? current.filter((item) => item !== ref) : [...current, ref]
    ));
  }

  return (
    <div className="criterion-evidence-detail">
      <div className="criterion-detail-topline">
        <Badge tone={evidenceBadgeTone(evidence.evidence_status)}>{t(evidenceStatusKey(evidence.evidence_status))}</Badge>
        <Badge tone={confidenceTone(evidence.confidence)}>{t(confidenceKey(evidence.confidence))}</Badge>
        <Badge tone={validationTone(decision?.status ?? 'unreviewed')}>{t(validationStatusKey(decision?.status ?? 'unreviewed'))}</Badge>
        <span className="criterion-origin-note">{t(evidenceOriginKey(evidence.evidence_origin))}</span>
      </div>

      <section>
        <Eyebrow>{t('icpRadar.rationale')}</Eyebrow>
        <p>{evidence.rationale}</p>
      </section>

      {evidence.facts.length ? (
        <section>
          <Eyebrow>{t('icpRadar.facts')}</Eyebrow>
          <div className="criterion-fact-list">
            {evidence.facts.map((fact) => (
              <div className="criterion-fact" key={`${criterion.code}-${fact.evidence_ref}-${fact.fact}`}>
                <ShieldCheck aria-hidden="true" />
                <div>
                  <strong>{fact.fact}</strong>
                  <small>{fact.why_it_matters}</small>
                  <a href={fact.source_url || undefined} target="_blank" rel="noreferrer">
                    <Mono>{fact.evidence_ref || t('icpRadar.source')}</Mono>
                    {fact.source_url && <ExternalLink aria-hidden="true" />}
                  </a>
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : (
        <p className="criterion-empty-note">{t('icpRadar.noCriterionFacts')}</p>
      )}

      <section className="criterion-review-panel">
        <div>
          <Eyebrow>{t('icpRadar.localValidation')}</Eyebrow>
          <p>{t('icpRadar.localValidationCopy')}</p>
        </div>
        <div className="criterion-review-form">
          <label>
            <span>{t('icpRadar.adjustedScore')}</span>
            <select value={draftScore} onChange={(event) => setDraftScore(Number(event.target.value))}>
              {[0, 1, 2, 3].map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>{t('icpRadar.confidenceOverride')}</span>
            <select
              value={confidence}
              onChange={(event) => setConfidence(event.target.value as CriterionEvidenceExplanation['confidence'])}
            >
              {(['high', 'medium', 'low', 'none'] as const).map((value) => (
                <option key={value} value={value}>
                  {t(confidenceKey(value))}
                </option>
              ))}
            </select>
          </label>
          <label className="criterion-comment-field">
            <span>{t('icpRadar.correctedSummary')}</span>
            <textarea
              placeholder={t('icpRadar.correctedSummaryPlaceholder')}
              value={correctedSummary}
              onChange={(event) => setCorrectedSummary(event.target.value)}
            />
          </label>
          {evidence.evidence_refs.length > 0 && (
            <fieldset className="criterion-evidence-ref-picker">
              <legend>{t('icpRadar.selectedEvidenceRefs')}</legend>
              {evidence.evidence_refs.map((ref) => (
                <label key={ref}>
                  <input
                    checked={selectedEvidenceRefs.includes(ref)}
                    type="checkbox"
                    onChange={() => toggleEvidenceRef(ref)}
                  />
                  <Mono>{ref}</Mono>
                </label>
              ))}
            </fieldset>
          )}
          <label className="criterion-comment-field">
            <span>{t('icpRadar.comment')}</span>
            <textarea
              placeholder={t('icpRadar.commentPlaceholder')}
              value={comment}
              onChange={(event) => setComment(event.target.value)}
            />
          </label>
          <div className="criterion-review-actions">
            <Button
              icon={<Check aria-hidden="true" />}
              variant="default"
              onClick={() => submitDecision('confirmed')}
            >
              {t('icpRadar.confirmSignal')}
            </Button>
            <Button
              disabled={commentRequired}
              icon={<X aria-hidden="true" />}
              variant="default"
              onClick={() => submitDecision('rejected')}
            >
              {t('icpRadar.rejectSignal')}
            </Button>
            <Button
              disabled={commentRequired}
              icon={<RotateCcw aria-hidden="true" />}
              variant="default"
              onClick={() => submitDecision('stale')}
            >
              {t('icpRadar.markSignalStale')}
            </Button>
            <Button
              disabled={commentRequired}
              icon={<SlidersHorizontal aria-hidden="true" />}
              variant="default"
              onClick={() => submitDecision('corrected')}
            >
              {t('icpRadar.correctSignal')}
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}

function matchesCriterionFilter(
  evidence: CriterionEvidenceExplanation | undefined,
  decision: SignalValidationDecision | undefined,
  filter: CriterionFilter,
) {
  if (filter === 'all') {
    return true;
  }
  if (filter === 'needs_review') {
    return !decision && (
      evidence?.evidence_status !== 'supported'
      || evidence.confidence === 'low'
      || evidence.confidence === 'none'
    );
  }
  return decision?.status === filter;
}

function compareCriterionRows(
  left: {
    evidence: CriterionEvidenceExplanation | undefined;
    decision: SignalValidationDecision | undefined;
    score: number;
    criterion: IntentSignalDefinition;
  },
  right: {
    evidence: CriterionEvidenceExplanation | undefined;
    decision: SignalValidationDecision | undefined;
    score: number;
    criterion: IntentSignalDefinition;
  },
  sort: CriterionSort,
) {
  if (sort === 'status') {
    return validationRank(left.decision?.status ?? 'unreviewed') - validationRank(right.decision?.status ?? 'unreviewed')
      || right.score - left.score
      || left.criterion.code.localeCompare(right.criterion.code);
  }
  if (sort === 'confidence') {
    return confidenceRank(right.evidence?.confidence) - confidenceRank(left.evidence?.confidence)
      || right.score - left.score
      || left.criterion.code.localeCompare(right.criterion.code);
  }
  return right.score - left.score
    || statusRank(left.evidence?.evidence_status) - statusRank(right.evidence?.evidence_status)
    || left.criterion.code.localeCompare(right.criterion.code);
}

function statusRank(status: CriterionEvidenceExplanation['evidence_status'] | undefined) {
  if (status === 'supported') {
    return 0;
  }
  if (status === 'inferred') {
    return 1;
  }
  return 2;
}

function confidenceRank(confidence: CriterionEvidenceExplanation['confidence'] | undefined) {
  if (confidence === 'high') {
    return 3;
  }
  if (confidence === 'medium') {
    return 2;
  }
  if (confidence === 'low') {
    return 1;
  }
  return 0;
}

function criterionFilterKey(filter: CriterionFilter) {
  return `icpRadar.criteriaFilters.${filter}`;
}

function criterionSortKey(sort: CriterionSort) {
  return `icpRadar.criteriaSort.${sort}`;
}

function confidenceTone(confidence: CriterionEvidenceExplanation['confidence'] | undefined) {
  if (confidence === 'high' || confidence === 'medium') {
    return 'ally';
  }
  if (confidence === 'low') {
    return 'unsurfaced';
  }
  return 'neutral';
}

function evidenceBadgeTone(status: CriterionEvidenceExplanation['evidence_status']) {
  if (status === 'supported') {
    return 'ally';
  }
  if (status === 'inferred') {
    return 'unsurfaced';
  }
  return 'neutral';
}

function evidenceStatusKey(status: CriterionEvidenceExplanation['evidence_status']) {
  if (status === 'supported') {
    return 'icpRadar.supported';
  }
  if (status === 'inferred') {
    return 'icpRadar.inferred';
  }
  return 'icpRadar.notObserved';
}

function confidenceKey(confidence: CriterionEvidenceExplanation['confidence']) {
  if (confidence === 'high') {
    return 'icpRadar.confidenceValues.high';
  }
  if (confidence === 'medium') {
    return 'icpRadar.confidenceValues.medium';
  }
  if (confidence === 'low') {
    return 'icpRadar.confidenceValues.low';
  }
  return 'icpRadar.confidenceValues.none';
}

function evidenceOriginKey(origin: CriterionEvidenceExplanation['evidence_origin']) {
  if (origin === 'synthetic_demo_annotation') {
    return 'icpRadar.syntheticAnnotation';
  }
  return 'icpRadar.workbookFallback';
}

function loadSignalValidationOverlay(): SignalValidationOverlay {
  try {
    const raw = window.localStorage.getItem(signalValidationStorageKey);
    if (!raw) {
      return {};
    }
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return Object.fromEntries(
      Object.entries(parsed)
        .map(([key, value]) => [key, normalizeSignalValidationDecision(value)])
        .filter((entry): entry is [string, SignalValidationDecision] => entry[1] !== null),
    );
  } catch {
    window.localStorage.removeItem(signalValidationStorageKey);
    return {};
  }
}

function normalizeSignalValidationDecision(value: unknown): SignalValidationDecision | null {
  if (!value || typeof value !== 'object') {
    return null;
  }
  const item = value as Partial<SignalValidationDecision>;
  if (!item.radar_id || !item.account_id || !item.signal_code || !isSignalValidationStatus(item.status)) {
    return null;
  }
  const originalScore = Number(item.original_score);
  const adjustedScore = item.adjusted_score === null || item.adjusted_score === undefined
    ? null
    : Number(item.adjusted_score);
  return {
    radar_id: String(item.radar_id),
    account_id: String(item.account_id),
    signal_code: String(item.signal_code),
    status: item.status,
    original_score: Number.isFinite(originalScore) ? originalScore : 0,
    adjusted_score: adjustedScore !== null && Number.isFinite(adjustedScore) ? adjustedScore : null,
    confidence: item.confidence ?? null,
    corrected_summary: item.corrected_summary ?? null,
    evidence_refs: Array.isArray(item.evidence_refs) ? item.evidence_refs.map(String) : [],
    comment: item.comment ?? '',
    reviewed_at: item.reviewed_at ?? '',
  };
}

function isSignalValidationStatus(status: unknown): status is SignalValidationStatus {
  return status === 'unreviewed'
    || status === 'confirmed'
    || status === 'corrected'
    || status === 'rejected'
    || status === 'stale';
}

function signalValidationKey(radarId: string, accountId: string, signalCode: string) {
  return `${radarId}:${accountId}:${signalCode}`;
}

function validationForCandidate(
  overlay: SignalValidationOverlay,
  radarId: string,
  accountId: string,
): Record<string, SignalValidationDecision> {
  return Object.fromEntries(
    Object.values(overlay)
      .filter((decision) => decision.radar_id === radarId && decision.account_id === accountId)
      .map((decision) => [decision.signal_code, decision]),
  );
}

function validatedCandidatesForArtifact(
  artifact: ICPRadarArtifact,
  radarId: string,
  overlay: SignalValidationOverlay,
) {
  return artifact.candidates
    .map((candidate) => ({
      candidate,
      score: buildValidatedCandidateScore(candidate, validationForCandidate(overlay, radarId, candidate.account_id)),
    }))
    .sort((left, right) => right.score.effective_score.total_score - left.score.effective_score.total_score
      || right.score.effective_score.intent_score - left.score.effective_score.intent_score
      || left.candidate.legal_name.localeCompare(right.candidate.legal_name, 'ru'));
}

function buildValidatedCandidateScore(
  candidate: ICPRadarCandidate,
  decisions: Record<string, SignalValidationDecision> = {},
): ValidatedCandidateScore {
  const status_counts: ValidatedCandidateScore['status_counts'] = {
    unreviewed: 0,
    confirmed: 0,
    corrected: 0,
    rejected: 0,
    stale: 0,
  };
  const effectiveScores: Record<string, number> = {};
  const signal_scores: ValidatedCandidateScore['signal_scores'] = {};

  signalCodes.forEach((code) => {
    const originalScore = Number(candidate.criteria_scores[code] ?? 0);
    const decision = decisions[code];
    const status = decision?.status ?? 'unreviewed';
    let effectiveScore = originalScore;
    if (status === 'corrected') {
      effectiveScore = Math.max(0, Number(decision?.adjusted_score ?? originalScore));
    }
    if (status === 'rejected' || status === 'stale') {
      effectiveScore = 0;
    }
    status_counts[status] += 1;
    effectiveScores[code] = effectiveScore;
    signal_scores[code] = {
      signal_code: code,
      original_score: originalScore,
      effective_score: effectiveScore,
      delta: effectiveScore - originalScore,
      status,
    };
  });

  return {
    original_score: candidate.score,
    effective_score: buildCandidateScore(effectiveScores),
    signal_scores,
    status_counts,
  };
}

function buildCandidateScore(scores: Record<string, number>) {
  const sumCodes = (codes: string[]) => codes.reduce((total, code) => total + Number(scores[code] ?? 0), 0);
  const fit_score = sumCodes(fitSignalCodes);
  const intent_score = sumCodes(intentSignalCodes);
  const trigger_score = sumCodes(triggerSignalCodes);
  const total_score = fit_score + intent_score + trigger_score;
  return {
    fit_score,
    intent_score,
    trigger_score,
    total_score,
    tier: tierForTotal(total_score),
  };
}

function tierForTotal(totalScore: number) {
  if (totalScore >= 38) {
    return 'Tier 1';
  }
  if (totalScore >= 25) {
    return 'Tier 2';
  }
  if (totalScore >= 15) {
    return 'Tier 3';
  }
  return 'Monitor';
}

function formatDelta(delta: number) {
  return delta > 0 ? `+${delta}` : String(delta);
}

function validationStatusKey(status: SignalValidationStatus) {
  return `icpRadar.reviewStatus.${status}`;
}

function validationTone(status: SignalValidationStatus) {
  if (status === 'confirmed') {
    return 'ally';
  }
  if (status === 'rejected' || status === 'stale') {
    return 'blocker';
  }
  if (status === 'corrected') {
    return 'cobalt';
  }
  return 'neutral';
}

function validationRank(status: SignalValidationStatus) {
  if (status === 'rejected' || status === 'stale') {
    return 0;
  }
  if (status === 'corrected') {
    return 1;
  }
  if (status === 'confirmed') {
    return 2;
  }
  return 3;
}

function radarStatusKey(status: string) {
  if (status === 'draft') {
    return 'icpRadar.radarStatus.draft';
  }
  if (status === 'active') {
    return 'icpRadar.radarStatus.active';
  }
  if (status === 'stopped') {
    return 'icpRadar.radarStatus.stopped';
  }
  if (status === 'configured') {
    return 'icpRadar.radarStatus.configured';
  }
  if (status === 'planned') {
    return 'icpRadar.radarStatus.planned';
  }
  if (status === 'local_draft') {
    return 'icpRadar.radarStatus.localDraft';
  }
  if (status === 'modified_locally') {
    return 'icpRadar.radarStatus.modifiedLocally';
  }
  return 'icpRadar.radarStatus.unknown';
}

function radarOperationalStatus(status: string): RadarOperationalStatus {
  if (status === 'active') {
    return 'active';
  }
  if (status === 'stopped') {
    return 'stopped';
  }
  return 'draft';
}

function liveTotalScore(candidate: LiveRadarCandidate): number {
  return candidate.score.fit_score + candidate.score.intent_score;
}

function cadenceKey(cadence: string) {
  if (cadence === 'weekly') {
    return 'icpRadar.cadence.weekly';
  }
  if (cadence === 'monthly') {
    return 'icpRadar.cadence.monthly';
  }
  return 'icpRadar.cadence.unknown';
}

function lastRunKey(lastRun: string) {
  if (lastRun === 'not_run') {
    return 'icpRadar.lastRun.notRun';
  }
  if (lastRun === 'not_scheduled') {
    return 'icpRadar.lastRun.notScheduled';
  }
  return 'icpRadar.lastRun.fixture';
}

function runModeKey(runMode: string) {
  if (runMode === 'incremental_signal_monitoring') {
    return 'icpRadar.runMode.incremental';
  }
  if (runMode === 'configured_not_generated') {
    return 'icpRadar.runMode.configured';
  }
  if (runMode === 'planned') {
    return 'icpRadar.runMode.planned';
  }
  if (runMode === 'fixture_import') {
    return 'icpRadar.runMode.fixtureImport';
  }
  return 'icpRadar.runMode.unknown';
}

function liveRuntimeKey(runtime: string) {
  if (runtime === 'openrouter_live') {
    return 'icpRadar.live.runtimeOpenRouter';
  }
  if (runtime === 'langgraph_dai') {
    return 'icpRadar.live.runtimeLanggraph';
  }
  if (runtime === 'recorded') {
    return 'icpRadar.live.runtimeRecorded';
  }
  return 'icpRadar.live.runtimeUnknown';
}

function liveQualificationTone(status: LiveRadarQualificationResult['status']) {
  if (status === 'confirmed') {
    return 'ally';
  }
  if (status === 'rejected') {
    return 'blocker';
  }
  if (status === 'weak') {
    return 'unsurfaced';
  }
  return 'neutral';
}

function liveSignalTone(status: LiveRadarSignalResult['status']) {
  if (status === 'observed') {
    return 'ally';
  }
  if (status === 'unclear') {
    return 'unsurfaced';
  }
  return 'neutral';
}

function discoveryModeKey(discoveryMode: string) {
  if (discoveryMode === 'one_time_import') {
    return 'icpRadar.discoveryMode.oneTimeImport';
  }
  if (discoveryMode === 'configured_seed') {
    return 'icpRadar.discoveryMode.configuredSeed';
  }
  return 'icpRadar.discoveryMode.unknown';
}

function sourceTypeKey(sourceType: string) {
  return `icpRadar.settings.sourceTypes.${sourceType}`;
}

function trustPolicyValue(value: string) {
  if (value === 'high' || value === 'trusted') {
    return 'trusted';
  }
  if (value === 'medium' || value === 'cross_check') {
    return 'cross_check';
  }
  return 'hitl_required';
}

function trustPolicyKey(value: string) {
  return `icpRadar.settings.trustPolicies.${trustPolicyValue(value)}`;
}

function trustPolicyTone(value: string) {
  const policy = trustPolicyValue(value);
  if (policy === 'trusted') {
    return 'ally';
  }
  if (policy === 'cross_check') {
    return 'unsurfaced';
  }
  return 'neutral';
}

function logicalOperatorKey(value: string) {
  return `icpRadar.settings.logicalOperators.${value}`;
}

function requirementKey(value: string) {
  return `icpRadar.settings.requirements.${value}`;
}

function ruleOperatorLabel(operator: string, rule: AtomicRule) {
  const base = operator === 'OR' ? 'OR' : 'AND';
  return isNotRule(rule) ? `${base} NOT` : base;
}

function isNotRule(rule: AtomicRule) {
  return rule.generated_comparison_operator?.startsWith('not') ?? false;
}

function signalRuleText(signal: IntentSignalDefinition) {
  return primaryRuleDescription(signal.trigger_rule_group) || signal.name || signal.description;
}

function sourcePolicySummary(policy: SourcePolicy, t: (key: string, options?: Record<string, unknown>) => string) {
  const localCount = policy.local_sources?.length ?? 0;
  if (policy.use_global_search_policy && localCount > 0) {
    return t('icpRadar.settings.globalAndLocalSources', { count: localCount });
  }
  if (policy.use_global_search_policy) {
    return t('icpRadar.settings.globalSources');
  }
  return t('icpRadar.settings.localSourceCount', { count: localCount });
}

function BooleanPill({ active }: { active: boolean }) {
  const { t } = useTranslation();
  return <Badge tone={active ? 'ally' : 'neutral'}>{active ? t('icpRadar.settings.yes') : t('icpRadar.settings.no')}</Badge>;
}

function deduplicationValue(value: string) {
  if (['source_url', 'source_url_and_signal', 'normalized_fact', 'none'].includes(value)) {
    return value;
  }
  if (value.includes('previous') || value.includes('evidence')) {
    return 'source_url_and_signal';
  }
  return 'normalized_fact';
}

function deduplicationKey(value: string) {
  return `icpRadar.settings.deduplicationPolicies.${deduplicationValue(value)}`;
}

function parseDuration(value: string) {
  const match = /^(\d+)\s+([a-zA-Z]+)$/.exec(value.trim());
  return {
    amount: match ? Number(match[1]) : 30,
    unit: match ? match[2] : 'days',
  };
}

function formatDuration(amount: string | number, unit: string) {
  const numericAmount = Number(amount);
  const safeAmount = Number.isFinite(numericAmount) && numericAmount > 0 ? Math.floor(numericAmount) : 1;
  return `${safeAmount} ${unit}`;
}

function durationUnitKey(unit: string) {
  return `icpRadar.settings.durationUnits.${unit}`;
}

function primaryRuleDescription(group: RuleGroup) {
  return group.rules[0]?.description ?? group.name ?? '';
}

function setPrimaryRuleDescription(group: RuleGroup, description: string): RuleGroup {
  const firstRule = group.rules[0] ?? newAtomicRule();
  const nextRule = { ...firstRule, description };
  return {
    ...group,
    rules: group.rules.length ? replaceAt(group.rules, 0, nextRule) : [nextRule],
    groups: [],
  };
}

function sameRubric(left: IntentSignalDefinition['scoring_rubric'], right: IntentSignalDefinition['scoring_rubric']) {
  return JSON.stringify(left.scale) === JSON.stringify(right.scale)
    && JSON.stringify(left.rules.map((rule) => rule.description)) === JSON.stringify(right.rules.map((rule) => rule.description));
}

function globalSignalRubric(definition: RadarDefinition) {
  return definition.intent_signals[0]?.scoring_rubric ?? {
    scale: [0, 1, 2],
    rules: [0, 1, 2].map((score) => ({ score, description: '', rule_group: newRuleGroup(`global-rubric-${score}`) })),
  };
}

function replaceAt<T>(items: T[], index: number, nextItem: T): T[] {
  return items.map((item, currentIndex) => (currentIndex === index ? nextItem : item));
}

function newSourceDefinition(): SourceDefinition {
  const id = `source-${Date.now()}`;
  return {
    source_id: id,
    source_type: 'url',
    label: '',
    reference: '',
    trust_level: 'cross_check',
  };
}

function newSourcePolicy(sourceIds: string[] = []): SourcePolicy {
  return {
    source_ids: sourceIds.slice(0, 1),
    source_logic: 'OR',
    use_global_search_policy: true,
    allow_additional_sources: true,
    fallback_confidence: 'hitl_required',
    local_sources: [],
  };
}

function newAtomicRule(): AtomicRule {
  const id = `rule-${Date.now()}`;
  return {
    rule_id: id,
    name: '',
    description: '',
    generated_target_field: '',
    generated_comparison_operator: '',
    generated_value: '',
    requirement_level: 'recommended',
    source_policy: newSourcePolicy(),
  };
}

function newRuleGroup(groupId: string): RuleGroup {
  return {
    group_id: groupId,
    name: '',
    operator: 'AND',
    rules: [],
    groups: [],
  };
}

function newIntentSignal(sourceIds: string[]): IntentSignalDefinition {
  const timestamp = Date.now();
  const code = `S${timestamp}`;
  const policy = newSourcePolicy(sourceIds);
  return {
    signal_id: `signal-${timestamp}`,
    code,
    name: '',
    description: '',
    trigger_rule_group: newRuleGroup(`trigger-${timestamp}`),
    source_policy: policy,
    scoring_rubric: {
      scale: [0, 1, 2],
      rules: [0, 1, 2].map((score) => ({
        score,
        description: '',
        rule_group: {
          group_id: `rubric-${timestamp}-${score}`,
          name: `${code} ${score}`,
          operator: 'AND',
          rules: [
            {
              ...newAtomicRule(),
              rule_id: `rubric-${timestamp}-${score}-rule`,
              name: `${code} ${score}`,
              generated_target_field: code,
              generated_comparison_operator: 'equals',
              generated_value: String(score),
              source_policy: policy,
            },
          ],
          groups: [],
        },
      })),
    },
  };
}

function loadRadarConfigOverrides(): Record<string, RadarConfigOverride> {
  try {
    const raw = window.localStorage.getItem(radarConfigStorageKey);
    if (!raw) {
      return {};
    }
    const parsed = JSON.parse(raw) as Record<string, RadarConfigOverride>;
    return Object.fromEntries(
      Object.entries(parsed)
        .filter(([, override]) => override?.radar?.radar_id)
        .map(([radarId, override]) => [
          radarId,
          {
            override_type: override.override_type === 'created' || override.override_type === 'deleted' ? override.override_type : 'edited',
            radar: normalizeRadarCatalogItem(override.radar),
            saved_at: override.saved_at || new Date(0).toISOString(),
          },
        ]),
    );
  } catch {
    window.localStorage.removeItem(radarConfigStorageKey);
    return {};
  }
}

function mergeRadarCatalog(
  catalog: ICPRadarCatalogArtifact | null,
  overrides: Record<string, RadarConfigOverride>,
) {
  if (!catalog) {
    return [];
  }
  const deletedIds = new Set(Object.entries(overrides)
    .filter(([, override]) => override.override_type === 'deleted')
    .map(([radarId]) => radarId));
  const merged = catalog.radars
    .filter((radar) => !deletedIds.has(radar.radar_id))
    .map((radar) => {
      const override = overrides[radar.radar_id];
      return normalizeRadarCatalogItem(override && override.override_type !== 'deleted' ? override.radar : radar);
    });
  const existingIds = new Set(merged.map((radar) => radar.radar_id));
  const created = Object.values(overrides)
    .filter((override) => override.override_type !== 'deleted' && !existingIds.has(override.radar.radar_id))
    .map((override) => normalizeRadarCatalogItem(override.radar));
  return [...merged, ...created];
}

function draftFromRadar(radar: ICPRadarCatalogItem): EditableRadarDefinitionDraft {
  return normalizeRadarDefinition(radar.definition);
}

function radarFromDraft(base: ICPRadarCatalogItem, draft: EditableRadarDefinitionDraft): ICPRadarCatalogItem {
  const definition = definitionFromDraft(draft);
  return {
    ...base,
    name: draft.metadata.name.trim(),
    owner: draft.metadata.owner.trim() || base.owner,
    status: base.artifact_path ? 'modified_locally' : 'local_draft',
    profile: {
      ...base.profile,
      icp_profile: draft.metadata.name,
      product: draft.scoring_model.fit_model.description,
      segment: draft.account_qualification.rule_group.name || draft.account_qualification.rule_group.group_id,
      scope: draft.metadata.description,
    },
    summary: {
      ...base.summary,
      cadence: draft.monitoring_policy.cadence,
      run_mode: draft.monitoring_policy.run_mode,
    },
    definition: normalizeRadarDefinition(definition),
  };
}

function createLocalRadarFromTemplate(
  template: RadarDefinition,
  name: string,
  owner: string,
  localDraftLimitation: string,
): ICPRadarCatalogItem {
  const id = `local-radar-${Date.now()}`;
  const definition: RadarDefinition = {
    ...cloneDefinition(template),
    definition_id: `${id}-definition`,
    metadata: {
      name,
      description: localDraftLimitation,
      owner,
      status: 'local_draft',
    },
    global_search_policy: {
      sources: [],
      keywords: [],
      exclusions: [],
      allow_system_sources: true,
    },
    intent_signals: [],
    monitoring_policy: {
      cadence: 'monthly',
      lookback_window: '30 days',
      run_mode: 'configured_not_generated',
      deduplication: 'dedupe_by_source_url_and_signal_code',
      stale_after: '180 days',
    },
  };

  return {
    radar_id: id,
    name,
    status: 'local_draft',
    owner,
    profile: {
      icp_profile: definition.metadata.name,
      product: '',
      segment: '',
      scope: definition.metadata.description,
    },
    summary: {
      cadence: definition.monitoring_policy.cadence,
      last_run: 'not_run',
      candidate_count: 0,
      needs_review_count: 0,
      accepted_count: 0,
      run_mode: definition.monitoring_policy.run_mode,
    },
    definition,
    artifact_path: null,
  };
}

function duplicateLocalRadar(radar: ICPRadarCatalogItem, name: string): ICPRadarCatalogItem {
  const id = `local-radar-${Date.now()}`;
  return {
    ...radar,
    radar_id: id,
    name,
    status: 'local_draft',
    summary: {
      ...radar.summary,
      last_run: 'not_run',
      candidate_count: 0,
      needs_review_count: 0,
      accepted_count: 0,
    },
    definition: {
      ...cloneDefinition(radar.definition),
      definition_id: `${id}-definition`,
      metadata: {
        ...radar.definition.metadata,
        name,
        status: 'local_draft',
      },
    },
    artifact_path: null,
  };
}

function normalizeRadarCatalogItem(radar: ICPRadarCatalogItem): ICPRadarCatalogItem {
  const definition = normalizeRadarDefinition(radar.definition);
  return {
    ...radar,
    radar_id: radar.radar_id || `radar-${Date.now()}`,
    name: radar.name || definition.metadata.name || 'ICP Radar',
    status: radar.status || definition.metadata.status || 'configured',
    owner: radar.owner || definition.metadata.owner || 'ABM Research',
    profile: {
      icp_profile: radar.profile?.icp_profile || definition.metadata.name || 'ICP Radar',
      product: radar.profile?.product || definition.scoring_model.fit_model.description || '',
      segment: radar.profile?.segment || definition.account_qualification.rule_group.name || '',
      scope: radar.profile?.scope || definition.metadata.description || '',
    },
    summary: {
      cadence: radar.summary?.cadence || definition.monitoring_policy.cadence || 'monthly',
      last_run: radar.summary?.last_run || 'not_run',
      candidate_count: Number.isFinite(Number(radar.summary?.candidate_count)) ? Number(radar.summary.candidate_count) : 0,
      needs_review_count: Number.isFinite(Number(radar.summary?.needs_review_count)) ? Number(radar.summary.needs_review_count) : 0,
      accepted_count: Number.isFinite(Number(radar.summary?.accepted_count)) ? Number(radar.summary.accepted_count) : 0,
      run_mode: radar.summary?.run_mode || definition.monitoring_policy.run_mode || 'configured_not_generated',
    },
    definition,
    artifact_path: radar.artifact_path ?? null,
  };
}

function normalizeRadarDefinition(definition: RadarDefinition): RadarDefinition {
  const fallbackDefinition = (definition ?? {}) as Partial<RadarDefinition>;
  const fallbackMetadata = (fallbackDefinition.metadata ?? {}) as Partial<RadarMetadata>;
  const fallbackGlobal = (fallbackDefinition.global_search_policy ?? {}) as Partial<GlobalSearchPolicy>;
  const fallbackMonitoring = (fallbackDefinition.monitoring_policy ?? {}) as Partial<MonitoringPolicy>;
  const fallbackScoring = (fallbackDefinition.scoring_model ?? {}) as Partial<RadarScoringModel>;
  const fallbackValidation = (fallbackDefinition.validation_report ?? {}) as Partial<RadarValidationReport>;
  const fitModel = (fallbackScoring.fit_model ?? {}) as Partial<RadarScoringModel['fit_model']>;
  const intentModel = (fallbackScoring.intent_model ?? {}) as Partial<RadarScoringModel['intent_model']>;
  const tierModel = (fallbackScoring.tier_model ?? {}) as Partial<RadarScoringModel['tier_model']>;

  return {
    definition_id: fallbackDefinition.definition_id || `definition-${Date.now()}`,
    metadata: {
      name: fallbackMetadata.name || 'ICP Radar',
      description: fallbackMetadata.description || '',
      owner: fallbackMetadata.owner || 'ABM Research',
      status: fallbackMetadata.status || 'configured',
    },
    global_search_policy: {
      sources: arrayOf(fallbackGlobal.sources).map(normalizeSourceDefinition),
      keywords: arrayOf(fallbackGlobal.keywords).map(String),
      exclusions: arrayOf(fallbackGlobal.exclusions).map(String),
      allow_system_sources: fallbackGlobal.allow_system_sources !== false,
    },
    account_qualification: {
      rule_group: normalizeRuleGroup(fallbackDefinition.account_qualification?.rule_group, 'qualification-root'),
    },
    intent_signals: arrayOf(fallbackDefinition.intent_signals).map(normalizeIntentSignal),
    monitoring_policy: {
      cadence: fallbackMonitoring.cadence || 'monthly',
      lookback_window: fallbackMonitoring.lookback_window || '30 days',
      run_mode: fallbackMonitoring.run_mode || 'configured_not_generated',
      deduplication: fallbackMonitoring.deduplication || 'dedupe_by_source_url_and_signal_code',
      stale_after: fallbackMonitoring.stale_after || '180 days',
    },
    scoring_model: {
      fit_model: {
        formula_preset: fitModel.formula_preset || 'weighted_average',
        description: fitModel.description || '',
        custom_formula: fitModel.custom_formula || '',
        uses: arrayOf(fitModel.uses).map(String),
      },
      intent_model: {
        formula_preset: intentModel.formula_preset || 'weighted_average',
        description: intentModel.description || '',
        custom_formula: intentModel.custom_formula || '',
        uses: arrayOf(intentModel.uses).map(String),
      },
      tier_model: {
        basis: tierModel.basis || 'fit + intent',
        description: tierModel.description || '',
      },
      tier_thresholds: fallbackScoring.tier_thresholds ?? {},
      confidence_penalties: fallbackScoring.confidence_penalties ?? {},
    },
    validation_report: {
      errors: arrayOf(fallbackValidation.errors),
      warnings: arrayOf(fallbackValidation.warnings),
      info: arrayOf(fallbackValidation.info),
    },
  };
}

function normalizeSourceDefinition(source: SourceDefinition): SourceDefinition {
  const fallbackSource = (source ?? {}) as Partial<SourceDefinition>;
  const label = fallbackSource.label || fallbackSource.reference || 'Source';
  const reference = fallbackSource.reference || '';
  return {
    source_id: fallbackSource.source_id || sourceIdFrom(label, reference),
    source_type: fallbackSource.source_type || 'url',
    label,
    reference,
    trust_level: fallbackSource.trust_level || 'cross_check',
  };
}

function normalizeSourcePolicy(policy: SourcePolicy | undefined): SourcePolicy {
  const fallbackPolicy = (policy ?? {}) as Partial<SourcePolicy>;
  return {
    source_ids: arrayOf(fallbackPolicy.source_ids).map(String),
    source_logic: fallbackPolicy.source_logic === 'AND' ? 'AND' : 'OR',
    use_global_search_policy: fallbackPolicy.use_global_search_policy !== false,
    allow_additional_sources: fallbackPolicy.allow_additional_sources !== false,
    fallback_confidence: fallbackPolicy.fallback_confidence || 'hitl_required',
    local_sources: arrayOf(fallbackPolicy.local_sources).map(normalizeSourceDefinition),
  };
}

function normalizeRuleGroup(group: RuleGroup | undefined, fallbackId: string): RuleGroup {
  const fallbackGroup = (group ?? {}) as Partial<RuleGroup>;
  return {
    group_id: fallbackGroup.group_id || fallbackId,
    name: fallbackGroup.name || '',
    operator: fallbackGroup.operator || 'AND',
    rules: arrayOf(fallbackGroup.rules).map(normalizeAtomicRule),
    groups: arrayOf(fallbackGroup.groups).map((nestedGroup, index) => normalizeRuleGroup(nestedGroup, `${fallbackId}-${index}`)),
  };
}

function normalizeAtomicRule(rule: AtomicRule): AtomicRule {
  const fallbackRule = (rule ?? {}) as Partial<AtomicRule>;
  const description = fallbackRule.description || fallbackRule.name || '';
  return {
    rule_id: fallbackRule.rule_id || ruleIdFrom(description),
    name: fallbackRule.name || description,
    description,
    generated_target_field: fallbackRule.generated_target_field || '',
    generated_comparison_operator: fallbackRule.generated_comparison_operator || '',
    generated_value: fallbackRule.generated_value || '',
    requirement_level: fallbackRule.requirement_level || 'recommended',
    source_policy: normalizeSourcePolicy(fallbackRule.source_policy),
  };
}

function normalizeIntentSignal(signal: IntentSignalDefinition): IntentSignalDefinition {
  const fallbackSignal = (signal ?? {}) as Partial<IntentSignalDefinition>;
  const code = fallbackSignal.code || fallbackSignal.signal_id || `S${Date.now()}`;
  const scoringRubric = fallbackSignal.scoring_rubric ?? { scale: [0, 1, 2], rules: [] };
  const scale = arrayOf(scoringRubric.scale).length ? arrayOf(scoringRubric.scale).map(Number) : [0, 1, 2];
  return {
    signal_id: fallbackSignal.signal_id || `signal-${code}`,
    code,
    name: fallbackSignal.name || code,
    description: fallbackSignal.description || '',
    trigger_rule_group: normalizeRuleGroup(fallbackSignal.trigger_rule_group, `trigger-${code}`),
    source_policy: normalizeSourcePolicy(fallbackSignal.source_policy),
    scoring_rubric: {
      scale,
      rules: scale.map((score) => {
        const sourceRule = arrayOf(scoringRubric.rules).find((rule) => Number(rule.score) === score);
        return {
          score,
          description: sourceRule?.description || '',
          rule_group: normalizeRuleGroup(sourceRule?.rule_group, `rubric-${code}-${score}`),
        };
      }),
    },
  };
}

function arrayOf<T>(value: T[] | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

function cloneDefinition(definition: RadarDefinition): RadarDefinition {
  return JSON.parse(JSON.stringify(definition)) as RadarDefinition;
}

function definitionFromDraft(draft: EditableRadarDefinitionDraft): RadarDefinition {
  return normalizeRadarDefinition(cloneDefinition(draft));
}

function validateRadarDraft(draft: EditableRadarDefinitionDraft, t: (key: string) => string) {
  const errors: string[] = [];
  if (!draft.metadata.name.trim()) {
    errors.push(t('icpRadar.validation.radarName'));
  }
  if (!draft.metadata.owner.trim()) {
    errors.push(t('icpRadar.validation.owner'));
  }
  if (!draft.monitoring_policy.cadence.trim()) {
    errors.push(t('icpRadar.validation.cadence'));
  }
  if (!draft.monitoring_policy.run_mode.trim()) {
    errors.push(t('icpRadar.validation.runMode'));
  }
  if (!draft.global_search_policy.sources.length && !draft.global_search_policy.allow_system_sources) {
    errors.push(t('icpRadar.validation.monitoringSources'));
  }
  return errors;
}

function sourceIdFrom(label: string, reference: string): string {
  const base = `${label || reference || 'source'}`
    .toLowerCase()
    .replace(/https?:\/\//g, '')
    .replace(/[^a-zа-я0-9]+/gi, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 48);
  return base || `source-${Date.now()}`;
}

function ruleIdFrom(label: string): string {
  const base = label
    .toLowerCase()
    .replace(/[^a-zа-я0-9]+/gi, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 48);
  return base ? `rule-${base}` : `rule-${Date.now()}`;
}

function isLocalRadarStatus(status: string) {
  return status === 'local_draft' || status === 'modified_locally';
}
