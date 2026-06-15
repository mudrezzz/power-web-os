import { useEffect, useState } from 'react';
import type { RadarConfigOverride } from '../../../types';
import { radarConfigStorageKey } from '../domain/constants';
import { loadRadarConfigOverrides } from '../settingsModel';

// Browser-local config overlays are a demo persistence boundary, not production storage.
export function useRadarConfigOverrides() {
  const [radarOverrides, setRadarOverrides] = useState<Record<string, RadarConfigOverride>>(() => loadRadarConfigOverrides());

  useEffect(() => {
    if (Object.keys(radarOverrides).length) {
      window.localStorage.setItem(radarConfigStorageKey, JSON.stringify(radarOverrides));
      return;
    }
    window.localStorage.removeItem(radarConfigStorageKey);
  }, [radarOverrides]);

  return { radarOverrides, setRadarOverrides };
}

