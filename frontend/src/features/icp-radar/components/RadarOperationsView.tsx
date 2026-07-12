import type { SignalMonitoringReportArtifact } from '../../../types';
import { useRadarWorkspace } from '../application/useRadarWorkspace';
import { LiveRadarOperationsTab } from '../liveOperations';

export function RadarOperationsView({
  signalMonitoringReport,
  workspace,
}: {
  signalMonitoringReport: SignalMonitoringReportArtifact | null;
  workspace: ReturnType<typeof useRadarWorkspace>;
}) {
  const { navigation } = workspace;
  if (workspace.radarViewModel?.sourceKind === 'live') {
    return (
      <LiveRadarOperationsTab
        artifact={workspace.selectedLiveArtifact}
        diagnosticsOpen={navigation.runDiagnosticsOpen}
        onCheckSetup={() => {
          navigation.setRunPreflightOpen(true);
          void workspace.checkRadarSetup(workspace.selectedRadar!.radar_id);
        }}
        onOpenSettings={() => navigation.setSelectedTab('settings')}
        onRunRadar={() => workspace.runRadar(workspace.selectedRadar!.radar_id)}
        onRunSignalMonitoring={() => {
          void workspace.runSignalMonitoring(workspace.selectedRadar!.radar_id);
        }}
        onCheckSignalMonitoringSetup={() => {
          void workspace.checkSignalMonitoringSetup(workspace.selectedRadar!.radar_id);
        }}
        onSelectSignalRun={(runId) => {
          void workspace.selectSignalRun(runId);
        }}
        onToggleDiagnostics={() => navigation.setRunDiagnosticsOpen(!navigation.runDiagnosticsOpen)}
        onTogglePreflight={() => navigation.setRunPreflightOpen(!navigation.runPreflightOpen)}
        preflightOpen={navigation.runPreflightOpen}
        preflightState={workspace.preflightState}
        radar={workspace.selectedRadar}
        runState={workspace.runState}
        signalMonitoringReport={workspace.runState.mode === 'api'
          ? workspace.selectedSignalReport
          : signalMonitoringReport}
        signalMonitoringSurface={workspace.runState.mode === 'api' ? workspace.selectedSignalSurface : null}
        signalPreflightState={workspace.signalPreflightState}
        signalRunHistory={workspace.selectedSignalRunHistory}
        signalRunState={workspace.signalRunState}
        selectedSignalRun={workspace.selectedSignalRun}
      />
    );
  }

  return null;
}
