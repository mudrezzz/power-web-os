import { useRef } from 'react';
import './workspaceTabs.css';

export type WorkspaceTabItem<T extends string> = {
  id: T;
  label: string;
  testId?: string;
};

export function WorkspaceTabs<T extends string>({
  id,
  items,
  activeId,
  ariaLabel,
  onChange,
  className = '',
}: {
  id: string;
  items: WorkspaceTabItem<T>[];
  activeId: T;
  ariaLabel: string;
  onChange: (id: T) => void;
  className?: string;
}) {
  const refs = useRef<Array<HTMLButtonElement | null>>([]);

  function moveFocus(index: number) {
    const next = (index + items.length) % items.length;
    refs.current[next]?.focus();
    onChange(items[next].id);
  }

  return (
    <div className={`workspace-tabs ${className}`.trim()} role="tablist" aria-label={ariaLabel}>
      {items.map((item, index) => (
        <button
          aria-controls={`${id}-panel-${item.id}`}
          aria-selected={activeId === item.id}
          className="workspace-tab"
          data-testid={item.testId}
          id={`${id}-tab-${item.id}`}
          key={item.id}
          ref={(node) => { refs.current[index] = node; }}
          role="tab"
          tabIndex={activeId === item.id ? 0 : -1}
          type="button"
          onClick={() => onChange(item.id)}
          onKeyDown={(event) => {
            if (event.key === 'ArrowRight') { event.preventDefault(); moveFocus(index + 1); }
            if (event.key === 'ArrowLeft') { event.preventDefault(); moveFocus(index - 1); }
            if (event.key === 'Home') { event.preventDefault(); moveFocus(0); }
            if (event.key === 'End') { event.preventDefault(); moveFocus(items.length - 1); }
          }}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}

export function WorkspaceTabPanel({
  groupId,
  tabId,
  children,
  className = '',
}: {
  groupId: string;
  tabId: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      aria-labelledby={`${groupId}-tab-${tabId}`}
      className={className}
      id={`${groupId}-panel-${tabId}`}
      role="tabpanel"
    >
      {children}
    </div>
  );
}
