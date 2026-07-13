import type {
  AtomicRule,
  EditableRadarDefinitionDraft,
  GlobalSearchPolicy,
  ICPRadarCatalogArtifact,
  ICPRadarCatalogItem,
  IntentSignalDefinition,
  MonitoringPolicy,
  RadarConfigOverride,
  RadarDefinition,
  RadarMetadata,
  RadarScoringModel,
  RadarValidationReport,
  RuleGroup,
  SourceDefinition,
  SourcePolicy,
} from '../../types';
import { radarConfigStorageKey } from './modelTypes';

export function discoveryModeKey(discoveryMode: string) {
  if (discoveryMode === 'one_time_import') {
    return 'icpRadar.discoveryMode.oneTimeImport';
  }
  if (discoveryMode === 'configured_seed') {
    return 'icpRadar.discoveryMode.configuredSeed';
  }
  return 'icpRadar.discoveryMode.unknown';
}

export function sourceTypeKey(sourceType: string) {
  return `icpRadar.settings.sourceTypes.${sourceType}`;
}

export function trustPolicyValue(value: string) {
  if (value === 'high' || value === 'trusted') {
    return 'trusted';
  }
  if (value === 'medium' || value === 'cross_check') {
    return 'cross_check';
  }
  return 'hitl_required';
}

export function trustPolicyKey(value: string) {
  return `icpRadar.settings.trustPolicies.${trustPolicyValue(value)}`;
}

export function trustPolicyTone(value: string) {
  const policy = trustPolicyValue(value);
  if (policy === 'trusted') {
    return 'ally';
  }
  if (policy === 'cross_check') {
    return 'unsurfaced';
  }
  return 'neutral';
}

export const sourceUsageObligations = [
  'required',
  'preferred',
  'optional',
  'fallback',
  'disabled',
  'required_for_identity',
  'required_for_coverage',
  'required_for_signal',
] as const;

export function sourceUsageObligationValue(value: string | undefined) {
  return sourceUsageObligations.includes(value as typeof sourceUsageObligations[number])
    ? value as typeof sourceUsageObligations[number]
    : 'preferred';
}

export function sourceUsageObligationKey(value: string | undefined) {
  return `icpRadar.settings.sourceUsageObligations.${sourceUsageObligationValue(value)}`;
}

export function sourceUsageObligationTone(value: string | undefined): 'ally' | 'blocker' | 'unsurfaced' | 'cobalt' | 'neutral' {
  const obligation = sourceUsageObligationValue(value);
  if (obligation === 'disabled') {
    return 'neutral';
  }
  if (obligation === 'optional' || obligation === 'fallback') {
    return 'unsurfaced';
  }
  if (obligation.startsWith('required')) {
    return 'blocker';
  }
  return 'cobalt';
}

export function logicalOperatorKey(value: string) {
  return `icpRadar.settings.logicalOperators.${value}`;
}

export function requirementKey(value: string) {
  return `icpRadar.settings.requirements.${value}`;
}

export function ruleOperatorLabel(operator: string, rule: AtomicRule) {
  const base = operator === 'OR' ? 'OR' : 'AND';
  return isNotRule(rule) ? `${base} NOT` : base;
}

export function isNotRule(rule: AtomicRule) {
  return rule.generated_comparison_operator?.startsWith('not') ?? false;
}

export function signalRuleText(signal: IntentSignalDefinition) {
  return primaryRuleDescription(signal.trigger_rule_group) || signal.name || signal.description;
}

export function sourcePolicySummary(policy: SourcePolicy, t: (key: string, options?: Record<string, unknown>) => string) {
  const localCount = policy.local_sources?.length ?? 0;
  if (policy.use_global_search_policy && localCount > 0) {
    return t('icpRadar.settings.globalAndLocalSources', { count: localCount });
  }
  if (policy.use_global_search_policy) {
    return t('icpRadar.settings.globalSources');
  }
  return t('icpRadar.settings.localSourceCount', { count: localCount });
}

export function deduplicationValue(value: string) {
  if (['source_url', 'source_url_and_signal', 'normalized_fact', 'none'].includes(value)) {
    return value;
  }
  if (value.includes('previous') || value.includes('evidence')) {
    return 'source_url_and_signal';
  }
  return 'normalized_fact';
}

export function deduplicationKey(value: string) {
  return `icpRadar.settings.deduplicationPolicies.${deduplicationValue(value)}`;
}

export function parseDuration(value: string) {
  const match = /^(\d+)\s+([a-zA-Z]+)$/.exec(value.trim());
  return {
    amount: match ? Number(match[1]) : 30,
    unit: match ? match[2] : 'days',
  };
}

export function formatDuration(amount: string | number, unit: string) {
  const numericAmount = Number(amount);
  const safeAmount = Number.isFinite(numericAmount) && numericAmount > 0 ? Math.floor(numericAmount) : 1;
  return `${safeAmount} ${unit}`;
}

export function durationUnitKey(unit: string) {
  return `icpRadar.settings.durationUnits.${unit}`;
}

export function primaryRuleDescription(group: RuleGroup) {
  return group.rules[0]?.description ?? group.name ?? '';
}

export function setPrimaryRuleDescription(group: RuleGroup, description: string): RuleGroup {
  const firstRule = group.rules[0] ?? newAtomicRule();
  const nextRule = { ...firstRule, description };
  return {
    ...group,
    rules: group.rules.length ? replaceAt(group.rules, 0, nextRule) : [nextRule],
    groups: [],
  };
}

export function sameRubric(left: IntentSignalDefinition['scoring_rubric'], right: IntentSignalDefinition['scoring_rubric']) {
  return JSON.stringify(left.scale) === JSON.stringify(right.scale)
    && JSON.stringify(left.rules.map((rule) => rule.description)) === JSON.stringify(right.rules.map((rule) => rule.description));
}

export function globalSignalRubric(definition: RadarDefinition) {
  return definition.intent_signals[0]?.scoring_rubric ?? {
    scale: [0, 1, 2],
    rules: [0, 1, 2].map((score) => ({ score, description: '', rule_group: newRuleGroup(`global-rubric-${score}`) })),
  };
}

export function replaceAt<T>(items: T[], index: number, nextItem: T): T[] {
  return items.map((item, currentIndex) => (currentIndex === index ? nextItem : item));
}

export function newSourceDefinition(): SourceDefinition {
  const id = `source-${Date.now()}`;
  return {
    source_id: id,
    source_type: 'url',
    label: '',
    reference: '',
    trust_level: 'cross_check',
    usage_obligation: 'preferred',
  };
}

export function newSourcePolicy(sourceIds: string[] = []): SourcePolicy {
  return {
    source_ids: sourceIds.slice(0, 1),
    source_logic: 'OR',
    use_global_search_policy: true,
    allow_additional_sources: true,
    fallback_confidence: 'hitl_required',
    local_sources: [],
  };
}

export function newAtomicRule(): AtomicRule {
  const id = `rule-${Date.now()}`;
  return {
    rule_id: id,
    name: '',
    description: '',
    generated_target_field: '',
    generated_comparison_operator: '',
    generated_value: '',
    requirement_level: 'recommended',
    source_policy: newSourcePolicy(),
  };
}

export function newRuleGroup(groupId: string): RuleGroup {
  return {
    group_id: groupId,
    name: '',
    operator: 'AND',
    rules: [],
    groups: [],
  };
}

export function newIntentSignal(sourceIds: string[]): IntentSignalDefinition {
  const timestamp = Date.now();
  const code = `S${timestamp}`;
  const policy = newSourcePolicy(sourceIds);
  return {
    signal_id: `signal-${timestamp}`,
    code,
    name: '',
    description: '',
    trigger_rule_group: newRuleGroup(`trigger-${timestamp}`),
    source_policy: policy,
    scoring_rubric: {
      scale: [0, 1, 2],
      rules: [0, 1, 2].map((score) => ({
        score,
        description: '',
        rule_group: {
          group_id: `rubric-${timestamp}-${score}`,
          name: `${code} ${score}`,
          operator: 'AND',
          rules: [
            {
              ...newAtomicRule(),
              rule_id: `rubric-${timestamp}-${score}-rule`,
              name: `${code} ${score}`,
              generated_target_field: code,
              generated_comparison_operator: 'equals',
              generated_value: String(score),
              source_policy: policy,
            },
          ],
          groups: [],
        },
      })),
    },
    monitoring_policy: {
      enabled: true,
      initial_lookback_days: 365,
      incremental_overlap_days: 2,
      cadence: 'manual',
      source_lanes: ['known_source', 'official_company', 'signal_specific', 'open_web'],
    },
  };
}

export function loadRadarConfigOverrides(): Record<string, RadarConfigOverride> {
  try {
    const raw = window.localStorage.getItem(radarConfigStorageKey);
    if (!raw) {
      return {};
    }
    const parsed = JSON.parse(raw) as Record<string, RadarConfigOverride>;
    return Object.fromEntries(
      Object.entries(parsed)
        .filter(([, override]) => override?.radar?.radar_id)
        .map(([radarId, override]) => [
          radarId,
          {
            override_type: override.override_type === 'created' || override.override_type === 'deleted' ? override.override_type : 'edited',
            radar: normalizeRadarCatalogItem(override.radar),
            saved_at: override.saved_at || new Date(0).toISOString(),
          },
        ]),
    );
  } catch {
    window.localStorage.removeItem(radarConfigStorageKey);
    return {};
  }
}

export function mergeRadarCatalog(
  catalog: ICPRadarCatalogArtifact | null,
  overrides: Record<string, RadarConfigOverride>,
) {
  if (!catalog) {
    return [];
  }
  const deletedIds = new Set(Object.entries(overrides)
    .filter(([, override]) => override.override_type === 'deleted')
    .map(([radarId]) => radarId));
  const merged = catalog.radars
    .filter((radar) => !deletedIds.has(radar.radar_id) || isProtectedBackendRadar(radar))
    .map((radar) => {
      const override = overrides[radar.radar_id];
      const normalized = normalizeRadarCatalogItem(override && override.override_type !== 'deleted' ? override.radar : radar);
      return deletedIds.has(radar.radar_id) && isProtectedBackendRadar(radar)
        ? { ...normalized, local_override_status: 'protected_from_delete' }
        : normalized;
    });
  const existingIds = new Set(merged.map((radar) => radar.radar_id));
  const created = Object.values(overrides)
    .filter((override) => override.override_type !== 'deleted' && !existingIds.has(override.radar.radar_id))
    .map((override) => normalizeRadarCatalogItem(override.radar));
  return [...merged, ...created];
}

export function draftFromRadar(radar: ICPRadarCatalogItem): EditableRadarDefinitionDraft {
  return normalizeRadarDefinition(radar.definition);
}

export function radarFromDraft(base: ICPRadarCatalogItem, draft: EditableRadarDefinitionDraft): ICPRadarCatalogItem {
  const definition = definitionFromDraft(draft);
  return {
    ...base,
    name: draft.metadata.name.trim(),
    owner: draft.metadata.owner.trim() || base.owner,
    status: base.artifact_path ? 'modified_locally' : 'local_draft',
    profile: {
      ...base.profile,
      icp_profile: draft.metadata.name,
      product: draft.scoring_model.fit_model.description,
      segment: draft.account_qualification.rule_group.name || draft.account_qualification.rule_group.group_id,
      scope: draft.metadata.description,
    },
    summary: {
      ...base.summary,
      cadence: draft.monitoring_policy.cadence,
      run_mode: draft.monitoring_policy.run_mode,
    },
    definition: normalizeRadarDefinition(definition),
  };
}

export function createLocalRadarFromTemplate(
  template: RadarDefinition,
  name: string,
  owner: string,
  localDraftLimitation: string,
): ICPRadarCatalogItem {
  const id = `local-radar-${Date.now()}`;
  const definition: RadarDefinition = {
    ...cloneDefinition(template),
    definition_id: `${id}-definition`,
    metadata: {
      name,
      description: localDraftLimitation,
      owner,
      status: 'local_draft',
    },
    global_search_policy: {
      sources: [],
      keywords: [],
      exclusions: [],
      allow_system_sources: true,
    },
    intent_signals: [],
    monitoring_policy: {
      cadence: 'monthly',
      lookback_window: '30 days',
      run_mode: 'configured_not_generated',
      deduplication: 'dedupe_by_source_url_and_signal_code',
      stale_after: '180 days',
    },
  };

  return {
    radar_id: id,
    name,
    status: 'local_draft',
    owner,
    profile: {
      icp_profile: definition.metadata.name,
      product: '',
      segment: '',
      scope: definition.metadata.description,
    },
    summary: {
      cadence: definition.monitoring_policy.cadence,
      last_run: 'not_run',
      candidate_count: 0,
      needs_review_count: 0,
      accepted_count: 0,
      run_mode: definition.monitoring_policy.run_mode,
    },
    definition,
    artifact_path: null,
  };
}

export function duplicateLocalRadar(radar: ICPRadarCatalogItem, name: string): ICPRadarCatalogItem {
  const id = `local-radar-${Date.now()}`;
  return {
    ...radar,
    radar_id: id,
    name,
    status: 'local_draft',
    summary: {
      ...radar.summary,
      last_run: 'not_run',
      candidate_count: 0,
      needs_review_count: 0,
      accepted_count: 0,
    },
    definition: {
      ...cloneDefinition(radar.definition),
      definition_id: `${id}-definition`,
      metadata: {
        ...radar.definition.metadata,
        name,
        status: 'local_draft',
      },
    },
    artifact_path: null,
  };
}

export function normalizeRadarCatalogItem(radar: ICPRadarCatalogItem): ICPRadarCatalogItem {
  const definition = normalizeRadarDefinition(radar.definition);
  return {
    ...radar,
    radar_id: radar.radar_id || `radar-${Date.now()}`,
    name: radar.name || definition.metadata.name || 'ICP Radar',
    status: radar.status || definition.metadata.status || 'configured',
    owner: radar.owner || definition.metadata.owner || 'ABM Research',
    profile: {
      icp_profile: radar.profile?.icp_profile || definition.metadata.name || 'ICP Radar',
      product: radar.profile?.product || definition.scoring_model.fit_model.description || '',
      segment: radar.profile?.segment || definition.account_qualification.rule_group.name || '',
      scope: radar.profile?.scope || definition.metadata.description || '',
    },
    summary: {
      cadence: radar.summary?.cadence || definition.monitoring_policy.cadence || 'monthly',
      last_run: radar.summary?.last_run || 'not_run',
      candidate_count: Number.isFinite(Number(radar.summary?.candidate_count)) ? Number(radar.summary.candidate_count) : 0,
      needs_review_count: Number.isFinite(Number(radar.summary?.needs_review_count)) ? Number(radar.summary.needs_review_count) : 0,
      accepted_count: Number.isFinite(Number(radar.summary?.accepted_count)) ? Number(radar.summary.accepted_count) : 0,
      run_mode: radar.summary?.run_mode || definition.monitoring_policy.run_mode || 'configured_not_generated',
    },
    local_override_status: typeof radar.local_override_status === 'string' ? radar.local_override_status : undefined,
    definition,
    artifact_path: radar.artifact_path ?? null,
  };
}

export function normalizeRadarDefinition(definition: RadarDefinition): RadarDefinition {
  const fallbackDefinition = (definition ?? {}) as Partial<RadarDefinition>;
  const fallbackMetadata = (fallbackDefinition.metadata ?? {}) as Partial<RadarMetadata>;
  const fallbackGlobal = (fallbackDefinition.global_search_policy ?? {}) as Partial<GlobalSearchPolicy>;
  const fallbackMonitoring = (fallbackDefinition.monitoring_policy ?? {}) as Partial<MonitoringPolicy>;
  const fallbackScoring = (fallbackDefinition.scoring_model ?? {}) as Partial<RadarScoringModel>;
  const fallbackValidation = (fallbackDefinition.validation_report ?? {}) as Partial<RadarValidationReport>;
  const fitModel = (fallbackScoring.fit_model ?? {}) as Partial<RadarScoringModel['fit_model']>;
  const intentModel = (fallbackScoring.intent_model ?? {}) as Partial<RadarScoringModel['intent_model']>;
  const tierModel = (fallbackScoring.tier_model ?? {}) as Partial<RadarScoringModel['tier_model']>;

  return {
    definition_id: fallbackDefinition.definition_id || `definition-${Date.now()}`,
    metadata: {
      name: fallbackMetadata.name || 'ICP Radar',
      description: fallbackMetadata.description || '',
      owner: fallbackMetadata.owner || 'ABM Research',
      status: fallbackMetadata.status || 'configured',
    },
    global_search_policy: {
      sources: arrayOf(fallbackGlobal.sources).map(normalizeSourceDefinition),
      keywords: arrayOf(fallbackGlobal.keywords).map(String),
      exclusions: arrayOf(fallbackGlobal.exclusions).map(String),
      allow_system_sources: fallbackGlobal.allow_system_sources !== false,
    },
    account_qualification: {
      rule_group: normalizeRuleGroup(fallbackDefinition.account_qualification?.rule_group, 'qualification-root'),
    },
    intent_signals: arrayOf(fallbackDefinition.intent_signals).map(normalizeIntentSignal),
    monitoring_policy: {
      cadence: fallbackMonitoring.cadence || 'monthly',
      lookback_window: fallbackMonitoring.lookback_window || '30 days',
      run_mode: fallbackMonitoring.run_mode || 'configured_not_generated',
      deduplication: fallbackMonitoring.deduplication || 'dedupe_by_source_url_and_signal_code',
      stale_after: fallbackMonitoring.stale_after || '180 days',
    },
    scoring_model: {
      fit_model: {
        formula_preset: fitModel.formula_preset || 'weighted_average',
        description: fitModel.description || '',
        custom_formula: fitModel.custom_formula || '',
        uses: arrayOf(fitModel.uses).map(String),
      },
      intent_model: {
        formula_preset: intentModel.formula_preset || 'weighted_average',
        description: intentModel.description || '',
        custom_formula: intentModel.custom_formula || '',
        uses: arrayOf(intentModel.uses).map(String),
      },
      tier_model: {
        basis: tierModel.basis || 'fit + intent',
        description: tierModel.description || '',
      },
      tier_thresholds: fallbackScoring.tier_thresholds ?? {},
      confidence_penalties: fallbackScoring.confidence_penalties ?? {},
    },
    validation_report: {
      errors: arrayOf(fallbackValidation.errors),
      warnings: arrayOf(fallbackValidation.warnings),
      info: arrayOf(fallbackValidation.info),
    },
  };
}

export function normalizeSourceDefinition(source: SourceDefinition): SourceDefinition {
  const fallbackSource = (source ?? {}) as Partial<SourceDefinition>;
  const label = fallbackSource.label || fallbackSource.reference || 'Source';
  const reference = fallbackSource.reference || '';
  return {
    source_id: fallbackSource.source_id || sourceIdFrom(label, reference),
    source_type: fallbackSource.source_type || 'url',
    label,
    reference,
    trust_level: fallbackSource.trust_level || 'cross_check',
    usage_obligation: fallbackSource.usage_obligation || 'preferred',
  };
}

export function normalizeSourcePolicy(policy: SourcePolicy | undefined): SourcePolicy {
  const fallbackPolicy = (policy ?? {}) as Partial<SourcePolicy>;
  return {
    source_ids: arrayOf(fallbackPolicy.source_ids).map(String),
    source_logic: fallbackPolicy.source_logic === 'AND' ? 'AND' : 'OR',
    use_global_search_policy: fallbackPolicy.use_global_search_policy !== false,
    allow_additional_sources: fallbackPolicy.allow_additional_sources !== false,
    fallback_confidence: fallbackPolicy.fallback_confidence || 'hitl_required',
    local_sources: arrayOf(fallbackPolicy.local_sources).map(normalizeSourceDefinition),
  };
}

export function normalizeRuleGroup(group: RuleGroup | undefined, fallbackId: string): RuleGroup {
  const fallbackGroup = (group ?? {}) as Partial<RuleGroup>;
  return {
    group_id: fallbackGroup.group_id || fallbackId,
    name: fallbackGroup.name || '',
    operator: fallbackGroup.operator || 'AND',
    rules: arrayOf(fallbackGroup.rules).map(normalizeAtomicRule),
    groups: arrayOf(fallbackGroup.groups).map((nestedGroup, index) => normalizeRuleGroup(nestedGroup, `${fallbackId}-${index}`)),
  };
}

export function normalizeAtomicRule(rule: AtomicRule): AtomicRule {
  const fallbackRule = (rule ?? {}) as Partial<AtomicRule>;
  const description = fallbackRule.description || fallbackRule.name || '';
  return {
    rule_id: fallbackRule.rule_id || ruleIdFrom(description),
    name: fallbackRule.name || description,
    description,
    generated_target_field: fallbackRule.generated_target_field || '',
    generated_comparison_operator: fallbackRule.generated_comparison_operator || '',
    generated_value: fallbackRule.generated_value || '',
    requirement_level: fallbackRule.requirement_level || 'recommended',
    source_policy: normalizeSourcePolicy(fallbackRule.source_policy),
  };
}

export function normalizeIntentSignal(signal: IntentSignalDefinition): IntentSignalDefinition {
  const fallbackSignal = (signal ?? {}) as Partial<IntentSignalDefinition>;
  const code = fallbackSignal.code || fallbackSignal.signal_id || `S${Date.now()}`;
  const scoringRubric = fallbackSignal.scoring_rubric ?? { scale: [0, 1, 2], rules: [] };
  const scale = arrayOf(scoringRubric.scale).length ? arrayOf(scoringRubric.scale).map(Number) : [0, 1, 2];
  const monitoring = fallbackSignal.monitoring_policy ?? {
    enabled: true,
    initial_lookback_days: null,
    incremental_overlap_days: 2,
    cadence: 'manual',
    source_lanes: ['known_source', 'official_company', 'signal_specific', 'open_web'],
  };
  return {
    signal_id: fallbackSignal.signal_id || `signal-${code}`,
    code,
    name: fallbackSignal.name || code,
    description: fallbackSignal.description || '',
    trigger_rule_group: normalizeRuleGroup(fallbackSignal.trigger_rule_group, `trigger-${code}`),
    source_policy: normalizeSourcePolicy(fallbackSignal.source_policy),
    scoring_rubric: {
      scale,
      rules: scale.map((score) => {
        const sourceRule = arrayOf(scoringRubric.rules).find((rule) => Number(rule.score) === score);
        return {
          score,
          description: sourceRule?.description || '',
          rule_group: normalizeRuleGroup(sourceRule?.rule_group, `rubric-${code}-${score}`),
        };
      }),
    },
    monitoring_policy: {
      enabled: monitoring.enabled !== false,
      initial_lookback_days: monitoring.initial_lookback_days == null ? null : Number(monitoring.initial_lookback_days),
      incremental_overlap_days: Number(monitoring.incremental_overlap_days ?? 2),
      cadence: monitoring.cadence || 'manual',
      source_lanes: arrayOf(monitoring.source_lanes).length
        ? arrayOf(monitoring.source_lanes).map(String)
        : ['known_source', 'official_company', 'signal_specific', 'open_web'],
    },
  };
}

export function arrayOf<T>(value: T[] | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

export function cloneDefinition(definition: RadarDefinition): RadarDefinition {
  return JSON.parse(JSON.stringify(definition)) as RadarDefinition;
}

export function definitionFromDraft(draft: EditableRadarDefinitionDraft): RadarDefinition {
  return normalizeRadarDefinition(cloneDefinition(draft));
}

export function validateRadarDraft(draft: EditableRadarDefinitionDraft, t: (key: string) => string) {
  const errors: string[] = [];
  if (!draft.metadata.name.trim()) {
    errors.push(t('icpRadar.validation.radarName'));
  }
  if (!draft.metadata.owner.trim()) {
    errors.push(t('icpRadar.validation.owner'));
  }
  if (!draft.monitoring_policy.cadence.trim()) {
    errors.push(t('icpRadar.validation.cadence'));
  }
  if (!draft.monitoring_policy.run_mode.trim()) {
    errors.push(t('icpRadar.validation.runMode'));
  }
  if (!draft.global_search_policy.sources.length && !draft.global_search_policy.allow_system_sources) {
    errors.push(t('icpRadar.validation.monitoringSources'));
  }
  return errors;
}

export function sourceIdFrom(label: string, reference: string): string {
  const base = `${label || reference || 'source'}`
    .toLowerCase()
    .replace(/https?:\/\//g, '')
    .replace(/[^a-zа-я0-9]+/gi, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 48);
  return base || `source-${Date.now()}`;
}

export function ruleIdFrom(label: string): string {
  const base = label
    .toLowerCase()
    .replace(/[^a-zа-я0-9]+/gi, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 48);
  return base ? `rule-${base}` : `rule-${Date.now()}`;
}

export function isLocalRadarStatus(status: string) {
  return status === 'local_draft' || status === 'modified_locally';
}

function isProtectedBackendRadar(radar: ICPRadarCatalogItem) {
  return radar.summary?.run_mode === 'benchmark';
}
