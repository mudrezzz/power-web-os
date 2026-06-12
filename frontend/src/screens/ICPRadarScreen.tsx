import {
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Radar,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Target,
  X,
} from 'lucide-react';
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Card, Eyebrow, Mono } from '../components/primitives';
import type {
  CriterionEvidenceExplanation,
  EvidenceSource,
  ICPRadarArtifact,
  ICPRadarCatalogArtifact,
  ICPRadarCatalogItem,
  ICPRadarCandidate,
  RadarDefinition,
  SignalCriterion,
} from '../types';

type RadarDetailTab = 'shortlist' | 'settings';

export function ICPRadarScreen({
  artifact,
  catalog,
  error,
}: {
  artifact: ICPRadarArtifact | null;
  catalog: ICPRadarCatalogArtifact | null;
  error: string | null;
}) {
  const { t } = useTranslation();
  const [selectedRadarId, setSelectedRadarId] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<RadarDetailTab>('shortlist');
  const [expandedCandidateId, setExpandedCandidateId] = useState<string | null>(null);
  const [detailCandidateId, setDetailCandidateId] = useState<string | null>(null);
  const [criterionReviews, setCriterionReviews] = useState<Record<string, CriterionReviewState>>({});
  const selectedRadar = catalog?.radars.find((item) => item.radar_id === selectedRadarId) ?? null;
  const activeFixtureRadarId = catalog?.workflow_metadata.active_fixture_radar_id ?? 'toir-sibur';
  const selectedRadarArtifact = selectedRadar?.radar_id === activeFixtureRadarId ? artifact : null;
  const detailCandidate = artifact?.candidates.find((item) => item.account_id === detailCandidateId) ?? null;
  const sourcesById = useMemo(() => {
    const entries = selectedRadarArtifact?.radar.sources.map((source) => [source.source_id, source]) ?? [];
    return new Map(entries as Array<[string, EvidenceSource]>);
  }, [selectedRadarArtifact]);

  if (error || !catalog) {
    return (
      <section className="screen status-screen" aria-label={t('icpRadar.aria')}>
        <Card>
          <Eyebrow>{t('icpRadar.statusEyebrow')}</Eyebrow>
          <h1>{error ? t('icpRadar.notReadyTitle') : t('icpRadar.loadingTitle')}</h1>
          <p>{error ? t('icpRadar.notReadyCopy') : t('icpRadar.loadingCopy')}</p>
          {error && <code>{error}</code>}
        </Card>
      </section>
    );
  }

  function openRadar(radar: ICPRadarCatalogItem) {
    setSelectedRadarId(radar.radar_id);
    setSelectedTab('shortlist');
    setExpandedCandidateId(null);
    setDetailCandidateId(null);
  }

  function backToCatalog() {
    setSelectedRadarId(null);
    setDetailCandidateId(null);
    setExpandedCandidateId(null);
  }

  if (!selectedRadar) {
    return <RadarCatalogScreen catalog={catalog} onOpenRadar={openRadar} />;
  }

  if (detailCandidate && selectedRadarArtifact) {
    return (
      <section className="screen icp-radar-screen icp-detail-screen" aria-label={t('icpRadar.aria')}>
        <div className="icp-detail-sticky-header">
          <div className="icp-detail-breadcrumbs" aria-label={t('icpRadar.breadcrumbs')}>
            <Button icon={<ArrowLeft aria-hidden="true" />} variant="quiet" onClick={() => setDetailCandidateId(null)}>
              {t('icpRadar.backToTable')}
            </Button>
            <span>{t('icpRadar.aria')}</span>
            <ChevronRight aria-hidden="true" />
            <span>{selectedRadar.name}</span>
            <ChevronRight aria-hidden="true" />
            <strong>{detailCandidate.legal_name}</strong>
          </div>

          <header className="icp-radar-header icp-detail-header">
            <span className="section-icon">
              <Target aria-hidden="true" />
            </span>
            <div>
              <Eyebrow>{t('icpRadar.detailEyebrow')}</Eyebrow>
              <h1>{detailCandidate.legal_name}</h1>
              <p>{detailCandidate.main_signal}</p>
            </div>
            <div className="icp-profile-meta">
              <Badge tone={detailCandidate.score.tier === 'Tier 1' ? 'ally' : 'neutral'}>{detailCandidate.score.tier}</Badge>
              <Mono>#{detailCandidate.rank}</Mono>
            </div>
          </header>
        </div>

        <div className="icp-candidate-detail-grid">
          <Card>
            <div className="icp-detail-card">
              <CandidateScoreGrid candidate={detailCandidate} />
              <CompanyContext candidate={detailCandidate} />
              <section className="icp-detail-section">
                <Eyebrow>{t('icpRadar.signalSummary')}</Eyebrow>
                <p>{detailCandidate.signal_summary || detailCandidate.comment}</p>
              </section>
              <section className="icp-detail-section">
                <Eyebrow>{t('icpRadar.plannedValidation')}</Eyebrow>
                <p>{t('icpRadar.validationPlannedCopy')}</p>
              </section>
            </div>
          </Card>

          <Card>
            <div className="icp-detail-card">
              <section className="icp-detail-section">
                <Eyebrow>{t('icpRadar.evidence')}</Eyebrow>
                <EvidenceList candidate={detailCandidate} sourcesById={sourcesById} />
              </section>
              <section className="icp-detail-section">
                <Eyebrow>{t('icpRadar.sourceUrls')}</Eyebrow>
                <SourceUrlList candidate={detailCandidate} />
              </section>
            </div>
          </Card>

          <Card>
            <div className="icp-detail-card">
              <section className="icp-detail-section">
                <Eyebrow>{t('icpRadar.criteria')}</Eyebrow>
                <CriteriaBreakdown
                  artifact={selectedRadarArtifact}
                  candidate={detailCandidate}
                  reviews={criterionReviews}
                  onReviewChange={setCriterionReviews}
                />
              </section>
            </div>
          </Card>
        </div>
      </section>
    );
  }

  return (
    <section className="screen icp-radar-screen" aria-label={t('icpRadar.aria')}>
      <RadarDetailHeader
        activeTab={selectedTab}
        artifact={selectedRadarArtifact}
        onBack={backToCatalog}
        onTabChange={setSelectedTab}
        radar={selectedRadar}
      />

      {selectedTab === 'settings' ? (
        <RadarSettings definition={selectedRadar.definition} status={selectedRadar.status} />
      ) : selectedRadarArtifact ? (
        <CandidateTable
          artifact={selectedRadarArtifact}
          expandedCandidateId={expandedCandidateId}
          onOpenDetails={setDetailCandidateId}
          onToggleCandidate={(candidateId) => setExpandedCandidateId(
            expandedCandidateId === candidateId ? null : candidateId,
          )}
          sourcesById={sourcesById}
        />
      ) : (
        <EmptyShortlist radar={selectedRadar} onOpenSettings={() => setSelectedTab('settings')} />
      )}
    </section>
  );
}

function RadarCatalogScreen({
  catalog,
  onOpenRadar,
}: {
  catalog: ICPRadarCatalogArtifact;
  onOpenRadar: (radar: ICPRadarCatalogItem) => void;
}) {
  const { t } = useTranslation();
  const totals = catalog.radars.reduce(
    (acc, radar) => ({
      candidates: acc.candidates + radar.summary.candidate_count,
      review: acc.review + radar.summary.needs_review_count,
      accepted: acc.accepted + radar.summary.accepted_count,
    }),
    { candidates: 0, review: 0, accepted: 0 },
  );

  return (
    <section className="screen icp-radar-screen" aria-label={t('icpRadar.catalogAria')}>
      <header className="icp-radar-header">
        <span className="section-icon">
          <Radar aria-hidden="true" />
        </span>
        <div>
          <Eyebrow>{t('icpRadar.catalogEyebrow')}</Eyebrow>
          <h1>{t('icpRadar.catalogTitle')}</h1>
          <p>{t('icpRadar.catalogSummary', { count: catalog.radars.length })}</p>
        </div>
        <div className="icp-profile-meta">
          <Badge tone="cobalt">{t('icpRadar.catalogTotals.candidates', { count: totals.candidates })}</Badge>
          <Badge tone="neutral">{t('icpRadar.catalogTotals.review', { count: totals.review })}</Badge>
        </div>
      </header>

      <div className="icp-radar-catalog-grid">
        {catalog.radars.map((radar) => (
          <Card interactive key={radar.radar_id} onClick={() => onOpenRadar(radar)}>
            <div className="icp-radar-card">
              <div className="icp-radar-card-head">
                <span className="section-icon">
                  <Radar aria-hidden="true" />
                </span>
                <div>
                  <Eyebrow>{t('icpRadar.radarCardEyebrow')}</Eyebrow>
                  <h2>{radar.name}</h2>
                  <p>{radar.profile.icp_profile}</p>
                </div>
                <Badge tone={radar.status === 'active' ? 'ally' : 'neutral'}>
                  {t(radarStatusKey(radar.status))}
                </Badge>
              </div>
              <p className="icp-radar-card-scope">{radar.profile.scope}</p>
              <dl className="icp-radar-card-metrics">
                <Metric label={t('icpRadar.cardFields.cadence')} value={t(cadenceKey(radar.summary.cadence))} />
                <Metric label={t('icpRadar.cardFields.lastRun')} value={t(lastRunKey(radar.summary.last_run))} />
                <Metric label={t('icpRadar.cardFields.candidates')} value={String(radar.summary.candidate_count)} />
                <Metric label={t('icpRadar.cardFields.needsReview')} value={String(radar.summary.needs_review_count)} />
                <Metric label={t('icpRadar.cardFields.accepted')} value={String(radar.summary.accepted_count)} />
                <Metric label={t('icpRadar.cardFields.owner')} value={radar.owner} />
              </dl>
              <div className="icp-radar-card-footer">
                <Mono>{t(runModeKey(radar.summary.run_mode))}</Mono>
                <span className="row-action">
                  {t('icpRadar.openRadar')}
                  <ChevronRight aria-hidden="true" />
                </span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </section>
  );
}

function RadarDetailHeader({
  activeTab,
  artifact,
  onBack,
  onTabChange,
  radar,
}: {
  activeTab: RadarDetailTab;
  artifact: ICPRadarArtifact | null;
  onBack: () => void;
  onTabChange: (tab: RadarDetailTab) => void;
  radar: ICPRadarCatalogItem;
}) {
  const { t } = useTranslation();
  return (
    <div className="icp-radar-selected-shell">
      <div className="icp-detail-breadcrumbs" aria-label={t('icpRadar.radarBreadcrumbs')}>
        <Button icon={<ArrowLeft aria-hidden="true" />} variant="quiet" onClick={onBack}>
          {t('icpRadar.backToCatalog')}
        </Button>
        <span>{t('icpRadar.aria')}</span>
        <ChevronRight aria-hidden="true" />
        <strong>{radar.name}</strong>
      </div>
      <header className="icp-radar-header">
        <span className="section-icon">
          <Radar aria-hidden="true" />
        </span>
        <div>
          <Eyebrow>{t('icpRadar.eyebrow')}</Eyebrow>
          <h1>{radar.name}</h1>
          <p>
            {artifact
              ? t('icpRadar.summary', {
                count: artifact.candidates.length,
                holding: artifact.radar.profile.holding,
                product: artifact.radar.profile.product,
              })
              : t('icpRadar.emptyShortlistSummary', { product: radar.profile.product })}
          </p>
        </div>
        <div className="icp-profile-meta">
          <Badge tone={radar.status === 'active' ? 'ally' : 'neutral'}>{t(radarStatusKey(radar.status))}</Badge>
          <Mono>{t(runModeKey(radar.summary.run_mode))}</Mono>
        </div>
      </header>
      <div className="icp-radar-tabs" aria-label={t('icpRadar.radarTabs')}>
        <button
          aria-pressed={activeTab === 'shortlist'}
          className={`criteria-chip${activeTab === 'shortlist' ? ' criteria-chip-active' : ''}`}
          type="button"
          onClick={() => onTabChange('shortlist')}
        >
          {t('icpRadar.shortlistTab')}
        </button>
        <button
          aria-pressed={activeTab === 'settings'}
          className={`criteria-chip${activeTab === 'settings' ? ' criteria-chip-active' : ''}`}
          type="button"
          onClick={() => onTabChange('settings')}
        >
          {t('icpRadar.settingsTab')}
        </button>
      </div>
    </div>
  );
}

function CandidateTable({
  artifact,
  expandedCandidateId,
  onOpenDetails,
  onToggleCandidate,
  sourcesById,
}: {
  artifact: ICPRadarArtifact;
  expandedCandidateId: string | null;
  onOpenDetails: (candidateId: string) => void;
  onToggleCandidate: (candidateId: string) => void;
  sourcesById: Map<string, EvidenceSource>;
}) {
  const { t } = useTranslation();
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
          {artifact.candidates.map((candidate) => {
            const expanded = expandedCandidateId === candidate.account_id;
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
                      <span className="score-fill" style={{ width: `${Math.min(100, candidate.score.total_score * 2)}%` }} />
                    </span>
                    <Mono>{candidate.score.total_score}</Mono>
                  </span>
                  <Mono>{candidate.score.fit_score}</Mono>
                  <Mono>{candidate.score.intent_score}</Mono>
                  <Mono>{candidate.score.trigger_score}</Mono>
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
                  <CandidatePreview
                    artifact={artifact}
                    candidate={candidate}
                    onOpenDetails={() => onOpenDetails(candidate.account_id)}
                    sourcesById={sourcesById}
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

function EmptyShortlist({
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

function RadarSettings({
  definition,
  status,
}: {
  definition: RadarDefinition;
  status: string;
}) {
  const { t } = useTranslation();
  return (
    <div className="icp-settings-grid">
      <Card>
        <div className="icp-settings-section">
          <div className="icp-settings-section-head">
            <Eyebrow>{t('icpRadar.settings.profile')}</Eyebrow>
            <Badge tone="neutral">{t('icpRadar.readOnly')}</Badge>
          </div>
          <dl className="icp-definition-list">
            <Metric label={t('icpRadar.settings.product')} value={definition.product} />
            <Metric label={t('icpRadar.settings.segment')} value={definition.segment} />
            <Metric label={t('icpRadar.settings.holding')} value={definition.holding} />
            <Metric label={t('icpRadar.settings.status')} value={t(radarStatusKey(status))} />
          </dl>
          <section className="icp-detail-section">
            <Eyebrow>{t('icpRadar.settings.scope')}</Eyebrow>
            <p>{definition.market_scope}</p>
          </section>
          <ListSection title={t('icpRadar.settings.exclusions')} items={definition.exclusions} />
          <ListSection title={t('icpRadar.settings.assumptions')} items={definition.assumptions} />
        </div>
      </Card>

      <Card>
        <div className="icp-settings-section">
          <div className="icp-settings-section-head">
            <Eyebrow>{t('icpRadar.settings.discovery')}</Eyebrow>
          </div>
          <dl className="icp-definition-list">
            <Metric label={t('icpRadar.settings.legalEntitySource')} value={definition.legal_entity_source} />
            <Metric label={t('icpRadar.settings.discoveryMode')} value={t(discoveryModeKey(definition.discovery_mode))} />
          </dl>
          <ListSection title={t('icpRadar.settings.discoveryFilters')} items={definition.discovery_filters} />
        </div>
      </Card>

      <Card>
        <div className="icp-settings-section">
          <div className="icp-settings-section-head">
            <Eyebrow>{t('icpRadar.settings.monitoring')}</Eyebrow>
          </div>
          <dl className="icp-definition-list">
            <Metric label={t('icpRadar.cardFields.cadence')} value={t(cadenceKey(definition.cadence))} />
            <Metric label={t('icpRadar.settings.lookbackWindow')} value={definition.lookback_window} />
            <Metric label={t('icpRadar.cardFields.runMode')} value={t(runModeKey(definition.run_mode))} />
          </dl>
          <ListSection title={t('icpRadar.settings.sources')} items={definition.monitoring_sources} />
        </div>
      </Card>

      <Card>
        <div className="icp-settings-section">
          <div className="icp-settings-section-head">
            <Eyebrow>{t('icpRadar.settings.scoring')}</Eyebrow>
          </div>
          <div className="icp-settings-formula-grid">
            {Object.entries(definition.scoring_formula).map(([name, value]) => (
              <div key={name}>
                <Mono>{name}</Mono>
                <strong>{typeof value === 'string' ? value : JSON.stringify(value)}</strong>
              </div>
            ))}
          </div>
          <div className="icp-settings-thresholds">
            {Object.entries(definition.tier_thresholds).map(([tier, value]) => (
              <Badge key={tier} tone={tier === 'Tier 1' ? 'ally' : 'neutral'}>{tier} {value}</Badge>
            ))}
          </div>
        </div>
      </Card>

      <Card>
        <div className="icp-settings-section">
          <div className="icp-settings-section-head">
            <Eyebrow>{t('icpRadar.settings.criteria')}</Eyebrow>
            <Mono>{t('icpRadar.settings.criteriaCount', { count: definition.criteria.length })}</Mono>
          </div>
          <div className="criteria-list">
            {definition.criteria.map((criterion) => (
              <div className="criterion-row" key={criterion.code}>
                <Mono>{criterion.code}</Mono>
                <span>
                  <strong>{criterion.name}</strong>
                  <small>{criterion.description}</small>
                  <small>{criterion.scoring_guidance}</small>
                </span>
              </div>
            ))}
          </div>
        </div>
      </Card>

      <Card>
        <div className="icp-settings-section">
          <div className="icp-settings-section-head">
            <Eyebrow>{t('icpRadar.settings.limitations')}</Eyebrow>
            <Badge tone="unsurfaced">{t('icpRadar.editingPlanned')}</Badge>
          </div>
          <ListSection title={t('icpRadar.settings.limitations')} items={definition.limitations} />
        </div>
      </Card>
    </div>
  );
}

function ListSection({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="icp-detail-section">
      <Eyebrow>{title}</Eyebrow>
      <ul className="icp-settings-list">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function CandidatePreview({
  artifact,
  candidate,
  onOpenDetails,
  sourcesById,
}: {
  artifact: ICPRadarArtifact;
  candidate: ICPRadarCandidate;
  onOpenDetails: () => void;
  sourcesById: Map<string, EvidenceSource>;
}) {
  const { t } = useTranslation();
  const criteria = topCriteria(artifact, candidate, 5);
  return (
    <div className="icp-candidate-preview">
      <div className="icp-preview-sticky-cell icp-sticky-cell">
        <Eyebrow>{t('icpRadar.previewEyebrow')}</Eyebrow>
        <strong>{candidate.legal_name}</strong>
        <Button icon={<ArrowRight aria-hidden="true" />} variant="default" onClick={onOpenDetails}>
          {t('icpRadar.openDetails')}
        </Button>
      </div>
      <div className="icp-preview-body">
        <div className="icp-preview-main">
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.mainSignal')}</Eyebrow>
            <p>{candidate.main_signal}</p>
          </section>
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.signalSummary')}</Eyebrow>
            <p>{candidate.comment || candidate.signal_summary}</p>
          </section>
        </div>
        <div className="icp-preview-lists">
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.evidence')}</Eyebrow>
            <EvidenceList candidate={candidate} sourcesById={sourcesById} compact />
          </section>
          <section className="icp-preview-section">
            <Eyebrow>{t('icpRadar.topCriteria')}</Eyebrow>
            <div className="criteria-list criteria-list-compact">
              {criteria.map(({ criterion, value }) => (
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
      </div>
    </div>
  );
}

function CandidateScoreGrid({ candidate }: { candidate: ICPRadarCandidate }) {
  const { t } = useTranslation();
  return (
    <div className="icp-score-grid">
      <ScoreBox label={t('icpRadar.fit')} value={candidate.score.fit_score} />
      <ScoreBox label={t('icpRadar.intent')} value={candidate.score.intent_score} />
      <ScoreBox label={t('icpRadar.trigger')} value={candidate.score.trigger_score} />
      <ScoreBox label={t('icpRadar.total')} value={candidate.score.total_score} />
    </div>
  );
}

function CompanyContext({ candidate }: { candidate: ICPRadarCandidate }) {
  const { t } = useTranslation();
  return (
    <section className="icp-detail-section">
      <Eyebrow>{t('icpRadar.companyContext')}</Eyebrow>
      <dl className="icp-definition-list">
        <div>
          <dt>{t('icpRadar.revenue')}</dt>
          <dd>{candidate.revenue || t('icpRadar.unknown')}</dd>
        </div>
        <div>
          <dt>{t('icpRadar.inn')}</dt>
          <dd>{candidate.inn || t('icpRadar.unknown')}</dd>
        </div>
        <div>
          <dt>{t('icpRadar.site')}</dt>
          <dd>{candidate.site || t('icpRadar.unknown')}</dd>
        </div>
        <div>
          <dt>{t('icpRadar.confidence')}</dt>
          <dd>{candidate.confidence || t('icpRadar.unknown')}</dd>
        </div>
      </dl>
    </section>
  );
}

function EvidenceList({
  candidate,
  sourcesById,
  compact = false,
}: {
  candidate: ICPRadarCandidate;
  sourcesById: Map<string, EvidenceSource>;
  compact?: boolean;
}) {
  const refs = compact ? candidate.evidence_refs.slice(0, 5) : candidate.evidence_refs;
  return (
    <div className={`icp-evidence-list${compact ? ' icp-evidence-list-compact' : ''}`}>
      {refs.map((ref) => {
        const source = sourcesById.get(ref);
        return (
          <a href={source?.url ?? ref} key={ref} target="_blank" rel="noreferrer">
            <ShieldCheck aria-hidden="true" />
            <span>
              <strong>{ref}</strong>
              <small>{source?.usage ?? ref}</small>
            </span>
            <ExternalLink aria-hidden="true" />
          </a>
        );
      })}
    </div>
  );
}

function SourceUrlList({ candidate }: { candidate: ICPRadarCandidate }) {
  const { t } = useTranslation();
  if (!candidate.source_urls.length) {
    return <p>{t('icpRadar.unknown')}</p>;
  }

  return (
    <div className="icp-evidence-list">
      {candidate.source_urls.map((url) => (
        <a href={url} key={url} target="_blank" rel="noreferrer">
          <ExternalLink aria-hidden="true" />
          <span>
            <strong>{url}</strong>
          </span>
        </a>
      ))}
    </div>
  );
}

function ScoreBox({ label, value }: { label: string; value: number }) {
  return (
    <div className="icp-score-box">
      <Mono>{label}</Mono>
      <strong>{value}</strong>
    </div>
  );
}

function topCriteria(artifact: ICPRadarArtifact, candidate: ICPRadarCandidate, count: number) {
  return artifact.radar.criteria
    .map((criterion) => ({
      criterion,
      value: candidate.criteria_scores[criterion.code] ?? 0,
    }))
    .filter((item): item is { criterion: SignalCriterion; value: number } => item.value > 0)
    .sort((left, right) => right.value - left.value || left.criterion.code.localeCompare(right.criterion.code))
    .slice(0, count);
}

type CriterionFilter = 'all' | 'supported' | 'inferred' | 'not_observed' | 'needs_review';
type CriterionSort = 'score_desc' | 'status' | 'confidence';

type CriterionReviewState = {
  status: 'accepted' | 'rejected' | 'edited';
  adjustedScore: number;
  comment: string;
};

function CriteriaBreakdown({
  artifact,
  candidate,
  reviews,
  onReviewChange,
}: {
  artifact: ICPRadarArtifact;
  candidate: ICPRadarCandidate;
  reviews: Record<string, CriterionReviewState>;
  onReviewChange: (reviews: Record<string, CriterionReviewState>) => void;
}) {
  const { t } = useTranslation();
  const [expandedCriterionCode, setExpandedCriterionCode] = useState<string | null>(null);
  const [filter, setFilter] = useState<CriterionFilter>('all');
  const [sort, setSort] = useState<CriterionSort>('score_desc');
  const rows = useMemo(() => (
    artifact.radar.criteria
      .map((criterion) => {
        const evidence = candidate.criteria_evidence[criterion.code];
        const review = reviews[criterion.code];
        return {
          criterion,
          evidence,
          review,
          score: evidence?.score ?? candidate.criteria_scores[criterion.code] ?? 0,
        };
      })
      .filter((row) => matchesCriterionFilter(row.evidence, row.review, filter))
      .sort((left, right) => compareCriterionRows(left, right, sort))
  ), [artifact.radar.criteria, candidate.criteria_evidence, candidate.criteria_scores, filter, reviews, sort]);

  function updateReview(code: string, review: CriterionReviewState) {
    onReviewChange({
      ...reviews,
      [code]: review,
    });
  }

  const filterOptions: CriterionFilter[] = ['all', 'supported', 'inferred', 'not_observed', 'needs_review'];
  const sortOptions: CriterionSort[] = ['score_desc', 'status', 'confidence'];

  return (
    <div className="criteria-evidence-list" aria-label={t('icpRadar.criterionEvidence')}>
      <div className="criteria-review-toolbar" aria-label={t('icpRadar.criteriaReviewToolbar')}>
        <div className="criteria-review-control">
          <Mono>{t('icpRadar.filter')}</Mono>
          <div className="criteria-review-segmented">
            {filterOptions.map((option) => (
              <button
                aria-pressed={filter === option}
                className={`criteria-chip${filter === option ? ' criteria-chip-active' : ''}`}
                key={option}
                type="button"
                onClick={() => setFilter(option)}
              >
                {t(criterionFilterKey(option))}
              </button>
            ))}
          </div>
        </div>

        <label className="criteria-sort-field">
          <SlidersHorizontal aria-hidden="true" />
          <span>{t('icpRadar.sort')}</span>
          <select value={sort} onChange={(event) => setSort(event.target.value as CriterionSort)}>
            {sortOptions.map((option) => (
              <option key={option} value={option}>
                {t(criterionSortKey(option))}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="criteria-review-table">
        <div className="criteria-review-head">
          <span>{t('icpRadar.criteriaColumns.code')}</span>
          <span>{t('icpRadar.criteriaColumns.criterion')}</span>
          <span>{t('icpRadar.criteriaColumns.score')}</span>
          <span>{t('icpRadar.criteriaColumns.status')}</span>
          <span>{t('icpRadar.criteriaColumns.confidence')}</span>
          <span>{t('icpRadar.criteriaColumns.facts')}</span>
          <span>{t('icpRadar.criteriaColumns.review')}</span>
          <span className="criteria-action-head" aria-label={t('icpRadar.criteriaColumns.action')} />
        </div>

        {rows.map(({ criterion, evidence, review, score }) => {
          const expanded = expandedCriterionCode === criterion.code;
          const adjusted = review?.status === 'edited' && review.adjustedScore !== score;
          const statusLabel = evidence ? t(evidenceStatusKey(evidence.evidence_status)) : t('icpRadar.notObserved');
          const confidenceLabel = evidence ? t(confidenceKey(evidence.confidence)) : t('icpRadar.confidenceValues.none');

          return (
            <div className={`criteria-review-record${expanded ? ' criteria-review-record-expanded' : ''}`} key={criterion.code}>
              <button
                aria-expanded={expanded}
                className="criteria-review-row"
                type="button"
                onClick={() => setExpandedCriterionCode(expanded ? null : criterion.code)}
              >
                <Mono>{criterion.code}</Mono>
                <span className="criteria-review-name">
                  <strong>{criterion.name}</strong>
                  <small>{criterion.description}</small>
                </span>
                <span className="criteria-score-inline">
                  <Mono>{score}</Mono>
                  {adjusted && (
                    <>
                      <span aria-hidden="true">-&gt;</span>
                      <Mono>{review.adjustedScore}</Mono>
                    </>
                  )}
                </span>
                <span>
                  <Badge tone={evidenceBadgeTone(evidence?.evidence_status ?? 'not_observed')}>{statusLabel}</Badge>
                </span>
                <span>
                  <Badge tone={confidenceTone(evidence?.confidence)}>{confidenceLabel}</Badge>
                </span>
                <Mono>{evidence?.facts.length ?? 0}</Mono>
                <span>
                  <Badge tone={reviewTone(review)}>{review ? t(reviewStatusKey(review.status)) : t('icpRadar.unreviewed')}</Badge>
                </span>
                <span className="row-action">
                  {expanded ? <ChevronDown aria-hidden="true" /> : <ChevronRight aria-hidden="true" />}
                </span>
              </button>

              {expanded && evidence && (
                <CriterionEvidenceDetail
                  criterion={criterion}
                  evidence={evidence}
                  review={review}
                  onReview={(nextReview) => updateReview(criterion.code, nextReview)}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CriterionEvidenceDetail({
  criterion,
  evidence,
  review,
  onReview,
}: {
  criterion: SignalCriterion;
  evidence: CriterionEvidenceExplanation;
  review: CriterionReviewState | undefined;
  onReview: (review: CriterionReviewState) => void;
}) {
  const { t } = useTranslation();
  const [draftScore, setDraftScore] = useState(review?.adjustedScore ?? evidence.score);
  const [comment, setComment] = useState(review?.comment ?? '');
  const commentRequired = !comment.trim();

  return (
    <div className="criterion-evidence-detail">
      <div className="criterion-detail-topline">
        <Badge tone={evidenceBadgeTone(evidence.evidence_status)}>{t(evidenceStatusKey(evidence.evidence_status))}</Badge>
        <Badge tone={confidenceTone(evidence.confidence)}>{t(confidenceKey(evidence.confidence))}</Badge>
        <span className="criterion-origin-note">{t(evidenceOriginKey(evidence.evidence_origin))}</span>
      </div>

      <section>
        <Eyebrow>{t('icpRadar.rationale')}</Eyebrow>
        <p>{evidence.rationale}</p>
      </section>

      {evidence.facts.length ? (
        <section>
          <Eyebrow>{t('icpRadar.facts')}</Eyebrow>
          <div className="criterion-fact-list">
            {evidence.facts.map((fact) => (
              <div className="criterion-fact" key={`${criterion.code}-${fact.evidence_ref}-${fact.fact}`}>
                <ShieldCheck aria-hidden="true" />
                <div>
                  <strong>{fact.fact}</strong>
                  <small>{fact.why_it_matters}</small>
                  <a href={fact.source_url || undefined} target="_blank" rel="noreferrer">
                    <Mono>{fact.evidence_ref || t('icpRadar.source')}</Mono>
                    {fact.source_url && <ExternalLink aria-hidden="true" />}
                  </a>
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : (
        <p className="criterion-empty-note">{t('icpRadar.noCriterionFacts')}</p>
      )}

      <section className="criterion-review-panel">
        <div>
          <Eyebrow>{t('icpRadar.localReview')}</Eyebrow>
          <p>{t('icpRadar.localReviewCopy')}</p>
        </div>
        <div className="criterion-review-form">
          <label>
            <span>{t('icpRadar.adjustedScore')}</span>
            <select value={draftScore} onChange={(event) => setDraftScore(Number(event.target.value))}>
              {[0, 1, 2, 3].map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <label className="criterion-comment-field">
            <span>{t('icpRadar.comment')}</span>
            <textarea
              placeholder={t('icpRadar.commentPlaceholder')}
              value={comment}
              onChange={(event) => setComment(event.target.value)}
            />
          </label>
          <div className="criterion-review-actions">
            <Button
              icon={<Check aria-hidden="true" />}
              variant="default"
              onClick={() => onReview({ status: 'accepted', adjustedScore: evidence.score, comment })}
            >
              {t('icpRadar.acceptCriterion')}
            </Button>
            <Button
              disabled={commentRequired}
              icon={<X aria-hidden="true" />}
              variant="default"
              onClick={() => onReview({ status: 'rejected', adjustedScore: 0, comment })}
            >
              {t('icpRadar.rejectCriterion')}
            </Button>
            <Button
              disabled={commentRequired}
              icon={<SlidersHorizontal aria-hidden="true" />}
              variant="default"
              onClick={() => onReview({ status: 'edited', adjustedScore: draftScore, comment })}
            >
              {t('icpRadar.editCriterionScore')}
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}

function matchesCriterionFilter(
  evidence: CriterionEvidenceExplanation | undefined,
  review: CriterionReviewState | undefined,
  filter: CriterionFilter,
) {
  if (filter === 'all') {
    return true;
  }
  if (filter === 'needs_review') {
    return !review && (
      evidence?.evidence_status !== 'supported'
      || evidence.confidence === 'low'
      || evidence.confidence === 'none'
    );
  }
  return evidence?.evidence_status === filter;
}

function compareCriterionRows(
  left: {
    evidence: CriterionEvidenceExplanation | undefined;
    review: CriterionReviewState | undefined;
    score: number;
    criterion: SignalCriterion;
  },
  right: {
    evidence: CriterionEvidenceExplanation | undefined;
    review: CriterionReviewState | undefined;
    score: number;
    criterion: SignalCriterion;
  },
  sort: CriterionSort,
) {
  if (sort === 'status') {
    return statusRank(left.evidence?.evidence_status) - statusRank(right.evidence?.evidence_status)
      || right.score - left.score
      || left.criterion.code.localeCompare(right.criterion.code);
  }
  if (sort === 'confidence') {
    return confidenceRank(right.evidence?.confidence) - confidenceRank(left.evidence?.confidence)
      || right.score - left.score
      || left.criterion.code.localeCompare(right.criterion.code);
  }
  return right.score - left.score
    || statusRank(left.evidence?.evidence_status) - statusRank(right.evidence?.evidence_status)
    || left.criterion.code.localeCompare(right.criterion.code);
}

function statusRank(status: CriterionEvidenceExplanation['evidence_status'] | undefined) {
  if (status === 'supported') {
    return 0;
  }
  if (status === 'inferred') {
    return 1;
  }
  return 2;
}

function confidenceRank(confidence: CriterionEvidenceExplanation['confidence'] | undefined) {
  if (confidence === 'high') {
    return 3;
  }
  if (confidence === 'medium') {
    return 2;
  }
  if (confidence === 'low') {
    return 1;
  }
  return 0;
}

function criterionFilterKey(filter: CriterionFilter) {
  return `icpRadar.criteriaFilters.${filter}`;
}

function criterionSortKey(sort: CriterionSort) {
  return `icpRadar.criteriaSort.${sort}`;
}

function reviewStatusKey(status: CriterionReviewState['status']) {
  return `icpRadar.reviewStatus.${status}`;
}

function reviewTone(review: CriterionReviewState | undefined) {
  if (review?.status === 'accepted') {
    return 'ally';
  }
  if (review?.status === 'rejected') {
    return 'blocker';
  }
  if (review?.status === 'edited') {
    return 'cobalt';
  }
  return 'neutral';
}

function confidenceTone(confidence: CriterionEvidenceExplanation['confidence'] | undefined) {
  if (confidence === 'high' || confidence === 'medium') {
    return 'ally';
  }
  if (confidence === 'low') {
    return 'unsurfaced';
  }
  return 'neutral';
}

function evidenceBadgeTone(status: CriterionEvidenceExplanation['evidence_status']) {
  if (status === 'supported') {
    return 'ally';
  }
  if (status === 'inferred') {
    return 'unsurfaced';
  }
  return 'neutral';
}

function evidenceStatusKey(status: CriterionEvidenceExplanation['evidence_status']) {
  if (status === 'supported') {
    return 'icpRadar.supported';
  }
  if (status === 'inferred') {
    return 'icpRadar.inferred';
  }
  return 'icpRadar.notObserved';
}

function confidenceKey(confidence: CriterionEvidenceExplanation['confidence']) {
  if (confidence === 'high') {
    return 'icpRadar.confidenceValues.high';
  }
  if (confidence === 'medium') {
    return 'icpRadar.confidenceValues.medium';
  }
  if (confidence === 'low') {
    return 'icpRadar.confidenceValues.low';
  }
  return 'icpRadar.confidenceValues.none';
}

function evidenceOriginKey(origin: CriterionEvidenceExplanation['evidence_origin']) {
  if (origin === 'synthetic_demo_annotation') {
    return 'icpRadar.syntheticAnnotation';
  }
  return 'icpRadar.workbookFallback';
}

function radarStatusKey(status: string) {
  if (status === 'active') {
    return 'icpRadar.radarStatus.active';
  }
  if (status === 'configured') {
    return 'icpRadar.radarStatus.configured';
  }
  if (status === 'planned') {
    return 'icpRadar.radarStatus.planned';
  }
  return 'icpRadar.radarStatus.unknown';
}

function cadenceKey(cadence: string) {
  if (cadence === 'weekly') {
    return 'icpRadar.cadence.weekly';
  }
  if (cadence === 'monthly') {
    return 'icpRadar.cadence.monthly';
  }
  return 'icpRadar.cadence.unknown';
}

function lastRunKey(lastRun: string) {
  if (lastRun === 'not_run') {
    return 'icpRadar.lastRun.notRun';
  }
  if (lastRun === 'not_scheduled') {
    return 'icpRadar.lastRun.notScheduled';
  }
  return 'icpRadar.lastRun.fixture';
}

function runModeKey(runMode: string) {
  if (runMode === 'incremental_signal_monitoring') {
    return 'icpRadar.runMode.incremental';
  }
  if (runMode === 'configured_not_generated') {
    return 'icpRadar.runMode.configured';
  }
  if (runMode === 'planned') {
    return 'icpRadar.runMode.planned';
  }
  if (runMode === 'fixture_import') {
    return 'icpRadar.runMode.fixtureImport';
  }
  return 'icpRadar.runMode.unknown';
}

function discoveryModeKey(discoveryMode: string) {
  if (discoveryMode === 'one_time_import') {
    return 'icpRadar.discoveryMode.oneTimeImport';
  }
  if (discoveryMode === 'configured_seed') {
    return 'icpRadar.discoveryMode.configuredSeed';
  }
  return 'icpRadar.discoveryMode.unknown';
}
