import { useTranslation } from 'react-i18next';
import { Badge, Mono } from '../../components/primitives';
import type { EditableRadarDefinitionDraft, RadarDefinition, RadarScoringModel } from '../../types';
import { SelectField, TextAreaField, TextField } from './settingsFields';

export function ScoringModelSummary({ definition }: { definition: RadarDefinition }) {
  const { t } = useTranslation();
  return (
    <>
      <Badge tone="unsurfaced">{t('icpRadar.settings.scoringRuntimePending')}</Badge>
      <div className="icp-settings-formula-grid">
        {[
          [t('icpRadar.fit'), presetLabel(definition.scoring_model.fit_model.formula_preset, t)],
          [t('icpRadar.intent'), presetLabel(definition.scoring_model.intent_model.formula_preset, t)],
          [t('icpRadar.columns.tier'), definition.scoring_model.tier_model.basis],
        ].map(([name, value]) => (
          <div key={name}>
            <Mono>{name}</Mono>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <div className="icp-settings-thresholds">
        {Object.entries(definition.scoring_model.tier_thresholds).map(([tier, value]) => (
          <Badge key={tier} tone={tier === 'Tier 1' ? 'ally' : 'neutral'}>{tier} {value}</Badge>
        ))}
      </div>
    </>
  );
}

export function ScoringModelEditor({
  draft,
  onDraftChange,
}: {
  draft: EditableRadarDefinitionDraft;
  onDraftChange: (draft: EditableRadarDefinitionDraft) => void;
}) {
  const { t } = useTranslation();
  const model = draft.scoring_model;
  function updateModel(patch: Partial<EditableRadarDefinitionDraft['scoring_model']>) {
    onDraftChange({ ...draft, scoring_model: { ...model, ...patch } });
  }
  return (
    <div className="criteria-editor-list">
      <Badge tone="unsurfaced">{t('icpRadar.settings.scoringRuntimePending')}</Badge>
      <FormulaModelEditor
        codes={draft.account_qualification.rule_group.rules.map((rule) => rule.rule_id)}
        label={t('icpRadar.fit')}
        model={model.fit_model}
        onChange={(fit_model) => updateModel({ fit_model })}
      />
      <FormulaModelEditor
        codes={draft.intent_signals.map((signal) => signal.code)}
        label={t('icpRadar.intent')}
        model={model.intent_model}
        onChange={(intent_model) => updateModel({ intent_model })}
      />
      <TextAreaField
        label={t('icpRadar.settings.tierModel')}
        value={model.tier_model.description}
        onChange={(description) => updateModel({ tier_model: { ...model.tier_model, description } })}
      />
      <div className="icp-threshold-editor">
        {Object.entries(model.tier_thresholds).map(([tier, value]) => (
          <TextField
            key={tier}
            label={tier}
            value={value}
            onChange={(nextValue) => updateModel({ tier_thresholds: { ...model.tier_thresholds, [tier]: nextValue } })}
          />
        ))}
      </div>
    </div>
  );
}

export function FormulaModelEditor({
  codes,
  label,
  model,
  onChange,
}: {
  codes: string[];
  label: string;
  model: RadarScoringModel['fit_model'];
  onChange: (model: RadarScoringModel['fit_model']) => void;
}) {
  const { t } = useTranslation();
  const presetOptions = ['arithmetic_mean', 'weighted_average', 'maximum_signal', 'capped_sum', 'custom'];
  return (
    <div className="formula-model-editor">
      <SelectField label={label} options={presetOptions} value={model.formula_preset} onChange={(formula_preset) => onChange({ ...model, formula_preset })} />
      <TextAreaField label={t('icpRadar.settings.description')} value={model.description} onChange={(description) => onChange({ ...model, description })} />
      {model.formula_preset === 'custom' && (
        <>
          <div className="formula-code-reference">
            <Mono>{t('icpRadar.settings.availableCodes')}</Mono>
            <span>{codes.join(', ')}</span>
          </div>
          <TextAreaField label={t('icpRadar.settings.customFormula')} value={model.custom_formula} onChange={(custom_formula) => onChange({ ...model, custom_formula })} />
        </>
      )}
    </div>
  );
}

function presetLabel(preset: string, t: (key: string) => string): string {
  const key = `icpRadar.settings.formulaPresets.${preset}`;
  const translated = t(key);
  return translated === key ? preset : translated;
}
