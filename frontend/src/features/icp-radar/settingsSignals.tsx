import { Plus, X } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button, Mono } from '../../components/primitives';
import type { EditableRadarDefinitionDraft, IntentSignalDefinition, RadarDefinition } from '../../types';
import { globalSignalRubric, newIntentSignal, primaryRuleDescription, replaceAt, sameRubric, setPrimaryRuleDescription, signalRuleText, sourcePolicySummary } from './model';
import { BooleanPill, TextAreaField, ToggleField } from './settingsFields';
import { SimpleSourcePolicyEditor } from './settingsQualification';

export function IntentSignalsSummary({ definition }: { definition: RadarDefinition }) {
  const { t } = useTranslation();
  const globalRubric = globalSignalRubric(definition);
  return (
    <div className="settings-table intent-signal-table">
      <div className="settings-table-head">
        <span>{t('icpRadar.settings.signalCode')}</span>
        <span>{t('icpRadar.settings.signalDetection')}</span>
        <span>{t('icpRadar.settings.sources')}</span>
        <span>{t('icpRadar.settings.crossValidationShort')}</span>
        <span>{t('icpRadar.settings.additionalSourcesShort')}</span>
        <span>{t('icpRadar.settings.scaleOverrideShort')}</span>
      </div>
      {definition.intent_signals.map((signal) => (
        <div className="settings-table-row criterion-row" key={signal.signal_id}>
          <Mono>{signal.code}</Mono>
          <span>
            <strong>{signalRuleText(signal)}</strong>
            <small>{signal.signal_id}</small>
          </span>
          <span>{sourcePolicySummary(signal.source_policy, t)}</span>
          <BooleanPill active={signal.source_policy.source_logic === 'AND'} />
          <BooleanPill active={signal.source_policy.allow_additional_sources} />
          <BooleanPill active={!sameRubric(signal.scoring_rubric, globalRubric)} />
        </div>
      ))}
    </div>
  );
}

export function SignalScaleSummary({ definition }: { definition: RadarDefinition }) {
  return <SignalRubricSummary rubric={globalSignalRubric(definition)} />;
}

export function SignalScaleEditor({
  draft,
  onDraftChange,
}: {
  draft: EditableRadarDefinitionDraft;
  onDraftChange: (draft: EditableRadarDefinitionDraft) => void;
}) {
  const { t } = useTranslation();
  const globalRubric = globalSignalRubric(draft);
  function updateAllRubrics(scoring_rubric: IntentSignalDefinition['scoring_rubric']) {
    onDraftChange({
      ...draft,
      intent_signals: draft.intent_signals.map((signal) => (
        sameRubric(signal.scoring_rubric, globalRubric)
          ? { ...signal, scoring_rubric }
          : signal
      )),
    });
  }
  return (
    <div className="signal-scale-editor">
      <div className="generated-code-row">
        <Mono>{globalRubric.scale.join(' / ')}</Mono>
        <small>{t('icpRadar.settings.signalScaleLocked')}</small>
      </div>
      <SignalRubricTable rubric={globalRubric} onChange={updateAllRubrics} />
    </div>
  );
}

export function IntentSignalsEditor({
  draft,
  onDraftChange,
}: {
  draft: EditableRadarDefinitionDraft;
  onDraftChange: (draft: EditableRadarDefinitionDraft) => void;
}) {
  const { t } = useTranslation();
  const globalSources = draft.global_search_policy.sources;
  const globalRubric = globalSignalRubric(draft);

  return (
    <div className="criteria-editor-list">
      {draft.intent_signals.map((signal, index) => (
        <div className="criteria-editor-row" key={`${signal.signal_id}-${index}`}>
          <div className="generated-code-row">
            <Mono>{signal.code}</Mono>
            <small>{t('icpRadar.settings.generatedCode')}</small>
          </div>
          <TextAreaField
            label={t('icpRadar.settings.signalDetection')}
            value={primaryRuleDescription(signal.trigger_rule_group)}
            onChange={(description) => onDraftChange({ ...draft, intent_signals: replaceAt(draft.intent_signals, index, { ...signal, trigger_rule_group: setPrimaryRuleDescription(signal.trigger_rule_group, description) }) })}
          />
          <SimpleSourcePolicyEditor globalSources={globalSources} policy={signal.source_policy} onChange={(source_policy) => onDraftChange({ ...draft, intent_signals: replaceAt(draft.intent_signals, index, { ...signal, source_policy }) })} />
          <SignalRubricOverride
            globalRubric={globalRubric}
            signal={signal}
            onChange={(nextSignal) => onDraftChange({ ...draft, intent_signals: replaceAt(draft.intent_signals, index, nextSignal) })}
          />
          <Button icon={<X aria-hidden="true" />} variant="default" onClick={() => onDraftChange({ ...draft, intent_signals: draft.intent_signals.filter((_, currentIndex) => currentIndex !== index) })}>
            {t('icpRadar.settings.remove')}
          </Button>
        </div>
      ))}
      <Button icon={<Plus aria-hidden="true" />} variant="default" onClick={() => onDraftChange({ ...draft, intent_signals: [...draft.intent_signals, newIntentSignal(globalSources.map((source) => source.source_id))] })}>
        {t('icpRadar.settings.addSignal')}
      </Button>
    </div>
  );
}

export function SignalRubricOverride({
  globalRubric,
  onChange,
  signal,
}: {
  globalRubric: IntentSignalDefinition['scoring_rubric'];
  onChange: (signal: IntentSignalDefinition) => void;
  signal: IntentSignalDefinition;
}) {
  const { t } = useTranslation();
  const [override, setOverride] = useState(!sameRubric(signal.scoring_rubric, globalRubric));
  return (
    <div className="scoring-rubric-editor">
      <ToggleField
        checked={override}
        label={t('icpRadar.settings.overrideSignalScoring')}
        onChange={(checked) => {
          setOverride(checked);
          if (!checked) {
            onChange({ ...signal, scoring_rubric: globalRubric });
          }
        }}
      />
      {override && (
        <SignalRubricTable
          rubric={signal.scoring_rubric}
          onChange={(scoring_rubric) => onChange({ ...signal, scoring_rubric })}
        />
      )}
    </div>
  );
}

export function SignalRubricSummary({ rubric }: { rubric: IntentSignalDefinition['scoring_rubric'] }) {
  const { t } = useTranslation();
  return (
    <table className="rubric-table rubric-table-compact">
      <thead>
        <tr>
          <th>{t('icpRadar.settings.scoreValue')}</th>
          <th>{t('icpRadar.settings.whenToScore')}</th>
        </tr>
      </thead>
      <tbody>
        {rubric.rules.map((rule) => (
          <tr key={rule.score}>
            <td><Mono>{rule.score}</Mono></td>
            <td>{rule.description}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function SignalRubricTable({
  onChange,
  rubric,
}: {
  onChange: (rubric: IntentSignalDefinition['scoring_rubric']) => void;
  rubric: IntentSignalDefinition['scoring_rubric'];
}) {
  const { t } = useTranslation();
  return (
      <table className="rubric-table">
        <thead>
          <tr>
            <th>{t('icpRadar.settings.scoreValue')}</th>
            <th>{t('icpRadar.settings.whenToScore')}</th>
          </tr>
        </thead>
        <tbody>
      {rubric.rules.map((rule, index) => (
        <tr key={rule.score}>
          <td><Mono>{rule.score}</Mono></td>
          <td>
            <TextAreaField
              label={`${rule.score}`}
              value={rule.description}
              onChange={(description) => onChange({ ...rubric, rules: replaceAt(rubric.rules, index, { ...rule, description }) })}
            />
          </td>
        </tr>
      ))}
        </tbody>
      </table>
  );
}
