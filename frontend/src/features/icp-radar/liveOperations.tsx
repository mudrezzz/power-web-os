import { useState } from 'react';
import { Activity, Settings } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Button, Card, Eyebrow } from '../../components/primitives';
import type { ICPRadarCatalogItem, LiveICPRadarRunArtifact, SignalMonitoringReportArtifact } from '../../types';
import type { RadarPreflightControlState, RadarRunControlState } from './application/useRadarBackend';
import { RadarPipelineControlPanel } from './livePipelineControls';
import { LiveRadarPreflightPanel } from './livePreflightPanel';
import { LiveRadarRunDiagnosticsView } from './liveRunDiagnostics';

// Operations owns run controls and diagnostics so the found-accounts tab can stay result-focused.
export function LiveRadarOperationsTab({
  artifact,
  diagnosticsOpen,
  onCheckSetup,
  onOpenSettings,
  onRunRadar,
  onToggleDiagnostics,
  onTogglePreflight,
  preflightOpen,
  preflightState,
  radar,
  runState,
  signalMonitoringReport,
}: {
  artifact: LiveICPRadarRunArtifact | null;
  diagnosticsOpen: boolean;
  onCheckSetup: () => void;
  onOpenSettings: () => void;
  onRunRadar: () => void;
  onToggleDiagnostics: () => void;
  onTogglePreflight: () => void;
  preflightOpen: boolean;
  preflightState: RadarPreflightControlState;
  radar: ICPRadarCatalogItem | null;
  runState: RadarRunControlState;
  signalMonitoringReport: SignalMonitoringReportArtifact | null;
}) {
  const { t } = useTranslation();
  const [signalReportOpen, setSignalReportOpen] = useState(false);

  return (
    <div className="radar-operations-stack">
      <Card>
        <div className="radar-operations-heading">
          <span className="section-icon">
            <Activity aria-hidden="true" />
          </span>
          <div>
            <Eyebrow>{t('icpRadar.operations.eyebrow')}</Eyebrow>
            <h2>{t('icpRadar.operations.title')}</h2>
            <p>{t('icpRadar.operations.copy')}</p>
          </div>
          <Button icon={<Settings aria-hidden="true" />} variant="quiet" onClick={onOpenSettings}>
            {t('icpRadar.openSettings')}
          </Button>
        </div>
      </Card>

      <RadarPipelineControlPanel
        artifact={artifact}
        diagnosticsOpen={diagnosticsOpen}
        onCheckSetup={onCheckSetup}
        onRunCandidateDiscovery={onRunRadar}
        onToggleDiagnostics={onToggleDiagnostics}
        onTogglePreflight={onTogglePreflight}
        onToggleSignalReport={() => setSignalReportOpen((current) => !current)}
        preflightOpen={preflightOpen}
        radar={radar}
        runState={runState}
        signalMonitoringReport={signalMonitoringReport}
        signalReportOpen={signalReportOpen}
      />

      {preflightOpen && <LiveRadarPreflightPanel artifact={artifact} preflightState={preflightState} runState={runState} />}
      {diagnosticsOpen && <LiveRadarRunDiagnosticsView artifact={artifact} runState={runState} />}
    </div>
  );
}
