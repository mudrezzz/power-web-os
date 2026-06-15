import type { RadarDetailTab } from '../modelTypes';

export type RadarSourceKind = 'fixture' | 'live' | 'empty';

// Canonical view models are the boundary between raw radar artifacts and UI surfaces.
export type RadarViewModel = {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'active' | 'stopped';
  owner: string;
  sourceKind: RadarSourceKind;
  hasArtifact: boolean;
  tabs: RadarDetailTab[];
};

export type RadarCandidateScoreSlot = {
  key: 'total' | 'fit' | 'intent' | 'trigger';
  value: number | null;
  maxValue?: number | null;
};

export type RadarCandidateViewModel = {
  id: string;
  legalName: string;
  description: string;
  tier: string;
  evidenceCount: number;
  scoreSlots: RadarCandidateScoreSlot[];
  qualificationRows: Array<{ id: string; label: string; status: string; score?: number | null }>;
  signalRows: Array<{ id: string; label: string; status: string; score?: number | null }>;
  sourceRows: Array<{ id: string; label: string; url: string | null }>;
  journalRows: Array<{ label: string; value: string }>;
};
