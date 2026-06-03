import { useEffect, useState } from 'react';
import { AppShell, type ScreenId } from './layout/AppShell';
import { AccessPlansScreen } from './screens/AccessPlansScreen';
import { PlannedScreen } from './screens/PlannedScreen';
import type { AccessPlanArtifact } from './types';

const artifactUrl = '/demo/access_plan.json';

export function App() {
  const [activeScreen, setActiveScreen] = useState<ScreenId>('plans');
  const [artifact, setArtifact] = useState<AccessPlanArtifact | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(artifactUrl)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Artifact request failed with ${response.status}`);
        }
        return response.json() as Promise<AccessPlanArtifact>;
      })
      .then(setArtifact)
      .catch((requestError: Error) => setError(requestError.message));
  }, []);

  return (
    <AppShell activeScreen={activeScreen} artifact={artifact} onNavigate={setActiveScreen}>
      {activeScreen === 'plans' ? (
        <AccessPlansScreen artifact={artifact} error={error} />
      ) : (
        <PlannedScreen screenId={activeScreen} />
      )}
    </AppShell>
  );
}
