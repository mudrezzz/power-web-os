import { lazy, Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, Eyebrow } from '../../components/primitives';
import type { ICPRadarArtifact, ICPRadarCatalogArtifact, LiveICPRadarRunArtifact } from '../../types';
import { useRadarWorkspace } from './application/useRadarWorkspace';
import {
  CandidateTable,
  EmptyShortlist,
  FixtureRadarCandidateDetailView,
} from './candidateViews';
import { LiveRadarCandidateDetailView, LiveRadarShortlistTable } from './liveCandidateViews';
import { RadarCatalogScreen } from './components/RadarCatalogScreen';
import { RadarDetailHeader } from './components/RadarDetailHeader';
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
  const workspace = useRadarWorkspace({ artifact, catalog, liveRunArtifact, t });
  const { navigation } = workspace;

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

  if (!workspace.selectedRadar) {
    return (
      <RadarCatalogScreen
        hasLocalChanges={workspace.mergedRadars.some((radar) => radar.status === 'local_draft' || radar.status === 'modified_locally')}
        radars={workspace.mergedRadars}
        onCreateRadar={workspace.createRadar}
        onOpenRadar={navigation.openRadar}
        onResetDemoChanges={workspace.resetDemoChanges}
      />
    );
  }

  if (workspace.detailCandidate && workspace.selectedFixtureArtifact && workspace.detailValidatedScore) {
    return (
      <FixtureRadarCandidateDetailView
        activeTab={navigation.candidateDetailTab}
        artifact={workspace.selectedFixtureArtifact}
        candidate={workspace.detailCandidate}
        onBack={() => navigation.setDetailCandidateId(null)}
        onDecisionChange={workspace.saveSignalValidationDecision}
        onResetValidation={() => workspace.resetCandidateSignalValidation(
          workspace.selectedRadar!.radar_id,
          workspace.detailCandidate!.account_id,
        )}
        onTabChange={navigation.setCandidateDetailTab}
        radarId={workspace.selectedRadar!.radar_id}
        radarName={workspace.selectedRadar!.name}
        signalValidation={workspace.signalValidation}
        sourcesById={workspace.sourcesById}
        validatedScore={workspace.detailValidatedScore}
      />
    );
  }

  if (workspace.detailLiveCandidate && workspace.selectedLiveArtifact) {
    return (
      <LiveRadarCandidateDetailView
        activeTab={navigation.candidateDetailTab}
        artifact={workspace.selectedLiveArtifact}
        candidate={workspace.detailLiveCandidate}
        onBack={() => navigation.setDetailLiveCandidateId(null)}
        onQualificationReviewChange={workspace.saveQualificationReviewDecision}
        onSignalDecisionChange={workspace.saveSignalValidationDecision}
        onSignalDecisionReset={workspace.resetSignalValidationDecision}
        onTabChange={navigation.setCandidateDetailTab}
        qualificationReview={workspace.qualificationReview}
        radarId={workspace.selectedRadar.radar_id}
        radarName={workspace.selectedRadar.name}
        signalValidation={workspace.signalValidation}
      />
    );
  }

  return (
    <section className="screen icp-radar-screen" aria-label={t('icpRadar.aria')}>
      <RadarDetailHeader
        activeTab={navigation.selectedTab}
        artifact={workspace.selectedFixtureArtifact}
        dirty={workspace.settingsDirty}
        draft={workspace.settingsDraft}
        editingBlock={workspace.editingBlock}
        isLocalDraft={workspace.selectedRadarOverride !== undefined}
        onBack={navigation.backToCatalog}
        onDelete={() => workspace.deleteRadar(workspace.selectedRadar!)}
        onDiscard={workspace.discardSettingsDraft}
        onDraftChange={workspace.setSettingsDraft}
        onDuplicate={() => workspace.duplicateRadar(workspace.selectedRadar!)}
        onEditHeader={workspace.startHeaderEdit}
        onReset={() => workspace.resetRadarToArtifact(workspace.selectedRadar!.radar_id)}
        onSave={workspace.saveSettingsDraft}
        onTabChange={navigation.setSelectedTab}
        overrideType={workspace.selectedRadarOverride?.override_type}
        radar={workspace.selectedRadar}
        validationErrors={workspace.validationErrors}
      />

      {navigation.selectedTab === 'settings' && workspace.activeSettingsDraft ? (
        <Suspense fallback={(
          <Card>
            <Eyebrow>{t('icpRadar.settings.loading')}</Eyebrow>
          </Card>
        )}
        >
          <RadarSettings
            dirty={workspace.settingsDirty}
            draft={workspace.activeSettingsDraft}
            editingBlock={workspace.editingBlock}
            onCancel={workspace.discardSettingsDraft}
            onDraftChange={workspace.setSettingsDraft}
            onEdit={workspace.setEditingBlock}
            onSave={workspace.saveSettingsDraft}
            validationErrors={workspace.validationErrors}
          />
        </Suspense>
      ) : (
        <RadarShortlist workspace={workspace} />
      )}
    </section>
  );
}

function RadarShortlist({ workspace }: { workspace: ReturnType<typeof useRadarWorkspace> }) {
  const { navigation } = workspace;
  if (workspace.selectedFixtureArtifact) {
    return (
      <CandidateTable
        artifact={workspace.selectedFixtureArtifact}
        expandedCandidateId={navigation.expandedCandidateId}
        onOpenDetails={navigation.setDetailCandidateId}
        onToggleCandidate={(candidateId) => navigation.setExpandedCandidateId(
          navigation.expandedCandidateId === candidateId ? null : candidateId,
        )}
        radarId={workspace.selectedRadar!.radar_id}
        signalValidation={workspace.signalValidation}
      />
    );
  }

  if (workspace.radarViewModel?.sourceKind === 'live') {
    return (
      <LiveRadarShortlistTable
        artifact={workspace.selectedLiveArtifact}
        expandedCandidateId={navigation.expandedLiveCandidateId}
        onOpenDetails={navigation.setDetailLiveCandidateId}
        onOpenSettings={() => navigation.setSelectedTab('settings')}
        onToggleCandidate={(candidateId) => navigation.setExpandedLiveCandidateId(
          navigation.expandedLiveCandidateId === candidateId ? null : candidateId,
        )}
      />
    );
  }

  return (
    <EmptyShortlist
      radar={workspace.selectedRadar!}
      onOpenSettings={() => navigation.setSelectedTab('settings')}
    />
  );
}
