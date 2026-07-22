import { CandidateTable, EmptyShortlist } from '../candidateViews';
import { LiveRadarShortlistTable } from '../liveCandidateViews';
import { useRadarWorkspace } from '../application/useRadarWorkspace';

export function RadarShortlist({ workspace }: { workspace: ReturnType<typeof useRadarWorkspace> }) {
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
        onOpenDetails={(candidateId) => workspace.openLiveCandidate(candidateId)}
        onOpenSettings={() => navigation.setSelectedTab('settings')}
        onPreparePowerWeb={(candidateId) => workspace.openLiveCandidate(candidateId, 'power_web')}
        onToggleCandidate={(candidateId) => navigation.setExpandedLiveCandidateId(
          navigation.expandedLiveCandidateId === candidateId ? null : candidateId,
        )}
        signalMonitoringSurface={workspace.selectedSignalSurface}
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
