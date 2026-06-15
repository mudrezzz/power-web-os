import type { RadarOperationalStatus } from './modelTypes';

export function radarStatusKey(status: string) {
  if (status === 'draft') {
    return 'icpRadar.radarStatus.draft';
  }
  if (status === 'active') {
    return 'icpRadar.radarStatus.active';
  }
  if (status === 'stopped') {
    return 'icpRadar.radarStatus.stopped';
  }
  if (status === 'configured') {
    return 'icpRadar.radarStatus.configured';
  }
  if (status === 'planned') {
    return 'icpRadar.radarStatus.planned';
  }
  if (status === 'local_draft') {
    return 'icpRadar.radarStatus.localDraft';
  }
  if (status === 'modified_locally') {
    return 'icpRadar.radarStatus.modifiedLocally';
  }
  return 'icpRadar.radarStatus.unknown';
}

export function radarOperationalStatus(status: string): RadarOperationalStatus {
  if (status === 'active') {
    return 'active';
  }
  if (status === 'stopped') {
    return 'stopped';
  }
  return 'draft';
}
