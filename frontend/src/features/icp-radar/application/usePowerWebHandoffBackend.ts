import { useCallback, useRef, useState } from 'react';
import type {
  PowerWebHandoffDto,
  PowerWebHandoffPreflightDto,
  RadarApiClient,
  RadarPowerWebPolicyDto,
} from '../../../api/radarApi';
import { salesPlaybookApi } from '../../../api/salesPlaybookApi';
import type { ProductSummary, SalesPlaybookVersion } from '../../../types';
import type { RadarBackendMode, RadarResourceState } from './useRadarBackend';

export type PowerWebHandoffBackendController = {
  powerWebPolicyByRadarId: Record<string, RadarPowerWebPolicyDto | null>;
  powerWebPolicyStateByRadarId: Record<string, RadarResourceState>;
  powerWebProducts: ProductSummary[];
  powerWebProductVersions: Record<string, SalesPlaybookVersion>;
  powerWebPreflightByKey: Record<string, PowerWebHandoffPreflightDto>;
  powerWebHandoffsByKey: Record<string, PowerWebHandoffDto[]>;
  loadPowerWebPolicy: (radarId: string) => Promise<void>;
  savePowerWebPolicy: (radarId: string, productIds: string[]) => Promise<boolean>;
  loadPowerWebCandidateBrief: (
    radarId: string, runId: string, candidateId: string, productIds?: string[], acknowledged?: boolean,
  ) => Promise<void>;
  preparePowerWebHandoff: (args: {
    radarId: string;
    runId: string;
    candidateId: string;
    productIds: string[];
    reviewNeeded: boolean;
    acknowledged: boolean;
    comment?: string;
  }) => Promise<PowerWebHandoffDto | null>;
};

export function powerWebCandidateKey(radarId: string, runId: string, candidateId: string) {
  return `${radarId}:${runId}:${candidateId}`;
}

export function usePowerWebHandoffBackend({
  api,
  mode,
}: {
  api: RadarApiClient;
  mode: RadarBackendMode;
}): PowerWebHandoffBackendController {
  const [powerWebPolicyByRadarId, setPolicyByRadarId] = useState<Record<string, RadarPowerWebPolicyDto | null>>({});
  const [powerWebPolicyStateByRadarId, setPolicyStateByRadarId] = useState<Record<string, RadarResourceState>>({});
  const [powerWebProducts, setProducts] = useState<ProductSummary[]>([]);
  const [powerWebProductVersions, setProductVersions] = useState<Record<string, SalesPlaybookVersion>>({});
  const [powerWebPreflightByKey, setPreflightByKey] = useState<Record<string, PowerWebHandoffPreflightDto>>({});
  const [powerWebHandoffsByKey, setHandoffsByKey] = useState<Record<string, PowerWebHandoffDto[]>>({});
  const candidateBriefGeneration = useRef<Record<string, number>>({});

  const loadPowerWebPolicy = useCallback(async (radarId: string) => {
    if (mode !== 'api') return;
    setPolicyStateByRadarId((current) => ({ ...current, [radarId]: { status: 'loading', error: null } }));
    try {
      const [policy, products] = await Promise.all([api.getPowerWebPolicy(radarId), salesPlaybookApi.listProducts()]);
      setPolicyByRadarId((current) => ({ ...current, [radarId]: policy }));
      const active = products.filter((product) => product.lifecycle === 'active' && product.active_version_id);
      const versions = await Promise.all(active.map(async (product) => {
        const history = await salesPlaybookApi.listVersions(product.product_id);
        return history.find((version) => version.version_id === product.active_version_id) ?? null;
      }));
      setProducts(active);
      setProductVersions(Object.fromEntries(versions.filter(Boolean).map((version) => [version!.product_id, version!])));
      setPolicyStateByRadarId((current) => ({
        ...current,
        [radarId]: { status: policy ? 'loaded' : 'empty', error: null },
      }));
    } catch (error) {
      setPolicyStateByRadarId((current) => ({
        ...current,
        [radarId]: { status: 'failed', error: message(error) },
      }));
    }
  }, [api, mode]);

  const savePowerWebPolicy = useCallback(async (radarId: string, productIds: string[]) => {
    if (mode !== 'api') return false;
    const currentPolicy = powerWebPolicyByRadarId[radarId] ?? null;
    setPolicyStateByRadarId((current) => ({ ...current, [radarId]: { status: 'loading', error: null } }));
    try {
      const policy = await api.updatePowerWebPolicy(radarId, {
        expected_policy_version_id: currentPolicy?.policy_version_id ?? null,
        product_ids: productIds,
        requester: 'frontend',
      });
      setPolicyByRadarId((current) => ({ ...current, [radarId]: policy }));
      setPolicyStateByRadarId((current) => ({ ...current, [radarId]: { status: 'loaded', error: null } }));
      return true;
    } catch (error) {
      setPolicyStateByRadarId((current) => ({
        ...current,
        [radarId]: { status: 'failed', error: message(error) },
      }));
      return false;
    }
  }, [api, mode, powerWebPolicyByRadarId]);

  const loadPowerWebCandidateBrief = useCallback(async (
    radarId: string,
    runId: string,
    candidateId: string,
    productIds?: string[],
    acknowledged = false,
  ) => {
    if (mode !== 'api') return;
    const key = powerWebCandidateKey(radarId, runId, candidateId);
    const generation = (candidateBriefGeneration.current[key] ?? 0) + 1;
    candidateBriefGeneration.current[key] = generation;
    const [preflight, handoffs] = await Promise.all([
      api.getPowerWebHandoffPreflight(radarId, runId, candidateId, productIds, acknowledged),
      api.listPowerWebHandoffs(radarId, runId, candidateId),
    ]);
    if (candidateBriefGeneration.current[key] !== generation) return;
    setPreflightByKey((current) => ({ ...current, [key]: preflight }));
    setHandoffsByKey((current) => ({ ...current, [key]: handoffs }));
  }, [api, mode]);

  const preparePowerWebHandoff = useCallback(async (args: {
    radarId: string;
    runId: string;
    candidateId: string;
    productIds: string[];
    reviewNeeded: boolean;
    acknowledged: boolean;
    comment?: string;
  }) => {
    if (mode !== 'api' || (args.reviewNeeded && !args.acknowledged)) return null;
    const handoff = await api.createPowerWebHandoff(args.radarId, {
      source_candidate_run_id: args.runId,
      candidate_id: args.candidateId,
      product_ids: args.productIds,
      include_latest_signal_context: true,
      review_needed_acknowledgement: args.reviewNeeded ? {
        acknowledged: true,
        reviewer: 'frontend',
        comment: args.comment,
      } : undefined,
      idempotency_key: `frontend:${args.runId}:${args.candidateId}:${args.productIds.join(',')}`,
      requester: 'frontend',
    });
    await loadPowerWebCandidateBrief(
      args.radarId, args.runId, args.candidateId, args.productIds, args.acknowledged,
    );
    return handoff;
  }, [api, loadPowerWebCandidateBrief, mode]);

  return {
    powerWebPolicyByRadarId,
    powerWebPolicyStateByRadarId,
    powerWebProducts,
    powerWebProductVersions,
    powerWebPreflightByKey,
    powerWebHandoffsByKey,
    loadPowerWebPolicy,
    savePowerWebPolicy,
    loadPowerWebCandidateBrief,
    preparePowerWebHandoff,
  };
}

function message(error: unknown) {
  return error instanceof Error ? error.message : 'Power Web API request failed';
}
