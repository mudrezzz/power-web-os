import { ArrowRight, ChevronDown, ChevronRight, Play, Radar, RotateCw, Settings, ShieldCheck } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Card, Eyebrow, Mono } from '../../components/primitives';
import type { LiveICPRadarRunArtifact, LiveRadarCandidate } from '../../types';
import { liveTotalScore, qualificationAssessmentTone, qualificationRuleText, qualificationStatusToAssessment } from './model';
import type { RadarRunControlState } from './application/useRadarBackend';

// Live shortlist deliberately mirrors fixture shortlist: table scan, inline preview, then explicit detail navigation.

export function LiveRadarShortlistTable({
  artifact,
  expandedCandidateId,
  onOpenDetails,
  onOpenSettings,
  onRunRadar,
  onToggleCandidate,
  runState,
}: {
  artifact: LiveICPRadarRunArtifact | null;
  expandedCandidateId: string | null;
  onOpenDetails: (candidateId: string) => void;
  onOpenSettings: () => void;
  onRunRadar: () => void;
  onToggleCandidate: (candidateId: string) => void;
  runState: RadarRunControlState;
}) {
  const { t } = useTranslation();

  if (!artifact) {
    return (
      <Card>
        <div className="icp-empty-shortlist live-radar-empty">
          <span className="section-icon">
            <Radar aria-hidden="true" />
          </span>
          <div>
            <Eyebrow>{t('icpRadar.live.emptyEyebrow')}</Eyebrow>
            <h2>{t('icpRadar.live.emptyTitle')}</h2>
            <p>{t('icpRadar.live.emptyCopy')}</p>
            <code>python -m power_web_os.demo run-live-mini-icp-radar --live</code>
            <LiveRunStatus state={runState} />
          </div>
          <div className="live-radar-actions">
            <Button disabled={runState.busy || runState.mode === 'loading'} icon={<Play aria-hidden="true" />} variant="primary" onClick={onRunRadar}>
              {runState.busy ? t('icpRadar.live.runInProgress') : t('icpRadar.live.runRadar')}
            </Button>
            <Button icon={<Settings aria-hidden="true" />} variant="quiet" onClick={onOpenSettings}>
              {t('icpRadar.openSettings')}
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <div className="live-radar-run-toolbar">
          <div>
            <Eyebrow>{t('icpRadar.live.runEyebrow')}</Eyebrow>
            <LiveRunStatus state={runState} />
          </div>
          <Button disabled={runState.busy || runState.mode === 'loading'} icon={<RotateCw aria-hidden="true" />} variant="default" onClick={onRunRadar}>
            {runState.busy ? t('icpRadar.live.runInProgress') : t('icpRadar.live.runAgain')}
          </Button>
        </div>
      </Card>
      {artifact.candidates.length === 0 ? (
        <Card>
          <div className="icp-empty-shortlist">
            <span className="section-icon">
              <ShieldCheck aria-hidden="true" />
            </span>
            <div>
              <Eyebrow>{t('icpRadar.live.noCandidatesEyebrow')}</Eyebrow>
              <h2>{t('icpRadar.live.noCandidatesTitle')}</h2>
              <p>{t('icpRadar.live.noCandidatesCopy')}</p>
            </div>
          </div>
        </Card>
      ) : (
        <Card>
          <div className="icp-radar-table-wrap" aria-label={t('icpRadar.live.tableAria')}>
            <div className="icp-radar-table icp-radar-table-live">
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
              {artifact.candidates.map((candidate, index) => {
                const expanded = expandedCandidateId === candidate.candidate_id;
                return (
                  <div className="icp-candidate-record" key={candidate.candidate_id}>
                    <button
                      aria-expanded={expanded}
                      className={`icp-candidate-row${expanded ? ' icp-candidate-row-selected' : ''}`}
                      type="button"
                      onClick={() => onToggleCandidate(candidate.candidate_id)}
                    >
                      <span className="icp-company-cell icp-sticky-cell">
                        <span className="account-initials">{index + 1}</span>
                        <span>
                          <strong>{candidate.legal_name}</strong>
                          <small>{candidate.description || t('icpRadar.live.noDescription')}</small>
                        </span>
                      </span>
                      <span className="score-cell">
                        <span className="score-track">
                          <span className="score-fill" style={{ width: `${Math.min(100, liveTotalScore(candidate) * 10)}%` }} />
                        </span>
                        <Mono>{liveTotalScore(candidate)}</Mono>
                      </span>
                      <Mono>{candidate.score.fit_score}</Mono>
                      <Mono>{candidate.score.intent_score}</Mono>
                      <Mono>{t('icpRadar.notAvailable')}</Mono>
                      <span>
                        <Badge tone={candidate.score.tier === 'Tier 1' ? 'ally' : 'neutral'}>{candidate.score.tier}</Badge>
                      </span>
                      <Mono>{candidate.evidence_refs.length}</Mono>
                      <span className="row-action">
                        <span className="planned-action">{t('icpRadar.takeIntoWorkPlanned')}</span>
                        {expanded ? <ChevronDown aria-hidden="true" /> : <ChevronRight aria-hidden="true" />}
                      </span>
                    </button>
                    {expanded && (
                      <LiveRadarCandidatePreview
                        candidate={candidate}
                        onOpenDetails={() => onOpenDetails(candidate.candidate_id)}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </Card>
      )}
    </>
  );
}

function LiveRunStatus({ state }: { state: RadarRunControlState }) {
  const { t } = useTranslation();
  const status = state.status ?? (state.mode === 'api' ? 'ready' : state.mode);
  return (
    <div className="live-radar-run-status">
      <Badge tone={state.error ? 'blocker' : state.busy || state.outputPending ? 'unsurfaced' : state.mode === 'api' ? 'ally' : 'neutral'}>
        {t(`icpRadar.live.runStatus.${status}`, { defaultValue: status })}
      </Badge>
      <span>{t(`icpRadar.live.backendMode.${state.mode}`)}</span>
      {state.runId && <Mono>{state.runId}</Mono>}
      {state.outputPending && <span>{t('icpRadar.live.outputPending')}</span>}
      {state.error && <span className="live-radar-run-error">{state.error}</span>}
    </div>
  );
}

export function LiveRadarCandidatePreview({
  candidate,
  onOpenDetails,
}: {
  candidate: LiveRadarCandidate;
  onOpenDetails: () => void;
}) {
  const { t } = useTranslation();
  const topSignals = candidate.signals.filter((item) => item.status !== 'not_observed').slice(0, 5);
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
            <p>{candidate.description || t('icpRadar.live.noDescription')}</p>
          </section>
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.canonicalPreview.tier')}</Eyebrow>
            <p>{t('icpRadar.live.tierExplanation', {
              fit: candidate.score.fit_score,
              intent: candidate.score.intent_score,
              tier: candidate.score.tier,
            })}</p>
          </section>
        </div>
        <div className="icp-preview-lists">
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.canonicalPreview.qualification')}</Eyebrow>
            <div className="criteria-list criteria-list-compact">
              {candidate.qualification.slice(0, 5).map((item) => (
                <div className="criterion-row" key={item.criterion_code}>
                  <Mono>{item.criterion_code}</Mono>
                  <span>
                    <strong>{qualificationRuleText(item)}</strong>
                  </span>
                  <Badge tone={qualificationAssessmentTone(item.final_assessment || qualificationStatusToAssessment(item.status))}>
                    {t(`icpRadar.live.assessment.${item.final_assessment || qualificationStatusToAssessment(item.status)}`)}
                  </Badge>
                </div>
              ))}
            </div>
          </section>
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.canonicalPreview.signals')}</Eyebrow>
            <div className="criteria-list criteria-list-compact">
              {(topSignals.length ? topSignals : candidate.signals.slice(0, 5)).map((item) => (
                <div className="criterion-row" key={item.signal_code}>
                  <Mono>{item.signal_code}</Mono>
                  <span>
                    <strong>{item.signal}</strong>
                    <small>{item.summary}</small>
                  </span>
                  <Mono>{item.score}</Mono>
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
