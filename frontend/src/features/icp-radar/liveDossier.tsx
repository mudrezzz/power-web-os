import { ExternalLink } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Badge, Mono } from '../../components/primitives';
import type { LiveICPRadarRunArtifact, LiveRadarCandidate, LiveRadarJournalEvent, LiveRadarRunDossier } from '../../types';
import { liveRuntimeKey } from './model';

export function LiveRunJournalFallback({
  artifact,
  events,
}: {
  artifact: LiveICPRadarRunArtifact;
  events: LiveRadarJournalEvent[];
}) {
  const { t } = useTranslation();
  return (
    <>
      <dl className="icp-definition-list">
        <div>
          <dt>{t('icpRadar.live.runtime')}</dt>
          <dd>{t(liveRuntimeKey(artifact.run_metadata.runtime))}</dd>
        </div>
        <div>
          <dt>{t('icpRadar.live.model')}</dt>
          <dd>{artifact.run_metadata.model ?? t('icpRadar.unknown')}</dd>
        </div>
        <div>
          <dt>{t('icpRadar.live.webMode')}</dt>
          <dd>{artifact.run_metadata.web_mode ?? t('icpRadar.unknown')}</dd>
        </div>
        <div>
          <dt>{t('icpRadar.live.queries')}</dt>
          <dd>{artifact.run_metadata.query_count}</dd>
        </div>
        <div>
          <dt>{t('icpRadar.live.sources')}</dt>
          <dd>{artifact.run_metadata.source_count}</dd>
        </div>
        <div>
          <dt>{t('icpRadar.canonicalDetail.runAt')}</dt>
          <dd>{artifact.run_metadata.run_at}</dd>
        </div>
      </dl>
      <div className="canonical-journal-list">
        {events.length > 0 ? events.map((event) => (
          <DossierJournalEventRow event={event} key={event.event_id} />
        )) : artifact.search_plan.queries.length > 0 ? artifact.search_plan.queries.map((query) => (
          <div className="canonical-journal-row" key={query.query_id}>
            <Mono>{query.query_id}</Mono>
            <strong>{query.query}</strong>
            <small>{query.purpose}</small>
          </div>
        )) : (
          <div className="canonical-journal-row">
            <Mono>0</Mono>
            <strong>{t('icpRadar.live.journal.empty')}</strong>
            <small>{t('icpRadar.live.journal.emptyCopy')}</small>
          </div>
        )}
      </div>
    </>
  );
}

export function LiveRunDossierPanel({
  artifact,
  candidate,
  dossier,
}: {
  artifact: LiveICPRadarRunArtifact;
  candidate: LiveRadarCandidate;
  dossier: LiveRadarRunDossier;
}) {
  const { t } = useTranslation();
  const taskContextEntries = readableEntries(dossier.run_context.task_context);
  const visibleTimeline = dossier.timeline.filter((event) => event.visibility !== 'debug');
  const discoverySteps = dossier.discovery_plan.steps ?? [];
  const sourcePolicyDecisions = dossier.source_policy_decisions.length > 0
    ? dossier.source_policy_decisions
    : dossier.discovery_plan.source_policy_decisions ?? [];
  const coverageWarnings = [
    ...(dossier.coverage_summary.warnings ?? []),
    ...(dossier.discovery_plan.warnings ?? []),
  ].filter(Boolean);
  const coverageHypotheses = dossier.coverage_summary.hypotheses ?? dossier.discovery_plan.coverage_hypotheses ?? [];
  return (
    <div className="run-dossier">
      <section className="run-dossier-section">
        <h3>{t('icpRadar.live.dossier.run')}</h3>
        <dl className="run-dossier-facts">
          <div>
            <dt>{t('icpRadar.live.dossier.status')}</dt>
            <dd>{t(`icpRadar.live.runStatus.${dossier.run_context.status}`, { defaultValue: dossier.run_context.status })}</dd>
          </div>
          <div>
            <dt>{t('icpRadar.live.dossier.runId')}</dt>
            <dd><Mono>{dossier.run_context.run_id}</Mono></dd>
          </div>
          <div>
            <dt>{t('icpRadar.live.model')}</dt>
            <dd>{dossier.run_context.model ?? artifact.run_metadata.model ?? t('icpRadar.unknown')}</dd>
          </div>
          <div>
            <dt>{t('icpRadar.live.webMode')}</dt>
            <dd>{dossier.run_context.web_mode ?? artifact.run_metadata.web_mode ?? t('icpRadar.unknown')}</dd>
          </div>
          <div>
            <dt>{t('icpRadar.live.dossier.requester')}</dt>
            <dd>{dossier.run_context.requester || t('icpRadar.unknown')}</dd>
          </div>
          <div>
            <dt>{t('icpRadar.live.dossier.definitionVersion')}</dt>
            <dd>{dossier.definition_snapshot?.definition_version ?? t('icpRadar.unknown')}</dd>
          </div>
        </dl>
      </section>

      <section className="run-dossier-section">
        <h3>{t('icpRadar.live.dossier.input')}</h3>
        <div className="run-dossier-grid">
          <DossierMetric label={t('icpRadar.live.dossier.qualificationRules')} value={artifact.radar.qualification_criteria.length} />
          <DossierMetric label={t('icpRadar.live.dossier.intentSignals')} value={artifact.radar.intent_signals.length} />
          <DossierMetric label={t('icpRadar.live.dossier.sources')} value={dossier.summary.source_count} />
          <DossierMetric label={t('icpRadar.live.dossier.reviewFlags')} value={dossier.summary.review_flag_count} />
        </div>
        <div className="run-dossier-card">
          <strong>{artifact.radar.name}</strong>
          <p>{artifact.radar.description || candidate.description || t('icpRadar.live.noDescription')}</p>
        </div>
        <div className="run-dossier-tags">
          {taskContextEntries.length > 0 ? taskContextEntries.map(([key, value]) => (
            <span key={key}><Mono>{key}</Mono>{value}</span>
          )) : <span>{t('icpRadar.live.dossier.noTaskContext')}</span>}
        </div>
      </section>

      <section className="run-dossier-section">
        <h3>{t('icpRadar.live.dossier.discoveryPlan')}</h3>
        <div className="run-dossier-grid">
          <DossierMetric label={t('icpRadar.live.dossier.usedSources')} value={dossier.summary.used_source_count} />
          <DossierMetric label={t('icpRadar.live.dossier.analyzedSources')} value={dossier.summary.analyzed_source_count} />
          <DossierMetric label={t('icpRadar.live.dossier.skippedSources')} value={dossier.summary.skipped_source_count} />
          <DossierMetric label={t('icpRadar.live.dossier.rejectedCandidates')} value={dossier.coverage_summary.rejected_candidate_count ?? 0} />
        </div>
        {dossier.discovery_plan.plan_summary && (
          <div className="run-dossier-card">
            <strong>{t('icpRadar.live.dossier.plannerSummary')}</strong>
            <p>{dossier.discovery_plan.plan_summary}</p>
          </div>
        )}
        <div className="run-dossier-query-list">
          {discoverySteps.length > 0 ? discoverySteps.map((step) => (
            <article className="run-dossier-card" key={step.step_id}>
              <header className="run-dossier-card-head">
                <Mono>{step.step_id}</Mono>
                <Badge tone="neutral">{t(`icpRadar.live.dossier.stage.${step.stage}`, { defaultValue: step.stage })}</Badge>
              </header>
              <strong>{step.query}</strong>
              <p>{step.purpose || t('icpRadar.live.journal.noSummary')}</p>
              <div className="run-dossier-tags">
                {step.source_scope && <span><Mono>{t('icpRadar.live.dossier.sourceScope')}</Mono>{step.source_scope}</span>}
                {step.subject_rule_ids?.map((ruleId) => <span key={`${step.step_id}-${ruleId}`}><Mono>{t('icpRadar.live.dossier.rule')}</Mono>{ruleId}</span>)}
                {step.source_ids?.map((sourceId) => <span key={`${step.step_id}-${sourceId}`}><Mono>{t('icpRadar.live.dossier.sourceBase')}</Mono>{sourceId}</span>)}
              </div>
              <DossierRefs label={t('icpRadar.live.dossier.expectedEvidence')} refs={step.expected_evidence ?? []} />
              <DossierRefs label={t('icpRadar.live.dossier.acceptanceCriteria')} refs={step.acceptance_criteria ?? []} />
              <DossierRefs label={t('icpRadar.live.dossier.dependsOn')} refs={step.depends_on ?? []} />
            </article>
          )) : <p>{t('icpRadar.live.dossier.noDiscoveryPlan')}</p>}
        </div>
      </section>

      <section className="run-dossier-section">
        <h3>{t('icpRadar.live.dossier.sourcePolicy')}</h3>
        <div className="run-dossier-source-list">
          {sourcePolicyDecisions.length > 0 ? sourcePolicyDecisions.map((decision) => (
            <article className="run-dossier-source" key={`${decision.source_id}-${decision.decision}`}>
              <header className="run-dossier-card-head">
                <Mono>{decision.source_id}</Mono>
                <Badge tone={decision.decision === 'selected' ? 'ally' : 'neutral'}>
                  {t(`icpRadar.live.dossier.sourceDecision.${decision.decision}`, { defaultValue: decision.decision })}
                </Badge>
              </header>
              <strong>{decision.source_label || decision.source_id}</strong>
              <p>{decision.reason || t('icpRadar.live.journal.noSummary')}</p>
              <DossierRefs label={t('icpRadar.live.dossier.ruleRefs')} refs={decision.rule_ids ?? []} />
            </article>
          )) : <p>{t('icpRadar.live.dossier.noSourcePolicy')}</p>}
        </div>
      </section>

      <section className="run-dossier-section">
        <h3>{t('icpRadar.live.dossier.coverage')}</h3>
        <div className="run-dossier-grid">
          <DossierMetric label={t('icpRadar.live.dossier.discoveryIterations')} value={dossier.discovery_iteration_count} />
          <DossierMetric label={t('icpRadar.live.dossier.coverageChecks')} value={dossier.coverage_checks.length} />
          <DossierMetric label={t('icpRadar.live.dossier.unresolvedGaps')} value={dossier.unresolved_candidate_gaps.length} />
          <DossierMetric label={t('icpRadar.live.dossier.coverageWarnings')} value={dossier.coverage_warnings.length} />
        </div>
        {dossier.candidate_universe.length > 0 && (
          <div className="run-dossier-query-list">
            {dossier.candidate_universe.map((entry) => (
              <article className="run-dossier-card" key={entry.candidate_id}>
                <header className="run-dossier-card-head">
                  <Mono>{entry.candidate_id}</Mono>
                  <Badge tone={candidateUniverseTone(entry.status)}>
                    {t(`icpRadar.live.dossier.candidateUniverseStatus.${entry.status}`, { defaultValue: entry.status })}
                  </Badge>
                </header>
                <strong>{entry.legal_name}</strong>
                {entry.origin_task_id && <p>{t('icpRadar.live.dossier.originTask', { taskId: entry.origin_task_id })}</p>}
                <DossierRefs label={t('icpRadar.live.dossier.sourceRefs')} refs={entry.source_refs} />
                <DossierRefs label={t('icpRadar.live.dossier.rejectionReasons')} refs={entry.rejection_reasons} />
                <DossierRefs label={t('icpRadar.live.dossier.coverageFlags')} refs={entry.coverage_flags} />
              </article>
            ))}
          </div>
        )}
        {coverageHypotheses.length > 0 || coverageWarnings.length > 0 || dossier.coverage_checks.length > 0 || dossier.unresolved_candidate_gaps.length > 0 || (dossier.coverage_summary.analyzed_source_reasons?.length ?? 0) > 0 ? (
          <div className="run-dossier-validation-list">
            {coverageHypotheses.map((item, index) => (
              <div className="run-dossier-card" key={`coverage-${index}`}>
                <Badge tone="neutral">{t('icpRadar.live.dossier.coverageHypothesis')}</Badge>
                <strong>{String(item.summary ?? t('icpRadar.live.journal.noSummary'))}</strong>
                <p>{coverageDetails(item)}</p>
              </div>
            ))}
            {coverageWarnings.map((warning) => (
              <div className="run-dossier-card" key={warning}>
                <Badge tone="unsurfaced">{t('icpRadar.live.dossier.coverageWarning')}</Badge>
                <p>{warning}</p>
              </div>
            ))}
            {dossier.coverage_checks.map((check, index) => (
              <div className="run-dossier-card" key={`coverage-check-${String(check.task_id ?? index)}-${index}`}>
                <Badge tone="neutral">{t('icpRadar.live.dossier.executedCoverageCheck')}</Badge>
                <strong>{String(check.task_id ?? t('icpRadar.unknown'))}</strong>
                <p>{coverageDetails(check)}</p>
              </div>
            ))}
            {dossier.unresolved_candidate_gaps.map((gap, index) => (
              <div className="run-dossier-card" key={`gap-${String(gap.candidate_id ?? index)}-${index}`}>
                <Badge tone="unsurfaced">{t('icpRadar.live.dossier.unresolvedGap')}</Badge>
                <strong>{String(gap.legal_name ?? gap.candidate_id ?? t('icpRadar.unknown'))}</strong>
                <p>{String(gap.reason ?? gap.resolution ?? t('icpRadar.live.journal.noSummary'))}</p>
              </div>
            ))}
            {dossier.coverage_summary.analyzed_source_reasons?.map((reason) => (
              <div className="run-dossier-card" key={reason}>
                <Badge tone="neutral">{t('icpRadar.live.dossier.analyzedNotUsed')}</Badge>
                <p>{reason}</p>
              </div>
            ))}
          </div>
        ) : <p>{t('icpRadar.live.dossier.noCoverage')}</p>}
      </section>

      <section className="run-dossier-section">
        <h3>{t('icpRadar.live.dossier.plan')}</h3>
        <div className="run-dossier-query-list">
          {dossier.search_plan.length > 0 ? dossier.search_plan.map((query) => (
            <article className="run-dossier-card" key={query.query_id}>
              <header className="run-dossier-card-head">
                <Mono>{query.query_id}</Mono>
                <Badge tone="neutral">{t('icpRadar.live.dossier.sourceCount', { count: query.source_count })}</Badge>
              </header>
              <strong>{query.query}</strong>
              <p>{query.purpose || t('icpRadar.live.journal.noSummary')}</p>
              {query.expected_evidence.length > 0 && (
                <div className="run-dossier-tags">
                  {query.stage && <span><Mono>stage</Mono>{query.stage}</span>}
                  {query.subject_id && <span><Mono>subject</Mono>{query.subject_id}</span>}
                  {query.source_scope && <span><Mono>{t('icpRadar.live.dossier.sourceScope')}</Mono>{query.source_scope}</span>}
                  {query.source_ids?.map((sourceId) => <span key={`${query.query_id}-${sourceId}`}><Mono>{t('icpRadar.live.dossier.sourceBase')}</Mono>{sourceId}</span>)}
                  {query.candidate_scope && query.candidate_scope.length > 0 && (
                    <span><Mono>scope</Mono>{query.candidate_scope.join(', ')}</span>
                  )}
                  {query.expected_evidence.map((item) => <span key={item}>{item}</span>)}
                </div>
              )}
              {query.rule_snapshot && <p>{query.rule_snapshot}</p>}
              <DossierRefs label={t('icpRadar.live.dossier.sourceRefs')} refs={query.source_refs} />
              <DossierRefs label={t('icpRadar.live.dossier.candidateRefs')} refs={query.candidate_refs} />
            </article>
          )) : <p>{t('icpRadar.live.dossier.noPlan')}</p>}
        </div>
      </section>

      <section className="run-dossier-section">
        <h3>{t('icpRadar.live.dossier.sourceLifecycle')}</h3>
        <div className="run-dossier-grid">
          <DossierMetric label={t('icpRadar.live.dossier.lifecycleTotal')} value={dossier.source_lifecycle_summary.total_count} />
          <DossierMetric label={t('icpRadar.live.dossier.lifecycleUsed')} value={dossier.source_lifecycle_summary.by_state.used_in_product ?? 0} />
          <DossierMetric label={t('icpRadar.live.dossier.lifecycleDiscarded')} value={dossier.source_lifecycle_summary.by_state.discarded ?? 0} />
          <DossierMetric label={t('icpRadar.live.dossier.lifecycleUnlinked')} value={dossier.source_lifecycle_summary.by_reason.not_used_by_candidate ?? 0} />
        </div>
        {dossier.source_lifecycle.length > 0 ? (
          <div className="run-dossier-source-list">
            {dossier.source_lifecycle.map((source) => (
              <article className="run-dossier-source" key={`${source.evidence_ref}-${source.state}-${source.reason}`}>
                <header className="run-dossier-card-head">
                  <Mono>{source.evidence_ref}</Mono>
                  <Badge tone={sourceLifecycleTone(source.state)}>
                    {t(`icpRadar.live.dossier.sourceLifecycleState.${source.state}`, { defaultValue: source.state })}
                  </Badge>
                  {source.verification_state && (
                    <Badge tone={sourceVerificationTone(source.verification_state)}>
                      {t(`icpRadar.live.dossier.sourceVerificationState.${source.verification_state}`, { defaultValue: source.verification_state })}
                    </Badge>
                  )}
                </header>
                <strong>{source.title || source.url || source.evidence_ref}</strong>
                <p>{t(`icpRadar.live.dossier.sourceLifecycleReason.${source.reason}`, { defaultValue: source.reason })}</p>
                {source.verification_reason && (
                  <p>{t('icpRadar.live.dossier.sourceVerificationReason', {
                    reason: source.verification_reason,
                    statusCode: source.verification_status_code ?? t('icpRadar.unknown'),
                  })}</p>
                )}
                {source.url && (
                  <a href={source.url} rel="noreferrer" target="_blank">
                    {source.url}<ExternalLink aria-hidden="true" />
                  </a>
                )}
                <span className="run-dossier-source-meta">
                  <Mono>{source.query_id ?? t('icpRadar.unknown')}</Mono>
                  <Mono>{source.origin}</Mono>
                  {source.verification_mode && <Mono>{source.verification_mode}</Mono>}
                </span>
                {source.usages.length > 0 && (
                  <div className="run-dossier-usages">
                    {source.usages.map((usage) => (
                      <span key={`${source.evidence_ref}-${usage.subject_type}-${usage.subject_id}`}>
                        <Mono>{usage.subject_type}</Mono>
                        {usage.candidate_name || usage.candidate_id}
                        {usage.subject_label && <small>{usage.subject_label}</small>}
                      </span>
                    ))}
                  </div>
                )}
              </article>
            ))}
          </div>
        ) : <p>{t('icpRadar.live.dossier.noSourceLifecycle')}</p>}
      </section>

      <section className="run-dossier-section">
        <h3>{t('icpRadar.live.dossier.sourcesTitle')}</h3>
        <div className="run-dossier-source-list">
          {dossier.sources.length > 0 ? dossier.sources.map((source) => (
            <article className="run-dossier-source" key={source.evidence_ref}>
              <header className="run-dossier-card-head">
                <Mono>{source.evidence_ref}</Mono>
                <Badge tone={source.usage_status === 'used' ? 'ally' : 'neutral'}>
                  {t(`icpRadar.live.dossier.usageStatus.${source.usage_status}`, { defaultValue: source.usage_status })}
                </Badge>
              </header>
              <strong>{source.title || source.url || source.evidence_ref}</strong>
              <p>{source.snippet || t('icpRadar.live.journal.noSummary')}</p>
              <a href={source.url} rel="noreferrer" target="_blank">
                {source.url}<ExternalLink aria-hidden="true" />
              </a>
              <span className="run-dossier-source-meta">
                <Mono>{source.query_id ?? t('icpRadar.unknown')}</Mono>
                <Mono>{source.source_type}</Mono>
              </span>
              {source.usages.length > 0 && (
                <div className="run-dossier-usages">
                  {source.usages.map((usage) => (
                    <span key={`${source.evidence_ref}-${usage.subject_type}-${usage.subject_id}`}>
                      <Mono>{usage.subject_type}</Mono>
                      {usage.candidate_name || usage.candidate_id}
                      {usage.subject_label && <small>{usage.subject_label}</small>}
                    </span>
                  ))}
                </div>
              )}
            </article>
          )) : <p>{t('icpRadar.live.dossier.noSources')}</p>}
        </div>
      </section>

      <section className="run-dossier-section">
        <h3>{t('icpRadar.live.dossier.validation')}</h3>
        {dossier.validation.length > 0 ? (
          <div className="run-dossier-validation-list">
            {dossier.validation.map((item, index) => (
              <div className="run-dossier-card" key={`${String(item.path ?? index)}-${String(item.message ?? '')}`}>
                <Badge tone={item.severity === 'error' ? 'blocker' : 'unsurfaced'}>{String(item.severity ?? 'warning')}</Badge>
                <strong>{String(item.path ?? t('icpRadar.unknown'))}</strong>
                <p>{String(item.message ?? t('icpRadar.live.journal.noSummary'))}</p>
              </div>
            ))}
          </div>
        ) : <p>{t('icpRadar.live.dossier.noValidation')}</p>}
      </section>

      <section className="run-dossier-section">
        <h3>{t('icpRadar.live.dossier.timeline')}</h3>
        <div className="canonical-journal-list">
          {visibleTimeline.length > 0 ? visibleTimeline.map((event) => (
            <DossierJournalEventRow event={event} key={event.event_id} />
          )) : (
            <div className="canonical-journal-row">
              <Mono>0</Mono>
              <strong>{t('icpRadar.live.journal.empty')}</strong>
              <small>{t('icpRadar.live.journal.emptyCopy')}</small>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function DossierMetric({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="run-dossier-metric">
      <span>{label}</span>
      <Mono>{value}</Mono>
    </div>
  );
}

function DossierRefs({ label, refs }: { label: string; refs: string[] }) {
  if (!refs.length) {
    return null;
  }
  return (
    <div className="run-dossier-refs">
      <span>{label}</span>
      <span>
        {refs.map((ref) => <Mono key={ref}>{ref}</Mono>)}
      </span>
    </div>
  );
}

function DossierJournalEventRow({ event }: { event: LiveRadarJournalEvent }) {
  const { t } = useTranslation();
  const refs = [...event.candidate_refs, ...event.source_refs].filter(Boolean);
  return (
    <div className="canonical-journal-row canonical-journal-row--event">
      <span className="journal-event-sequence"><Mono>{event.sequence}</Mono></span>
      <span className="journal-event-main">
        <strong className="journal-event-title">
          {t(`icpRadar.live.journal.eventType.${event.event_type}`, { defaultValue: event.event_type })}
        </strong>
        <p className="journal-event-summary">{event.summary || t('icpRadar.live.journal.noSummary')}</p>
        <span className="journal-event-meta">
          <Badge tone={event.visibility === 'operator' ? 'unsurfaced' : 'neutral'}>
            {t(`icpRadar.live.journal.visibility.${event.visibility}`, { defaultValue: event.visibility })}
          </Badge>
          <Mono>{event.actor}</Mono>
          <Mono>{event.phase}</Mono>
          {event.created_at && <span className="journal-event-time">{formatJournalTime(event.created_at)}</span>}
        </span>
        {refs.length > 0 && (
          <span className="journal-event-refs">
            {refs.map((ref) => <Mono key={`${event.event_id}-${ref}`}>{ref}</Mono>)}
          </span>
        )}
      </span>
    </div>
  );
}

function formatJournalTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(undefined, {
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    month: '2-digit',
  });
}

function readableEntries(value: Record<string, unknown>) {
  return Object.entries(value)
    .map(([key, entry]) => [key, readableValue(entry)] as const)
    .filter(([, entry]) => entry.length > 0);
}

function readableValue(value: unknown) {
  if (typeof value === 'string') {
    return value;
  }
  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }
  if (Array.isArray(value) && value.every((item) => ['string', 'number', 'boolean'].includes(typeof item))) {
    return value.map(String).join(', ');
  }
  return '';
}

function coverageDetails(value: Record<string, unknown>) {
  return readableEntries(value)
    .filter(([key]) => key !== 'summary')
    .map(([key, entry]) => `${key}: ${entry}`)
    .join(' · ');
}

function candidateUniverseTone(status: string): 'ally' | 'blocker' | 'unsurfaced' | 'neutral' {
  if (status === 'qualified') {
    return 'ally';
  }
  if (status === 'rejected') {
    return 'blocker';
  }
  if (status === 'gap' || status === 'unknown_review_needed') {
    return 'unsurfaced';
  }
  return 'neutral';
}

function sourceLifecycleTone(state: string): 'ally' | 'blocker' | 'unsurfaced' | 'neutral' {
  if (state === 'used_in_product') {
    return 'ally';
  }
  if (state === 'discarded') {
    return 'unsurfaced';
  }
  return 'neutral';
}

function sourceVerificationTone(state: string): 'ally' | 'blocker' | 'unsurfaced' | 'neutral' {
  if (state === 'reachable' || state === 'not_checked') {
    return state === 'reachable' ? 'ally' : 'neutral';
  }
  if (state === 'invalid_url') {
    return 'blocker';
  }
  return 'unsurfaced';
}
