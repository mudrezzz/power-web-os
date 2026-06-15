import { Plus, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Mono } from '../../components/primitives';
import type { AtomicRule, RuleGroup, SourceDefinition, SourcePolicy } from '../../types';
import { isNotRule, logicalOperatorKey, newAtomicRule, replaceAt, requirementKey, ruleOperatorLabel, sourcePolicySummary } from './model';
import { BooleanPill, SelectField, TextAreaField, ToggleField } from './settingsFields';
import { SourceListEditor } from './settingsSearch';

export function RuleGroupSummary({ group }: { group: RuleGroup }) {
  const { t } = useTranslation();
  return (
    <div className="settings-table qualification-table">
      <div className="settings-table-head">
        <span>{t('icpRadar.settings.operator')}</span>
        <span>{t('icpRadar.settings.rule')}</span>
        <span>{t('icpRadar.settings.sources')}</span>
        <span>{t('icpRadar.settings.crossValidationShort')}</span>
        <span>{t('icpRadar.settings.additionalSourcesShort')}</span>
        <span>{t('icpRadar.settings.requirement')}</span>
      </div>
      {group.rules.map((rule) => (
        <div className="settings-table-row simple-rule-row" key={rule.rule_id}>
          <Mono>{ruleOperatorLabel(group.operator, rule)}</Mono>
          <span>
            <strong>{rule.description || t('icpRadar.settings.rule')}</strong>
            <small>{rule.rule_id}</small>
          </span>
          <span>{sourcePolicySummary(rule.source_policy, t)}</span>
          <BooleanPill active={rule.source_policy.source_logic === 'AND'} />
          <BooleanPill active={rule.source_policy.allow_additional_sources} />
          <Badge tone={rule.requirement_level === 'required' ? 'ally' : 'neutral'}>{t(requirementKey(rule.requirement_level))}</Badge>
        </div>
      ))}
    </div>
  );
}

export function QualificationRulesEditor({
  globalSources,
  group,
  onChange,
}: {
  globalSources: SourceDefinition[];
  group: RuleGroup;
  onChange: (group: RuleGroup) => void;
}) {
  const { t } = useTranslation();
  function updateRule(index: number, nextRule: AtomicRule) {
    onChange({ ...group, rules: replaceAt(group.rules, index, nextRule), groups: [] });
  }
  return (
    <div className="criteria-editor-list">
      <div className="icp-section-toolbar">
        <SelectField
          label={t('icpRadar.settings.logicalOperator')}
          options={['AND', 'OR']}
          value={group.operator === 'OR' ? 'OR' : 'AND'}
          onChange={(operator) => onChange({ ...group, operator, groups: [] })}
          optionLabel={(option) => t(logicalOperatorKey(option))}
        />
      </div>
      {group.rules.map((rule, index) => (
        <SimpleRuleEditor
          globalSources={globalSources}
          key={`${rule.rule_id || 'rule'}-${index}`}
          rule={rule}
          onChange={(nextRule) => updateRule(index, nextRule)}
          onRemove={() => onChange({ ...group, rules: group.rules.filter((_, currentIndex) => currentIndex !== index) })}
        />
      ))}
      <Button icon={<Plus aria-hidden="true" />} variant="default" onClick={() => onChange({ ...group, rules: [...group.rules, newAtomicRule()] })}>
        {t('icpRadar.settings.addRule')}
      </Button>
    </div>
  );
}

export function SimpleRuleEditor({
  globalSources,
  onChange,
  onRemove,
  rule,
}: {
  globalSources: SourceDefinition[];
  onChange: (rule: AtomicRule) => void;
  onRemove: () => void;
  rule: AtomicRule;
}) {
  const { t } = useTranslation();
  return (
    <div className="criteria-editor-row">
      <div className="generated-code-row">
        <Mono>{rule.rule_id || t('icpRadar.settings.rule')}</Mono>
        <small>{t('icpRadar.settings.generatedIdReadonly')}</small>
      </div>
      <div className="simple-rule-editor-main">
        <ToggleField
          checked={isNotRule(rule)}
          label={t('icpRadar.settings.notRule')}
          onChange={(checked) => onChange({ ...rule, generated_comparison_operator: checked ? 'not_equals' : '' })}
        />
        <TextAreaField label={t('icpRadar.settings.ruleDescription')} value={rule.description} onChange={(description) => onChange({ ...rule, description })} />
        <SelectField label={t('icpRadar.settings.requirement')} options={['required', 'recommended']} value={rule.requirement_level} onChange={(requirement_level) => onChange({ ...rule, requirement_level })} optionLabel={(option) => t(requirementKey(option))} />
      </div>
      <SimpleSourcePolicyEditor globalSources={globalSources} policy={rule.source_policy} onChange={(source_policy) => onChange({ ...rule, source_policy })} />
      <Button icon={<X aria-hidden="true" />} variant="default" onClick={onRemove}>
        {t('icpRadar.settings.remove')}
      </Button>
    </div>
  );
}

export function SimpleSourcePolicyEditor({
  globalSources,
  onChange,
  policy,
}: {
  globalSources: SourceDefinition[];
  onChange: (policy: SourcePolicy) => void;
  policy: SourcePolicy;
}) {
  const { t } = useTranslation();
  return (
    <div className="source-policy-editor">
      <div className="policy-switch-strip">
        <ToggleField checked={policy.use_global_search_policy} label={t('icpRadar.settings.useGlobalSearchPolicy')} onChange={(use_global_search_policy) => onChange({ ...policy, use_global_search_policy })} />
        <ToggleField
          checked={policy.source_logic === 'AND'}
          label={t('icpRadar.settings.crossValidation')}
          onChange={(checked) => onChange({ ...policy, source_logic: checked ? 'AND' : 'OR' })}
        />
        <ToggleField
          checked={policy.allow_additional_sources}
          label={t('icpRadar.settings.hitlAdditionalSources')}
          onChange={(allow_additional_sources) => onChange({ ...policy, allow_additional_sources, fallback_confidence: allow_additional_sources ? 'hitl_required' : 'trusted' })}
        />
      </div>
      {policy.use_global_search_policy && (
        <small>{t('icpRadar.settings.globalSearchPolicyCopy', { count: globalSources.length })}</small>
      )}
      <SourceListEditor
        sources={policy.local_sources ?? []}
        onChange={(local_sources) => onChange({ ...policy, local_sources })}
      />
    </div>
  );
}
