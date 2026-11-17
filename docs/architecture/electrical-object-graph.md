# Electrical Object Graph — format 0.1

## Purpose

Represent an electrical installation as a partial graph extracted from diagrams. The graph is intended for diagnostic reasoning; it is not a replacement for the source drawing or an as-built inspection.

## Main entities

- **Source document** — original diagram/specification/protocol and page reference.
- **Component** — supply, busbar, protective device, switching device, meter, load, cable, etc.
- **Connection** — explicit relation between two components, with conductor and confidence.
- **Circuit** — logical outgoing circuit with its protective device, loads, cable and attributes.
- **Issue** — unresolved reading, missing link, contradiction or review item.

The normative field definitions are in `schema/electrical-object-model.schema.json`.

## Mandatory provenance

Every extracted component, connection and circuit must retain one or more source references. A source reference may include page, bounding box and recognized text. This makes it possible to trace a model value back to the exact place in the drawing.

## Unknowns and confidence

- `recognized`: directly legible in the source.
- `ambiguous`: a candidate reading exists but is not reliable.
- `unknown`: the source does not provide the value or relation.
- `inferred`: derived from explicit source facts; never presented as directly observed.

Confidence is a recognition estimate, not a probability that the electrical installation is physically correct.

## Graph integrity rules

1. Component IDs are unique.
2. Connection endpoints must refer to existing component IDs.
3. Circuit protective-device, load and cable references must resolve when non-null.
4. A missing protective-device reference is allowed only when the circuit status or an issue explains the uncertainty.
5. No inferred connection may be silently upgraded to recognized.
6. No absent value may be filled from typical practice.
7. Totals and derived quantities must retain their source or calculation provenance.

## Diagnostic readiness

A graph is not simply “complete” or “incomplete”. It is sufficient or insufficient **for a particular diagnostic question**. A scenario declares the graph facts it requires. The engine must identify missing prerequisites before proposing a measurement.

## Relationship to the existing diagnostic core

This model is an input/context layer. It does not replace `MeasurementRequest`, `MeasurementResult`, `InstrumentAdapter`, `SafetyGateway` or `Session`. Integration should map a scenario's requested observation to the existing measurement contracts after validating the required graph context and safety constraints.

## Connection domains

Connections carry a `connection_type` so that graph traversal does not conflate electrical energy paths with automation and evidence channels:

- `power` — normal power-distribution path;
- `auxiliary_power` — auxiliary supply for control or monitoring equipment;
- `control` — command/control path;
- `monitoring` — telemetry or status acquisition path;
- `control_monitoring` — a documented relationship that combines command and feedback/telemetry where the source does not separate the conductors;
- `test_power` — temporary or test-only power path.

The type describes the semantic role of the relationship, not its voltage, conductor, safety class, or physical wiring details. Those remain separate attributes and require source evidence. Do not infer a missing connection type from typical practice.
