import { useEffect, useState } from 'react';
import type { ICPRadarCatalogItem } from '../../../types';
import type { CandidateDetailTab, RadarDetailTab } from '../modelTypes';

// Navigation owns purely local screen state so data hooks stay independent from presentation routing.
export function useRadarNavigation() {
  const [selectedRadarId, setSelectedRadarId] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<RadarDetailTab>('shortlist');
  const [expandedCandidateId, setExpandedCandidateId] = useState<string | null>(null);
  const [detailCandidateId, setDetailCandidateId] = useState<string | null>(null);
  const [expandedLiveCandidateId, setExpandedLiveCandidateId] = useState<string | null>(null);
  const [detailLiveCandidateId, setDetailLiveCandidateId] = useState<string | null>(null);
  const [runDiagnosticsOpen, setRunDiagnosticsOpen] = useState(false);
  const [runPreflightOpen, setRunPreflightOpen] = useState(false);
  const [candidateDetailTab, setCandidateDetailTab] = useState<CandidateDetailTab>('overview');

  useEffect(() => {
    if (detailCandidateId || detailLiveCandidateId) {
      document.querySelector('.workspace-body')?.scrollTo({ top: 0 });
      setCandidateDetailTab('overview');
    }
  }, [detailCandidateId, detailLiveCandidateId]);

  function clearCandidateState() {
    setExpandedCandidateId(null);
    setDetailCandidateId(null);
    setExpandedLiveCandidateId(null);
    setDetailLiveCandidateId(null);
    setRunDiagnosticsOpen(false);
    setRunPreflightOpen(false);
  }

  function openRadar(radar: ICPRadarCatalogItem) {
    setSelectedRadarId(radar.radar_id);
    setSelectedTab('shortlist');
    clearCandidateState();
  }

  function backToCatalog() {
    setSelectedRadarId(null);
    clearCandidateState();
  }

  return {
    selectedRadarId,
    setSelectedRadarId,
    selectedTab,
    setSelectedTab,
    expandedCandidateId,
    setExpandedCandidateId,
    detailCandidateId,
    setDetailCandidateId,
    expandedLiveCandidateId,
    setExpandedLiveCandidateId,
    detailLiveCandidateId,
    setDetailLiveCandidateId,
    runDiagnosticsOpen,
    setRunDiagnosticsOpen,
    runPreflightOpen,
    setRunPreflightOpen,
    candidateDetailTab,
    setCandidateDetailTab,
    clearCandidateState,
    openRadar,
    backToCatalog,
  };
}
