# ADR: Radar retrieval contract and structured source providers

## Status

Accepted

## Context

Recent live Radar traces showed that bounded provider calls still receive heavy
JSON payloads with repeated Radar context, duplicated single-query search plans,
verbose output schemas, and broad rules. In practice, the model often compresses
that payload into a short internal web query. This suggests that the current
execution prompt shape can waste tokens and obscure the real task instead of
helping retrieval.

The same traces also showed that budget semantics are too broad. A limit such as
`POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT=5` can stop signal search after a
few candidates for a signal, even though the business expectation is closer to a
budget per candidate and per signal. When unsearched candidates are normalized
as negative observations, diagnostics become misleading.

Finally, general web search is not the right source for every fact. Company
identity, INN/OGRN, official registration facts, address data, OKVED, status,
and financial facts need structured company-data sources. DaData is the first
implemented provider in this class: its MCP/API surface is intended to provide
AI agents fresh data about companies and addresses, including organization
lookup and related business facts.

## Decision

Radar execution will be split into four explicit responsibilities:

1. **Planner** proposes strategy from rich context: Radar definition, source
   policy, qualification criteria, intent signals, run limits, and available
   source providers.
2. **Retrieval plan** stores accepted strategy as compact executable task cards:
   task type, rule/signal/candidate scope, selected source policy, query or
   provider action, expected evidence, budget key, stop condition, and response
   contract.
3. **Retrieval/source providers** execute bounded tasks and return structured
   retrieval or company-data observations. Provider adapters live in
   `integrations` behind application ports.
4. **Extractor/evaluator** converts retrieved material into evidence-linked
   observations, while application/domain services keep ownership of source
   policy, verification, candidate state, scoring, and review semantics.

Execution prompts must be compiled from compact task cards. They should not
repeat the full Radar artifact, duplicate a one-query search plan, or carry
large generic schemas that do not change for the task. Technical trace should
show the task card, compiled prompt/request, provider result, parsed output, and
final source usage.

Budgeting will move from broad subject counters to hierarchical keys:

- total run budget;
- discovery budget per qualification rule;
- qualification gate budget per candidate and rule;
- signal budget per candidate and signal;
- provider-specific caps.

Unsearched findings must be explicit. `not_observed` means a relevant bounded
task ran and no evidence was found. Budget-limited or policy-limited cases must
use explicit not-searched states.

DaData is introduced as the first structured company-source provider, not as a
web retrieval replacement. Radar may use it for legal-entity resolution and
company facts, while open web retrieval remains responsible for current evidence
and intent signals. The UI may expose DaData as a source only after source
configuration UX and permissions are designed; backend execution and recorded
tests now exist.

## Consequences

- Live Radar traces should become cheaper and easier to debug because provider
  calls show compact task cards instead of large repeated JSON blobs.
- Product dossier can explain the accepted retrieval plan before showing
  candidates and scores.
- Budget-limited candidates will no longer be confused with searched negative
  results.
- DaData and later structured sources can be selected by source policy without
  leaking MCP/API details into domain logic.
- Perplexity/OpenRouter provider comparisons happen behind the retrieval
  contract. The first implementation uses OpenRouter server-tools
  `engine=perplexity` so it can reuse current OpenRouter credentials; direct
  Perplexity Search API remains a later provider adapter.

## Alternatives considered

- **Keep heavy JSON prompts and tune only the model.** Rejected because traces
  show the model already reduces them to simpler internal queries; a stronger
  model would not fix redundant context or wrong budget semantics.
- **Add direct Perplexity Search API first.** Deferred because it requires a
  separate `PERPLEXITY_API_KEY` and a different HTTP contract; the current slice
  uses OpenRouter's Perplexity engine to validate the retrieval boundary first.
- **Use DaData as the full discovery engine.** Rejected because registry-style
  facts do not replace open web evidence or intent signal monitoring.
- **Expose DaData in UI before backend support.** Rejected because source
  settings must not advertise sources the backend cannot execute.
