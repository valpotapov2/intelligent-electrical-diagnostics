# FAA DRPDS — integration with the real diagnostic core

## Purpose

This is the engine-level companion to the generic graph benchmark. It exercises the real private `diagnostics-mvp` engine through the bridge in `src/edi_ingest/diagnostic_core.py`, not through the graph-only `scenario_runner.py`.

The integration follows the same contract path as the kindergarten benchmark:
`diag.module.load → diag.model.build → diag.engine.Session → MeasurementRequest → SafetyGateway.measure → MeasurementResult → Session.add_reply`.

## Synthetic module

`benchmarks/faa-drpds/diagnostic-core-module.synthetic.yaml` defines six virtual observation points and six synthetic modes:

- Healthy;
- Critical A path loss;
- Critical B path loss;
- simultaneous loss of both critical paths;
- SATS output loss;
- essential feed loss.

The fixture uses only synthetic 0–5.5 V software values and a virtual adapter. These are not AC voltages, not values measured on FAA equipment, not validated measurement bands, not a physical circuit model and not a field test plan. Priors are equal synthetic test weights, not historical failure probabilities.

The virtual adapter keeps the selected hidden mode private and returns only the requested `MeasurementResult`. The engine is expected to update its posterior from the observations it requests.

## Tests

`tests/test_faa_drpds_core_scenarios.py` tests:

1. Posterior discrimination for each of the six synthetic modes.
2. Rejection of an instrument error with a null value, without an automatic retry.
3. Blocking an undeclared internal SATS test point before the adapter is called.

The tests are wired into the existing Python 3.13 real-core integration workflow. The workflow requires the repository secret `DIAGNOSTICS_MVP_TOKEN` to checkout the pinned private core commit. Without that secret, the real-core test job is intentionally skipped and reports a warning.

## Interpretation

A passing test demonstrates that the actual engine contracts can process a synthetic DRPDS-like redundancy fixture. It does not establish that the engine can diagnose a real FAA facility.

The synthetic modes are intentionally simplified. In particular, they do not model actual UPS electronics, battery autonomy, generator synchronization, source transfer timing, protection coordination, breaker interlocks, individual PDU/SATS/CDP wiring, or the physical independence of redundant paths.

The generic object graph remains the source-traceable architecture layer. The synthetic diagnostic module is a separate engine test fixture and must not be mistaken for a transformation of the generic graph into a verified site-specific measurement model.

## Next requirement for field-grade reasoning

Before any real diagnostic use, a site-specific module would need:
- individually identified equipment and verified input/output topology;
- approved measurement points and test procedures;
- voltage/current ranges, instrument profiles and uncertainty requirements from equipment documentation;
- qualified-personnel and authorization rules;
- validated failure modes and evidence likelihoods;
- real operating/event records or engineering-approved priors.

No live measurement or switching is enabled by this integration.
