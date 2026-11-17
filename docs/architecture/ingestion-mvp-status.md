# OCR ingestion MVP — implementation status

## Implemented

- PDF rasterization using PyMuPDF.
- Raster image loading using Pillow.
- Tesseract OCR with configurable language, DPI and page segmentation mode.
- Word-level OCR tokens with bounding boxes and confidence values.
- Deterministic regex extraction of common diagram references: QF, KM, TA, busbar labels and АВР.
- Draft model JSON output with source document metadata and provenance for extracted candidates.
- Explicit issue stating that topology construction is not implemented.

## Not implemented

- Symbol detection by image shape.
- Wire and junction tracing.
- Electrical connection graph.
- Schedule/table extraction and association to circuits.
- Robust symbol/label association.
- Validation against the full JSON Schema.
- OCR accuracy benchmark on the kindergarten drawing.

## Why this boundary is deliberate

OCR recognition of a text label does not prove that the nearby symbol is a breaker or that a line is electrically connected. The MVP therefore emits candidates and provenance, while leaving connections empty until geometric topology processing exists.
