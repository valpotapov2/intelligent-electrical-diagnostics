# Diagram ingestion pipeline

## Target user experience

The electrician uploads an electrical diagram. The system produces a preliminary model automatically. No full manual questionnaire is required to start.

## Pipeline

1. **Ingest** — preserve the original file, hash it, identify format and pages.
2. **Preprocess** — render PDF/vector pages, deskew raster images, normalize resolution while retaining the original coordinates.
3. **Extract text** — OCR labels, designations, ratings, cable markings and schedule cells.
4. **Detect symbols** — identify candidate protective devices, contactors, meters, busbars, loads and terminals.
5. **Trace topology** — detect wires/bus lines and junctions; build candidate connection paths.
6. **Associate labels** — connect text and schedule rows to symbol candidates using geometry and electrical context.
7. **Normalize** — map recognized symbols and labels to canonical component kinds and attributes, retaining the original text.
8. **Build graph** — emit components, connections and circuits using the graph schema.
9. **Validate** — check IDs, references, topology consistency, schedule totals and unresolved contradictions.
10. **Assess scenario readiness** — determine whether the graph supports a specific diagnostic scenario.
11. **Ask only blocking questions** — ask the electrician only when an unknown prevents the next safe and justified step.

## Extraction strategy

Use a staged hybrid approach rather than one opaque “understand the whole drawing” call:
- text/OCR extraction;
- symbol detection;
- geometric line/junction tracing;
- domain-specific association and consistency checks;
- optional vision-language review for difficult regions;
- deterministic graph validation.

All candidate detections must preserve provenance and confidence. A model-generated guess is not a confirmed connection.

## Failure handling

- unreadable label → ambiguous/unknown attribute;
- uncertain line crossing → do not assume a junction;
- missing connection endpoint → unresolved connection issue;
- conflicting schedule and diagram → preserve both source claims and open a contradiction issue;
- absent protective device → null reference plus issue, not an invented breaker;
- low-quality input → return partial model and explain which regions could not be parsed.

## MVP boundary

First MVP should handle clean single-line diagrams with:
- supply and busbars;
- breakers and switching devices;
- outgoing feeders;
- cable and load schedule tables;
- explicit source references and unresolved issues.

Complex control wiring, multi-page cross-references, automatic code compliance and as-built verification are out of scope for the first MVP.
