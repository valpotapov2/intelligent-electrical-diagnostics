from __future__ import annotations

from typing import Any

from PIL import Image
import pytesseract
from pytesseract import Output


def propose_regions(width: int, height: int) -> list[dict[str, Any]]:
    """Return overlapping, scale-independent page regions for a second OCR pass.

    These are generic layout proposals, not semantic claims about equipment locations.
    """
    w, h = width, height
    specs = [
        ("top_left", (0.00, 0.00, 0.55, 0.48)),
        ("top_right", (0.45, 0.00, 1.00, 0.48)),
        ("middle_left", (0.00, 0.30, 0.55, 0.76)),
        ("middle_right", (0.45, 0.30, 1.00, 0.76)),
        ("bottom_full", (0.08, 0.66, 0.96, 1.00)),
    ]
    regions = []
    for name, (x1, y1, x2, y2) in specs:
        box = [
            max(0, int(round(x1 * w))),
            max(0, int(round(y1 * h))),
            min(w, int(round(x2 * w))),
            min(h, int(round(y2 * h))),
        ]
        if box[2] - box[0] >= 40 and box[3] - box[1] >= 40:
            regions.append({"id": name, "bbox": box})
    return regions


def _tokens(image: Image.Image, lang: str, psm: int, scale: int) -> list[dict[str, Any]]:
    resized = image.resize((image.width * scale, image.height * scale))
    data = pytesseract.image_to_data(
        resized, lang=lang, config=f"--psm {psm}", output_type=Output.DICT
    )
    result = []
    for i, raw in enumerate(data["text"]):
        value = str(raw).strip()
        if not value:
            continue
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            conf = -1.0
        # Convert token boxes back to original page pixel coordinates.
        x1 = int(data["left"][i] / scale)
        y1 = int(data["top"][i] / scale)
        x2 = int((data["left"][i] + data["width"][i]) / scale)
        y2 = int((data["top"][i] + data["height"][i]) / scale)
        result.append({
            "text": value,
            "confidence": conf if conf >= 0 else None,
            "bbox": [x1, y1, x2, y2],
        })
    return result


def run_roi_ocr(
    image: Image.Image, lang: str = "rus+eng", psm: int = 11, scale: int = 3
) -> dict[str, Any]:
    """Run OCR on overlapping enlarged regions and preserve page-coordinate provenance."""
    regions = []
    for region in propose_regions(image.width, image.height):
        x1, y1, x2, y2 = region["bbox"]
        crop = image.crop((x1, y1, x2, y2))
        tokens = _tokens(crop, lang=lang, psm=psm, scale=scale)
        for token in tokens:
            bx1, by1, bx2, by2 = token["bbox"]
            token["bbox"] = [bx1 + x1, by1 + y1, bx2 + x1, by2 + y1]
        regions.append({
            **region,
            "scale": scale,
            "psm": psm,
            "tokens": tokens,
            "text": " ".join(token["text"] for token in tokens),
        })
    return {
        "method": "overlapping_normalized_page_regions_upscaled_tesseract",
        "coordinate_space": "source_page_pixels",
        "regions": regions,
        "limitations": [
            "Region proposals are generic overlapping page partitions, not semantic equipment detection.",
            "OCR boxes are mapped back to source-page pixels and may differ by rounding.",
            "Overlapping regions can produce duplicate tokens; deduplication is intentionally left explicit.",
        ],
    }
