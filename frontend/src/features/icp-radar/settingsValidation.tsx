import { useTranslation } from 'react-i18next';
import { Badge, Mono } from '../../components/primitives';
import type { RadarDefinition } from '../../types';

export function ValidationReportView({ report }: { report: RadarDefinition['validation_report'] }) {
  const { t } = useTranslation();
  const actionableIssues = [...report.errors, ...report.warnings];
  const groupedIssues = groupValidationIssues(actionableIssues);
  if (actionableIssues.length === 0) {
    return (
      <div className="validation-summary valid">
        <Badge tone="ally">{t('icpRadar.settings.validConfiguration')}</Badge>
        <span>{t('icpRadar.settings.validConfigurationCopy')}</span>
      </div>
    );
  }
  return (
    <div className="validation-summary">
      {Object.entries(groupedIssues).map(([block, issues]) => (
        <div className="validation-group" key={block}>
          <Badge tone={issues.some((issue) => issue.level === 'error') ? 'blocker' : 'unsurfaced'}>{t(validationBlockKey(block))}</Badge>
          <span>{issues.length}</span>
          <ul>
            {issues.slice(0, 4).map((issue) => (
              <li key={`${issue.code}-${issue.path}`}>{issue.message}</li>
            ))}
          </ul>
        </div>
      ))}
      <details>
        <summary>{t('icpRadar.settings.validationDetails')}</summary>
        <div className="criteria-list">
          {actionableIssues.map((issue) => (
            <div className="criterion-row" key={`${issue.code}-${issue.path}`}>
              <Mono>{issue.code}</Mono>
              <span>
                <strong>{issue.message}</strong>
                <small>{issue.path}</small>
              </span>
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}

function groupValidationIssues(issues: RadarDefinition['validation_report']['errors']): Record<string, typeof issues> {
  return issues.reduce<Record<string, typeof issues>>((result, issue) => {
    const block = issue.path.includes('metadata')
      ? 'overview'
      : issue.path.includes('global_search_policy')
        ? 'globalSearch'
        : issue.path.includes('account_qualification')
          ? 'qualification'
          : issue.path.includes('intent_signals')
            ? 'intentSignals'
            : issue.path.includes('scoring_model')
              ? 'scoring'
              : 'validation';
    result[block] = [...(result[block] ?? []), issue];
    return result;
  }, {});
}

function validationBlockKey(block: string): string {
  return `icpRadar.settings.validationBlocks.${block}`;
}
