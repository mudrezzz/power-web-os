# RCA: Signal Monitoring Live Reproducibility

Slice `0.7.6.4.19.1` remains `In Progress`. The frozen acceptance manifest SHA-256 is
`9dfab1ee6a2a449109d35b8cf53b097cae3a4b48797bfedfb4c7214df2d6d82e` and was not
changed after live output inspection.

## Accepted evidence

- Initial A: `signal-run-8eb6d673-a6f6-417a-8519-8cc50e7e94f8` matched 4/4 positive,
  4/4 negative, and 1/1 unknown-date controls.
- Final initial B: `signal-run-6754eba6-a43a-4594-8236-d7ed60f6d2c5` matched 3/4
  positive, 4/4 negative, and 1/1 unknown-date controls.
- Both runs used independent monitoring series with zero previous source keys.
- Both runs had zero receipt gaps, orphan decisions, false `not_observed`, identity-only
  confirmations, unresolved capabilities, and score-zero confirmed observations.
- Candidate/criterion obligations, cross-criterion validation, task-scoped source refs,
  canonical URL matching, temporal validation, and bounded transport retries remained
  auditable.

## Failed attempts

The acceptance freeze records four superseded B attempts. B2 and B4 were stopped once
their frozen controls became unreachable, avoiding the remaining provider calls. B3 and
B5 completed with 3/4 positive controls. The latest B found all three Voronezh controls,
including `abireg.ru/newsitem/112663`, but did not reproduce the frozen SIBUR-Khimprom
control `kommersant.ru/doc/8232236`.

## Root cause

The remaining failure is live-search reproducibility, not evidence projection. OpenRouter
returns different relevant source sets for the same candidate, criterion, date window, and
accepted query obligations. One independent run reached the frozen Khimprom URL; the next
independent run returned other Khimprom modernization sources. Post-run validation correctly
refused to substitute a similar URL for the frozen control.

Local defects found and fixed during the bounded loop:

- provider-local refs such as `source_1` collided across tasks; refs are now task-scoped;
- one cross-criterion control was physically retrieved but not independently revalidated;
- source URL path terms could leak from an unbound candidate source;
- quarter expressions were not projected as deterministic event intervals;
- the evaluator required only one temporal field instead of accepting a valid event or
  publication interval;
- the initial runner gated A but could continue from a failed B;
- an incomplete A/B/C session raised a traceback instead of writing a machine `FAIL` report;
- modernization search terms mixed completion-stage and automation hypotheses in one query;
  they now remain separate bounded variants.

## Decision

The five-cycle autofix limit was exhausted and the original v1 acceptance remains an immutable
`FAIL`. The user then explicitly approved a v2 acceptance revision: every independent initial
run must find at least 3/4 controls, at least one must find 4/4, their union must find 4/4, and
both must still pass all negative, unknown-date, temporal, source-binding, provenance and budget
checks. The missing Khimprom URL in B is classified as `provider_search_drift`, not hidden as a
successful exact match.

This decision allows incremental C and process closure without pretending that live search is
fully stable. Search-engine stability is moved into dedicated OpenRouter routing experiments and
a conditional independent-provider fallback slice. Any aggregate miss or semantic integrity
failure still blocks closure.
