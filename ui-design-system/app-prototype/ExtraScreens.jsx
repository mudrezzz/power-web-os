/* Power Web OS — Playbook (config) + Signals (feed) screens */

function Toggle({ on, onClick }) {
  return (
    <button onClick={onClick} style={{
      width: 38, height: 22, borderRadius: 99, border: 'none', cursor: 'pointer', padding: 2,
      background: on ? 'var(--cobalt)' : 'var(--surface-3)', transition: 'background var(--dur) var(--ease)',
      display: 'flex', justifyContent: on ? 'flex-end' : 'flex-start',
    }}>
      <span style={{ width: 18, height: 18, borderRadius: '50%', background: '#fff', boxShadow: 'var(--shadow-xs)', transition: 'all var(--dur) var(--ease)' }} />
    </button>
  );
}

function PlaybookScreen({ search, onSearch }) {
  const [signals, setSignals] = React.useState(PLAYBOOK.signals);
  const toggle = i => setSignals(s => s.map((x, j) => j === i ? { ...x, on: !x.on } : x));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <TopBar search={search} onSearch={onSearch}>
        <div>
          <div style={{ font: '650 17px/1.1 var(--font-sans)', letterSpacing: '-0.01em', color: 'var(--ink)' }}>Sales Playbook</div>
          <div style={{ font: 'var(--meta)', color: 'var(--fg3)', marginTop: 2 }}>The rules the system reasons with · Enterprise DACH</div>
        </div>
      </TopBar>

      <div style={{ flex: 1, overflowY: 'auto', padding: '24px', maxWidth: 920, margin: '0 auto', width: '100%' }}>
        <PlaybookSection icon="users" title="Roles to map" desc="The figures every account board must surface before a deal can progress.">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {PLAYBOOK.roles.map(r => <Chip key={r} active>{r}</Chip>)}
            <Chip icon="plus">Add role</Chip>
          </div>
        </PlaybookSection>

        <PlaybookSection icon="activity" title="Signals & weights" desc="What counts as buying intent, and how strongly it moves the score.">
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {signals.map((s, i) => (
              <div key={s.name} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 0', borderBottom: i === signals.length - 1 ? 'none' : '1px solid var(--border-faint)' }}>
                <Toggle on={s.on} onClick={() => toggle(i)} />
                <span style={{ flex: 1, font: '500 14px/1.3 var(--font-sans)', color: s.on ? 'var(--ink)' : 'var(--fg4)' }}>{s.name}</span>
                <WeightPill weight={s.weight} dim={!s.on} />
              </div>
            ))}
          </div>
        </PlaybookSection>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <PlaybookSection icon="check" title="Allowed moves" desc="Plays the system may recommend." tight>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {PLAYBOOK.allowed.map(m => (
                <div key={m} style={{ display: 'flex', alignItems: 'center', gap: 9, font: 'var(--body-sm)', color: 'var(--fg2)' }}>
                  <Icon name="circle-check" size={16} color="var(--ally)" /> {m}
                </div>
              ))}
            </div>
          </PlaybookSection>
          <PlaybookSection icon="lock" title="Forbidden moves" desc="Hard guardrails — never suggested." tight>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {PLAYBOOK.forbidden.map(m => (
                <div key={m} style={{ display: 'flex', alignItems: 'center', gap: 9, font: 'var(--body-sm)', color: 'var(--fg2)' }}>
                  <Icon name="x" size={16} color="var(--blocker)" strokeWidth={2.4} /> {m}
                </div>
              ))}
            </div>
          </PlaybookSection>
        </div>

        <PlaybookSection icon="share" title="Channels" desc="Where outreach is allowed to happen." tight>
          <div style={{ display: 'flex', gap: 8 }}>
            {PLAYBOOK.channels.map((c, i) => <Chip key={c} active={i < 3} icon={c === 'Email' ? 'mail' : c === 'LinkedIn' ? 'linkedin' : c === 'Partner' ? 'share' : 'calendar'}>{c}</Chip>)}
          </div>
        </PlaybookSection>
      </div>
    </div>
  );
}

function PlaybookSection({ icon, title, desc, children, tight }) {
  return (
    <div style={{ marginBottom: tight ? 0 : 18 }}>
      <div style={{ display: 'flex', gap: 11, marginBottom: 12 }}>
        <div style={{ width: 32, height: 32, borderRadius: 'var(--r-md)', background: 'var(--surface-2)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <Icon name={icon} size={17} color="var(--fg2)" />
        </div>
        <div>
          <div style={{ font: '650 15px/1.2 var(--font-sans)', color: 'var(--ink)' }}>{title}</div>
          <div style={{ font: 'var(--body-sm)', color: 'var(--fg3)' }}>{desc}</div>
        </div>
      </div>
      <Card pad="16px 18px">{children}</Card>
    </div>
  );
}

function WeightPill({ weight, dim }) {
  const tone = weight === 'High' ? 'cobalt' : weight === 'Medium' ? 'neutral' : 'neutral';
  return <Badge tone={dim ? 'neutral' : tone} style={dim ? { opacity: 0.5 } : {}}>{weight}</Badge>;
}

/* ---------------- Signals feed ---------------- */
function SignalsScreen({ search, onSearch }) {
  const tones = { cobalt: ['cobalt-50', 'cobalt'], ally: ['ally-tint', 'ally'], blocker: ['blocker-tint', 'blocker'], unsurfaced: ['unsurfaced-tint', 'unsurfaced'] };
  const feed = [...SIGNALS, ...SIGNALS.map((s, i) => ({ ...s, id: s.id + 'b', when: (3 + i) + 'w' }))];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <TopBar search={search} onSearch={onSearch}>
        <div>
          <div style={{ font: '650 17px/1.1 var(--font-sans)', letterSpacing: '-0.01em', color: 'var(--ink)' }}>Signals</div>
          <div style={{ font: 'var(--meta)', color: 'var(--fg3)', marginTop: 2 }}>Public & first-party signals across your book</div>
        </div>
      </TopBar>
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px 48px', maxWidth: 760, margin: '0 auto', width: '100%' }}>
        <div style={{ display: 'flex', gap: 8, marginBottom: 18 }}>
          <Chip icon="activity" active>All signals</Chip>
          <Chip>Buying intent</Chip>
          <Chip>Risk</Chip>
          <Chip>People moves</Chip>
        </div>
        <div style={{ font: 'var(--mono-sm)', letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--fg4)', margin: '0 0 10px 2px' }}>This week</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {feed.slice(0, 5).map(s => <SignalRow key={s.id} s={s} tones={tones} />)}
        </div>
        <div style={{ font: 'var(--mono-sm)', letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--fg4)', margin: '22px 0 10px 2px' }}>Earlier</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {feed.slice(5, 9).map(s => <SignalRow key={s.id} s={s} tones={tones} />)}
        </div>
      </div>
    </div>
  );
}

function SignalRow({ s, tones }) {
  const [t1, t2] = tones[s.tone];
  return (
    <Card pad="14px 16px" hover>
      <div style={{ display: 'flex', gap: 13, alignItems: 'flex-start' }}>
        <div style={{ width: 38, height: 38, borderRadius: 'var(--r-md)', background: `var(--${t1})`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <Icon name={s.icon} size={18} color={`var(--${t2})`} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
            <Badge tone={s.tone === 'cobalt' ? 'cobalt' : s.tone}>{s.type}</Badge>
            <span style={{ font: 'var(--meta)', color: 'var(--fg4)' }}>{ACCOUNT.name} · {s.when} ago</span>
            <div style={{ flex: 1 }} />
            <span style={{ font: 'var(--mono-sm)', color: 'var(--fg3)' }}>{s.strength}</span>
          </div>
          <div style={{ font: '450 14px/1.45 var(--font-sans)', color: 'var(--ink)' }}>{s.text}</div>
        </div>
        <IconButton name="arrow-up-right" iconSize={16} title="Open account" />
      </div>
    </Card>
  );
}

Object.assign(window, { PlaybookScreen, SignalsScreen, Toggle, PlaybookSection, SignalRow, WeightPill });
