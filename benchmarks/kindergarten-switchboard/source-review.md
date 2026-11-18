# Kindergarten switchboard — source review v1

## Source and status

- Source drawing: `1000055928.jpg`, raster image supplied in the project conversation.
- Image dimensions: 1536 × 1109 px.
- This review is a human-readable transcription of visible source labels and table values. It is not an as-built inspection and is not an approved electrical design.
- The existing `ground-truth.draft.json` remains a coarse annotation draft. Its bounding boxes are not independently audited.
- The source JPEG is still not committed in this repository. The review records what was read from the supplied image; it does not make the OCR experiment reproducible without the image.

## Visible single-line structure

- Switchboard designation: ВРУ.
- Supply arrangement: two incoming supplies, each marked 380/220 V.
- Automatic transfer arrangement: АВР between two contactors.
- Incoming protective devices: 1QF and 2QF; markings read as 3C200, ВА88-35, 35 kA.
- Contactors: KM1 and KM2, each marked 200 A.
- Meter: Меркурий 230 AR, marking 5(60).
- Current transformers: TA1–TA3, 100/5.
- Distribution system: TN-C-S.
- Bus labels: L1/L2/L3, N and PE.
- Ten outgoing protective devices are drawn and labelled QF1–QF10.

## Incoming summary printed on the drawing

| Field | Printed value |
|---|---:|
| Installed power (Ру) | 223.21 kW |
| Calculated power (Рр) | 115.64 kW |
| Calculated current (Ip) | 176 A |

These are source transcriptions, not recalculated or independently verified engineering values.

The eleven displayed installed-power values sum arithmetically to **223.22 kW**, while the drawing's printed summary reads **223.21 kW**. Preserve both source values and record this 0.01 kW discrepancy; do not silently overwrite either. The sum of the displayed calculated-current values is 175.68 A, while the drawing's printed summary reads 176 A (consistent with rounding to a whole ampere, but not proof of the underlying calculation method).

## Outgoing protective-device labels

The following ratings are transcribed from the labels next to the drawn outgoing devices. The exact manufacturer/type strings should be checked against a higher-resolution source before being treated as equipment identity.

| Device | Readable current marking |
|---|---:|
| QF1 | C25 |
| QF2 | C25 |
| QF3 | C25 |
| QF4 | C32 |
| QF5 | C10 |
| QF6 | C10 |
| QF7 | 1C10 (single-pole marking) |
| QF8 | 1C10 (single-pole marking) |
| QF9 | C80 |
| QF10 | C10 |

The labels also appear to show 4.5 kA and ВА47-29 for the outgoing devices; retain these as provisional readings until checked against the original device schedule or a sharper scan.

## Load schedule transcription

The table has plan positions 1–12. Positions 1–11 contain values; position 12 is blank in the shown power/current rows.

| Plan position | Installed power, kW | Calculated current, A |
|---:|---:|---:|
| 1 | 25.88 | 16.52 |
| 2 | 38.93 | 19.80 |
| 3 | 45.26 | 24.55 |
| 4 | 53.07 | 29.86 |
| 5 | 4.09 | 3.18 |
| 6 | 1.65 | 2.51 |
| 7 | 2.60 | 3.95 |
| 8 | 1.37 | 2.07 |
| 9 | 0.50 | 0.47 |
| 10 | 47.37 | 68.97 |
| 11 | 2.50 | 3.80 |
| 12 | — | — |

The source table's rows for starting current and mechanism name are not filled in.

## Open interpretation issues

1. **Feeder/load count is now explained by the SVG.** There are ten outgoing breakers and eleven populated plan positions because QF4 has a drawn branch to the separate plan-position-5 load ЩОЧ (labelled “Чердачное помещение”). This is not evidence of an omitted eleventh breaker.
2. **QF9 C80.** The visible SVG marking reads 3C80. This is a drawing transcription, not confirmation of the installed device.
3. **Physical implementation.** The drawing does not prove that the real panel matches the design, that the devices are currently installed, or that the circuit is energized as drawn.
4. **Terminal-level graph.** The SVG gives explicit drawn line geometry and supports feeder-level relationships. It does not establish all internal device terminals, hidden junction semantics, or as-built wiring. Preserve those as unverified until separately reviewed.

## Modeling rules for the benchmark

- Preserve source text, normalized interpretation, source coordinates and review status separately.
- Keep all load schedule values as source-transcribed candidates until cell-level review.
- Preserve eleven load positions and ten QF devices as separate entity sets; the SVG-derived mapping links positions 1–4 to QF1–QF4, positions 5 as a branch from QF4, and positions 6–11 to QF5–QF10.
- Represent unresolved links as issues or unknown relations; do not fill them using typical wiring practice.
- Treat the model as an offline diagnostic-software benchmark only. It is not authorization to measure or operate the live switchboard.
- Any future measurement scenario must pass a qualified electrical safety review and the project's SafetyGateway; this source review does not define safe live test points.


## Machine-graph scope boundary

The current machine-readable graph models the ten outgoing feeder circuits QF1–QF10, including the QF4 branch to plan position 5. It does **not** yet model the incoming protective devices 1QF/2QF or the upstream power-path connections involving the two supplies, ATS and contactors KM1/KM2. Their visible labels and ratings are transcribed above, but no incoming-side topology should be inferred from their omission in the graph. This is a graph-coverage limitation, not evidence that the equipment is absent from the source drawing.

## Load-schedule value provenance

The machine graph stores installed-power and calculated-current values for plan positions 1–11. The current component source boxes identify the plan labels below the diagram (for example, Щр1), not the corresponding numeric cells in the load-schedule table. The values are transcribed in this review, but cell-level source coordinates have not yet been recorded in the graph. Do not treat the existing component bbox as coordinate evidence for those numeric attributes; preserve the values while this provenance gap remains open.
