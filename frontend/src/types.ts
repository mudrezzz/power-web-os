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
