import {
  ArrowLeft,
  ChevronRight,
  Copy,
  Radar,
  RotateCcw,
  Save,
  SlidersHorizontal,
  Trash2,
  X,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Eyebrow } from '../../../components/primitives';
import type {
  EditableRadarDefinitionDraft,
  ICPRadarArtifact,
  ICPRadarCatalogItem,
  RadarConfigOverride,
} from '../../../types';
import type { RadarDetailTab } from '../modelTypes';
import { radarOperationalStatus, radarStatusKey } from '../domain/radarStatus';
import { RadarHeaderEditor, type SettingsBlockId } from '../settingsHeader';

export function RadarDetailHeader({
  activeTab,
  artifact,
  dirty,
  draft,
  editingBlock,
  isLocalDraft,
  onBack,
  onDelete,
  onDiscard,
  onDraftChange,
  onDuplicate,
  onEditHeader,
  onReset,
  onSave,
  onTabChange,
  overrideType,
  radar,
  validationErrors,
}: {
  activeTab: RadarDetailTab;
  artifact: ICPRadarArtifact | null;
  dirty: boolean;
  draft: EditableRadarDefinitionDraft | null;
  editingBlock: SettingsBlockId | null;
  isLocalDraft: boolean;
  onBack: () => void;
  onDelete: () => void;
  onDiscard: () => void;
  onDraftChange: (draft: EditableRadarDefinitionDraft) => void;
  onDuplicate: () => void;
  onEditHeader: () => void;
  onReset: () => void;
  onSave: () => void;
  onTabChange: (tab: RadarDetailTab) => void;
  overrideType: RadarConfigOverride['override_type'] | undefined;
  radar: ICPRadarCatalogItem;
  validationErrors: string[];
}) {
  const { t } = useTranslation();
  const headerDraft = draft ?? radar.definition;
  const headerDescription = headerDraft.metadata.description || radar.profile.scope || (
    artifact
      ? t('icpRadar.summary', {
        count: artifact.candidates.length,
        holding: artifact.radar.profile.holding,
        product: artifact.radar.profile.product,
      })
      : t('icpRadar.emptyShortlistSummary', { product: radar.profile.product })
  );
  const editingHeader = activeTab === 'settings' && editingBlock === 'overview';
  const effectiveHeaderStatus = radarOperationalStatus(headerDraft.metadata.status || radar.status);
  const statusTone = effectiveHeaderStatus === 'active' ? 'ally' : 'neutral';

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
        <div className="icp-radar-header-main">
          {editingHeader ? (
            <RadarHeaderEditor draft={headerDraft} onDraftChange={onDraftChange} />
          ) : (
            <>
              <Eyebrow>{t('icpRadar.eyebrow')}</Eyebrow>
              <h1>{headerDraft.metadata.name || radar.name}</h1>
              <p>{headerDescription}</p>
              <div className="icp-radar-header-meta-row">
                <Badge tone={statusTone}>{t(radarStatusKey(effectiveHeaderStatus))}</Badge>
                {isLocalDraft && <Badge tone="unsurfaced">{t('icpRadar.localDraft')}</Badge>}
                {dirty && <Badge tone="unsurfaced">{t('icpRadar.unsavedChanges')}</Badge>}
                <span>{t('icpRadar.cardFields.owner')}: {headerDraft.metadata.owner || radar.owner}</span>
              </div>
            </>
          )}
        </div>
        <div className="icp-radar-header-actions">
          {activeTab === 'settings' && (
            <div className="icp-editor-actions">
              {editingHeader ? (
                <>
                  <Button disabled={validationErrors.length > 0} icon={<Save aria-hidden="true" />} variant="default" onClick={onSave}>
                    {t('icpRadar.saveDraft')}
                  </Button>
                  <Button icon={<X aria-hidden="true" />} variant="default" onClick={onDiscard}>
                    {t('icpRadar.discardChanges')}
                  </Button>
                </>
              ) : (
                <>
                  <Button icon={<SlidersHorizontal aria-hidden="true" />} variant="default" onClick={onEditHeader}>
                    {t('icpRadar.editSettings')}
                  </Button>
                  <Button icon={<Copy aria-hidden="true" />} variant="default" onClick={onDuplicate}>
                    {t('icpRadar.duplicateRadar')}
                  </Button>
                  <Button icon={<Trash2 aria-hidden="true" />} variant="default" onClick={onDelete}>
                    {t('icpRadar.deleteRadar')}
                  </Button>
                  {overrideType && (
                    <Button icon={<RotateCcw aria-hidden="true" />} variant="default" onClick={onReset}>
                      {t('icpRadar.resetToArtifact')}
                    </Button>
                  )}
                </>
              )}
            </div>
          )}
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
          aria-pressed={activeTab === 'operations'}
          className={`criteria-chip${activeTab === 'operations' ? ' criteria-chip-active' : ''}`}
          type="button"
          onClick={() => onTabChange('operations')}
        >
          {t('icpRadar.operationsTab')}
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
