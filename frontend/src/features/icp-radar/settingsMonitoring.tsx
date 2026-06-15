import { useTranslation } from 'react-i18next';
import type { EditableRadarDefinitionDraft, RadarDefinition } from '../../types';
import { cadenceKey, deduplicationKey, deduplicationValue, runModeKey } from './model';
import { DurationField, SelectField } from './settingsFields';
import { Metric } from './settingsBlocks';

export function MonitoringSummary({ definition }: { definition: RadarDefinition }) {
  const { t } = useTranslation();
  return (
    <dl className="icp-definition-list">
      <Metric label={t('icpRadar.cardFields.cadence')} value={t(cadenceKey(definition.monitoring_policy.cadence))} />
      <Metric label={t('icpRadar.settings.lookbackWindow')} value={definition.monitoring_policy.lookback_window} />
      <Metric label={t('icpRadar.cardFields.runMode')} value={t(runModeKey(definition.monitoring_policy.run_mode))} />
      <Metric label={t('icpRadar.settings.deduplication')} value={definition.monitoring_policy.deduplication} />
      <Metric label={t('icpRadar.settings.staleAfter')} value={definition.monitoring_policy.stale_after} />
    </dl>
  );
}

export function MonitoringEditor({
  draft,
  onDraftChange,
}: {
  draft: EditableRadarDefinitionDraft;
  onDraftChange: (draft: EditableRadarDefinitionDraft) => void;
}) {
  const { t } = useTranslation();
  const policy = draft.monitoring_policy;
  function updatePolicy(patch: Partial<EditableRadarDefinitionDraft['monitoring_policy']>) {
    onDraftChange({ ...draft, monitoring_policy: { ...policy, ...patch } });
  }
  return (
    <div className="criteria-editor-list">
      <SelectField label={t('icpRadar.cardFields.cadence')} options={['weekly', 'monthly']} value={policy.cadence} onChange={(cadence) => updatePolicy({ cadence })} optionLabel={(option) => t(cadenceKey(option))} />
      <DurationField label={t('icpRadar.settings.lookbackWindow')} value={policy.lookback_window} onChange={(lookback_window) => updatePolicy({ lookback_window })} />
      <SelectField label={t('icpRadar.cardFields.runMode')} options={['incremental_signal_monitoring', 'configured_not_generated', 'fixture_import']} value={policy.run_mode} onChange={(run_mode) => updatePolicy({ run_mode })} optionLabel={(option) => t(runModeKey(option))} />
      <SelectField label={t('icpRadar.settings.deduplication')} options={['source_url', 'source_url_and_signal', 'normalized_fact', 'none']} value={deduplicationValue(policy.deduplication)} onChange={(deduplication) => updatePolicy({ deduplication })} optionLabel={(option) => t(deduplicationKey(option))} />
      <DurationField label={t('icpRadar.settings.staleAfter')} value={policy.stale_after} onChange={(stale_after) => updatePolicy({ stale_after })} />
    </div>
  );
}
