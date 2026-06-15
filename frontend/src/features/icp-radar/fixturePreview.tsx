import { ArrowRight, ExternalLink } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Eyebrow, Mono } from '../../components/primitives';
import type { CriterionEvidenceExplanation, ICPRadarArtifact, ICPRadarCandidate, IntentSignalDefinition } from '../../types';
import { fitSignalCodes, intentSignalCodes, triggerSignalCodes } from './model';

// Preview stays intentionally bounded: only the top evidence and criteria needed for scan decisions are shown.

export function CandidatePreview({
  artifact,
  candidate,
  onOpenDetails,
}: {
  artifact: ICPRadarArtifact;
  candidate: ICPRadarCandidate;
  onOpenDetails: () => void;
}) {
  const { t } = useTranslation();
  const qualificationRows = topCriteriaByCodes(artifact, candidate, fitSignalCodes, 5);
  const signalRows = topCriteriaByCodes(
    artifact,
    candidate,
    [...intentSignalCodes, ...triggerSignalCodes],
    5,
  );
  return (
    <div className="icp-candidate-preview">
      <div className="icp-preview-body">
        <header className="icp-preview-heading">
          <div>
            <Eyebrow>{t('icpRadar.previewEyebrow')}</Eyebrow>
            <strong>{candidate.legal_name}</strong>
          </div>
        </header>
        <div className="icp-preview-main">
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.canonicalPreview.summary')}</Eyebrow>
            <p>{candidate.main_signal}</p>
          </section>
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.canonicalPreview.tier')}</Eyebrow>
            <p>{candidate.comment || candidate.signal_summary}</p>
          </section>
        </div>
        <div className="icp-preview-lists">
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.canonicalPreview.qualification')}</Eyebrow>
            <div className="criteria-list criteria-list-compact">
              {(qualificationRows.length ? qualificationRows : topCriteria(artifact, candidate, 5)).map(({ criterion, value }) => (
                <div className="criterion-row" key={criterion.code}>
                  <Mono>{criterion.code}</Mono>
                  <span>
                    <strong>{criterion.name}</strong>
                  </span>
                  <Mono>{value}</Mono>
                </div>
              ))}
            </div>
          </section>
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.canonicalPreview.signals')}</Eyebrow>
            <div className="criteria-list criteria-list-compact">
              {(signalRows.length ? signalRows : topCriteria(artifact, candidate, 5)).map(({ criterion, value }) => (
                <div className="criterion-row" key={criterion.code}>
                  <Mono>{criterion.code}</Mono>
                  <span>
                    <strong>{criterion.name}</strong>
                  </span>
                  <Mono>{value}</Mono>
                </div>
              ))}
            </div>
          </section>
        </div>
        <div className="icp-preview-actions">
          <Button icon={<ArrowRight aria-hidden="true" />} variant="default" onClick={onOpenDetails}>
            {t('icpRadar.openDetails')}
          </Button>
        </div>
      </div>
    </div>
  );
}

export function topCriteria(artifact: ICPRadarArtifact, candidate: ICPRadarCandidate, count: number) {
  return artifact.radar.definition.intent_signals
    .map((signal) => ({
      criterion: signal,
      value: candidate.criteria_scores[signal.code] ?? 0,
    }))
    .filter((item): item is { criterion: IntentSignalDefinition; value: number } => item.value > 0)
    .sort((left, right) => right.value - left.value || left.criterion.code.localeCompare(right.criterion.code))
    .slice(0, count);
}

export function topCriteriaByCodes(artifact: ICPRadarArtifact, candidate: ICPRadarCandidate, codes: string[], count: number) {
  const codeSet = new Set(codes);
  return topCriteria(artifact, candidate, artifact.radar.definition.intent_signals.length)
    .filter((item) => codeSet.has(item.criterion.code))
    .slice(0, count);
}
