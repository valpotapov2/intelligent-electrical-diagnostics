# Geometry extraction — prototype status

## Implemented

- Adaptive thresholding of raster pages.
- Morphological extraction of long horizontal and vertical strokes.
- Probabilistic Hough line-segment candidates.
- Duplicate/overlapping Hough fragments are merged into normalized axis-aligned segments.
- Intersections are derived from normalized horizontal/vertical segment extents.
- Native PDF vector line and rectangle primitives are retained separately in PDF-point coordinates.
- Pixel coordinates retained in page coordinate space.
- Synthetic tests for orthogonal lines and blank images.

## Not implemented

- Distinguishing electrical conductors from table borders, dimension lines or symbol strokes.
- Detecting junction dots and bridge/no-connect conventions robustly.
- Connecting line segments across gaps.
- Detecting component terminals and attaching wires to them.
- Determining net identity or phase/neutral/PE semantics.
- Creating confirmed electrical graph edges.

## Safety of interpretation

All outputs are labelled candidates. A crossing is not assumed to be a junction. A detected line is not assumed to be a conductor. The next stage must combine geometry with symbol/terminal recognition and source review before promoting any candidate to a confirmed connection.
