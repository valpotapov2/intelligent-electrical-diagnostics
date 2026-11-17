# Kindergarten switchboard — benchmark v0.1

## Source

A user-supplied single-page electrical switchboard schematic (1536 × 1109 px, JPEG). It is the first real-world benchmark for diagram ingestion.

The source image is intended to be stored at `benchmarks/kindergarten-switchboard/source.jpg`. The image is available in the originating ChatGPT conversation, but the GitHub connector used for this change does not expose a binary upload operation. Therefore the image is **not yet committed**; do not treat this path as present until a later binary upload is verified.

## Benchmark purpose

Measure, on one real drawing, what the ingestion pipeline extracts before implementing electrical-semantic recognition:

1. OCR token recall for equipment tags, ratings, bus labels and load-table values.
2. Geometric candidate recall for visible closed outlines and line segments.
3. Correctness of object grouping and page coordinates.
4. False positives caused by table borders, labels and conductor crossings.
5. Whether topology claims are supported by the drawing or remain unresolved.

## Drawing inventory — human visual transcription

### Supply and switching

- Drawing identifies the assembly as `ВРУ`.
- Two incoming protective devices are labelled `1QF` and `2QF`.
- Both incoming devices show `3C200`, `BA88-35` / `ВА88-35`, and `35 кА` in the raster; exact manufacturer/type spelling needs OCR/manual confirmation.
- Switching devices are labelled `KM1` and `KM2`, each marked `200 A`.
- An `АВР` block is drawn between the two switching paths.

### Metering and distribution

- Meter text appears as `Меркурий 230 AR`, with `5(60)`.
- Current transformers are labelled `TA1–TA3`, ratio `100/5`.
- System marking: `TN-C-S`.
- Bus labels: `L1, L2, L3`, `N`, `PE`.
- Ten outgoing protective devices are visible, labelled `QF1`–`QF10`.
- Earthing symbol and N/PE separation are shown. Exact electrical connectivity must be established from line geometry and junction evidence, not inferred from visual proximity alone.

### Summary values printed on drawing

- `Py = 223.21 kW` (printed as 223,21)
- `Pp = 115.64 kW` (printed as 115,64)
- `Ip = 176 A`
- System: `TN-C-S`

### Load table

Values below are transcribed visually. They are reference labels, not independently recalculated values.

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
| 12 | blank | blank |

Position 12 is blank in the visible power/current rows. Do not synthesize a load.

## Annotation policy

Every annotation must carry:
- page number (1-based);
- bounding box in source-image pixel coordinates `[x1, y1, x2, y2]`;
- observed text exactly as read, if any;
- class and status;
- evidence/source (visual transcription, OCR, vector geometry, or reviewer confirmation);
- confidence or `null`;
- unresolved questions.

Allowed statuses:
- `observed`: directly legible or visually unambiguous;
- `ambiguous`: multiple plausible readings;
- `not_readable`: present but not legible;
- `inferred`: derived from other evidence; never present as observed;
- `not_annotated`: not yet reviewed.

Do not label generic circles/rectangles as electrical devices without symbol-level evidence. Do not treat line intersections as junctions unless a junction dot, T-connection, or other explicit convention supports it.

## Next benchmark tasks

1. Commit the original source JPEG to this directory.
2. Run `edi-ingest` on the source and retain raw OCR and geometry outputs.
3. Create coordinate-grounded object annotations for the incoming devices, ATS, meter/CTs, busbars, outgoing devices and load table.
4. Review uncertain tags and ratings manually.
5. Compare automated extraction with the reviewed annotations; publish precision/recall by class and OCR exact-match rate.
6. Only then implement semantic symbol classification and topology reconstruction.

## Known transcription cautions

- Some type strings around `1QF`/`2QF` are small and visually ambiguous.
- The outgoing device labels/rating text should be verified at higher zoom.
- The table contains a visually read value `68.97 A` for position 10; preserve it as a source transcription and flag for review rather than correcting it.
