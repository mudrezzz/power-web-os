export type Evidence = {
  source: string;
  url: string | null;
  summary: string;
  confidence: number;
};

export type Signal = {
  kind: string;
  summary: string;
  strength: number;
  evidence: Evidence[];
};

export type Role = {
  role: string;
  person_name: string | null;
  state: string;
  influence: number;
  relation: string | null;
};

export type Route = {
  route_type: string;
  title: string;
  score: number;
  reason: string;
  risk: string;
  owner: string;
  evidence_refs: string[];
  expected_state_change: string | null;
  requires_human_review: boolean;
};

export type PowerWebNode = {
  node_id: string;
  label: string;
  node_type: 'account' | 'person' | 'partner' | 'missing';
  role: string;
  state: string;
  stance: 'ally' | 'blocker' | 'unsurfaced' | 'neutral';
  influence: number;
  surfaced: boolean;
  route_member: boolean;
  x: number;
  y: number;
  relation: string | null;
};

export type PowerWebEdge = {
  edge_id: string;
  source: string;
  target: string;
  edge_type: 'account_to_role' | 'partner_to_account' | 'missing_gap';
  highlighted: boolean;
  label: string;
};

export type PowerWebBoard = {
  account_id: string;
  account_name: string;
  summary: {
    visible_count: number;
    missing_count: number;
    total_count: number;
    route_coverage: number;
    primary_route_type: string | null;
    primary_route_score: number | null;
  };
  nodes: PowerWebNode[];
  edges: PowerWebEdge[];
  route_path: string[];
};

export type AccessPlanArtifact = {
  artifact_type: 'access_plan';
  artifact_version: string;
  account: {
    account_id: string;
    name: string;
    icp_fit: number;
    signals: Signal[];
    roles: Role[];
    missing_roles: string[];
  };
  playbook: {
    name: string;
    allowed_routes: string[];
    blocked_channels: string[];
    available_assets: string[];
    required_review_for: string[];
  };
  access_plan: {
    account_id: string;
    account_name: string;
    unresolved_gaps: string[];
    routes: Route[];
  };
  power_web_board: PowerWebBoard;
  workflow_metadata: {
    workflow_name: string;
    runtime: string;
    framework_available: boolean;
    runtime_mode: string;
    node_name: string;
    task_id: string | null;
    correlation_id: string | null;
    planner: string;
  };
};

export type AccountRadarItem = {
  account_id: string;
  account_name: string;
  stage: string;
  radar_score: number;
  signal_count: number;
  missing_role_count: number;
  top_reason: string;
  best_route_type: string | null;
  best_route_title: string | null;
  best_route_score: number;
  owner: string | null;
  review_required: boolean;
  access_plan_path: string;
};

export type AccountRadarArtifact = {
  artifact_type: 'account_radar';
  artifact_version: string;
  accounts: AccountRadarItem[];
  workflow_metadata: {
    workflow_name: string;
    artifact_version: string;
    account_count: number;
    access_workflow: string;
    planner: string;
    task_id: string;
    correlation_id: string;
  };
};
