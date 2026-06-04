import { useEffect, useState } from 'react';
import { AppShell, type ScreenId } from './layout/AppShell';
import { AccessPlansScreen } from './screens/AccessPlansScreen';
import { AccountsScreen } from './screens/AccountsScreen';
import { AccountMapScreen } from './screens/AccountMapScreen';
import { PlannedScreen } from './screens/PlannedScreen';
import { PlaybookScreen } from './screens/PlaybookScreen';
import type { AccountRadarArtifact, AccountRadarItem, AccessPlanArtifact } from './types';

const radarArtifactUrl = '/demo/account_radar.json';

export function App() {
  const [activeScreen, setActiveScreen] = useState<ScreenId>('accounts');
  const [radarArtifact, setRadarArtifact] = useState<AccountRadarArtifact | null>(null);
  const [radarError, setRadarError] = useState<string | null>(null);
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);
  const [artifact, setArtifact] = useState<AccessPlanArtifact | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <AppShell activeScreen={activeScreen} artifact={artifact} onNavigate={setActiveScreen}>
      {activeScreen === 'accounts' ? (
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
