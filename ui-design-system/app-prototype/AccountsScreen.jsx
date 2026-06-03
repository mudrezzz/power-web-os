/* Power Web OS — Accounts portfolio screen */

function AccountsScreen({ search, onSearch, onOpen }) {
  const [view, setView] = React.useState('table');
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <TopBar search={search} onSearch={onSearch}>
        <div>
          <div style={{ font: '650 17px/1.1 var(--font-sans)', letterSpacing: '-0.01em', color: 'var(--ink)' }}>Accounts</div>
          <div style={{ font: 'var(--meta)', color: 'var(--fg3)', marginTop: 2 }}>6 target accounts · 2 need a route</div>
        </div>
      </TopBar>

      <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px 40px' }}>
        {/* filter row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 18 }}>
          <Chip icon="layers" active>All accounts</Chip>
          <Chip>My book</Chip>
          <Chip>Needs route</Chip>
          <Chip>Blocker active</Chip>
          <div style={{ flex: 1 }} />
          <div style={{ display: 'flex', background: 'var(--surface-2)', borderRadius: 'var(--r-md)', padding: 3, gap: 2 }}>
            <IconButton name="list" size={30} iconSize={16} active={view === 'table'} onClick={() => setView('table')} />
            <IconButton name="layout-grid" size={30} iconSize={16} active={view === 'grid'} onClick={() => setView('grid')} />
          </div>
        </div>

        {view === 'table' ? <AccountsTable onOpen={onOpen} /> : <AccountsGrid onOpen={onOpen} />}
      </div>
    </div>
  );
}

function StageTag({ stage }) {
  const map = { Mapping: 'cobalt', Access: 'ally', Qualifying: 'neutral' };
  return <Badge tone={map[stage] || 'neutral'}>{stage}</Badge>;
}

function AccountsTable({ onOpen }) {
  const cols = ['Account', 'Stage', 'Board health', 'Missing', 'Best route', 'Owner'];
  return (
    <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', overflow: 'hidden', boxShadow: 'var(--shadow-sm)' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '2.2fr 1fr 1.4fr 0.8fr 1.6fr 0.9fr', padding: '12px 18px', borderBottom: '1px solid var(--border)', background: 'var(--surface-2)' }}>
        {cols.map(c => <div key={c} style={{ font: 'var(--mono-sm)', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--fg3)' }}>{c}</div>)}
      </div>
      {ACCOUNTS.map((a, i) => (
        <Row key={a.name} a={a} last={i === ACCOUNTS.length - 1} onOpen={onOpen} />
      ))}
    </div>
  );
}

function Row({ a, last, onOpen }) {
  const [hover, setHover] = React.useState(false);
  return (
    <div onClick={onOpen}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        display: 'grid', gridTemplateColumns: '2.2fr 1fr 1.4fr 0.8fr 1.6fr 0.9fr', alignItems: 'center',
        padding: '14px 18px', borderBottom: last ? 'none' : '1px solid var(--border-faint)',
        background: hover ? 'var(--surface-2)' : 'transparent', cursor: 'pointer', transition: 'background var(--dur-fast)',
      }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
        <div style={{ width: 34, height: 34, borderRadius: 'var(--r-sm)', background: 'var(--surface-3)', display: 'flex', alignItems: 'center', justifyContent: 'center', font: '600 13px/1 var(--font-sans)', color: 'var(--fg2)', flexShrink: 0 }}>{a.name.split(' ').map(w => w[0]).join('').slice(0, 2)}</div>
        <div>
          <div style={{ font: '600 14px/1.2 var(--font-sans)', color: 'var(--ink)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{a.name}</div>
          <div style={{ font: 'var(--meta)', color: 'var(--fg3)' }}>{a.industry}</div>
        </div>
      </div>
      <div><StageTag stage={a.stage} /></div>
      <div><HealthBar value={a.health} width={72} /></div>
      <div>{a.missing > 0
        ? <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, font: 'var(--mono-sm)', color: 'var(--unsurfaced)' }}><Icon name="eye-off" size={13} color="var(--unsurfaced)" />{a.missing}</span>
        : <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, font: 'var(--mono-sm)', color: 'var(--ally)' }}><Icon name="check" size={13} color="var(--ally)" />0</span>}</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
        <StanceDot stance={a.stance} size={8} />
        <span style={{ font: '500 13px/1.3 var(--font-sans)', color: 'var(--fg2)' }}>{a.route}</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ font: '500 13px/1.3 var(--font-sans)', color: a.owner === 'You' ? 'var(--ink)' : 'var(--fg3)' }}>{a.owner}</span>
        <Icon name="chevron-right" size={16} color={hover ? 'var(--fg2)' : 'transparent'} />
      </div>
    </div>
  );
}

function AccountsGrid({ onOpen }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
      {ACCOUNTS.map(a => (
        <Card key={a.name} hover onClick={onOpen} pad="16px">
          <div style={{ display: 'flex', alignItems: 'center', gap: 11, marginBottom: 14 }}>
            <div style={{ width: 38, height: 38, borderRadius: 'var(--r-md)', background: 'var(--surface-3)', display: 'flex', alignItems: 'center', justifyContent: 'center', font: '600 14px/1 var(--font-sans)', color: 'var(--fg2)' }}>{a.name.split(' ').map(w => w[0]).join('').slice(0, 2)}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ font: '600 14px/1.2 var(--font-sans)', color: 'var(--ink)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{a.name}</div>
              <div style={{ font: 'var(--meta)', color: 'var(--fg3)' }}>{a.industry}</div>
            </div>
            <StageTag stage={a.stage} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <span style={{ font: 'var(--meta)', color: 'var(--fg3)' }}>Board health</span>
            <HealthBar value={a.health} width={90} />
          </div>
          <Divider style={{ margin: '12px 0' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            <StanceDot stance={a.stance} size={8} />
            <span style={{ font: '500 13px/1.3 var(--font-sans)', color: 'var(--fg2)', flex: 1 }}>{a.route}</span>
            {a.missing > 0 && <Badge tone="unsurfaced">{a.missing} missing</Badge>}
          </div>
        </Card>
      ))}
    </div>
  );
}

Object.assign(window, { AccountsScreen, AccountsTable, AccountsGrid, StageTag });
