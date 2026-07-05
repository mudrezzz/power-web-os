# Radar Shared Budgets

## Ownership

Owns provider-level external-call budget contracts shared by Radar application
pipelines: settings, reservation decisions, counters, exhaustion records,
context-local reservation helpers, and recall-expansion reservation metadata.

It does not own candidate-discovery task budgets, useful-result retry budgets,
signal-monitoring execution budgets, provider adapters, persistence, API routes,
or workflow orchestration.

## Allowed imports

- Python standard library.
- Other modules in `power_web_os.application.radar.shared.budgets`.
- Provider-neutral shared Radar contracts.

## Forbidden imports

- `power_web_os.application.radar.candidate_discovery`.
- `power_web_os.application.radar.signal_monitoring`.
- `power_web_os.application.radar.power_web_discovery`.
- `power_web_os.integrations`, `power_web_os.persistence`, `power_web_os.api`,
  Celery, Redis, OpenAI, Anthropic, or HTTP clients.

## How to extend

Add shared budget records here only when more than one Radar pipeline needs the
same provider-level accounting semantics. Pipeline-specific admission, task
limits, projection, and dossier metadata stay in the owning pipeline package.
