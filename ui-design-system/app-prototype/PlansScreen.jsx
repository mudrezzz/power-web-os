/* Power Web OS — Access Plans screen: explainable top-3 routes */

function PlansScreen({ search, onSearch }) {
  const [open, setOpen] = React.useState('p1');
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <TopBar search={search} onSearch={onSearch}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Icon name="chevron-left" size={18} color="var(--fg3)" />
          <div>
            <div style={{ font: '650 17px/1.1 var(--font-sans)', letterSpacing: '-0.01em', color: 'var(--ink)' }}>Access Plans · {ACCOUNT.name}</div>
            <div style={{ font: 'var(--meta)', color: 'var(--fg3)', marginTop: 2 }}>3 routes ranked by reach, trust & timing</div>
          </div>
        </div>
      </TopBar>

      <div style={{ flex: 1, overflowY: 'auto', padding: '22px 24px 48px', maxWidth: 880, margin: '0 auto', width: '100%' }}>
        {/* objective banner */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '16px 18px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', boxShadow: 'var(--shadow-sm)', marginBottom: 18 }}>
          <div style={{ width: 40, height: 40, borderRadius: 'var(--r-md)', background: 'var(--cobalt-50)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Icon name="target" size={20} color="var(--cobalt)" />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ font: 'var(--meta)', color: 'var(--fg3)' }}>OBJECTIVE</div>
            <div style={{ font: '600 15px/1.3 var(--font-sans)', color: 'var(--ink)' }}>Reach the economic buyer (Diane Okafor) with a trusted, in-policy path</div>
          </div>
          <Button variant="default" icon="settings-2">Playbook rules</Button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {PLANS.map(p => <PlanCard key={p.id} plan={p} open={open === p.id} onToggle={() => setOpen(open === p.id ? null : p.id)} />)}
        </div>
      </div>
    </div>
  );
}

function PlanCard({ plan, open, onToggle }) {
  return (
    <div style={{
      background: 'var(--surface)', border: `1px solid ${plan.recommended ? 'var(--cobalt-200)' : 'var(--border)'}`,
      borderRadius: 'var(--r-lg)', boxShadow: open ? 'var(--shadow-md)' : 'var(--shadow-sm)', overflow: 'hidden',
      transition: 'box-shadow var(--dur) var(--ease)',
    }}>
      {/* header */}
      <div onClick={onToggle} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '16px 18px', cursor: 'pointer' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, width: 40 }}>
          <span style={{ font: 'var(--mono-sm)', color: 'var(--fg4)' }}>RANK</span>
          <span style={{ font: '700 22px/1 var(--font-sans)', color: plan.recommended ? 'var(--cobalt)' : 'var(--ink)' }}>{plan.rank}</span>
        </div>
        <div style={{ width: 1, height: 40, background: 'var(--border)' }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ font: '650 16px/1.2 var(--font-sans)', color: 'var(--ink)', whiteSpace: 'nowrap' }}>{plan.title}</span>
            {plan.recommended && <Badge tone="cobalt" icon="sparkles">Recommended</Badge>}
          </div>
          <div style={{ font: '500 13px/1.3 var(--font-sans)', color: 'var(--fg3)', marginTop: 3 }}>Target · {plan.target}</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ font: 'var(--mono-sm)', color: 'var(--fg4)' }}>SCORE</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 56, height: 6, borderRadius: 99, background: 'var(--surface-3)', overflow: 'hidden' }}>
              <div style={{ width: `${plan.score}%`, height: '100%', background: plan.recommended ? 'var(--cobalt)' : 'var(--fg3)', borderRadius: 99 }} />
            </div>
            <span style={{ font: '700 16px/1 var(--font-sans)', color: 'var(--ink)' }}>{plan.score}</span>
          </div>
        </div>
        <Icon name="chevron-down" size={18} color="var(--fg3)" style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform var(--dur)' }} />
      </div>

      {open && (
        <div style={{ padding: '0 18px 18px', borderTop: '1px solid var(--border-faint)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 22, paddingTop: 16 }}>
            {/* left: route + why + steps */}
            <div>
              <Eyebrow style={{ marginBottom: 8 }}>Route</Eyebrow>
              <RoutePath via={plan.via} />
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginTop: 14, padding: 12, background: 'var(--surface-2)', borderRadius: 'var(--r-md)' }}>
                <Icon name="lightbulb" size={16} color="var(--unsurfaced)" style={{ marginTop: 1 }} />
                <div>
                  <span style={{ font: '600 12px/1 var(--font-sans)', color: 'var(--fg2)' }}>WHY THIS ROUTE</span>
                  <p style={{ font: 'var(--body-sm)', color: 'var(--fg2)', margin: '5px 0 0' }}>{plan.why}</p>
                </div>
              </div>

              <Eyebrow style={{ margin: '18px 0 10px' }}>Plan steps</Eyebrow>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
                {plan.steps.map((st, i) => (
                  <div key={i} style={{ display: 'flex', gap: 12, paddingBottom: i === plan.steps.length - 1 ? 0 : 14 }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <div style={{ width: 22, height: 22, borderRadius: '50%', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: st.done ? 'var(--ally)' : 'var(--surface)', border: `2px solid ${st.done ? 'var(--ally)' : 'var(--border-strong)'}` }}>
                        {st.done && <Icon name="check" size={12} color="#fff" strokeWidth={3} />}
                      </div>
                      {i < plan.steps.length - 1 && <div style={{ width: 2, flex: 1, background: 'var(--border)', minHeight: 18 }} />}
                    </div>
                    <div style={{ paddingTop: 1 }}>
                      <div style={{ font: '600 13.5px/1.3 var(--font-sans)', color: 'var(--ink)' }}>{st.who}</div>
                      <div style={{ font: 'var(--body-sm)', color: 'var(--fg3)' }}>{st.move}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* right: hook + evidence + meta + actions */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div style={{ padding: 12, background: 'var(--cobalt-50)', border: '1px solid var(--cobalt-200)', borderRadius: 'var(--r-md)' }}>
                <div style={{ font: 'var(--meta)', color: 'var(--cobalt-700)', marginBottom: 4 }}>OPENING HOOK</div>
                <div style={{ font: '500 13.5px/1.4 var(--font-sans)', color: 'var(--ink)' }}>{plan.hook}</div>
              </div>
              <div>
                <Eyebrow style={{ marginBottom: 8 }}>Evidence</Eyebrow>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {plan.evidence.map((e, i) => (
                    <div key={i} style={{ display: 'flex', gap: 7, alignItems: 'center', font: 'var(--body-sm)', color: 'var(--fg2)' }}>
                      <Icon name="circle-check" size={14} color="var(--ally)" /> {e}
                    </div>
                  ))}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, font: 'var(--meta)', color: 'var(--fg3)' }}>
                <Badge tone="neutral" icon="user">{plan.owner}</Badge>
                <Badge tone="neutral" icon="clock">Next: {plan.next}</Badge>
              </div>
              <Button variant="primary" icon="sparkles" style={{ width: '100%' }}>Create tasks & draft move</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

Object.assign(window, { PlansScreen, PlanCard });
