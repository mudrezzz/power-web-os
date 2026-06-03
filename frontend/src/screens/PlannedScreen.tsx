import { Activity, CheckCircle2, LayoutGrid, Route, Settings2, Share2 } from 'lucide-react';
import { Badge, Card, Eyebrow } from '../components/primitives';
import type { ScreenId } from '../layout/AppShell';

const plannedScreens: Record<
  Exclude<ScreenId, 'plans'>,
  {
    title: string;
    eyebrow: string;
    description: string;
    nextSlice: string;
    icon: typeof LayoutGrid;
  }
> = {
  accounts: {
    title: 'Accounts portfolio',
    eyebrow: 'PLANNED WORKSPACE',
    description: 'The portfolio view will rank target accounts and drill into the same Access Planning loop.',
    nextSlice: 'Slice 0.4',
    icon: LayoutGrid,
  },
  map: {
    title: 'Account Map',
    eyebrow: 'PLANNED WORKSPACE',
    description: 'The Power Web map will show visible and missing buying-committee figures around the account.',
    nextSlice: 'Slice 0.5',
    icon: Share2,
  },
  signals: {
    title: 'Signals',
    eyebrow: 'PLANNED WORKSPACE',
    description: 'The signals feed will expose source evidence, recency, confidence, and governance warnings.',
    nextSlice: 'Slice 0.11',
    icon: Activity,
  },
  playbook: {
    title: 'Playbook',
    eyebrow: 'PLANNED WORKSPACE',
    description: 'The playbook workspace will show allowed routes, blocked channels, assets, and review rules.',
    nextSlice: 'Slice 0.6',
    icon: Settings2,
  },
  tasks: {
    title: 'My Tasks',
    eyebrow: 'PLANNED QUEUE',
    description: 'Approved routes will become task candidates after the human-review loop is implemented.',
    nextSlice: 'Slice 0.7',
    icon: CheckCircle2,
  },
  inbox: {
    title: 'Signals Inbox',
    eyebrow: 'PLANNED QUEUE',
    description: 'New signals will be triaged here once the radar and source-governance loops exist.',
    nextSlice: 'Slice 0.10',
    icon: Route,
  },
};

export function PlannedScreen({ screenId }: { screenId: Exclude<ScreenId, 'plans'> }) {
  const screen = plannedScreens[screenId];
  const Icon = screen.icon;

  return (
    <section className="screen planned-screen" aria-label={screen.title}>
      <Card>
        <div className="planned-content">
          <div className="planned-icon">
            <Icon aria-hidden="true" />
          </div>
          <div>
            <Eyebrow>{screen.eyebrow}</Eyebrow>
            <h1>{screen.title}</h1>
            <p>{screen.description}</p>
            <Badge tone="neutral">{screen.nextSlice}</Badge>
          </div>
        </div>
      </Card>
    </section>
  );
}
