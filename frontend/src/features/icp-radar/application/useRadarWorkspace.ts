import { useEffect, useMemo, useState } from 'react';
import type {
  EditableRadarDefinitionDraft,
  ICPRadarArtifact,
  ICPRadarCatalogArtifact,
  ICPRadarCatalogItem,
  LiveICPRadarRunArtifact,
  QualificationReviewDecision,
  RadarConfigOverride,
  SignalValidationDecision,
  SourceDefinition,
} from '../../../types';
import { radarToViewModel, mergeCatalogWithOverrides } from '../adapters/catalogAdapter';
import { buildValidatedCandidateScore } from '../domain/scoring';
import { validationForCandidate } from '../domain/validation';
import {
  createLocalRadarFromTemplate,
  draftFromRadar,
  duplicateLocalRadar,
  normalizeRadarCatalogItem,
  radarFromDraft,
  validateRadarDraft,
} from '../settingsModel';
import type { SettingsBlockId } from '../settingsHeader';
import { useQualificationReviewOverlay } from './useQualificationReviewOverlay';
import { useRadarConfigOverrides } from './useRadarConfigOverrides';
import { useRadarNavigation } from './useRadarNavigation';
import { useSignalValidationOverlay } from './useSignalValidationOverlay';
import type { RadarBackendController } from './useRadarBackend';

type Translate = (key: string, options?: Record<string, unknown>) => string;

// The workspace hook composes adapters, navigation, and local overlays for the feature entrypoint.
export function useRadarWorkspace({
  artifact,
  catalog,
  liveRunArtifact,
  backend,
  t,
}: {
  artifact: ICPRadarArtifact | null;
  catalog: ICPRadarCatalogArtifact | null;
  liveRunArtifact: LiveICPRadarRunArtifact | null;
  backend: RadarBackendController;
  t: Translate;
}) {
  const navigation = useRadarNavigation();
  const { radarOverrides, setRadarOverrides } = useRadarConfigOverrides();
  const {
    signalValidation,
    saveSignalValidationDecision,
    resetCandidateSignalValidation,
    resetSignalValidationDecision,
  } = useSignalValidationOverlay();
  const { qualificationReview, saveQualificationReviewDecision } = useQualificationReviewOverlay();
  const [settingsDraft, setSettingsDraft] = useState<EditableRadarDefinitionDraft | null>(null);
  const [savedSettingsDraftSnapshot, setSavedSettingsDraftSnapshot] = useState('');
  const [editingBlock, setEditingBlock] = useState<SettingsBlockId | null>(null);

  const mergedRadars = useMemo(() => mergeCatalogWithOverrides(catalog, radarOverrides), [catalog, radarOverrides]);
  const selectedRadar = mergedRadars.find((item) => item.radar_id === navigation.selectedRadarId) ?? null;
  const selectedRadarOverride = selectedRadar ? radarOverrides[selectedRadar.radar_id] : undefined;
  const activeFixtureRadarId = catalog?.workflow_metadata.active_fixture_radar_id ?? 'toir-sibur';
  const selectedFixtureArtifact = selectedRadar?.radar_id === activeFixtureRadarId ? artifact : null;
  const selectedLiveArtifact = selectedRadar?.radar_id === 'toir-quick-live' ? liveRunArtifact : null;
  const apiBackedLiveArtifact = Boolean(selectedLiveArtifact && backend.runState.mode === 'api');
  const radarViewModel = selectedRadar
    ? radarToViewModel(selectedRadar, activeFixtureRadarId, selectedFixtureArtifact, selectedLiveArtifact)
    : null;
  const detailCandidate = artifact?.candidates.find((item) => item.account_id === navigation.detailCandidateId) ?? null;
  const detailLiveCandidate = selectedLiveArtifact?.candidates.find((item) => item.candidate_id === navigation.detailLiveCandidateId) ?? null;
  const sourcesById = useMemo(() => {
    const entries = selectedFixtureArtifact?.radar.definition.global_search_policy.sources.map((source) => [source.source_id, source]) ?? [];
    return new Map(entries as Array<[string, SourceDefinition]>);
  }, [selectedFixtureArtifact]);
  const validationErrors = settingsDraft ? validateRadarDraft(settingsDraft, t) : [];
  const settingsDirty = settingsDraft ? JSON.stringify(settingsDraft) !== savedSettingsDraftSnapshot : false;
  const detailValidatedScore = detailCandidate && selectedRadar
    ? buildValidatedCandidateScore(detailCandidate, validationForCandidate(signalValidation, selectedRadar.radar_id, detailCandidate.account_id))
    : null;

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
    navigation.setSelectedRadarId(created.radar_id);
    navigation.setSelectedTab('settings');
    setEditingBlock('overview');
    navigation.clearCandidateState();
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
    navigation.setSelectedRadarId(normalizedRadar.radar_id);
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
    navigation.setSelectedRadarId(null);
    navigation.setSelectedTab('shortlist');
    navigation.clearCandidateState();
  }

  function resetRadarToArtifact(radarId: string) {
    setRadarOverrides((current) => {
      const next = { ...current };
      delete next[radarId];
      return next;
    });
    if (!catalog?.radars.some((radar) => radar.radar_id === radarId)) {
      navigation.setSelectedRadarId(null);
      navigation.setSelectedTab('shortlist');
    }
    setEditingBlock(null);
  }

  function resetDemoChanges() {
    setRadarOverrides({});
    navigation.setSelectedRadarId(null);
    navigation.setSelectedTab('shortlist');
    setEditingBlock(null);
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
    navigation.setSelectedRadarId(duplicate.radar_id);
    navigation.setSelectedTab('settings');
    setEditingBlock('overview');
  }

  function startHeaderEdit() {
    navigation.setSelectedTab('settings');
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

  async function saveLiveQualificationReviewDecision(
    radarId: string,
    candidateId: string,
    ruleId: string,
    decision: QualificationReviewDecision | null,
  ) {
    if (await backend.saveQualificationReview(radarId, candidateId, ruleId, decision)) {
      return;
    }
    saveQualificationReviewDecision(radarId, candidateId, ruleId, decision);
  }

  async function saveLiveSignalDecision(decision: SignalValidationDecision) {
    if (await backend.saveSignalReview(decision)) {
      return;
    }
    saveSignalValidationDecision(decision);
  }

  async function resetLiveSignalDecision(radarId: string, candidateId: string, signalCode: string) {
    if (await backend.resetSignalReview(radarId, candidateId, signalCode)) {
      return;
    }
    resetSignalValidationDecision(radarId, candidateId, signalCode);
  }

  return {
    navigation,
    mergedRadars,
    selectedRadar,
    selectedRadarOverride,
    selectedFixtureArtifact,
    selectedLiveArtifact,
    radarViewModel,
    detailCandidate,
    detailLiveCandidate,
    detailValidatedScore,
    settingsDraft,
    activeSettingsDraft: selectedRadar ? settingsDraft ?? draftFromRadar(selectedRadar) : null,
    setSettingsDraft,
    editingBlock,
    setEditingBlock,
    settingsDirty,
    sourcesById,
    validationErrors,
    signalValidation,
    liveSignalValidation: apiBackedLiveArtifact ? {} : signalValidation,
    qualificationReview,
    liveQualificationReview: apiBackedLiveArtifact ? {} : qualificationReview,
    saveSignalValidationDecision,
    saveQualificationReviewDecision: saveLiveQualificationReviewDecision,
    saveLiveSignalDecision,
    resetLiveSignalDecision,
    resetCandidateSignalValidation,
    resetSignalValidationDecision,
    runState: backend.runState,
    preflightState: backend.preflightState,
    checkRadarSetup: backend.checkRadarSetup,
    runRadar: backend.runRadar,
    createRadar,
    deleteRadar,
    resetRadarToArtifact,
    resetDemoChanges,
    duplicateRadar,
    startHeaderEdit,
    saveSettingsDraft,
    discardSettingsDraft,
  };
}
