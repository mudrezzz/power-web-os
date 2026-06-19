import type { LiveRadarTechnicalTrace, LiveRadarTechnicalTraceItem } from '../../types';

export type TraceGroupKey =
  | 'planning'
  | 'collection'
  | 'qualification'
  | 'coverage'
  | 'signal'
  | 'normalization'
  | 'validation'
  | 'provider'
  | 'artifact'
  | 'other';

export type TraceStatus = 'ok' | 'warning' | 'error';

export type TraceFilterKey = 'all' | 'errors' | 'provider' | 'planning' | 'validation';

export type ReadableTraceSection = {
  key: 'summary' | 'request' | 'provider' | 'parsed' | 'validation' | 'redaction' | 'raw';
  value: Record<string, unknown>;
};

export type ReadableTraceStep = {
  item: LiveRadarTechnicalTraceItem;
  groupKey: TraceGroupKey;
  status: TraceStatus;
  title: string;
  summary: string;
  hints: string[];
  searchableText: string;
  sections: ReadableTraceSection[];
};

export type ReadableTraceGroup = {
  key: TraceGroupKey;
  steps: ReadableTraceStep[];
};

const GROUP_ORDER: TraceGroupKey[] = [
  'planning',
  'collection',
  'qualification',
  'coverage',
  'signal',
  'normalization',
  'validation',
  'provider',
  'artifact',
  'other',
];

const HIDDEN_REASONING_KEYS = [
  ['chain', 'of', 'thought'].join('_'),
  ['hidden', 'reasoning'].join('_'),
  ['internal', 'thoughts'].join('_'),
];

const SECRET_KEY_PARTS = ['authorization', 'api_key', 'token', 'bearer', 'secret', 'password'];

export function readableTraceGroups(trace: LiveRadarTechnicalTrace | undefined): ReadableTraceGroup[] {
  const steps = (trace?.traces ?? []).map(readableTraceStep);
  return GROUP_ORDER.map((key) => ({ key, steps: steps.filter((step) => step.groupKey === key) })).filter((group) => group.steps.length > 0);
}

export function filterReadableTraceGroups(
  groups: ReadableTraceGroup[],
  filter: TraceFilterKey,
  query: string,
): ReadableTraceGroup[] {
  const normalizedQuery = query.trim().toLowerCase();
  return groups
    .map((group) => ({
      ...group,
      steps: group.steps.filter((step) => matchesTraceFilter(step, filter) && matchesTraceQuery(step, normalizedQuery)),
    }))
    .filter((group) => group.steps.length > 0);
}

export function readableTraceStep(item: LiveRadarTechnicalTraceItem): ReadableTraceStep {
  const safePayload = safeTraceObject(item.payload);
  const safeRedaction = safeTraceObject(item.redaction_report);
  const title = item.title || item.trace_type;
  const summary = item.summary || '';
  const sections = traceSections(item, safePayload, safeRedaction);
  const hints = traceHints(item, safePayload);
  return {
    item: { ...item, payload: safePayload, redaction_report: safeRedaction },
    groupKey: traceGroup(item, safePayload),
    status: traceStatus(item, safePayload, safeRedaction),
    title,
    summary,
    hints,
    sections,
    searchableText: [item.sequence, item.phase, item.node_name, item.trace_type, title, summary, ...hints, compactValue(safePayload)]
      .join(' ')
      .toLowerCase(),
  };
}

export function stringifyTraceValue(value: Record<string, unknown>) {
  return JSON.stringify(value, null, 2);
}

function matchesTraceFilter(step: ReadableTraceStep, filter: TraceFilterKey) {
  if (filter === 'errors') {
    return step.status === 'error';
  }
  if (filter === 'provider') {
    return step.item.trace_type.startsWith('provider_') || step.groupKey === 'provider';
  }
  if (filter === 'planning') {
    return step.groupKey === 'planning';
  }
  if (filter === 'validation') {
    return step.groupKey === 'validation' || step.item.trace_type === 'validation_result';
  }
  return true;
}

function matchesTraceQuery(step: ReadableTraceStep, normalizedQuery: string) {
  return !normalizedQuery || step.searchableText.includes(normalizedQuery);
}

function traceGroup(item: LiveRadarTechnicalTraceItem, payload: Record<string, unknown>): TraceGroupKey {
  const haystack = `${item.phase} ${item.node_name} ${item.trace_type} ${item.title} ${item.summary} ${compactValue(payload)}`.toLowerCase();
  if (haystack.includes('planner') || haystack.includes('plan')) return 'planning';
  if (haystack.includes('coverage')) return 'coverage';
  if (haystack.includes('qualification') || haystack.includes('gate')) return 'qualification';
  if (haystack.includes('signal')) return 'signal';
  if (haystack.includes('normalization') || haystack.includes('extraction') || haystack.includes('extract')) return 'normalization';
  if (haystack.includes('validation') || haystack.includes('warning')) return 'validation';
  if (item.trace_type.startsWith('provider_') || haystack.includes('provider') || haystack.includes('openrouter')) return 'provider';
  if (haystack.includes('artifact') || haystack.includes('shape')) return 'artifact';
  if (haystack.includes('collection') || haystack.includes('source') || haystack.includes('discovery')) return 'collection';
  return 'other';
}

function traceStatus(
  item: LiveRadarTechnicalTraceItem,
  payload: Record<string, unknown>,
  redaction: Record<string, unknown>,
): TraceStatus {
  const text = compactValue({ payload, redaction, trace_type: item.trace_type }).toLowerCase();
  if (item.trace_type === 'provider_error' || text.includes('"error"') || text.includes('exception')) return 'error';
  if (text.includes('warning') || text.includes('limited') || text.includes('masked') || text.includes('truncated')) return 'warning';
  return 'ok';
}

function traceSections(
  item: LiveRadarTechnicalTraceItem,
  payload: Record<string, unknown>,
  redaction: Record<string, unknown>,
): ReadableTraceSection[] {
  const sections: ReadableTraceSection[] = [];
  sections.push({ key: 'summary', value: traceSummaryPayload(item, payload) });
  addSection(sections, 'request', pickPayload(payload, ['request', 'messages', 'prompt', 'task', 'query', 'search_plan', 'current_task']));
  addSection(sections, 'provider', pickPayload(payload, ['provider', 'model', 'web_mode', 'usage', 'response', 'results', 'sources', 'source_outcomes']));
  addSection(sections, 'parsed', pickPayload(payload, ['parsed', 'normalized', 'plan', 'steps', 'candidates', 'candidate_universe', 'signals', 'qualification']));
  addSection(sections, 'validation', pickPayload(payload, ['validation', 'warnings', 'errors', 'coverage', 'issues']));
  if (Object.keys(redaction).length > 0) {
    sections.push({ key: 'redaction', value: redaction });
  }
  sections.push({ key: 'raw', value: payload });
  return sections;
}

function traceSummaryPayload(item: LiveRadarTechnicalTraceItem, payload: Record<string, unknown>) {
  return compactObject({
    sequence: item.sequence,
    phase: item.phase,
    node: item.node_name,
    type: item.trace_type,
    duration_ms: item.duration_ms,
    model: stringHint(payload, ['model', 'selected_model']),
    provider: stringHint(payload, ['provider', 'provider_name']),
    task: stringHint(payload, ['task_id', 'query_id', 'step_id']),
    candidate: stringHint(payload, ['candidate_id', 'candidate_name', 'legal_name']),
  });
}

function traceHints(item: LiveRadarTechnicalTraceItem, payload: Record<string, unknown>) {
  const hints = [
    stringHint(payload, ['model', 'selected_model']),
    stringHint(payload, ['provider', 'provider_name']),
    stringHint(payload, ['task_id', 'query_id', 'step_id']),
    stringHint(payload, ['candidate_id', 'candidate_name', 'legal_name']),
  ].filter((value): value is string => Boolean(value));
  if (item.duration_ms != null) hints.push(`${item.duration_ms} ms`);
  return Array.from(new Set(hints)).slice(0, 5);
}

function addSection(sections: ReadableTraceSection[], key: ReadableTraceSection['key'], value: Record<string, unknown>) {
  if (Object.keys(value).length > 0) {
    sections.push({ key, value });
  }
}

function pickPayload(payload: Record<string, unknown>, keys: string[]) {
  return Object.fromEntries(Object.entries(payload).filter(([key]) => keys.some((needle) => key.toLowerCase().includes(needle))));
}

function stringHint(payload: Record<string, unknown>, keys: string[]) {
  for (const [key, value] of Object.entries(payload)) {
    if (keys.includes(key) && (typeof value === 'string' || typeof value === 'number')) {
      return String(value);
    }
  }
  return null;
}

function safeTraceObject(value: Record<string, unknown>) {
  return safeTraceValue(value) as Record<string, unknown>;
}

function safeTraceValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(safeTraceValue);
  }
  if (value && typeof value === 'object') {
    const safe: Record<string, unknown> = {};
    for (const [key, nested] of Object.entries(value)) {
      if (isForbiddenTraceKey(key)) {
        safe.redacted_field = '[removed]';
      } else {
        safe[key] = safeTraceValue(nested);
      }
    }
    return safe;
  }
  if (typeof value === 'string' && looksSecretLike(value)) {
    return '[masked]';
  }
  return value;
}

function isForbiddenTraceKey(key: string) {
  const normalized = key.toLowerCase();
  return HIDDEN_REASONING_KEYS.includes(normalized) || SECRET_KEY_PARTS.some((part) => normalized.includes(part));
}

function looksSecretLike(value: string) {
  const normalized = value.toLowerCase();
  return SECRET_KEY_PARTS.some((part) => normalized.includes(part)) || normalized.startsWith('sk-');
}

function compactValue(value: unknown) {
  return JSON.stringify(value);
}

function compactObject(value: Record<string, unknown>) {
  return Object.fromEntries(Object.entries(value).filter(([, nested]) => nested !== null && nested !== undefined && nested !== ''));
}
