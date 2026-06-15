import { Save, SlidersHorizontal, Sparkles, X } from 'lucide-react';
import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { Button, Card, Eyebrow } from '../../components/primitives';
import type { SettingsBlockId } from './settingsHeader';

export function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

export function SettingsBlockCard({
  blockId,
  children,
  editingBlock,
  headerAction,
  onCancel,
  onEdit,
  onSave,
  title,
}: {
  blockId: SettingsBlockId;
  children: ReactNode;
  editingBlock: SettingsBlockId | null;
  headerAction?: ReactNode;
  onCancel: () => void;
  onEdit: (block: SettingsBlockId | null) => void;
  onSave: () => void;
  title: string;
}) {
  const { t } = useTranslation();
  const editing = editingBlock === blockId;
  return (
    <Card>
      <div className="icp-settings-section">
        <div className="icp-settings-section-head">
          <Eyebrow>{title}</Eyebrow>
          {blockId !== 'validation' && (
            <div className="icp-editor-actions">
              {headerAction}
              {editing ? (
                <>
                  <Button icon={<Save aria-hidden="true" />} variant="default" onClick={onSave}>
                    {t('icpRadar.saveDraft')}
                  </Button>
                  <Button icon={<X aria-hidden="true" />} variant="default" onClick={onCancel}>
                    {t('icpRadar.discardChanges')}
                  </Button>
                </>
              ) : (
                <Button icon={<SlidersHorizontal aria-hidden="true" />} variant="default" onClick={() => onEdit(blockId)}>
                  {t('icpRadar.editSettings')}
                </Button>
              )}
            </div>
          )}
        </div>
        {children}
      </div>
    </Card>
  );
}

export function AiSuggestButton() {
  const { t } = useTranslation();
  return (
    <Button disabled icon={<Sparkles aria-hidden="true" />} variant="default">
      {t('icpRadar.settings.aiSuggest')}
    </Button>
  );
}
