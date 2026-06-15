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
import { lazy, Suspense, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Card, Eyebrow, Mono } from '../../components/primitives';
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
  QualificationAssessmentStatus,
  QualificationReviewDecision,
  QualificationSourceUsage,
  SourceDefinition,
  SourcePolicy,
  ValidatedCandidateScore,
} from '../../types';
import {
  CandidateTable,
  EmptyShortlist,
  FixtureRadarCandidateDetailView,
} from './candidateViews';
import {
  LiveRadarCandidateDetailView,
  LiveRadarShortlistTable,
} from './liveCandidateViews';
import {
  type CandidateDetailTab,
  type QualificationReviewOverlay,
  type RadarDetailTab,
  type RadarOperationalStatus,
  buildValidatedCandidateScore,
  cadenceKey,
  createLocalRadarFromTemplate,
  draftFromRadar,
  duplicateLocalRadar,
  effectiveQualificationAssessment,
  fallbackQualificationSourceUsages,
  fitSignalCodes,
  formatDelta,
  intentSignalCodes,
  isLocalRadarStatus,
  lastRunKey,
  liveFitScoreMax,
  liveIntentScoreMax,
  liveRuntimeKey,
  liveSignalTone,
  liveTotalScore,
  liveTotalScoreMax,
  loadQualificationReviewOverlay,
  loadRadarConfigOverrides,
  loadSignalValidationOverlay,
  mergeRadarCatalog,
  qualificationAssessmentTone,
  qualificationCrossValidationTone,
  qualificationDecisionTone,
  qualificationOperatorLabel,
  qualificationReviewKey,
  qualificationRuleId,
  qualificationRuleText,
  qualificationStatusToAssessment,
  qualificationTrustTone,
  radarConfigStorageKey,
  radarFromDraft,
  radarOperationalStatus,
  radarStatusKey,
  runModeKey,
  scoreWithMax,
  signalCodes,
  signalValidationKey,
  signalValidationStorageKey,
  triggerSignalCodes,
  validateRadarDraft,
  validatedCandidatesForArtifact,
  validationForCandidate,
  validationRank,
  validationStatusKey,
  validationTone,
  qualificationReviewStorageKey,
  normalizeRadarCatalogItem,
} from './model';
import { RadarHeaderEditor, type SettingsBlockId } from './settingsHeader';
import './icpRadar.css';

const RadarSettings = lazy(() => import('./settings').then((module) => ({ default: module.RadarSettings })));

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
  const [qualificationReview, setQualificationReview] = useState<QualificationReviewOverlay>(() => loadQualificationReviewOverlay());
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
    if (Object.keys(qualificationReview).length) {
      window.localStorage.setItem(qualificationReviewStorageKey, JSON.stringify(qualificationReview));
      return;
    }
    window.localStorage.removeItem(qualificationReviewStorageKey);
  }, [qualificationReview]);

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

  function saveQualificationReviewDecision(
    radarId: string,
    candidateId: string,
    ruleId: string,
    decision: QualificationReviewDecision | null,
  ) {
    const key = qualificationReviewKey(radarId, candidateId, ruleId);
    setQualificationReview((current) => {
      const next = { ...current };
      if (decision) {
        next[key] = decision;
      } else {
        delete next[key];
      }
      return next;
    });
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
        onQualificationReviewChange={saveQualificationReviewDecision}
        onTabChange={setCandidateDetailTab}
        qualificationReview={qualificationReview}
        radarId={selectedRadar.radar_id}
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
        <Suspense fallback={(
          <Card>
            <Eyebrow>{t('icpRadar.settings.loading')}</Eyebrow>
          </Card>
        )}
        >
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
        </Suspense>
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

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
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
