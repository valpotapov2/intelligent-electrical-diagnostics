# Shape candidate extraction

## Implemented

- Closed-contour extraction from rasterized pages.
- Geometric descriptors: bounding box, center, area, perimeter, aspect ratio, circularity and polygon vertex count.
- Broad shape families: circular, quadrilateral, rectangular, polygonal and irregular closed outlines.
- Suppression of candidates substantially overlapping OCR token boxes.
- Nested contour suppression to reduce duplicate candidates.

## Explicitly not claimed

This stage does not recognize a circuit breaker, contactor, current transformer, meter, relay, switch or any other electrical component. A circle or rectangle is only a geometric shape candidate. The result has no electrical type, terminal positions, pin count or connectivity.

## Known limitations

- Symbols drawn as open paths or assembled from disconnected strokes may not form a closed contour.
- Connected conductors can merge with a symbol contour.
- Tables, callout frames and decorative drawing elements can resemble symbol outlines.
- OCR-based text suppression can remove a genuine shape if a text box overlaps it.
- Native PDF vector primitives are retained by ingestion, but this detector currently operates on the raster page.
