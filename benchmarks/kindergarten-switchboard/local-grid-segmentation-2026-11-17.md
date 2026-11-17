# Kindergarten switchboard — local grid segmentation follow-up

## Source and execution

- Source image: user-provided `1000055928.jpg`, 1536 × 1109 px.
- Tesseract: 5.5.0; languages `rus+eng`; whole-page OCR uses `--psm 11`.
- Geometry: current repository Hough/morphology implementation, run locally against the supplied image.
- The source JPEG is not committed to this repository.

## Why the previous method failed

The previous implementation joined every intersection sharing a detected horizontal or vertical segment ID. On this image, long merged lines span unrelated drawing areas. The 272 detected intersections therefore collapsed into one component, which was rejected as page-sized. No local line-grid candidate survived.

## Change in this iteration

Intersections are now connected only to their neighboring intersections along a shared segment. The allowed gap is derived from the median spacing on that segment (1.6×), capped at 25% of the corresponding page dimension. This keeps regularly spaced grid points together while splitting large gaps along long merged lines.

## Result on the supplied image

- Detected horizontal segments: 80.
- Detected vertical segments: 84.
- Intersection candidates: 272.
- Previous shared-segment grouping: 1 page-wide component; rejected.
- New local-neighbor grouping: 7 bounded grid candidates survived the existing size filters.
- Largest lower-page grid candidate:
  - bbox: `[434, 863, 1218, 1109]`
  - 72 intersections
  - 6 horizontal segments
  - 12 vertical segments
- A table-like proposal was produced for that lower-page candidate:
  - 28 whole-page OCR tokens fall inside the proposal
  - 7 horizontal text bands
- The OCR crop of the lower-page candidate still returns heavily corrupted text; this is localization progress, not successful table transcription.
- A second table-like proposal was also produced in the upper-right area (`[750, 174, 1157, 397]`, 44 intersections, 8 whole-page tokens, 5 text bands). This is a false-positive risk and demonstrates that the current table heuristic is not semantically specific.

## Interpretation

The change fixes the specific page-wide chaining failure and recovers a bounded lower-page grid around the load-table area. The result is not yet a verified table detection: the draft reference box `[300, 828, 1155, 1053]` is not independently reviewed ground truth, and the candidate extends to the bottom page edge. No precision, recall, or IoU is claimed.

## Remaining work

1. Improve the table-specific proposal to reject orthogonal equipment/control graphics such as the upper-right candidate.
2. Tighten the lower-page table boundary using row/column evidence rather than broad intersection extent.
3. Review the candidate boxes against independently annotated ground truth before reporting localization accuracy.
4. Improve OCR separately; the current lower-page crop does not yield usable load-table text.
5. Keep all geometry and table outputs as candidates. No electrical connectivity, equipment identity, or topology is inferred.

## Reproducibility limit

The JPEG remains outside the repository. The reported image experiment was run locally using the supplied attachment and current repository algorithms; it cannot be reproduced from the repository alone.
