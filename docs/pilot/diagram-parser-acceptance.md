# Acceptance criteria: diagram-to-model MVP

The kindergarten distribution-board drawing is the first regression fixture.

## Functional acceptance

- Accept a PDF or raster image of a single-line diagram.
- Preserve the original source and page coordinates.
- Extract component labels, visible ratings, circuit schedule rows and cable annotations.
- Emit a graph conforming to `schema/electrical-object-model.schema.json`.
- Every extracted entity has source provenance.
- Ambiguous labels and connections are explicitly marked.
- Contradictions between schedule and drawing become issues.
- Partial extraction is allowed; the parser must not invent missing data.
- Produce a scenario-specific readiness report.

## Regression checks for the kindergarten drawing

The first fixture should preserve these user-provided/source-derived facts:
- 3-phase, 380/220 V, 50 Hz, TN-C-S;
- two incoming supplies and ATS;
- KM1/KM2 shown as 200 A;
- TA1–TA3 ratio 100/5;
- Mercury 230 AR meter marking;
- busbars L1/L2/L3/N/PE;
- schedule groups 1–11 populated, column 12 blank;
- drawing visually shows QF1–QF10;
- installed-power sum 223.22 kW from visible group values vs diagram total 223.21 kW;
- calculated-current sum 175.68 A vs diagram total 176 A.

The mismatch between 11 populated groups and 10 visible group protective devices must remain an open issue unless the source drawing is clarified.

## Non-functional acceptance

- Deterministic validation results for the same extracted JSON.
- No hidden assumption that the design drawing equals the as-built installation.
- No client-facing instruction to open an energized board or perform electrical measurements.
- Parser uncertainty must be visible to a reviewing electrician.

## Not an MVP acceptance claim

Passing these checks does not prove safe operation, code compliance, complete topology recovery or diagnostic accuracy on arbitrary electrical drawings.
