from __future__ import annotations

from typing import Any

from PIL import Image
import pytesseract
from pytesseract import Output


def read_table_cells(
    image: Image.Image,
    structures: list[dict[str, Any]],
    lang: str = "rus+eng",
    scale: int = 4,
    psm: int = 7,
) -> list[dict[str, Any]]:
    """OCR each geometric cell independently; retain raw text and confidence."""
    page_width, page_height = image.size
    results = []
    for structure in structures:
        cells = []
        for cell in structure.get("cells", []):
            x1, y1, x2, y2 = [int(value) for value in cell["bbox"]]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(page_width, x2), min(page_height, y2)
            if x2 <= x1 or y2 <= y1:
                continue
            crop = image.crop((x1, y1, x2, y2))
            enlarged = crop.resize((max(1, crop.width * scale), max(1, crop.height * scale)))
            data = pytesseract.image_to_data(
                enlarged, lang=lang, config=f"--psm {psm}", output_type=Output.DICT
            )
            tokens = []
            for index, raw in enumerate(data["text"]):
                value = str(raw).strip()
                if not value:
                    continue
                try:
                    confidence = float(data["conf"][index])
                except (TypeError, ValueError):
                    confidence = -1.0
                if confidence < 0:
                    confidence_value = None
                else:
                    confidence_value = confidence
                tokens.append({"text": value, "confidence": confidence_value})
            text = " ".join(token["text"] for token in tokens)
            confidences = [token["confidence"] for token in tokens if token["confidence"] is not None]
            cells.append({
                **cell,
                "text_raw": text,
                "tokens": tokens,
                "mean_confidence": round(sum(confidences) / len(confidences), 1) if confidences else None,
                "status": "ocr_read" if text else "ocr_empty",
            })
        results.append({
            "id": f"ocr-{structure.get('id', len(results) + 1)}",
            "source_structure_id": structure.get("id"),
            "kind": "table_cell_ocr_candidate",
            "cells": cells,
            "status": "ocr_candidates",
            "limitations": [
                "OCR output is raw and may contain substitutions or omissions.",
                "No row label, column header, unit, or electrical meaning is inferred.",
                "Confidence is Tesseract confidence, not calibrated probability of correctness.",
            ],
        })
    return results
