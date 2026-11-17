# Kindergarten switchboard — local grid segmentation follow-up

## Source and execution

- Source image: user-provided `1000055928.jpg`, 1536 × 1109 px.
- Tesseract: 5.5.0; languages `rus+eng`; whole-page OCR uses `--psm 11`.
- Geometry: current repository Hough/morphology implementation, run locally against the supplied image.
- The source JPEG is not committed to this repository.

## Why the previous method failed

The previous implementation joined every intersection sharing a detected horizontal or vertical segment ID. On this image, long merged lines span unrelated drawing areas. The 272 detected intersections therefore collapsed into one component, which was rejected as page-sized. No local line-grid candidate survived.

## Change in this iteration

Intersections are now connected only to their neighboring intersections along a shared segment. The allowed gap is derived from the median spacing on that segment (1.6×), capped at 50% of the corresponding page dimension. This keeps regularly spaced grid points together while splitting large gaps along long merged lines.

## Result on the supplied image

- Detected horizontal segments: 80.
- Detected vertical segments: 84.
- Intersection candidates: 272.
- Previous shared-segment grouping: 1 page-wide component; rejected.
- New local-neighbor grouping: 8 bounded grid candidates survived the existing size filters.
- Largest lower-page grid candidate:
  - bbox: `[434, 863, 1218, 1109]`
  - 72 intersections
  - 6 horizontal segments
  - 12 vertical segments
- The table-specific filter now requires at least five detected horizontal rules in addition to repeated OCR text bands.
- After the filter, exactly one table candidate remains: `[434, 863, 1218, 1109]`.
- That candidate contains 28 whole-page OCR tokens in 7 horizontal text bands, and its underlying grid has 6 horizontal and 12 vertical segments.
- The upper-right candidate (`[758, 182, 1149, 389]`) has only 4 horizontal segments and is no longer promoted to a table candidate.
- The lower candidate is still an incomplete crop: it misses the leftmost portion and upper header row of the visible table. The OCR crop remains heavily corrupted. This is coarse localization, not successful table extraction.

## Interpretation

The change fixes page-wide chaining and the added row-count filter removes the observed upper-right false positive. One lower-page table candidate remains, but its bounding box is incomplete. The draft reference box `[300, 828, 1155, 1053]` is not independently reviewed ground truth. This is a useful first-pass localization only; no precision, recall, or IoU is claimed.

## Remaining work

1. Tighten the lower-page table boundary to include the leftmost columns and upper header row.
2. Reconstruct rows, columns, and cell boundaries.
3. Improve OCR separately; the current lower-page crop does not yield usable load-table text.
4. Review candidate boxes against independently annotated ground truth before reporting localization accuracy.
5. Keep all geometry and table outputs as candidates. No electrical connectivity, equipment identity, or topology is inferred.

## Reproducibility limit

The JPEG remains outside the repository. The reported image experiment was run locally using the supplied attachment and current repository algorithms; it cannot be reproduced from the repository alone.
