import { ChevronDown, ChevronRight, Settings } from 'lucide-react';
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Card, Eyebrow, Mono } from '../../components/primitives';
import type { ICPRadarArtifact, ICPRadarCatalogItem, SignalValidationOverlay } from '../../types';
import { formatDelta, validatedCandidatesForArtifact } from './model';
import { CandidatePreview } from './fixturePreview';

// Fixture shortlist is optimized for scanning: scores stay in the row, and detail opens only through the preview action.

export function CandidateTable({
  artifact,
  expandedCandidateId,
  onOpenDetails,
  onToggleCandidate,
  radarId,
  signalValidation,
}: {
  artifact: ICPRadarArtifact;
  expandedCandidateId: string | null;
  onOpenDetails: (candidateId: string) => void;
  onToggleCandidate: (candidateId: string) => void;
  radarId: string;
  signalValidation: SignalValidationOverlay;
}) {
  const { t } = useTranslation();
  const candidates = useMemo(() => validatedCandidatesForArtifact(artifact, radarId, signalValidation), [artifact, radarId, signalValidation]);
  return (
    <Card>
      <div className="icp-radar-table-wrap" aria-label={t('icpRadar.tableAria')}>
        <div className="icp-radar-table">
          <div className="icp-radar-table-head">
            <span className="icp-sticky-cell">{t('icpRadar.columns.company')}</span>
            <span>{t('icpRadar.columns.total')}</span>
            <span>{t('icpRadar.columns.fit')}</span>
            <span>{t('icpRadar.columns.intent')}</span>
            <span>{t('icpRadar.columns.trigger')}</span>
            <span>{t('icpRadar.columns.tier')}</span>
            <span>{t('icpRadar.columns.evidence')}</span>
            <span>{t('icpRadar.columns.action')}</span>
          </div>
          {candidates.map(({ candidate, score }) => {
            const expanded = expandedCandidateId === candidate.account_id;
            const scoreDelta = score.effective_score.total_score - score.original_score.total_score;
            return (
              <div className="icp-candidate-record" key={candidate.account_id}>
                <button
                  aria-expanded={expanded}
                  className={`icp-candidate-row${expanded ? ' icp-candidate-row-selected' : ''}`}
                  type="button"
                  onClick={() => onToggleCandidate(candidate.account_id)}
                >
                  <span className="icp-company-cell icp-sticky-cell">
                    <span className="account-initials">{candidate.rank}</span>
                    <span>
                      <strong>{candidate.legal_name}</strong>
                      <small>{candidate.description}</small>
                    </span>
                  </span>
                  <span className="score-cell">
                    <span className="score-track">
                      <span className="score-fill" style={{ width: `${Math.min(100, score.effective_score.total_score * 2)}%` }} />
                    </span>
                    <Mono>{score.effective_score.total_score}</Mono>
                    {scoreDelta !== 0 && <span className="score-delta">{formatDelta(scoreDelta)}</span>}
                  </span>
                  <Mono>{score.effective_score.fit_score}</Mono>
                  <Mono>{score.effective_score.intent_score}</Mono>
                  <Mono>{score.effective_score.trigger_score}</Mono>
                  <span>
                    <Badge tone={score.effective_score.tier === 'Tier 1' ? 'ally' : 'neutral'}>{score.effective_score.tier}</Badge>
                  </span>
                  <Mono>{candidate.evidence_refs.length}</Mono>
                  <span className="row-action">
                    <span className="planned-action">{t('icpRadar.takeIntoWorkPlanned')}</span>
                    {expanded ? <ChevronDown aria-hidden="true" /> : <ChevronRight aria-hidden="true" />}
                  </span>
                </button>
                {expanded && (
                  <CandidatePreview
                    artifact={artifact}
                    candidate={candidate}
                    onOpenDetails={() => onOpenDetails(candidate.account_id)}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}

export function EmptyShortlist({
  radar,
  onOpenSettings,
}: {
  radar: ICPRadarCatalogItem;
  onOpenSettings: () => void;
}) {
  const { t } = useTranslation();
  return (
    <Card>
      <div className="icp-empty-shortlist">
        <span className="section-icon">
          <Settings aria-hidden="true" />
        </span>
        <div>
          <Eyebrow>{t('icpRadar.emptyShortlistEyebrow')}</Eyebrow>
          <h2>{t('icpRadar.emptyShortlistTitle')}</h2>
          <p>{t('icpRadar.emptyShortlistCopy', { radarName: radar.name })}</p>
        </div>
        <Button icon={<Settings aria-hidden="true" />} variant="default" onClick={onOpenSettings}>
          {t('icpRadar.openSettings')}
        </Button>
      </div>
    </Card>
  );
}
