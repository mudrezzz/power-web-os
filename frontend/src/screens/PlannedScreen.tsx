import { Activity, CheckCircle2, LayoutGrid, Route } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Badge, Card, Eyebrow } from '../components/primitives';
import type { ScreenId } from '../layout/AppShell';

const plannedScreens: Record<
  Exclude<ScreenId, 'accounts' | 'plans' | 'map' | 'playbook'>,
  {
    descriptionKey: string;
    eyebrowKey: string;
    icon: typeof LayoutGrid;
    nextSliceKey: string;
    titleKey: string;
  }
> = {
  signals: {
    descriptionKey: 'planned.signals.description',
    eyebrowKey: 'planned.workspaceEyebrow',
    icon: Activity,
    nextSliceKey: 'planned.signals.nextSlice',
    titleKey: 'planned.signals.title',
  },
  tasks: {
    descriptionKey: 'planned.tasks.description',
    eyebrowKey: 'planned.queueEyebrow',
    icon: CheckCircle2,
    nextSliceKey: 'planned.tasks.nextSlice',
    titleKey: 'planned.tasks.title',
  },
  inbox: {
    descriptionKey: 'planned.inbox.description',
    eyebrowKey: 'planned.queueEyebrow',
    icon: Route,
    nextSliceKey: 'planned.inbox.nextSlice',
    titleKey: 'planned.inbox.title',
  },
};

export function PlannedScreen({ screenId }: { screenId: Exclude<ScreenId, 'accounts' | 'plans' | 'map' | 'playbook'> }) {
  const { t } = useTranslation();
  const screen = plannedScreens[screenId];
  const Icon = screen.icon;

  return (
    <section className="screen planned-screen" aria-label={t(screen.titleKey)}>
      <Card>
        <div className="planned-content">
          <div className="planned-icon">
            <Icon aria-hidden="true" />
          </div>
          <div>
            <Eyebrow>{t(screen.eyebrowKey)}</Eyebrow>
            <h1>{t(screen.titleKey)}</h1>
            <p>{t(screen.descriptionKey)}</p>
            <Badge tone="neutral">{t(screen.nextSliceKey)}</Badge>
          </div>
        </div>
      </Card>
    </section>
  );
}
