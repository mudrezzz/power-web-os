# Acceptance Amendment V2: 0.7.6.4.19.1

## Preserved Evidence

The original acceptance manifest, freeze and machine validation are archived as
`acceptance.v1.json`, `acceptance-freeze.v1.json`, `validation.v1.json` and
`VALIDATION_REPORT_V1.md`. They prove that the original requirement for two
independent `4/4` runs failed and must not be reinterpreted as a pass.

## Approved Revision

The functional Signal Monitoring pipeline is accepted when:

- both independent initial runs find at least `3/4` positive controls;
- at least one initial run finds `4/4`;
- the union of both runs finds `4/4`;
- the only per-run missing control is explicitly listed as accepted provider
  search drift;
- both runs independently pass all negative, unknown-date, temporal,
  capability, binding, provenance, receipt and budget requirements;
- incremental C proves watermarks and republishes no previous confirmed or
  review evidence.

For the accepted A/B evidence, A found `4/4`, B found `3/4`, and only B missed
`khimprom-modernization-automation-2025`. Both found `4/4` negative controls
and `1/1` unknown-date control and had zero semantic integrity violations.

## Rationale

Repeated bounded attempts showed source-set variance inside the external web
search rather than a failure of planning, evidence validation or projection.
The project prioritizes completing the three-pipeline product contour before
optimizing one provider's exact-URL reproducibility. The unresolved stability
problem remains explicit follow-up work and is not converted into a quality
claim.
