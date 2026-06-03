/* Power Web OS — Shared UI primitives */

/* ---------- Button ---------- */
function Button({ children, variant = 'default', size = 'md', icon, iconRight, onClick, style, title, disabled }) {
  const [hover, setHover] = React.useState(false);
  const [press, setPress] = React.useState(false);
  const sizes = {
    sm: { h: 30, px: 11, fs: 13, gap: 6, ic: 15 },
    md: { h: 36, px: 14, fs: 14, gap: 7, ic: 17 },
    lg: { h: 44, px: 18, fs: 15, gap: 8, ic: 18 },
  }[size];
  const variants = {
    primary: {
      bg: hover ? 'var(--cobalt-600)' : 'var(--cobalt)', color: '#fff',
      border: '1px solid transparent', shadow: '0 1px 2px rgba(31,58,166,.25)',
    },
    default: {
      bg: hover ? 'var(--surface-2)' : 'var(--surface)', color: 'var(--ink)',
      border: '1px solid var(--border)', shadow: 'var(--shadow-xs)',
    },
    ghost: {
      bg: hover ? 'var(--surface-2)' : 'transparent', color: 'var(--fg2)',
      border: '1px solid transparent', shadow: 'none',
    },
    quiet: {
      bg: hover ? 'var(--cobalt-50)' : 'transparent', color: 'var(--cobalt-600)',
      border: '1px solid transparent', shadow: 'none',
    },
    danger: {
      bg: hover ? 'var(--blocker)' : 'var(--blocker-tint)', color: hover ? '#fff' : 'var(--blocker)',
      border: '1px solid transparent', shadow: 'none',
    },
  }[variant];
  return (
    <button
      onClick={disabled ? undefined : onClick} title={title} disabled={disabled}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => { setHover(false); setPress(false); }}
      onMouseDown={() => setPress(true)} onMouseUp={() => setPress(false)}
      style={{
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: sizes.gap,
        height: sizes.h, padding: `0 ${sizes.px}px`, font: `560 ${sizes.fs}px/1 var(--font-sans)`,
        letterSpacing: '-0.005em', borderRadius: 'var(--r-md)', cursor: disabled ? 'not-allowed' : 'pointer',
        background: variants.bg, color: variants.color, border: variants.border, boxShadow: variants.shadow,
        transform: press ? 'translateY(0.5px)' : 'none', opacity: disabled ? 0.5 : 1,
        transition: 'background var(--dur-fast) var(--ease), transform var(--dur-fast) var(--ease)',
        whiteSpace: 'nowrap', ...style,
      }}>
      {icon && <Icon name={icon} size={sizes.ic} strokeWidth={2} />}
      {children}
      {iconRight && <Icon name={iconRight} size={sizes.ic} strokeWidth={2} />}
    </button>
  );
}

/* ---------- Icon-only button ---------- */
function IconButton({ name, size = 36, iconSize = 18, active, onClick, title, style }) {
  const [hover, setHover] = React.useState(false);
  return (
    <button onClick={onClick} title={title}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        width: size, height: size, display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        borderRadius: 'var(--r-md)', border: '1px solid', cursor: 'pointer',
        borderColor: active ? 'var(--cobalt-200)' : (hover ? 'var(--border)' : 'transparent'),
        background: active ? 'var(--cobalt-50)' : (hover ? 'var(--surface-2)' : 'transparent'),
        color: active ? 'var(--cobalt-600)' : 'var(--fg2)',
        transition: 'all var(--dur-fast) var(--ease)', ...style,
      }}>
      <Icon name={name} size={iconSize} />
    </button>
  );
}

/* ---------- Chip (pill, optionally selectable) ---------- */
function Chip({ children, icon, active, onClick, tone = 'neutral', style }) {
  const [hover, setHover] = React.useState(false);
  const tones = {
    neutral: { bg: 'var(--surface)', bd: 'var(--border)', fg: 'var(--fg2)' },
    cobalt: { bg: 'var(--cobalt-50)', bd: 'var(--cobalt-200)', fg: 'var(--cobalt-700)' },
  }[tone];
  return (
    <button onClick={onClick}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 6, height: 30, padding: '0 12px',
        borderRadius: 'var(--r-pill)', font: '530 13px/1 var(--font-sans)', cursor: 'pointer',
        background: active ? 'var(--cobalt-50)' : (hover ? 'var(--surface-2)' : tones.bg),
        border: `1px solid ${active ? 'var(--cobalt-200)' : tones.bd}`,
        color: active ? 'var(--cobalt-700)' : tones.fg,
        transition: 'all var(--dur-fast) var(--ease)', whiteSpace: 'nowrap', ...style,
      }}>
      {icon && <Icon name={icon} size={14} />}
      {children}
    </button>
  );
}

/* ---------- Stance system (ally / blocker / unsurfaced / neutral) ---------- */
const STANCE = {
  ally: { label: 'Ally', color: 'var(--ally)', tint: 'var(--ally-tint)', ring: 'var(--ally-200)' },
  blocker: { label: 'Blocker', color: 'var(--blocker)', tint: 'var(--blocker-tint)', ring: 'var(--blocker-200)' },
  unsurfaced: { label: 'Unsurfaced', color: 'var(--unsurfaced)', tint: 'var(--unsurfaced-tint)', ring: 'var(--unsurfaced-200)' },
  neutral: { label: 'Neutral', color: 'var(--fg3)', tint: 'var(--surface-2)', ring: 'var(--border-strong)' },
};

function StanceDot({ stance = 'neutral', size = 9, ring }) {
  const s = STANCE[stance];
  return (
    <span style={{
      width: size, height: size, borderRadius: '50%', background: s.color, flexShrink: 0,
      display: 'inline-block', boxShadow: ring ? `0 0 0 3px ${s.tint}` : 'none',
    }} />
  );
}

function Badge({ children, tone = 'neutral', icon, solid, style }) {
  const map = {
    ally: { fg: 'var(--ally)', bg: 'var(--ally-tint)' },
    blocker: { fg: 'var(--blocker)', bg: 'var(--blocker-tint)' },
    unsurfaced: { fg: 'var(--unsurfaced)', bg: 'var(--unsurfaced-tint)' },
    cobalt: { fg: 'var(--cobalt-700)', bg: 'var(--cobalt-50)' },
    neutral: { fg: 'var(--fg2)', bg: 'var(--surface-2)' },
  }[tone];
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5, height: 22, padding: '0 9px',
      borderRadius: 'var(--r-pill)', font: '600 11.5px/1 var(--font-sans)', letterSpacing: '0.005em',
      color: solid ? '#fff' : map.fg, background: solid ? map.fg : map.bg, whiteSpace: 'nowrap', ...style,
    }}>
      {icon && <Icon name={icon} size={12} strokeWidth={2.2} />}
      {children}
    </span>
  );
}

/* ---------- Avatar (monogram) ---------- */
function Avatar({ name, size = 34, stance, src, style }) {
  const initials = (name || '?').split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
  const palette = ['#5A6B8C', '#6B7A5A', '#8C6B5A', '#7A5A8C', '#5A8C82', '#8C7A5A'];
  const idx = (name || '').split('').reduce((a, c) => a + c.charCodeAt(0), 0) % palette.length;
  const s = stance ? STANCE[stance] : null;
  return (
    <div style={{ position: 'relative', width: size, height: size, flexShrink: 0, ...style }}>
      <div style={{
        width: size, height: size, borderRadius: '50%', overflow: 'hidden',
        background: src ? '#eee' : palette[idx], color: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        font: `600 ${Math.round(size * 0.38)}px/1 var(--font-sans)`, letterSpacing: '0.01em',
        boxShadow: s ? `0 0 0 2px var(--surface), 0 0 0 3.5px ${s.color}` : 'inset 0 0 0 1px rgba(0,0,0,.06)',
      }}>
        {src ? <img src={src} alt={name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : initials}
      </div>
    </div>
  );
}

/* ---------- Card ---------- */
function Card({ children, pad = 'var(--s-5)', hover, onClick, style }) {
  const [h, setH] = React.useState(false);
  return (
    <div onClick={onClick}
      onMouseEnter={() => hover && setH(true)} onMouseLeave={() => setH(false)}
      style={{
        background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)',
        boxShadow: h ? 'var(--shadow-md)' : 'var(--shadow-sm)', padding: pad,
        cursor: onClick ? 'pointer' : 'default', transition: 'box-shadow var(--dur) var(--ease), border-color var(--dur) var(--ease)',
        borderColor: h ? 'var(--border-strong)' : 'var(--border)', ...style,
      }}>
      {children}
    </div>
  );
}

/* ---------- Input field ---------- */
function Field({ value, onChange, placeholder, icon, size = 'md', style }) {
  const [focus, setFocus] = React.useState(false);
  const h = size === 'sm' ? 32 : 38;
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 8, height: h, padding: '0 12px',
      background: 'var(--surface)', borderRadius: 'var(--r-md)',
      border: `1px solid ${focus ? 'var(--cobalt)' : 'var(--border)'}`,
      boxShadow: focus ? 'var(--shadow-focus)' : 'var(--shadow-xs)',
      transition: 'all var(--dur-fast) var(--ease)', ...style,
    }}>
      {icon && <Icon name={icon} size={16} color="var(--fg3)" />}
      <input value={value} placeholder={placeholder}
        onChange={e => onChange && onChange(e.target.value)}
        onFocus={() => setFocus(true)} onBlur={() => setFocus(false)}
        style={{
          border: 'none', outline: 'none', background: 'transparent', flex: 1, minWidth: 0,
          font: '400 14px/1 var(--font-sans)', color: 'var(--ink)',
        }} />
    </div>
  );
}

/* ---------- Misc bits ---------- */
function Eyebrow({ children, style }) {
  return <div style={{ font: 'var(--mono-sm)', letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--fg3)', ...style }}>{children}</div>;
}
function Divider({ style }) { return <div style={{ height: 1, background: 'var(--border)', ...style }} />; }
function Mono({ children, style }) { return <span style={{ font: 'var(--mono)', ...style }}>{children}</span>; }

/* ---------- Health meter ---------- */
function HealthBar({ value = 0, width = 64 }) {
  const tone = value >= 70 ? 'var(--ally)' : value >= 40 ? 'var(--unsurfaced)' : 'var(--blocker)';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ width, height: 6, borderRadius: 99, background: 'var(--surface-3)', overflow: 'hidden' }}>
        <div style={{ width: `${value}%`, height: '100%', background: tone, borderRadius: 99 }} />
      </div>
      <span style={{ font: 'var(--mono-sm)', color: 'var(--fg2)' }}>{value}</span>
    </div>
  );
}

Object.assign(window, {
  Button, IconButton, Chip, STANCE, StanceDot, Badge, Avatar, Card, Field,
  Eyebrow, Divider, Mono, HealthBar,
});
