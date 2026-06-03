/* Power Web OS — App shell: Sidebar + TopBar */

function Sidebar({ active, onNav }) {
  const nav = [
    { id: 'accounts', label: 'Accounts', icon: 'layout-grid' },
    { id: 'map', label: 'Account Map', icon: 'share' },
    { id: 'plans', label: 'Access Plans', icon: 'route' },
    { id: 'signals', label: 'Signals', icon: 'activity' },
    { id: 'playbook', label: 'Playbook', icon: 'settings-2' },
  ];
  return (
    <aside style={{
      width: 232, flexShrink: 0, background: 'var(--surface)', borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column', height: '100%',
    }}>
      <div style={{ padding: '18px 18px 14px' }}>
        <Wordmark size={26} />
      </div>

      <div style={{ padding: '4px 12px', flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
        <div style={{ font: 'var(--mono-sm)', letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--fg4)', padding: '10px 10px 6px' }}>Workspace</div>
        {nav.map(n => <NavItem key={n.id} {...n} active={active === n.id} onClick={() => onNav(n.id)} />)}

        <div style={{ font: 'var(--mono-sm)', letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--fg4)', padding: '18px 10px 6px' }}>Queue</div>
        <NavItem id="tasks" label="My Tasks" icon="circle-check" badge="5" onClick={() => onNav('plans')} />
        <NavItem id="inbox" label="Signals Inbox" icon="bell" badge="12" onClick={() => onNav('signals')} />
      </div>

      <div style={{ padding: 12, borderTop: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 8px', borderRadius: 'var(--r-md)' }}>
          <Avatar name="Alex Rivera" size={32} />
          <div style={{ minWidth: 0, flex: 1 }}>
            <div style={{ font: '600 13px/1.2 var(--font-sans)', color: 'var(--ink)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>Alex Rivera</div>
            <div style={{ font: 'var(--meta)', color: 'var(--fg3)' }}>Enterprise AE</div>
          </div>
          <Icon name="chevron-down" size={15} color="var(--fg4)" />
        </div>
      </div>
    </aside>
  );
}

function NavItem({ label, icon, active, badge, onClick }) {
  const [hover, setHover] = React.useState(false);
  return (
    <button onClick={onClick}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        display: 'flex', alignItems: 'center', gap: 10, width: '100%', height: 38, padding: '0 10px',
        borderRadius: 'var(--r-md)', border: 'none', cursor: 'pointer', textAlign: 'left',
        background: active ? 'var(--cobalt-50)' : (hover ? 'var(--surface-2)' : 'transparent'),
        color: active ? 'var(--cobalt-700)' : 'var(--fg2)',
        font: `${active ? 600 : 520} 14px/1 var(--font-sans)`,
        transition: 'all var(--dur-fast) var(--ease)', position: 'relative',
      }}>
      {active && <span style={{ position: 'absolute', left: -12, top: 9, bottom: 9, width: 3, background: 'var(--cobalt)', borderRadius: 99 }} />}
      <Icon name={icon} size={18} strokeWidth={active ? 2.1 : 1.9} />
      <span style={{ flex: 1 }}>{label}</span>
      {badge && <span style={{
        font: 'var(--mono-sm)', height: 18, minWidth: 18, padding: '0 5px', borderRadius: 99,
        background: active ? 'var(--cobalt-100)' : 'var(--surface-3)', color: active ? 'var(--cobalt-700)' : 'var(--fg3)',
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      }}>{badge}</span>}
    </button>
  );
}

/* Top bar — account context + search + actions */
function TopBar({ children, search, onSearch }) {
  return (
    <header style={{
      height: 60, flexShrink: 0, borderBottom: '1px solid var(--border)', background: 'rgba(251,251,249,0.82)',
      backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)',
      display: 'flex', alignItems: 'center', gap: 16, padding: '0 22px', position: 'sticky', top: 0, zIndex: 20,
    }}>
      <div style={{ flex: 1, minWidth: 0, display: 'flex', alignItems: 'center', gap: 14 }}>{children}</div>
      <div style={{ width: 260 }}>
        <Field icon="search" placeholder="Search accounts, people…" value={search} onChange={onSearch} size="sm" />
      </div>
      <IconButton name="filter" title="Filters" />
      <div style={{ position: 'relative' }}>
        <IconButton name="bell" title="Notifications" />
        <span style={{ position: 'absolute', top: 6, right: 6, width: 7, height: 7, borderRadius: 99, background: 'var(--cobalt)', boxShadow: '0 0 0 2px var(--paper)' }} />
      </div>
      <Button variant="primary" size="sm" icon="plus">Add account</Button>
    </header>
  );
}

Object.assign(window, { Sidebar, NavItem, TopBar });
