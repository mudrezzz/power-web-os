import { useTranslation } from 'react-i18next';
import type { EditableRadarDefinitionDraft, RadarEditorState } from '../../types';
import type { RadarRunConfigurationDto } from '../../api/radarApi';
import { GlobalSearchEditor, GlobalSearchSummary } from './settingsSearch';
import { MonitoringEditor, MonitoringSummary } from './settingsMonitoring';
import { QualificationRulesEditor, RuleGroupSummary } from './settingsQualification';
import { IntentSignalsEditor, IntentSignalsSummary, SignalScaleEditor, SignalScaleSummary } from './settingsSignals';
import { ScoringModelEditor, ScoringModelSummary } from './settingsScoring';
import { ValidationReportView } from './settingsValidation';
import { AiSuggestButton, SettingsBlockCard } from './settingsBlocks';
import type { SettingsBlockId } from './settingsHeader';
import { PowerWebPolicySettings } from './components/PowerWebPolicySettings';
import type { PowerWebHandoffBackendController } from './application/usePowerWebHandoffBackend';

// Settings is block-editable by design: each block owns its save/discard controls so radar editing stays reviewable.

export function RadarSettings({
  dirty,
  draft,
  editingBlock,
  onCancel,
  onDraftChange,
  onEdit,
  onSave,
  validationErrors,
  runConfiguration,
  powerWebBackend,
  radarId,
}: {
  dirty: boolean;
  draft: EditableRadarDefinitionDraft;
  editingBlock: SettingsBlockId | null;
  onCancel: () => void;
  onDraftChange: (draft: EditableRadarDefinitionDraft) => void;
  onEdit: (block: SettingsBlockId | null) => void;
  onSave: () => void;
  validationErrors: string[];
  runConfiguration: RadarRunConfigurationDto | null;
  powerWebBackend: PowerWebHandoffBackendController;
  radarId: string;
}) {
  const { t } = useTranslation();
  const editorState: RadarEditorState = {
    mode: editingBlock ? 'edit' : 'view',
    dirty,
    errors: validationErrors,
  };

  return (
    <div className="icp-settings-stack">
      <div className="settings-configuration-context">
        <section>
          <strong>{t('icpRadar.settings.activeDefinition')}</strong>
          <span>{draft.definition_version ?? t('icpRadar.unknown')}</span>
        </section>
        {runConfiguration && (
          <section>
            <strong>{t('icpRadar.settings.historicalSnapshot')}</strong>
            <span>{runConfiguration.run_id}</span>
            <span>{runConfiguration.definition_version || t('icpRadar.unknown')}</span>
            <span>{runConfiguration.run_profile || t('icpRadar.unknown')}</span>
          </section>
        )}
      </div>
      {editorState.dirty && (
        <div className="icp-editor-errors" role="status">
          <span>{t('icpRadar.unsavedChanges')}</span>
        </div>
      )}
      {editorState.errors.length > 0 && (
        <div className="icp-editor-errors" role="alert">
          {editorState.errors.map((error) => <span key={error}>{error}</span>)}
        </div>
      )}

      <div className="icp-settings-grid">
        <SettingsBlockCard
          blockId="global_search"
          editingBlock={editingBlock}
          headerAction={<AiSuggestButton />}
          onCancel={onCancel}
          onEdit={onEdit}
          onSave={onSave}
          title={t('icpRadar.settings.globalSearch')}
        >
          {editingBlock === 'global_search' ? (
            <GlobalSearchEditor draft={draft} onDraftChange={onDraftChange} />
          ) : (
            <GlobalSearchSummary definition={draft} />
          )}
        </SettingsBlockCard>

        <SettingsBlockCard
          blockId="qualification"
          editingBlock={editingBlock}
          headerAction={<AiSuggestButton />}
          onCancel={onCancel}
          onEdit={onEdit}
          onSave={onSave}
          title={t('icpRadar.settings.qualificationRules')}
        >
          {editingBlock === 'qualification' ? (
            <QualificationRulesEditor
              group={draft.account_qualification.rule_group}
              globalSources={draft.global_search_policy.sources}
              onChange={(rule_group) => onDraftChange({ ...draft, account_qualification: { rule_group } })}
            />
          ) : (
            <RuleGroupSummary group={draft.account_qualification.rule_group} />
          )}
        </SettingsBlockCard>

        <SettingsBlockCard
          blockId="monitoring"
          editingBlock={editingBlock}
          onCancel={onCancel}
          onEdit={onEdit}
          onSave={onSave}
          title={t('icpRadar.settings.monitoring')}
        >
          {editingBlock === 'monitoring' ? (
            <MonitoringEditor draft={draft} onDraftChange={onDraftChange} />
          ) : (
            <MonitoringSummary definition={draft} />
          )}
        </SettingsBlockCard>

        <SettingsBlockCard
          blockId="signal_scale"
          editingBlock={editingBlock}
          onCancel={onCancel}
          onEdit={onEdit}
          onSave={onSave}
          title={t('icpRadar.settings.signalScale')}
        >
          {editingBlock === 'signal_scale' ? (
            <SignalScaleEditor draft={draft} onDraftChange={onDraftChange} />
          ) : (
            <SignalScaleSummary definition={draft} />
          )}
        </SettingsBlockCard>

        <SettingsBlockCard
          blockId="intent_signals"
          editingBlock={editingBlock}
          onCancel={onCancel}
          onEdit={onEdit}
          onSave={onSave}
          title={t('icpRadar.settings.intentSignals')}
        >
          {editingBlock === 'intent_signals' ? (
            <IntentSignalsEditor draft={draft} onDraftChange={onDraftChange} />
          ) : (
            <IntentSignalsSummary definition={draft} />
          )}
        </SettingsBlockCard>

        <SettingsBlockCard
          blockId="scoring"
          editingBlock={editingBlock}
          onCancel={onCancel}
          onEdit={onEdit}
          onSave={onSave}
          title={t('icpRadar.settings.scoring')}
        >
          {editingBlock === 'scoring' ? (
            <ScoringModelEditor draft={draft} onDraftChange={onDraftChange} />
          ) : (
            <ScoringModelSummary definition={draft} />
          )}
        </SettingsBlockCard>

        <SettingsBlockCard
          blockId="validation"
          editingBlock={editingBlock}
          onCancel={onCancel}
          onEdit={onEdit}
          onSave={onSave}
          title={t('icpRadar.settings.validation')}
        >
          <ValidationReportView report={draft.validation_report} />
        </SettingsBlockCard>
      </div>
      <PowerWebPolicySettings backend={powerWebBackend} radarId={radarId} />
    </div>
  );
}
