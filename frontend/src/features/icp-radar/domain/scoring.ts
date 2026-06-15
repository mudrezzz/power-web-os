// Scoring helpers remain pure so fixture and live adapters can share score semantics.
export {
  buildCandidateScore,
  buildValidatedCandidateScore,
  formatDelta,
  validatedCandidatesForArtifact,
} from '../validationModel';

export {
  liveFitScoreMax,
  liveIntentScoreMax,
  liveTotalScore,
  liveTotalScoreMax,
  scoreWithMax,
} from '../liveModel';

