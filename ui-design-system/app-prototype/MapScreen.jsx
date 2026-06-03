/* Power Web OS — Map screen: account context + board + inspector */

function AccountContext() {
  const a = ACCOUNT;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
      <div style={{ width: 38, height: 38, borderRadius: 'var(--r-md)', background: 'var(--ink)', color: 'var(--paper)', display: 'flex', alignItems: 'center', justifyContent: 'center', font: '700 15px/1 var(--font-sans)', flexShrink: 0 }}>NR</div>
      <div style={{ minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ font: '650 17px/1.1 var(--font-sans)', letterSpacing: '-0.01em', color: 'var(--ink)' }}>{a.name}</span>
          <Icon name="chevron-down" size={15} color="var(--fg4)" />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 2, font: 'var(--meta)', color: 'var(--fg3)' }}>
          <span>{a.industry}</span><span style={{ color: 'var(--fg4)' }}>·</span><span>{a.region}</span>
        </div>
      </div>
      <div style={{ width: 1, height: 30, background: 'var(--border)', margin: '0 4px' }} />
      <Badge tone="cobalt" icon="target">{a.stage}</Badge>
      <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
        <span style={{ font: 'var(--meta)', color: 'var(--fg3)' }}>Health</span>
        <HealthBar value={a.health} width={56} />
      </div>
    </div>
  );
}

function MapScreen({ search, onSearch }) {
  const [sel, setSel] = React.useState(null);
  const [plan, setPlan] = React.useState('p1');
  const person = sel && PEOPLE.find(p => p.id === sel);
  const surfaced = PEOPLE.filter(p => p.surfaced).length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <TopBar search={search} onSearch={onSearch}><AccountContext /></TopBar>

      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        {/* board */}
        <div style={{ flex: 1, position: 'relative', minWidth: 0 }}>
          {/* missing-figures banner */}
          <div style={{
            position: 'absolute', top: 16, left: '50%', transform: 'translateX(-50%)', zIndex: 15,
            display: 'flex', alignItems: 'center', gap: 10, background: 'var(--surface)', border: '1px solid var(--unsurfaced-200)',
            borderRadius: 'var(--r-pill)', boxShadow: 'var(--shadow-md)', padding: '7px 8px 7px 14px',
          }}>
            <Icon name="alert-triangle" size={15} color="var(--unsurfaced)" />
            <span style={{ font: '550 13px/1 var(--font-sans)', color: 'var(--ink)' }}>2 power figures unsurfaced</span>
            <span style={{ font: 'var(--meta)', color: 'var(--fg3)' }}>Economic Buyer · Procurement</span>
            <Button size="sm" variant="quiet" iconRight="arrow-right">Find them</Button>
          </div>

          <AccountMap selectedId={sel} onSelect={setSel} activePlan={plan} />
        </div>

        {/* inspector */}
        <aside style={{ width: 344, flexShrink: 0, borderLeft: '1px solid var(--border)', background: 'var(--surface)', overflowY: 'auto' }}>
          {person ? <PersonInspector person={person} onClose={() => setSel(null)} />
                  : <BoardInspector surfaced={surfaced} plan={plan} setPlan={setPlan} onPick={setSel} />}
        </aside>
      </div>
    </div>
  );
}

/* ---- Default inspector: board summary + route picker ---- */
function BoardInspector({ surfaced, plan, setPlan, onPick }) {
  const active = PLANS.find(p => p.id === plan);
  const roleCount = {};
  PEOPLE.forEach(p => { roleCount[p.role] = (roleCount[p.role] || 0) + 1; });
  return (
    <div style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 18 }}>
      <div>
        <Eyebrow>Board coverage</Eyebrow>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginTop: 8 }}>
          <span style={{ font: '700 30px/1 var(--font-sans)', letterSpacing: '-0.02em', color: 'var(--ink)' }}>{surfaced}<span style={{ color: 'var(--fg4)' }}>/{PEOPLE.length}</span></span>
          <span style={{ font: '500 13px/1 var(--font-sans)', color: 'var(--fg3)' }}>figures surfaced</span>
        </div>
        <div style={{ display: 'flex', gap: 14, marginTop: 12 }}>
          {[['ally', 'Allies', 3], ['blocker', 'Blockers', 1], ['unsurfaced', 'Missing', 2]].map(([s, l, n]) => (
            <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
              <StanceDot stance={s} size={9} ring />
              <div>
                <div style={{ font: '700 15px/1 var(--font-sans)', color: 'var(--ink)' }}>{n}</div>
                <div style={{ font: 'var(--meta)', color: 'var(--fg3)' }}>{l}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <Divider />

      {/* recommended route */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
          <Eyebrow>Recommended route</Eyebrow>
          <span style={{ font: 'var(--mono-sm)', color: 'var(--ally)' }}>score {active.score}</span>
        </div>
        <div style={{ background: 'var(--cobalt-50)', border: '1px solid var(--cobalt-200)', borderRadius: 'var(--r-lg)', padding: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 8 }}>
            <Icon name="route" size={16} color="var(--cobalt)" />
            <span style={{ font: '650 14px/1.2 var(--font-sans)', color: 'var(--ink)' }}>{active.title}</span>
          </div>
          <RoutePath via={active.via} />
          <p style={{ font: 'var(--body-sm)', color: 'var(--fg2)', margin: '10px 0 0' }}>{active.why}</p>
          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
            <Button variant="primary" size="sm" icon="sparkles" style={{ flex: 1 }}>Draft next move</Button>
            <Button size="sm" icon="plus" title="Add task" />
          </div>
        </div>
      </div>

      {/* alt routes */}
      <div>
        <Eyebrow style={{ marginBottom: 8 }}>Alternative routes</Eyebrow>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {PLANS.filter(p => p.id !== plan).map(p => (
            <button key={p.id} onClick={() => setPlan(p.id)} style={{
              display: 'flex', alignItems: 'center', gap: 10, textAlign: 'left', cursor: 'pointer',
              background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--r-md)', padding: '10px 12px',
            }}>
              <span style={{ font: 'var(--mono-sm)', color: 'var(--fg3)', width: 28 }}>#{p.rank}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ font: '600 13px/1.2 var(--font-sans)', color: 'var(--ink)' }}>{p.title}</div>
                <div style={{ font: 'var(--meta)', color: 'var(--fg3)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{p.target}</div>
              </div>
              <span style={{ font: 'var(--mono-sm)', color: 'var(--fg2)' }}>{p.score}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function RoutePath({ via }) {
  const parts = via.split('→').map(s => s.trim());
  return (
    <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 6 }}>
      {parts.map((p, i) => (
        <React.Fragment key={i}>
          <span style={{ font: '600 12px/1 var(--font-sans)', color: 'var(--ink)', background: 'var(--surface)', border: '1px solid var(--cobalt-200)', borderRadius: 99, padding: '4px 9px' }}>{p}</span>
          {i < parts.length - 1 && <Icon name="arrow-right" size={13} color="var(--cobalt)" strokeWidth={2.2} />}
        </React.Fragment>
      ))}
    </div>
  );
}

/* ---- Person inspector ---- */
function PersonInspector({ person, onClose }) {
  const s = STANCE[person.stance];
  const sigs = SIGNALS.slice(0, 3);
  return (
    <div style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        <Avatar name={person.name} size={48} stance={person.stance} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ font: '650 16px/1.2 var(--font-sans)', color: 'var(--ink)' }}>{person.name}</div>
          <div style={{ font: '500 13px/1.3 var(--font-sans)', color: 'var(--fg2)' }}>{person.title}</div>
        </div>
        <IconButton name="x" iconSize={16} onClick={onClose} />
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <Badge tone={person.stance === 'neutral' ? 'neutral' : person.stance} icon={person.stance === 'blocker' ? 'shield' : person.stance === 'ally' ? 'check' : 'eye-off'}>{STANCE[person.stance].label}</Badge>
        <Badge tone="neutral">{person.role}</Badge>
        {!person.surfaced && <Badge tone="unsurfaced">Not engaged</Badge>}
      </div>

      <div style={{ background: 'var(--surface-2)', borderRadius: 'var(--r-md)', padding: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
          <span style={{ font: 'var(--meta)', color: 'var(--fg3)' }}>Confidence</span>
          <span style={{ font: 'var(--mono-sm)', color: 'var(--ink)' }}>{Math.round(person.conf * 100)}%</span>
        </div>
        <div style={{ height: 6, borderRadius: 99, background: 'var(--surface-3)', overflow: 'hidden' }}>
          <div style={{ width: `${person.conf * 100}%`, height: '100%', background: s.color, borderRadius: 99 }} />
        </div>
        <p style={{ font: 'var(--body-sm)', color: 'var(--fg2)', margin: '10px 0 0' }}>{person.note}</p>
      </div>

      <div>
        <Eyebrow style={{ marginBottom: 8 }}>Evidence & signals</Eyebrow>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {sigs.map(sig => (
            <div key={sig.id} style={{ display: 'flex', gap: 9, alignItems: 'flex-start' }}>
              <div style={{ width: 26, height: 26, borderRadius: 'var(--r-sm)', background: `var(--${sig.tone === 'cobalt' ? 'cobalt-50' : sig.tone === 'ally' ? 'ally-tint' : sig.tone === 'blocker' ? 'blocker-tint' : 'unsurfaced-tint'})`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <Icon name={sig.icon} size={14} color={`var(--${sig.tone === 'cobalt' ? 'cobalt' : sig.tone})`} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ font: '400 12.5px/1.4 var(--font-sans)', color: 'var(--fg2)' }}>{sig.text}</div>
                <div style={{ font: 'var(--mono-sm)', color: 'var(--fg4)', marginTop: 2 }}>{sig.type} · {sig.when} ago</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <Divider />

      <div>
        <Eyebrow style={{ marginBottom: 8 }}>Suggested move</Eyebrow>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <Button variant="primary" icon="sparkles" style={{ width: '100%', justifyContent: 'flex-start' }}>Draft outreach to {person.name.split(' ')[0]}</Button>
          <div style={{ display: 'flex', gap: 8 }}>
            <Button icon="share" style={{ flex: 1 }}>Request intro</Button>
            <Button icon="circle-check" style={{ flex: 1 }}>Add task</Button>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { MapScreen, AccountContext, BoardInspector, PersonInspector, RoutePath });
