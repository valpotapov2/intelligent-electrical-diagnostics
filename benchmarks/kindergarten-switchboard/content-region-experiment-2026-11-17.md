# Kindergarten switchboard — content-aware region experiment

## Source and execution

- Source image: user-provided `1000055928.jpg`, 1536 × 1109 px.
- Tesseract: 5.5.0; languages `rus+eng`; whole-page and region OCR use `--psm 11`.
- Region OCR scale: 3×.
- The experiment was run locally against the attached image, reproducing the algorithms and parameters from the merged `main` implementation. It was not a packaged CLI run from a checked-out repository.
- The source JPEG is still not committed to this repository.

## Proposal counts

| Proposal type | Count |
|---|---:|
| OCR text blocks | 36 |
| Line-grid regions | 1 |
| Graphic-shape clusters | 12 |
| **Total regions sent to OCR** | **49** |

Whole-page OCR produced 200 non-empty tokens (98 with confidence >= 50). The 49 content regions produced 606 non-empty token observations in aggregate. Region totals are not unique tokens: regions overlap, and some proposals substantially overlap.

## What the proposals found

### Incoming equipment group

One graphic cluster was found near the incoming-device area:

- ID: `shape-cluster-2`
- bbox: `[1060, 45, 1240, 170]`
- 4 shape candidates
- Enlarged OCR fragments: `3€200`, `88-35`, `BABB`, `35KA`, `км!`

This is a useful coarse localization of the incoming equipment group, but the OCR remains too confused to reliably recover `1QF`, `2QF`, `BA88-35` or `KM1`. It is not a validated component detection.

### Load table

The algorithm did **not** isolate the load table as its own region.

A large cluster, `shape-cluster-8`, had bbox `[297, 518, 1018, 1109]` and 23 shape candidates. It includes a broad lower drawing area and is not a table-specific proposal. Other lower-page clusters were also fragmented. The line-grid proposal was `[4, 4, 1528, 1109]`, effectively the whole page, because drawing-frame and other line intersections satisfy the current threshold.

The table's coarse visual reference box in the draft annotation is `[300, 828, 1155, 1053]`. That box is not independently reviewed ground truth; it is used here only to explain the observed localization failure.

## Result

The experiment demonstrates one useful improvement: shape density can localize the incoming-device cluster approximately. It does not yet produce reliable table localization, and it does not materially improve the difficult incoming tags.

The current line-grid rule is too permissive for this drawing. The connected-component clustering is also susceptible to chain-link merging: a sequence of nearby candidates can create a very large region even when the full group is not one semantic object.

## Required next corrections

1. Replace the single page-wide grid proposal with bounded connected grid components or candidate rectangular cell groups; reject regions close to the page frame.
2. Split shape clusters when their resulting bounding box becomes disproportionately large relative to member density; avoid unconstrained chain-link merging.
3. Add a table-specific proposal based on repeated row/column separators and text alignment, with a strict bbox and cell-grid evidence.
4. Evaluate region proposals against reviewed boxes before tuning OCR. Report localization overlap separately from OCR string correctness.
5. Keep all outputs as candidates; do not infer equipment class, terminals, electrical connectivity or topology.

## Measurement limits

- No independently reviewed token-level or region-level ground truth was used.
- Precision, recall and IoU are therefore not reported.
- OCR confidence is not a substitute for correctness.
- The image itself remains outside the repository, so this result is not independently reproducible from the repository alone.
