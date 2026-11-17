# Kindergarten switchboard — SVG geometry review v1

## Source

- File: `schema.svg`, supplied in the project conversation.
- SVG viewBox: `0 0 1280 925`.
- This review reads the actual SVG XML: text nodes, line endpoints and polylines. It does not infer connections from a raster image alone.
- The SVG is a redrawn/structured representation supplied for review. It is not proof of as-built wiring or device terminal internals.

## Key result: why there are 10 breakers and 11 load positions

The SVG explicitly draws ten outgoing breaker columns and their downstream lines. QF4 has a branch: its vertical feeder at x=516 continues to plan-position 4 (Щр4) and branches horizontally at y=598 to x=578, ending at the plan-position-5 symbol ЩОЧ, labelled “Чердачное помещение”.

Therefore the eleven populated plan positions are explained by ten breakers: QF4 feeds two downstream loads in the drawing. No missing eleventh breaker needs to be invented.

## Feeder-to-load mapping visible in SVG

| Breaker | SVG feeder x | Plan position | Plan label | Installed power, kW | Calculated current, A | Relationship |
|---|---:|---:|---|---:|---:|---|
| QF1 | 343 | 1 | Щр1 | 25.88 | 16.52 | Direct |
| QF2 | 400 | 2 | Щр2 | 38.93 | 19.80 | Direct |
| QF3 | 458 | 3 | Щр3 | 45.26 | 24.55 | Direct |
| QF4 | 516 | 4 | Щр4 | 53.07 | 29.86 | Main branch |
| QF4 | 516 → 578 | 5 | ЩОЧ, Чердачное помещение | 4.09 | 3.18 | Branch from QF4 |
| QF5 | 632 | 6 | ЩУВ 1 | 1.65 | 2.51 | Direct |
| QF6 | 690 | 7 | ЩУВ 2 | 2.60 | 3.95 | Direct |
| QF7 | 748 | 8 | ЩАО | 1.37 | 2.07 | Direct |
| QF8 | 806 | 9 | ЯПТ | 0.50 | 0.47 | Direct |
| QF9 | 864 | 10 | ЩПБ | 47.37 | 68.97 | Direct |
| QF10 | 922 | 11 | ЩСБ | 2.50 | 3.80 | Direct |
| — | — | 12 | blank | — | — | No feeder/load symbol shown |

The plan labels are transcribed as drawn. Their expansions and functional meanings are not defined in the SVG and should not be guessed.

## Outgoing breaker labels

| Breaker | Pole/current marking read from SVG | Breaking-capacity/type text |
|---|---|---|
| QF1 | 3C25 | 4.5 kA, BA47-29 |
| QF2 | 3C25 | 4.5 kA, BA47-29 |
| QF3 | 3C25 | 4.5 kA, BA47-29 |
| QF4 | 3C32 | 4.5 kA, BA47-29 |
| QF5 | 3C10 | 4.5 kA, BA47-29 |
| QF6 | 3C10 | 4.5 kA, BA47-29 |
| QF7 | 1C10 | 4.5 kA, BA47-29 |
| QF8 | 1C10 | 4.5 kA, BA47-29 |
| QF9 | 3C80 | 4.5 kA, BA47-29 |
| QF10 | 3C10 | 4.5 kA, BA47-29 |

This corrects the earlier rough transcription: QF2 and QF3 read 3C25 (not 3C32); QF7 and QF8 read 1C10; QF9 reads 3C80.

## Outgoing cable inscriptions

All ten outgoing cable labels are placed beside their corresponding vertical feeder columns in the SVG.

| Feeder | Cable inscription | Length |
|---|---|---:|
| QF1 | ВВГнг(A)-LSLTx 5×4 | 10 m |
| QF2 | ВВГнг(A)-LSLTx 5×4 | 15 m |
| QF3 | ВВГнг(A)-LSLTx 5×4 | 26 m |
| QF4 | ВВГнг(A)-LSLTx 5×4 | 30 m |
| QF5 | ВВГнг(A)-LSLTx 5×1.5 | 15 m |
| QF6 | ВВГнг(A)-LSLTx 5×1.5 | 15 m |
| QF7 | ВВГнг(A)-LSLTx 5×1.5 | 10 m |
| QF8 | ВВГнг(A)-LSLTx 5×1.5 | 5 m |
| QF9 | ВВГнг(A)-LSLTx 5×25 | 21.5 m |
| QF10 | ВВГнг(A)-LSLTx 5×1.5 | 33.8 m |

The type string is preserved as rendered in the SVG. Confirm exact cable nomenclature against the original project specification before engineering use.

## Incoming cables

| Input | Cable inscription | Length |
|---|---|---:|
| Ввод 1 | ВВГнг(A)-LSLTx 4×70 | 9.8 m |
| Ввод 2 | ВВГнг(A)-LSLTx 4×70 | 9.8 m |

Both are labelled approximately 380/220 V in the drawing.

## Geometry observations

- Main horizontal bus lines are drawn at y=292 (L1/L2/L3), y=315 (N) and y=323 (PE) in the SVG coordinate system.
- Outgoing feeder columns start at the phase bus at y=292 and continue through the breaker symbols to the lower distribution/plan area.
- The QF4 branch is explicit geometry: x=516 from y=612 to y=598, then x=516 to x=578 horizontally.
- Dashed horizontal lines at y=577 and y=660 are floor-level separators (“2-й этаж” and “1-й этаж”), not electrical conductors.
- The plan-position-5 symbol is placed on the second-floor band and is labelled ЩОЧ / “Чердачное помещение”.

## What this SVG does and does not prove

It supports a feeder-level graph for the drawn outgoing lines and resolves the apparent count mismatch. It does not establish:
- actual wiring in the physical switchboard;
- hidden terminal connections inside breakers, contactors, ATS or loads;
- whether line crossings not represented as explicit branch geometry are electrical junctions;
- device condition, actual installed ratings, conductor condition or safe test points.

Keep this as a source-derived diagram graph with provenance, not an as-built certification or permission to perform live measurements.
