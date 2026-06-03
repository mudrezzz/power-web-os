/* Power Web OS — Demo data (fictional). Target account: Northwind Robotics. */

const ACCOUNT = {
  name: 'Northwind Robotics',
  domain: 'northwind-robotics.com',
  industry: 'Industrial Automation',
  size: '2,400 employees',
  region: 'DACH · EMEA',
  stage: 'Mapping',
  health: 58,
  arr: '$420K potential',
  updated: '2h ago',
};

/* Buying committee — each node on the board */
const PEOPLE = [
  { id: 'okafor', name: 'Diane Okafor', title: 'Chief Financial Officer', role: 'Economic Buyer', stance: 'unsurfaced', surfaced: false, x: 0.76, y: 0.15, conf: 0.41, note: 'Not yet engaged · approves >$250K', signal: 'Missing figure' },
  { id: 'anand', name: 'Priya Anand', title: 'Chief Technology Officer', role: 'Decision Maker', stance: 'neutral', surfaced: true, x: 0.45, y: 0.20, conf: 0.74, note: 'Owns platform budget line', signal: 'Power line' },
  { id: 'lin', name: 'Grace Lin', title: 'Procurement Lead', role: 'Procurement', stance: 'unsurfaced', surfaced: false, x: 0.88, y: 0.46, conf: 0.33, note: 'Engages at contract stage', signal: 'Missing figure' },
  { id: 'reuter', name: 'Tom Reuter', title: 'Head of Security', role: 'Blocker', stance: 'blocker', surfaced: true, x: 0.64, y: 0.52, conf: 0.69, note: 'Raised SOC 2 concern in eval', signal: 'Risk to clear' },
  { id: 'bell', name: 'Marcus Bell', title: 'VP Engineering', role: 'Champion', stance: 'ally', surfaced: true, x: 0.27, y: 0.46, conf: 0.86, note: 'Replied to last touch · attended webinar', signal: 'Champion candidate' },
  { id: 'vogt', name: 'Lena Vogt', title: 'Director, Platform', role: 'Influencer', stance: 'ally', surfaced: true, x: 0.36, y: 0.82, conf: 0.71, note: 'Advocates internally · POC owner', signal: 'Internal advocate' },
  { id: 'cho', name: 'Sam Cho', title: 'Staff Engineer', role: 'Evaluator', stance: 'neutral', surfaced: true, x: 0.10, y: 0.74, conf: 0.62, note: 'Running technical evaluation', signal: 'Hands-on eval' },
];

/* Relationship edges between committee members */
const EDGES = [
  { a: 'bell', b: 'anand', kind: 'reports' },
  { a: 'anand', b: 'okafor', kind: 'reports' },
  { a: 'vogt', b: 'bell', kind: 'reports' },
  { a: 'cho', b: 'vogt', kind: 'reports' },
  { a: 'reuter', b: 'anand', kind: 'reports' },
  { a: 'lin', b: 'okafor', kind: 'works' },
  { a: 'bell', b: 'reuter', kind: 'works' },
];

/* External ecosystem (warm paths in) */
const EXTERNAL = [
  { id: 'ext-si', name: 'Helix Systems', kind: 'SI Partner', via: 'Your partner manager', warm: true },
  { id: 'ext-adv', name: 'Jonas Frei', kind: 'Ex-colleague of Marcus Bell', via: 'Mutual: Anika R.', warm: true },
];

/* Top-3 access plans — explainable routes */
const PLANS = [
  {
    id: 'p1', rank: 1, score: 82, recommended: true,
    title: 'Warm intro through your champion',
    target: 'Diane Okafor · Economic Buyer',
    via: 'Marcus Bell → Priya Anand → Diane Okafor',
    why: 'Marcus is engaged and reports into Priya, who owns the budget line that rolls up to Diane. Shortest trusted path to the unsurfaced economic buyer.',
    hook: 'Q3 automation efficiency benchmark Northwind cited in earnings',
    next: 'Ask Marcus for a 3-way intro to Priya',
    owner: 'Sales',
    steps: [
      { who: 'Marcus Bell', move: 'Confirm value & ask for intro up', done: true },
      { who: 'Priya Anand', move: 'Align on platform business case', done: false },
      { who: 'Diane Okafor', move: 'Surface ROI to economic buyer', done: false },
    ],
    evidence: ['Webinar attendance · 14 Mar', 'Reply to sequence · 09 Mar', 'Org chart: Bell→Anand→Okafor'],
  },
  {
    id: 'p2', rank: 2, score: 67, recommended: false,
    title: 'Partner-sourced introduction',
    target: 'Priya Anand · Decision Maker',
    via: 'Helix Systems (SI Partner) → Priya Anand',
    why: 'Helix is an active Northwind integrator with a standing relationship to the platform org. A co-sell motion bypasses cold outreach and adds credibility.',
    hook: 'Joint reference architecture with Helix',
    next: 'Brief partner manager; request warm path',
    owner: 'Partner Manager',
    steps: [
      { who: 'Helix Systems', move: 'Partner manager opens door', done: false },
      { who: 'Priya Anand', move: 'Co-sell technical framing', done: false },
    ],
    evidence: ['Helix listed as Northwind vendor', 'Co-sell agreement active'],
  },
  {
    id: 'p3', rank: 3, score: 54, recommended: false,
    title: 'Clear the blocker first',
    target: 'Tom Reuter · Blocker',
    via: 'Lena Vogt → Tom Reuter',
    why: 'Security concern is the live risk. Lena can broker a scoped security review with Tom before it escalates and stalls the deal.',
    hook: 'SOC 2 Type II + pen-test summary',
    next: 'Send security pack via Lena',
    owner: 'RevOps',
    steps: [
      { who: 'Lena Vogt', move: 'Broker security conversation', done: false },
      { who: 'Tom Reuter', move: 'Resolve SOC 2 objection', done: false },
    ],
    evidence: ['Objection logged in eval · 11 Mar', 'Vogt↔Reuter peer relationship'],
  },
];

/* Signals feed */
const SIGNALS = [
  { id: 's1', type: 'Hiring', icon: 'briefcase', tone: 'cobalt', text: 'Opened 6 roles in "Automation Platform" — buying intent up', when: '1d', strength: 'High' },
  { id: 's2', type: 'Earnings', icon: 'trending-up', tone: 'ally', text: 'CFO Okafor cited "efficiency program" on Q2 call', when: '3d', strength: 'High' },
  { id: 's3', type: 'Risk', icon: 'shield', tone: 'blocker', text: 'Security review flagged in evaluation thread', when: '4d', strength: 'Med' },
  { id: 's4', type: 'Tech', icon: 'zap', tone: 'cobalt', text: 'Adopted a competing point tool in one BU', when: '1w', strength: 'Med' },
  { id: 's5', type: 'Move', icon: 'arrow-up-right', tone: 'unsurfaced', text: 'New Director of Platform hired (Lena Vogt)', when: '2w', strength: 'Low' },
];

/* Accounts portfolio */
const ACCOUNTS = [
  { name: 'Northwind Robotics', industry: 'Industrial Automation', stage: 'Mapping', health: 58, missing: 2, route: 'Warm intro ready', owner: 'You', stance: 'ally' },
  { name: 'Vantage Logistics', industry: 'Supply Chain', stage: 'Access', health: 74, missing: 0, route: 'Champion engaged', owner: 'You', stance: 'ally' },
  { name: 'Caldera Energy', industry: 'Utilities', stage: 'Mapping', health: 41, missing: 4, route: 'Blocker active', owner: 'R. Mehta', stance: 'blocker' },
  { name: 'Brightline Health', industry: 'Healthcare', stage: 'Qualifying', health: 63, missing: 1, route: 'Partner path', owner: 'You', stance: 'neutral' },
  { name: 'Orbit Manufacturing', industry: 'Manufacturing', stage: 'Access', health: 81, missing: 0, route: 'EB surfaced', owner: 'K. Sole', stance: 'ally' },
  { name: 'Meridian Freight', industry: 'Transportation', stage: 'Mapping', health: 36, missing: 5, route: 'No path yet', owner: 'You', stance: 'unsurfaced' },
];

/* Playbook config */
const PLAYBOOK = {
  roles: ['Economic Buyer', 'Decision Maker', 'Champion', 'Influencer', 'Evaluator', 'Blocker', 'Procurement'],
  signals: [
    { name: 'Hiring surge in target function', weight: 'High', on: true },
    { name: 'Exec mention on earnings call', weight: 'High', on: true },
    { name: 'Competing tool adoption', weight: 'Medium', on: true },
    { name: 'Leadership change', weight: 'Medium', on: true },
    { name: 'Funding / M&A event', weight: 'Low', on: false },
  ],
  allowed: ['Warm intro via mutual', 'Partner co-sell', 'Event / webinar follow-up', 'Executive briefing'],
  forbidden: ['Cold call C-suite directly', 'Reference unannounced news', 'Contact during quiet period'],
  channels: ['Email', 'LinkedIn', 'Partner', 'Event'],
};

Object.assign(window, { ACCOUNT, PEOPLE, EDGES, EXTERNAL, PLANS, SIGNALS, ACCOUNTS, PLAYBOOK });
