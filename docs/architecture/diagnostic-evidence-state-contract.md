# Diagnostic evidence-state contract

**Status:** interface/data contract proposal. It does not change the diagnostic engine, create measurements, or authorize field work.

Schema: `schema/diagnostic-evidence.schema.json`.
Validation API: `src/edi_ingest/evidence.py`.

## Purpose

A diagnostic question lists evidence requirements. The interface needs to show whether each requirement is known, observed, stale, unavailable, or contradicted without turning missing data into a healthy/faulty conclusion.

One record represents the current evidence state for one exact `evidence_key` belonging to one `question_id`. The key must match an item in that question's `required_evidence` list. This contract does not redefine those requirements.

## States

| State | Meaning | UI treatment |
|---|---|---|
| `unknown` | No observation has been recorded for this requirement. | Show as not yet known; do not infer a normal condition. |
| `unavailable` | An attempt to obtain the evidence was made, but it could not be obtained. Record the attempt time and reason. | Show unavailable, distinct from not yet checked. |
| `stale` | An observation exists but is outside the applicable freshness rule. | Retain and display the observation and the source/site-defined freshness basis; do not silently reuse it as current. |
| `contradicted` | Two or more observations conflict and the conflict has not been resolved. | Show all conflicting observations; do not average, choose the newest automatically, or hide one. |
| `observed` | At least one observation is recorded for the requirement. | Show its value and provenance. This state alone says nothing about whether the value is normal, abnormal, healthy, or faulty. |

## Observation and quality are separate

Each observation records its source reference, timestamp and quality:

- `valid`: the source's documented validity checks passed.
- `invalid`: the source or acquisition reports an invalid observation.
- `uncertain`: validity cannot be established.
- `not_assessed`: no validity assessment has been made.

An `observed` record may therefore contain an invalid or uncertain observation. The state answers whether evidence exists; quality answers whether that observation can be relied upon. Neither field is a diagnosis.

## Rules

1. Keep the original observations and provenance. A derived state must not erase its inputs.
2. `unknown` has no observations. `unavailable` has no observation and must include an attempt time and reason.
3. `stale` requires an observation and an explicit freshness basis. No universal time-to-live is defined here.
4. `contradicted` requires at least two observations and a reason identifying the unresolved conflict.
5. `observed` requires at least one observation, but does not assert that the observation is valid or that the equipment is healthy.
6. A state transition must preserve prior observations in the record/history layer. This schema describes the current snapshot; it does not prescribe storage or event sourcing.
7. An evidence record must satisfy the JSON Schema and refer to exactly one declared diagnostic question and one of that question's requirement keys. `validate_evidence_record()` performs both checks.
8. Do not derive a physical measurement point, equipment tag, threshold, freshness interval, or acceptance criterion from this contract.

## Validation API

`validate_evidence_record(record, dependency_model, schema)` is the combined integration boundary:

1. Validate the record against the Draft 2020-12 evidence JSON Schema, including date-time format checks.
2. Resolve `question_id` to exactly one question in the dependency model.
3. Require `evidence_key` to be an exact member of that question's `required_evidence` list.

The lower-level `validate_evidence_reference()` remains available when only cross-file linkage needs checking. Validation rejects malformed or undeclared references; it does not validate the engineering truth of an observation or establish a diagnosis.

The FAA DRPDS dependency model currently contains **53 questions and 276 declared evidence keys**. Tests enumerate all 276 declared links and cover schema failures, unknown questions, duplicate question IDs, and keys borrowed from another question.

## Deliberately out of scope

- Fault hypotheses, probabilities, posterior updates, or diagnostic conclusions.
- Automatic evidence collection and instrument control.
- Site-specific signal maps, measurement points, freshness policies, thresholds, and protection settings.
- Resolution policy for contradictory observations.
- Authorization for switching, testing, or live measurements.

## Interface acceptance checks

- Every required evidence row can be rendered in any of the five states.
- `unknown` and `unavailable` are visibly different.
- Stale observations remain visible with the basis for staleness.
- Contradictory observations remain side by side with their source and timestamps.
- An observed value is not styled or worded as a pass/fail result unless a separate, approved diagnostic rule establishes that result.
- A question with missing evidence is shown as insufficient evidence, not as a negative diagnosis.
