import type { ButtonHTMLAttributes, ReactNode } from 'react';

type Tone = 'ally' | 'blocker' | 'unsurfaced' | 'cobalt' | 'neutral';

export function Button({
  children,
  icon,
  variant = 'default',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  children?: ReactNode;
  icon?: ReactNode;
  variant?: 'primary' | 'default' | 'ghost' | 'quiet';
}) {
  return (
    <button className={`button button-${variant}`} type="button" {...props}>
      {icon}
      {children && <span>{children}</span>}
    </button>
  );
}

export function IconButton({
  children,
  active = false,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  active?: boolean;
}) {
  return (
    <button className={`icon-button${active ? ' icon-button-active' : ''}`} type="button" {...props}>
      {children}
    </button>
  );
}

export function Badge({
  children,
  tone = 'neutral',
}: {
  children: ReactNode;
  tone?: Tone;
}) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function Card({
  children,
  interactive = false,
  selected = false,
  onClick,
}: {
  children: ReactNode;
  interactive?: boolean;
  selected?: boolean;
  onClick?: () => void;
}) {
  if (interactive) {
    return (
      <button className={`card card-action${selected ? ' card-selected' : ''}`} type="button" onClick={onClick}>
        {children}
      </button>
    );
  }

  return <article className={`card${selected ? ' card-selected' : ''}`}>{children}</article>;
}

export function Eyebrow({ children }: { children: ReactNode }) {
  return <p className="eyebrow">{children}</p>;
}

export function Mono({ children }: { children: ReactNode }) {
  return <span className="mono">{children}</span>;
}

export function Avatar({ label }: { label: string }) {
  return (
    <div className="avatar" aria-hidden="true">
      {initials(label)}
    </div>
  );
}

export function HealthBar({ value, label }: { value: number; label: string }) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className="health" aria-label={label}>
      <span className="health-track">
        <span className="health-fill" style={{ width: `${clamped}%` }} />
      </span>
      <Mono>{clamped}</Mono>
    </div>
  );
}

function initials(value: string) {
  return value
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}
