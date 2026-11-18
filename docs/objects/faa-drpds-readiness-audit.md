# FAA DRPDS — diagnostic readiness and coverage audit

**Baseline:** merged PR #48; architecture-only model, not an installed facility.
**Sources in this repository:** `examples/objects/faa-drpds.generic.json`, `diagnostics/scenarios/faa-drpds-diagnostic-dependencies.v0.1.json`, `diagnostics/scenarios/faa-drpds-core-crosswalk.v0.1.json`.

## 1. What is actually available

| Layer | Current inventory | What it demonstrates |
|---|---:|---|
| Generic electrical object graph | 29 components, 36 connections | Historical FAA functional architecture with source references; not an as-built one-line |
| Diagnostic dependency model | 44 questions | Evidence prerequisites and limits on conclusions; not executable causal hypotheses |
| Architecture-to-synthetic crosswalk | 44 mappings | Traceability of software-only analogue coverage |
| Crosswalk coverage: partial | 7 questions | Simplified virtual endpoint/evidence patterns only |
| Crosswalk coverage: none | 37 questions | No synthetic analogue for that question |
| Crosswalk coverage: full | 0 questions | No architecture question has validated full diagnostic coverage |
| Generic graph open issues | 5 | Site evidence and engineering limitations recorded in graph |

**Interpretation:** 7/39 is **not** a 17.9% diagnostic success rate or field readiness score. A partial mapping is not a validated fault diagnosis. The crosswalk is not executable and does not itself create measurement requests.

## 2. Readiness gates for interface trials

| Gate | Status | Evidence / next action |
|---|---|---|
| Display generic graph and distinguish family nodes from installed instances | Architecture data available; UI unverified | Show 29 components/36 connections with provenance; never imply a verified site diagram |
| Browse a diagnostic question and its evidence prerequisites | Architecture data available; UI unverified | Present all 44 questions and prerequisite relationships, including conditional branches |
| Show unsupported/unknown evidence explicitly | Required; UI unverified | `coverage:none`, missing equipment mapping and missing observations must remain unknown |
| Exercise real diagnostic core on virtual observations | Synthetic integration available | Existing real-core tests; virtual 0–5.5 V signals are not FAA voltages |
| Diagnose an installed FAA facility | **Blocked** | Current site drawings, equipment/feeder tags, approved measurement points, signal map, settings, validated failure modes and likelihoods required |
| Field switching or live electrical measurements | **Not authorized by this model** | Requires approved procedures and qualified personnel; no field plan is provided |

**MVP decision:** An interface demonstration can proceed using architecture navigation, prerequisite inspection, missing-evidence states, and the existing synthetic core fixture. Do not wait for a site-specific feeder map merely to demonstrate those interactions. Do not present the synthetic fixture as a simulation of actual switchgear operation.

## 3. Suggested deterministic interface acceptance cases

These are *display and state-handling* cases, not electrical diagnosis validation:

1. Select `DQ-ESSENTIAL-FEED`; the UI shows feeder, MCC/control, and load-response prerequisites separately, with no invented feeder identifiers.
2. Select `DQ-SWGR-STANDBY-TRANSFER`; show the chain of source, transformer, generator, control power, mode, permissives, and breaker actuation. If evidence is missing, show **insufficient evidence**, not “transfer succeeded” or “failed”.
3. Select `DQ-SATS-DUAL-INPUT-AVAILABILITY`; show both source assignments as **site mapping required** until documented. Two aggregate inputs are not a pair map.
4. Select `DQ-COMMERCIAL-SOURCE-INDEPENDENCE`; labels U1/U2 are not accepted as proof of physical independence.
5. Select `DQ-ESSENTIAL-LOAD-SHED-RESTORE`; require event-time generator capacity and site load-priority criteria; do not use historical generator count as a threshold.
6. Select any `coverage:none` question; display “no synthetic coverage”, not “no fault”.
7. For a partial synthetic analogue, show that the virtual mode does not localize the listed physical failure hypotheses.
8. Select `DQ-UPS-HEALTH`; show the UPS input feeder, rectifier/inverter, bypass and DC/battery evidence as separate prerequisites. Output voltage alone must not be displayed as proof of inverter operation or battery autonomy.

## 4. Priority gaps before advancing beyond architecture UI

**P0 — Block field claims:** current site one-lines, installed device and feeder assignments, approved observation methods, protection/interlock/control documentation, and signal source/quality records. These are missing by design from the generic model.

**P1 — Needed for useful interactive diagnosis:** an explicit evidence-state contract (unknown, unavailable, stale, contradicted, observed) and UI representation of prerequisite traversal. The current JSON contains requirements but not measured site evidence.

**P2 — Expand synthetic tests selectively:** exercise *software handling* of missing, conflicting and stale evidence without inventing FAA equipment behavior or converting architecture questions into physical fault probabilities.

## 5. Audit rules

- Every dependency refers to an existing question; all question component references must resolve to the generic graph.
- Each question has exactly one crosswalk mapping, with only declared synthetic modes.
- Prerequisite graph is acyclic.
- No crosswalk `none` mapping may claim synthetic modes.
- Source labels, family counts and functional observation templates do not establish site wiring or physical terminals.

The accompanying tests enforce these machine-checkable invariants. Passing tests do **not** verify installed topology, electrical safety, or diagnostic accuracy.
