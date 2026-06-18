import { useTranslation } from 'react-i18next';
import { Mono } from '../../components/primitives';
import type { CandidateDetailTab } from './model';
import { formatDelta } from './model';

// These tiny primitives keep fixture and live candidate detail tabs visually identical.

export function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}


export function CandidateDetailTabs({
  activeTab,
  onTabChange,
  showTrace = false,
}: {
  activeTab: CandidateDetailTab;
  onTabChange: (tab: CandidateDetailTab) => void;
  showTrace?: boolean;
}) {
  const { t } = useTranslation();
  const tabs: CandidateDetailTab[] = showTrace
    ? ['overview', 'qualification', 'signals', 'sources', 'journal', 'trace']
    : ['overview', 'qualification', 'signals', 'sources', 'journal'];
  return (
    <div className="icp-candidate-detail-tabs" aria-label={t('icpRadar.canonicalDetail.tabsAria')}>
      {tabs.map((tab) => (
        <button
          aria-pressed={activeTab === tab}
          className={`criteria-chip${activeTab === tab ? ' criteria-chip-active' : ''}`}
          key={tab}
          type="button"
          onClick={() => onTabChange(tab)}
        >
          {t(`icpRadar.canonicalDetail.tabs.${tab}`)}
        </button>
      ))}
    </div>
  );
}

export function ScoreBox({ delta = 0, label, value }: { delta?: number; label: string; value: number | string }) {
  return (
    <div className="icp-score-box">
      <Mono>{label}</Mono>
      <strong>{value}</strong>
      {delta !== 0 && <small className="score-delta">{formatDelta(delta)}</small>}
    </div>
  );
}

