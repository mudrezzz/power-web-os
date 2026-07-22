import type { QualificationReviewDecision } from '../../types';

export type RadarDetailTab = 'shortlist' | 'operations' | 'settings';
export type CandidateDetailTab = 'overview' | 'qualification' | 'signals' | 'sources' | 'power_web' | 'journal' | 'trace';
export type RadarOperationalStatus = 'draft' | 'active' | 'stopped';
export type QualificationReviewOverlay = Record<string, QualificationReviewDecision>;

export const radarConfigStorageKey = 'power-web-os-icp-radar-config-overrides';
export const signalValidationStorageKey = 'power-web-os-icp-radar-signal-validation';
export const qualificationReviewStorageKey = 'power-web-os-icp-radar-qualification-review';
export const signalCodes = Array.from({ length: 20 }, (_, index) => `C${index + 1}`);
export const fitSignalCodes = ['C13', 'C14', 'C15', 'C16', 'C17'];
export const intentSignalCodes = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C18', 'C19'];
export const triggerSignalCodes = ['C10', 'C11', 'C12', 'C20'];
