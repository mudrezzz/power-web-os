import { AlertTriangle, CheckCircle2, EyeOff, Route, ShieldCheck } from 'lucide-react';
import type { ReactNode } from 'react';
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, Card, Eyebrow, Mono } from '../components/primitives';
import { useDemoLocalization } from '../demoLocalization';
import type { AccessPlanArtifact, PowerWebEdge, PowerWebNode } from '../types';

export function AccountMapScreen({
  artifact,
  error,
}: {
  artifact: AccessPlanArtifact | null;
  error: string | null;
}) {
  const { t } = useTranslation();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  if (error || !artifact?.power_web_board) {
    return (
      <section className="screen status-screen">
        <Card>
          <Eyebrow>{t('board.eyebrow')}</Eyebrow>
          <h1>{t('board.noBoardTitle')}</h1>
          <p>{t('board.noBoardCopy')}</p>
          <code>python demo/run_demo.py generate-account-radar</code>
        </Card>
      </section>
    );
  }

  const board = artifact.power_web_board;
  const selectedNode = selectedNodeId ? board.nodes.find((node) => node.node_id === selectedNodeId) ?? null : null;

  return (
    <section className="account-map-screen" aria-label={t('board.aria')}>
      <div className="map-board">
        <div className="map-board-header">
          <div>
            <Eyebrow>{t('board.eyebrow')}</Eyebrow>
            <h1>{t('board.title')}</h1>
            <p>
              {t('board.summary', {
                accountName: board.account_name,
                missing: board.summary.missing_count,
                visible: board.summary.visible_count,
              })}
            </p>
          </div>
          {board.summary.missing_count > 0 && (
            <div className="missing-banner">
              <AlertTriangle aria-hidden="true" />
              <span>{t('board.missingBanner', { count: board.summary.missing_count })}</span>
              <Badge tone="unsurfaced">{t('board.findThem')}</Badge>
            </div>
          )}
        </div>

        <div className="map-canvas">
          <BoardScene nodes={board.nodes} edges={board.edges} selectedNodeId={selectedNodeId} onSelect={setSelectedNodeId} />
        </div>
      </div>

      <aside className="map-inspector">
        {selectedNode ? (
          <NodeInspector node={selectedNode} />
        ) : (
          <BoardInspector artifact={artifact} />
        )}
      </aside>
    </section>
  );
}

function BoardScene({
  edges,
  nodes,
  onSelect,
  selectedNodeId,
}: {
  edges: PowerWebEdge[];
  nodes: PowerWebNode[];
  onSelect: (nodeId: string) => void;
  selectedNodeId: string | null;
}) {
  const { t } = useTranslation();
  const demo = useDemoLocalization();
  const nodeById = useMemo(() => new Map(nodes.map((node) => [node.node_id, node])), [nodes]);

  return (
    <div className="board-scene">
      <svg className="board-edges" role="presentation" viewBox="0 0 100 100" preserveAspectRatio="none">
        {edges.map((edge) => {
          const source = nodeById.get(edge.source);
          const target = nodeById.get(edge.target);
          if (!source || !target) {
            return null;
          }
          return (
            <line
              className={`board-edge${edge.highlighted ? ' board-edge-highlighted' : ''}`}
              key={edge.edge_id}
              x1={source.x * 100}
              x2={target.x * 100}
              y1={source.y * 100}
              y2={target.y * 100}
            />
          );
        })}
      </svg>

      {nodes.map((node) => (
        <button
          className={`board-node board-node-${node.node_type} stance-${node.stance}${
            node.route_member ? ' board-node-route' : ''
          }${selectedNodeId === node.node_id ? ' board-node-selected' : ''}`}
          key={node.node_id}
          style={{ left: `${node.x * 100}%`, top: `${node.y * 100}%` }}
          type="button"
          onClick={() => onSelect(node.node_id)}
        >
            <span className="board-node-avatar">{initials(node.label)}</span>
            <span className="board-node-copy">
              <strong>{displayNodeLabel(node, demo)}</strong>
              <small>{displayNodeRole(node, demo, t)}</small>
            </span>
          </button>
        ))}
    </div>
  );
}

function BoardInspector({ artifact }: { artifact: AccessPlanArtifact }) {
  const { t } = useTranslation();
  const demo = useDemoLocalization();
  const board = artifact.power_web_board;
  const primaryRoute = artifact.access_plan.routes[0];
  const routeNodes = board.route_path
    .map((nodeId) => board.nodes.find((node) => node.node_id === nodeId))
    .filter((node): node is PowerWebNode => Boolean(node));

  return (
    <div className="map-inspector-content">
      <section>
        <Eyebrow>{t('board.coverage')}</Eyebrow>
        <div className="coverage-number">
          <span>{board.summary.visible_count}</span>
          <span>/{board.summary.total_count}</span>
        </div>
        <p className="muted">{t('board.figuresSurfaced')}</p>
        <div className="board-stats">
          <StatBadge icon={<CheckCircle2 aria-hidden="true" />} label={t('board.allies')} value={countStance(board.nodes, 'ally')} />
          <StatBadge icon={<ShieldCheck aria-hidden="true" />} label={t('board.blockers')} value={countStance(board.nodes, 'blocker')} />
          <StatBadge icon={<EyeOff aria-hidden="true" />} label={t('board.missing')} value={board.summary.missing_count} />
        </div>
      </section>

      {primaryRoute && (
        <section className="recommended-route-panel">
          <div className="panel-title-row">
            <Eyebrow>{t('board.recommendedRoute')}</Eyebrow>
            <Mono>{t('board.routeScore', { score: primaryRoute.score })}</Mono>
          </div>
          <div className="map-route-title">
            <Route aria-hidden="true" />
            <strong>{demo.routeTitle(primaryRoute.route_type, primaryRoute.title)}</strong>
          </div>
          <div className="map-route-path">
            {routeNodes.map((node, index) => (
              <span key={node.node_id}>
                {displayNodeLabel(node, demo)}
                {index < routeNodes.length - 1 && <Route aria-hidden="true" />}
              </span>
            ))}
          </div>
          <p>{demo.text(primaryRoute.reason)}</p>
          <Badge tone="cobalt">{t('board.routeCoverage', { count: board.summary.route_coverage })}</Badge>
        </section>
      )}
    </div>
  );
}

function NodeInspector({ node }: { node: PowerWebNode }) {
  const { t } = useTranslation();
  const demo = useDemoLocalization();

  return (
    <div className="map-inspector-content">
      <section>
        <Eyebrow>{t('board.selectedFigure')}</Eyebrow>
        <div className="node-detail-heading">
          <span className={`board-node-avatar stance-${node.stance}`}>{initials(node.label)}</span>
          <div>
            <h2>{displayNodeLabel(node, demo)}</h2>
            <p>{node.node_type === 'account' ? t('board.accountNode') : demo.role(node.role)}</p>
          </div>
        </div>
        <div className="metadata-row">
          <Badge tone={badgeTone(node.stance)}>{t(`board.stance.${node.stance}`)}</Badge>
          <Badge tone="neutral">{demo.state(node.state)}</Badge>
          {node.route_member && <Badge tone="cobalt">{t('board.routePath')}</Badge>}
        </div>
      </section>
      <section>
        <Eyebrow>{t('board.evidence')}</Eyebrow>
        <p className="muted">
          {node.surfaced
            ? t('board.relation.account_to_role')
            : t('board.relation.missing_gap')}
        </p>
        <Mono>{Math.round(node.influence * 100)}</Mono>
      </section>
    </div>
  );
}

function StatBadge({ icon, label, value }: { icon: ReactNode; label: string; value: number }) {
  return (
    <div className="board-stat">
      {icon}
      <Mono>{value}</Mono>
      <span>{label}</span>
    </div>
  );
}

function countStance(nodes: PowerWebNode[], stance: PowerWebNode['stance']) {
  return nodes.filter((node) => node.stance === stance).length;
}

function displayNodeLabel(node: PowerWebNode, demo: ReturnType<typeof useDemoLocalization>) {
  if (node.node_type === 'missing') {
    return demo.role(node.role);
  }
  if (node.node_type === 'account') {
    return node.label;
  }
  return node.label;
}

function displayNodeRole(
  node: PowerWebNode,
  demo: ReturnType<typeof useDemoLocalization>,
  t: ReturnType<typeof useTranslation>['t'],
) {
  return node.node_type === 'account' ? t('board.accountNode') : demo.role(node.role);
}

function badgeTone(stance: PowerWebNode['stance']) {
  return stance === 'ally' || stance === 'blocker' || stance === 'unsurfaced' ? stance : 'neutral';
}

function initials(value: string) {
  return value
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}
