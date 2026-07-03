import { useEffect, useState } from 'react';
import { AppShell, type ScreenId } from './layout/AppShell';
import { AccessPlansScreen } from './screens/AccessPlansScreen';
import { AccountsScreen } from './screens/AccountsScreen';
import { AccountMapScreen } from './screens/AccountMapScreen';
import { ICPRadarScreen } from './screens/ICPRadarScreen';
import { PlannedScreen } from './screens/PlannedScreen';
import { useRadarBackend } from './features/icp-radar/application/useRadarBackend';
import { signalMonitoringReportFromJson } from './features/icp-radar/signalMonitoringReport';
import { PlaybookScreen } from './screens/PlaybookScreen';
import type {
  AccountRadarArtifact,
  AccountRadarItem,
  AccessPlanArtifact,
  ICPRadarArtifact,
  ICPRadarCatalogArtifact,
  LiveICPRadarRunArtifact,
  SignalMonitoringReportArtifact,
} from './types';

const icpRadarCatalogUrl = '/demo/icp_radars.json';
const icpRadarArtifactUrl = '/demo/icp_radar.json';
const liveMiniRadarArtifactUrl = '/demo/live_mini_icp_radar_run.json';
const signalMonitoringReportUrl = '/demo/radar_signal_monitoring_report.json';
const radarArtifactUrl = '/demo/account_radar.json';

export function App() {
  const [activeScreen, setActiveScreen] = useState<ScreenId>('icp_radar');
  const [icpRadarCatalog, setIcpRadarCatalog] = useState<ICPRadarCatalogArtifact | null>(null);
  const [icpRadarCatalogError, setIcpRadarCatalogError] = useState<string | null>(null);
  const [icpRadarArtifact, setIcpRadarArtifact] = useState<ICPRadarArtifact | null>(null);
  const [icpRadarError, setIcpRadarError] = useState<string | null>(null);
  const [liveMiniRadarArtifact, setLiveMiniRadarArtifact] = useState<LiveICPRadarRunArtifact | null>(null);
  const [signalMonitoringReport, setSignalMonitoringReport] = useState<SignalMonitoringReportArtifact | null>(null);
  const [radarArtifact, setRadarArtifact] = useState<AccountRadarArtifact | null>(null);
  const [radarError, setRadarError] = useState<string | null>(null);
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);
  const [artifact, setArtifact] = useState<AccessPlanArtifact | null>(null);
  const [error, setError] = useState<string | null>(null);
  const icpRadarBackend = useRadarBackend({
    fallbackCatalog: icpRadarCatalog,
    fallbackLiveRunArtifact: liveMiniRadarArtifact,
  });

  useEffect(() => {
    fetch(icpRadarCatalogUrl)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`ICP Radar catalog request failed with ${response.status}`);
        }
        return response.json() as Promise<ICPRadarCatalogArtifact>;
      })
      .then(setIcpRadarCatalog)
      .catch((requestError: Error) => setIcpRadarCatalogError(requestError.message));
  }, []);

  useEffect(() => {
    fetch(icpRadarArtifactUrl)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`ICP Radar artifact request failed with ${response.status}`);
        }
        return response.json() as Promise<ICPRadarArtifact>;
      })
      .then(setIcpRadarArtifact)
      .catch((requestError: Error) => setIcpRadarError(requestError.message));
  }, []);

  useEffect(() => {
    fetch(liveMiniRadarArtifactUrl)
      .then((response) => {
        if (!response.ok) {
          return null;
        }
        return response.json() as Promise<LiveICPRadarRunArtifact>;
      })
      .then(setLiveMiniRadarArtifact)
      .catch(() => setLiveMiniRadarArtifact(null));
  }, []);

  useEffect(() => {
    fetch(signalMonitoringReportUrl)
      .then((response) => {
        if (!response.ok) {
          return null;
        }
        return response.json();
      })
      .then((payload) => setSignalMonitoringReport(signalMonitoringReportFromJson(payload)))
      .catch(() => setSignalMonitoringReport(null));
  }, []);

  useEffect(() => {
    fetch(radarArtifactUrl)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Radar artifact request failed with ${response.status}`);
        }
        return response.json() as Promise<AccountRadarArtifact>;
      })
      .then((radar) => {
        setRadarArtifact(radar);
        setSelectedAccountId((current) => current ?? radar.accounts[0]?.account_id ?? null);
      })
      .catch((requestError: Error) => setRadarError(requestError.message));
  }, []);

  useEffect(() => {
    const selected = radarArtifact?.accounts.find((item) => item.account_id === selectedAccountId);
    if (!selected) {
      return;
    }

    setError(null);
    fetch(selected.access_plan_path)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Access Plan artifact request failed with ${response.status}`);
        }
        return response.json() as Promise<AccessPlanArtifact>;
      })
      .then(setArtifact)
      .catch((requestError: Error) => setError(requestError.message));
  }, [radarArtifact, selectedAccountId]);

  function openAccount(item: AccountRadarItem) {
    setSelectedAccountId(item.account_id);
    setActiveScreen('plans');
  }

  const activeIcpRadarCatalog = icpRadarBackend.catalog ?? icpRadarCatalog;
  const activeLiveMiniRadarArtifact = icpRadarBackend.liveRunArtifact ?? liveMiniRadarArtifact;
  const activeIcpRadarError = activeIcpRadarCatalog ? icpRadarError : (icpRadarCatalogError ?? icpRadarError);

  return (
    <AppShell activeScreen={activeScreen} artifact={artifact} onNavigate={setActiveScreen}>
      {activeScreen === 'icp_radar' ? (
        <ICPRadarScreen
          artifact={icpRadarArtifact}
          backend={icpRadarBackend}
          catalog={activeIcpRadarCatalog}
          error={activeIcpRadarError}
          liveRunArtifact={activeLiveMiniRadarArtifact}
          signalMonitoringReport={signalMonitoringReport}
        />
      ) : activeScreen === 'accounts' ? (
        <AccountsScreen
          artifact={radarArtifact}
          error={radarError}
          selectedAccountId={selectedAccountId}
          onOpenAccount={openAccount}
        />
      ) : activeScreen === 'plans' ? (
        <AccessPlansScreen artifact={artifact} error={error} />
      ) : activeScreen === 'map' ? (
        <AccountMapScreen artifact={artifact} error={error} />
      ) : activeScreen === 'playbook' ? (
        <PlaybookScreen artifact={artifact} error={error} />
      ) : (
        <PlannedScreen screenId={activeScreen} />
      )}
    </AppShell>
  );
}
