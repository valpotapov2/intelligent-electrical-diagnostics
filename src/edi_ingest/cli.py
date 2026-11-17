from __future__ import annotations

import argparse
import json
from pathlib import Path

from .extract import build_model
from .ingest import ingest_document


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
    print("Topology graph: not yet generated; see TOPOLOGY-NOT-IMPLEMENTED issue.")


if __name__ == "__main__":
    main()
