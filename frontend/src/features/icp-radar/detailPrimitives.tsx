import { useTranslation } from 'react-i18next';
import { Mono } from '../../components/primitives';
import { WorkspaceTabs } from '../../components/WorkspaceTabs';
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
    : ['overview', 'qualification', 'signals', 'sources', 'journal', 'trace'];
  return <WorkspaceTabs
    id="candidate-detail"
    activeId={activeTab}
    ariaLabel={t('icpRadar.canonicalDetail.tabsAria')}
    className="icp-candidate-detail-tabs"
    items={tabs.map((tab) => ({ id: tab, label: t(`icpRadar.canonicalDetail.tabs.${tab}`) }))}
    onChange={onTabChange}
  />;
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

