# Kindergarten switchboard — ROI OCR follow-up

## Run conditions

- Source: user-provided `1000055928.jpg`, 1536 × 1109 px.
- Tesseract 5.5.0, languages `rus+eng`, `--psm 11`.
- Five overlapping regions from `src/edi_ingest/roi.py`, each enlarged 3×.
- Token boxes mapped back to source-page pixel coordinates.
- This was a local run of the same ROI procedure against the attached image; the image itself is not committed to the repository.

## Results

| Region | Non-empty tokens | Confidence >= 50 |
|---|---:|---:|
| top_left | 60 | 44 |
| top_right | 57 | 17 |
| middle_left | 69 | 34 |
| middle_right | 58 | 12 |
| bottom_full | 52 | 23 |
| **Sum across regions** | **296** | **130** |

The sums are not unique page-token counts: the regions overlap, so the same printed text can be recognized more than once.

For comparison, whole-page PSM 11 on the same image produced 200 non-empty tokens, 98 with confidence >= 50. This is not a direct accuracy comparison because ROI crops cover overlapping portions and produce duplicate observations.

## Equipment/text observations

The top-right ROI recovered readable fragments including:
- `KM2`
- `АВР` (OCR token includes a leading bracket in this run)
- `35kA`
- `200A`
- `Меркурий` (meter model text is only partly recovered)
- a partial `TA1–TA3` string

Across all ROI tokens, exact token matches included `KM2` and `PE`. `KM1`, `1QF`, and `2QF` were not recovered as exact tokens. The incoming-device strings remain confused (for example, `20F` and `3€200`).

## Interpretation

1. The ROI pass does not materially improve recognition of the incoming protective-device tags on this scan.
2. The top-right crop makes some control/meter annotations more visible, including the АВР label, but does not reliably transcribe the full device cluster.
3. Five fixed page partitions are a useful diagnostic experiment, not a sufficient region detector.
4. The next step should be content-driven region proposals: detect text/table blocks and equipment clusters, then apply crop-specific OCR settings. Keep equipment labels and the load table as separate recognition tasks.

## Limits

- No reviewed token-level ground truth was used; precision and recall are not measured.
- Region overlap means token totals must not be interpreted as unique detections.
- OCR strings are candidates, not verified electrical facts.
- No electrical connectivity, topology, or safety conclusion is inferred.
- The source JPEG remains outside the repository.
