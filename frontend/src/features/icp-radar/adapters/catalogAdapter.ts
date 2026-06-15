import type {
  ICPRadarArtifact,
  ICPRadarCatalogArtifact,
  ICPRadarCatalogItem,
  LiveICPRadarRunArtifact,
  RadarConfigOverride,
} from '../../../types';
import { mergeRadarCatalog } from '../settingsModel';
import { fixtureRadarToViewModel } from './fixtureRadarAdapter';
import { liveRadarToViewModel } from './liveRadarAdapter';
import type { RadarViewModel } from './viewModels';

// Catalog mapping is the only place that decides which raw artifact adapter owns a radar.
export function mergeCatalogWithOverrides(
  catalog: ICPRadarCatalogArtifact | null,
  overrides: Record<string, RadarConfigOverride>,
): ICPRadarCatalogItem[] {
  return mergeRadarCatalog(catalog, overrides);
}

export function radarToViewModel(
  radar: ICPRadarCatalogItem,
  activeFixtureRadarId: string,
  fixtureArtifact: ICPRadarArtifact | null,
  liveArtifact: LiveICPRadarRunArtifact | null,
): RadarViewModel {
  if (radar.radar_id === activeFixtureRadarId) {
    return fixtureRadarToViewModel(radar, fixtureArtifact);
  }
  if (radar.radar_id === 'toir-quick-live') {
    return liveRadarToViewModel(radar, liveArtifact);
  }
  return {
    id: radar.radar_id,
    name: radar.name,
    description: radar.definition.metadata.description || radar.profile.scope,
    status: radar.status === 'active' ? 'active' : radar.status === 'stopped' ? 'stopped' : 'draft',
    owner: radar.definition.metadata.owner || radar.owner,
    sourceKind: 'empty',
    hasArtifact: false,
    tabs: ['shortlist', 'settings'],
  };
}
