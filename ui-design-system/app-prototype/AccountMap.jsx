/* Power Web OS — Account Map: the buying-committee graph ("the board") */

const ROUTE_PATHS = {
  p1: ['bell', 'anand', 'okafor'],
  p2: ['anand'],
  p3: ['vogt', 'reuter'],
};

function AccountMap({ selectedId, onSelect, activePlan = 'p1', filters }) {
  const ref = React.useRef(null);
  const [dim, setDim] = React.useState({ w: 760, h: 540 });

  React.useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setDim({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el);
    setDim({ w: el.clientWidth, h: el.clientHeight });
    return () => ro.disconnect();
  }, []);

  const pad = 58;
  const px = p => ({ x: pad + p.x * (dim.w - pad * 2), y: pad + p.y * (dim.h - pad * 2) });
  const byId = id => PEOPLE.find(p => p.id === id);
  const routeIds = ROUTE_PATHS[activePlan] || [];
  const routeSet = new Set(routeIds);
  const routePairs = routeIds.slice(0, -1).map((a, i) => [a, routeIds[i + 1]]);
  const onRoute = (a, b) => routePairs.some(([x, y]) => (x === a && y === b) || (x === b && y === a));

  return (
    <div ref={ref} style={{ position: 'absolute', inset: 0, overflow: 'hidden' }}>
      {/* dotted research-grid background */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: 'radial-gradient(circle, #E3E3DD 1px, transparent 1px)',
        backgroundSize: '22px 22px', opacity: 0.6,
      }} />

      {/* edges */}
      <svg width={dim.w} height={dim.h} style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
        {EDGES.map((e, i) => {
          const a = px(byId(e.a)), b = px(byId(e.b));
          const lit = onRoute(e.a, e.b);
          return (
            <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y}
              stroke={lit ? 'var(--cobalt)' : 'var(--border-strong)'}
              strokeWidth={lit ? 2.4 : 1.4}
              strokeDasharray={e.kind === 'works' ? '4 5' : 'none'}
              strokeLinecap="round"
              opacity={lit ? 1 : 0.85} />
          );
        })}
        {/* route flow dots */}
        {routePairs.map(([a, b], i) => {
          const p1 = px(byId(a)), p2 = px(byId(b));
          return <circle key={i} r="3.5" fill="var(--cobalt)">
            <animateMotion dur="2.4s" repeatCount="indefinite" path={`M${p1.x},${p1.y} L${p2.x},${p2.y}`} />
          </circle>;
        })}
      </svg>

      {/* nodes */}
      {PEOPLE.map(p => {
        const pos = px(p);
        const sel = selectedId === p.id;
        const lit = routeSet.has(p.id);
        return <MapNode key={p.id} person={p} pos={pos} selected={sel} lit={lit} onClick={() => onSelect(p.id)} />;
      })}

      {/* legend */}
      <div style={{
        position: 'absolute', left: 16, bottom: 16, background: 'var(--surface)', border: '1px solid var(--border)',
        borderRadius: 'var(--r-md)', boxShadow: 'var(--shadow-sm)', padding: '10px 12px', display: 'flex', gap: 16,
      }}>
        {[['ally', 'Ally'], ['blocker', 'Blocker'], ['unsurfaced', 'Unsurfaced'], ['neutral', 'Neutral']].map(([s, l]) => (
          <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 6, font: 'var(--meta)', color: 'var(--fg2)' }}>
            <StanceDot stance={s} size={8} /> {l}
          </div>
        ))}
        <div style={{ width: 1, background: 'var(--border)' }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, font: 'var(--meta)', color: 'var(--cobalt-700)' }}>
          <span style={{ width: 14, height: 2.4, background: 'var(--cobalt)', borderRadius: 9 }} /> Access route
        </div>
      </div>

      {/* map toolbar */}
      <div style={{ position: 'absolute', left: 16, top: 16, display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--r-md)', boxShadow: 'var(--shadow-sm)', display: 'flex', flexDirection: 'column' }}>
          <IconButton name="plus" iconSize={16} title="Zoom in" />
          <IconButton name="minus" iconSize={16} title="Zoom out" />
        </div>
        <IconButton name="compass" iconSize={17} title="Fit to view" style={{ background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--shadow-sm)' }} />
      </div>
    </div>
  );
}

function MapNode({ person, pos, selected, lit, onClick }) {
  const [hover, setHover] = React.useState(false);
  const ghost = !person.surfaced;
  const s = STANCE[person.stance];
  return (
    <div onClick={onClick}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        position: 'absolute', left: pos.x, top: pos.y, transform: 'translate(-50%,-50%)',
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, cursor: 'pointer',
        zIndex: selected ? 12 : (hover ? 11 : 5), width: 104,
      }}>
      <div style={{ position: 'relative' }}>
        {/* selection / route halo */}
        {(selected || lit) && <span style={{
          position: 'absolute', inset: -7, borderRadius: '50%',
          border: `2px solid ${selected ? 'var(--cobalt)' : s.color}`,
          boxShadow: lit ? `0 0 0 5px ${s.tint}` : 'none',
        }} />}
        <div style={{
          width: 52, height: 52, borderRadius: '50%',
          background: ghost ? 'repeating-linear-gradient(135deg, var(--surface-2), var(--surface-2) 5px, var(--surface-3) 5px, var(--surface-3) 10px)' : 'var(--surface)',
          border: `2.5px solid ${s.color}`,
          boxShadow: hover ? 'var(--shadow-md)' : 'var(--shadow-sm)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          opacity: ghost ? 0.92 : 1, transition: 'box-shadow var(--dur) var(--ease)',
        }}>
          {ghost
            ? <Icon name="user" size={22} color={s.color} strokeWidth={2} />
            : <span style={{ font: '600 16px/1 var(--font-sans)', color: 'var(--ink)' }}>
                {person.name.split(' ').map(w => w[0]).join('')}
              </span>}
        </div>
        {/* role tag */}
        <span style={{
          position: 'absolute', bottom: -5, left: '50%', transform: 'translateX(-50%)',
          font: '600 9.5px/1 var(--font-mono)', letterSpacing: '0.03em', textTransform: 'uppercase',
          color: s.color, background: 'var(--surface)', border: `1px solid ${s.ring}`,
          padding: '2px 6px', borderRadius: 99, whiteSpace: 'nowrap',
        }}>{person.role}</span>
      </div>
      <div style={{ textAlign: 'center', marginTop: 8 }}>
        <div style={{ font: '600 12.5px/1.15 var(--font-sans)', color: 'var(--ink)' }}>{person.name}</div>
        <div style={{ font: '500 11px/1.2 var(--font-sans)', color: 'var(--fg3)' }}>{person.title}</div>
      </div>
    </div>
  );
}

Object.assign(window, { AccountMap, ROUTE_PATHS, MapNode });
