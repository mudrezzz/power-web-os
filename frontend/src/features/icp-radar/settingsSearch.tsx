import { Plus, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Mono } from '../../components/primitives';
import type { EditableRadarDefinitionDraft, RadarDefinition, SourceDefinition } from '../../types';
import {
  newSourceDefinition,
  replaceAt,
  sourceTypeKey,
  sourceUsageObligations,
  sourceUsageObligationKey,
  sourceUsageObligationTone,
  sourceUsageObligationValue,
  trustPolicyKey,
  trustPolicyTone,
  trustPolicyValue,
} from './model';
import { ArrayTextAreaField, ListSection, SelectField, TextField, ToggleField } from './settingsFields';

export function GlobalSearchSummary({ definition }: { definition: RadarDefinition }) {
  const { t } = useTranslation();
  return (
    <>
      <div className="icp-search-policy-grid">
        <ListSection bounded title={t('icpRadar.settings.keywords')} items={definition.global_search_policy.keywords} />
        <ListSection bounded title={t('icpRadar.settings.exclusions')} items={definition.global_search_policy.exclusions} />
      </div>
      <SourceTable sources={definition.global_search_policy.sources} />
      <div className="policy-switch-strip policy-switch-strip-end">
        <ToggleField
          checked={definition.global_search_policy.allow_system_sources}
          disabled
          label={t('icpRadar.settings.systemSources')}
          onChange={() => undefined}
        />
      </div>
    </>
  );
}

export function GlobalSearchEditor({
  draft,
  onDraftChange,
}: {
  draft: EditableRadarDefinitionDraft;
  onDraftChange: (draft: EditableRadarDefinitionDraft) => void;
}) {
  const { t } = useTranslation();
  const policy = draft.global_search_policy;
  function updatePolicy(patch: Partial<EditableRadarDefinitionDraft['global_search_policy']>) {
    onDraftChange({ ...draft, global_search_policy: { ...policy, ...patch } });
  }
  return (
    <div className="criteria-editor-list">
      <ArrayTextAreaField label={t('icpRadar.settings.keywords')} value={policy.keywords} onChange={(keywords) => updatePolicy({ keywords })} />
      <ArrayTextAreaField label={t('icpRadar.settings.exclusions')} value={policy.exclusions} onChange={(exclusions) => updatePolicy({ exclusions })} />
      <SourceListEditor
        sources={policy.sources}
        onChange={(sources) => updatePolicy({ sources })}
      />
      <div className="policy-switch-strip policy-switch-strip-end">
        <ToggleField
          checked={policy.allow_system_sources}
          label={t('icpRadar.settings.systemSources')}
          onChange={(allow_system_sources) => updatePolicy({ allow_system_sources })}
        />
      </div>
    </div>
  );
}

export function SourceTable({ sources }: { sources: SourceDefinition[] }) {
  const { t } = useTranslation();
  return (
    <div className="source-table-wrap">
      <table className="source-table source-table--settings">
        <thead>
          <tr>
            <th>{t('icpRadar.settings.sourceNumber')}</th>
            <th>{t('icpRadar.settings.sourceLabel')}</th>
            <th>{t('icpRadar.settings.sourceType')}</th>
            <th>{t('icpRadar.settings.trustLevel')}</th>
            <th>{t('icpRadar.settings.usageObligation')}</th>
            <th>{t('icpRadar.settings.sourceReference')}</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((source, index) => (
            <tr key={source.source_id}>
              <td><Mono>{index + 1}</Mono></td>
              <td><strong>{source.label}</strong></td>
              <td>{t(sourceTypeKey(source.source_type))}</td>
              <td><Badge tone={trustPolicyTone(source.trust_level)}>{t(trustPolicyKey(source.trust_level))}</Badge></td>
              <td><Badge tone={sourceUsageObligationTone(source.usage_obligation)}>{t(sourceUsageObligationKey(source.usage_obligation))}</Badge></td>
              <td><span className="source-reference-cell">{source.reference}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function SourceListEditor({
  onChange,
  sources,
}: {
  onChange: (sources: SourceDefinition[]) => void;
  sources: SourceDefinition[];
}) {
  const { t } = useTranslation();
  return (
    <div className="source-list-editor">
      {sources.map((source, index) => (
        <div className="source-editor-row" key={`${source.source_id || 'source'}-${index}`}>
          <SelectField label={t('icpRadar.settings.sourceType')} options={['url', 'search_engine', 'api', 'mcp', 'manual_dataset']} value={source.source_type} onChange={(source_type) => onChange(replaceAt(sources, index, { ...source, source_type }))} optionLabel={(option) => t(sourceTypeKey(option))} />
          <TextField label={t('icpRadar.settings.sourceLabel')} value={source.label} onChange={(label) => onChange(replaceAt(sources, index, { ...source, label }))} />
          <TextField label={t('icpRadar.settings.sourceReference')} value={source.reference} onChange={(reference) => onChange(replaceAt(sources, index, { ...source, reference }))} />
          <SelectField label={t('icpRadar.settings.trustLevel')} options={['trusted', 'cross_check', 'hitl_required']} value={trustPolicyValue(source.trust_level)} onChange={(trust_level) => onChange(replaceAt(sources, index, { ...source, trust_level }))} optionLabel={(option) => t(trustPolicyKey(option))} />
          <SelectField label={t('icpRadar.settings.usageObligation')} options={[...sourceUsageObligations]} value={sourceUsageObligationValue(source.usage_obligation)} onChange={(usage_obligation) => onChange(replaceAt(sources, index, { ...source, usage_obligation }))} optionLabel={(option) => t(sourceUsageObligationKey(option))} />
          <Button icon={<X aria-hidden="true" />} variant="default" onClick={() => onChange(sources.filter((_, currentIndex) => currentIndex !== index))}>
            {t('icpRadar.settings.remove')}
          </Button>
        </div>
      ))}
      <Button icon={<Plus aria-hidden="true" />} variant="default" onClick={() => onChange([...sources, newSourceDefinition()])}>
        {t('icpRadar.settings.addSource')}
      </Button>
    </div>
  );
}
