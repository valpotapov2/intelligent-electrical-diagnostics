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
| QF2 | C32 |
| QF3 | C32 |
| QF4 | C32 |
| QF5 | C10 |
| QF6 | C10 |
| QF7 | C10 |
| QF8 | C10 |
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

1. **Ten outgoing breakers versus eleven populated load positions.** The drawing alone does not establish a one-to-one mapping between QF1–QF10 and plan positions 1–11. Do not synthesize a missing breaker or merge two loads.
2. **Branch labelled “Чердачное помещение”.** A branch/connection is drawn near the fourth outgoing feeder area, but its exact electrical association and whether it is a separate load position are not resolved in this review.
3. **Cable inscriptions and lengths.** Cable text is present beside the outgoing lines, but must be transcribed and aligned to feeder IDs in a separate coordinate-based review. Do not infer feeder identity from proximity alone.
4. **QF9 C80.** The visible marking reads C80. This is a drawing transcription, not confirmation of the installed device.
5. **Physical implementation.** The drawing does not prove that the real panel matches the design, that the devices are currently installed, or that the circuit is energized as drawn.
6. **Connection graph.** No electrical connection should be marked as validated solely because raster lines touch or cross. Junctions, device terminals and bus connections need explicit trace review.

## Modeling rules for the benchmark

- Preserve source text, normalized interpretation, source coordinates and review status separately.
- Keep all load schedule values as source-transcribed candidates until cell-level review.
- Keep the eleven load positions separate from the ten QF devices until the feeder-to-load association is established.
- Represent unresolved links as issues or unknown relations; do not fill them using typical wiring practice.
- Treat the model as an offline diagnostic-software benchmark only. It is not authorization to measure or operate the live switchboard.
- Any future measurement scenario must pass a qualified electrical safety review and the project's SafetyGateway; this source review does not define safe live test points.
