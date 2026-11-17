# FAA DRPDS — diagnostic-core readiness benchmark

**Benchmark:** `faa-drpds-graph-readiness-001`  
**Mode:** `offline_simulation_only`  
**Engine capability exercised:** graph reachability only.

## Purpose

This benchmark checks whether the current offline scenario runner can consume the DRPDS graph without assuming a single fixed source node, model multiple independent source nodes, simulate one or more unavailable connections, and preserve explicit model-knowledge boundaries.

It is not a benchmark of full fault diagnosis.

## Runner changes required for this object

The original `scenario_runner.py` assumed the source node was always `bus-l123` and could remove only one edge per scenario. DRPDS has multiple supply sources and requires combined path-loss scenarios. The runner was generalized to:

- read `source_component_ids` from an individual scenario, or from `object.supply.diagnostic_source_ids`, while retaining the kindergarten fallback `bus-l123`;
- accept both `open_edge` and `open_edges`;
- validate every referenced source component and removed edge;
- report `diagnostic_capability: graph_reachability_only` so the result is not mistaken for causal diagnosis;
- return the missing prerequisites supplied by a `question` injection instead of hard-coding an ATS-specific explanation;
- keep the safety gateway closed for live measurement and operation.

## Scenarios

| ID | Synthetic condition | Expected affected scope | What is checked |
|---|---|---|---|
| DRPDS-BASE-001 | Both utility sources available | None | Baseline reachability |
| DRPDS-UTILITY-1-LOSS-001 | Remove T1-to-SWGR1 path | None | Alternate utility path remains in this abstract graph |
| DRPDS-CRITICAL-A-LOSS-001 | Remove path to Critical Bus A | None | Bus B remains an alternate path |
| DRPDS-CRITICAL-BOTH-LOSS-001 | Remove paths to buses A and B | CRIT-LOADS | Critical loads become unreachable; essential loads remain reachable |
| DRPDS-ESSENTIAL-BOTH-FEEDS-LOSS-001 | Remove both essential distribution feeds | ESS-LOADS | Essential loads become unreachable; critical path remains |
| DRPDS-INSTRUMENT-ERROR-001 | Instrument adapter reports error | None | Error is not accepted as a physical measurement |
| DRPDS-UNKNOWN-SATS-DETAIL-001 | Ask to localize a specific SATS/CDP failure | None | Missing per-device topology is reported |
| DRPDS-UNKNOWN-UPS-UNIT-001 | Ask to distinguish UPS 2 from UPS 3 | None | Aggregated UPS model is not falsely treated as unit-level topology |

## Static graph evaluation

The eight scenarios were evaluated against the committed graph and scenario JSON:

- all referenced source IDs exist;
- all referenced edge IDs exist;
- all eight expected affected-load sets match the reachability calculation;
- loss of both critical paths isolates only the critical load group;
- loss of both essential feeds isolates only the essential load group.

This is a deterministic graph calculation, not an executed pytest run. The new pytest file is committed for CI/local execution; runtime tests were not run in this work session.

## What this proves

The current runner can distinguish, at the graph-connectivity level, between:
- a single failed path with an alternate route still available;
- simultaneous loss of both modeled paths to a load group;
- insufficient topology detail for a requested device-level conclusion;
- an invalid instrument result that must not be treated as a measurement.

## What this does not prove

The runner does **not**:
- identify a root cause from symptoms;
- rank competing fault hypotheses;
- select the next diagnostic measurement;
- reason about voltage, current, frequency, phase, load, timing or protection settings;
- model breaker states, source quality, generator synchronization, UPS operating modes, battery autonomy or automatic transfer sequences;
- validate physical independence of the two paths;
- prove that a real DRPDS facility will behave like this generic graph.

The generic model aggregates multiple real devices into groups. In particular, the UPS units, PDU units, SATS units and CDP panels are not yet represented as individually wired instances. A device-level diagnosis must be blocked until site drawings, individual device identities, input/output relationships and event/measurement data are available.

## Next engineering increment

The next increment should not add more synthetic fault labels to this runner. It should define the diagnostic reasoning contract:

1. A symptom/observation with source, timestamp, quality and provenance.
2. A set of competing hypotheses, each with required and contradictory evidence.
3. A readiness check that lists missing graph facts before any measurement request.
4. A measurement request bound to a documented test point, approved procedure, instrument capability and authorization.
5. An explicit result interpretation that updates hypothesis support without treating a single observation as proof.

Only after that contract exists should DRPDS scenarios test hypothesis discrimination and measurement selection. Live electrical operation remains outside the runner.
