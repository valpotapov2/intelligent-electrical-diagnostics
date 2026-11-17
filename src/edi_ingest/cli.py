from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .extract import build_model
from .ingest import ingest_document


def _print_table_summary(page_number: int, page: dict[str, Any]) -> None:
    structures = page.get("table_structures", [])
    ocr_results = page.get("table_cell_ocr", [])
    print(f"  Page {page_number}: table structures={len(structures)}")
    ocr_by_structure = {
        item.get("source_structure_id"): item for item in ocr_results
    }
    for structure in structures:
        structure_id = structure.get("id")
        rows = structure.get("row_count", 0)
        columns = structure.get("column_count", 0)
        cells = structure.get("cells", [])
        ocr = ocr_by_structure.get(structure_id, {})
        ocr_cells = {
            (cell.get("row"), cell.get("column")): cell
            for cell in ocr.get("cells", [])
        }
        print(
            f"    {structure_id}: {rows} rows × {columns} columns; "
            f"{len(cells)} cell candidates"
        )
        for cell in cells:
            key = (cell.get("row"), cell.get("column"))
            read = ocr_cells.get(key, {})
            raw = read.get("text_raw", "")
            confidence = read.get("mean_confidence")
            confidence_text = f"{confidence:.1f}" if isinstance(confidence, (int, float)) else "n/a"
            value = raw if raw else "[empty]"
            print(
                f"      r{key[0] + 1} c{key[1] + 1}: {value} "
                f"(OCR confidence: {confidence_text}; {read.get('status', 'not_read')})"
            )
        print("    Note: OCR text and confidence are raw candidates, not verified values.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract OCR candidates from an electrical diagram.")
    parser.add_argument("input", help="PDF or raster image")
    parser.add_argument("-o", "--output", default="electrical-object-model.draft.json")
    parser.add_argument("--object-name", default="Unspecified electrical object")
    parser.add_argument("--lang", default="rus+eng", help="Tesseract language packs, e.g. rus+eng")
    parser.add_argument("--dpi", type=int, default=220, help="PDF render DPI")
    parser.add_argument("--psm", type=int, default=11, help="Tesseract page segmentation mode")
    parser.add_argument("--ocr-output", help="Optional path to save raw OCR result")
    args = parser.parse_args()

    ingested = ingest_document(args.input, lang=args.lang, dpi=args.dpi, psm=args.psm)
    model = build_model(ingested, object_name=args.object_name)
    Path(args.output).write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.ocr_output:
        Path(args.ocr_output).write_text(json.dumps(ingested, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Model written: {args.output}")
    print(f"Pages: {len(ingested['ocr']['pages'])}")
    print(f"Component candidates: {len(model['components'])}")
    print("Load-table extraction:")
    for page_number, page in enumerate(ingested["ocr"]["pages"], start=1):
        _print_table_summary(page_number, page)
    print("Topology graph: not yet generated; detected lines and cells are not electrical connectivity.")


if __name__ == "__main__":
    main()
