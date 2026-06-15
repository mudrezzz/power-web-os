import { useTranslation } from 'react-i18next';
import type { EditableRadarDefinitionDraft } from '../../types';
import { TextAreaField, TextField, ToggleField } from './settingsFields';

export type SettingsBlockId = 'overview' | 'global_search' | 'qualification' | 'monitoring' | 'signal_scale' | 'intent_signals' | 'scoring' | 'validation';

// Header editing is intentionally lightweight so the radar header can stay interactive without loading the full settings editor.

export function RadarHeaderEditor({
  draft,
  onDraftChange,
}: {
  draft: EditableRadarDefinitionDraft;
  onDraftChange: (draft: EditableRadarDefinitionDraft) => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="icp-settings-header-editor">
      <TextField label={t('icpRadar.settings.radarName')} value={draft.metadata.name} onChange={(name) => onDraftChange({ ...draft, metadata: { ...draft.metadata, name } })} />
      <TextAreaField label={t('icpRadar.settings.description')} value={draft.metadata.description} onChange={(description) => onDraftChange({ ...draft, metadata: { ...draft.metadata, description } })} />
      <div className="icp-radar-header-meta-row">
        <ToggleField
          checked={draft.metadata.status === 'active'}
          label={t('icpRadar.settings.activeStatus')}
          onChange={(active) => onDraftChange({ ...draft, metadata: { ...draft.metadata, status: active ? 'active' : 'configured' } })}
        />
        <span>{t('icpRadar.cardFields.owner')}: {draft.metadata.owner}</span>
      </div>
    </div>
  );
}
