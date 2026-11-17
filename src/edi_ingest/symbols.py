from __future__ import annotations

from typing import Any

import cv2
import numpy as np
from PIL import Image


def _overlap_ratio(box: tuple[int, int, int, int], token_box: list[int]) -> float:
    x, y, width, height = box
    tx1, ty1, tx2, ty2 = token_box
    ix1, iy1 = max(x, tx1), max(y, ty1)
    ix2, iy2 = min(x + width, tx2), min(y + height, ty2)
    intersection = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area = max(1, width * height)
    return intersection / area


def detect_symbol_candidates(
    image: Image.Image,
    ocr_tokens: list[dict[str, Any]] | None = None,
    min_area: int = 90,
    max_area_ratio: float = 0.04,
) -> dict[str, Any]:
    """Find closed graphic-shape candidates; deliberately does not name electrical symbols."""
    gray = cv2.cvtColor(np.asarray(image.convert("RGB")), cv2.COLOR_RGB2GRAY)
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 31, 12
    )
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    page_area = image.width * image.height
    max_area = int(page_area * max_area_ratio)
    tokens = ocr_tokens or []
    candidates = []

    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < min_area or area > max_area:
            continue
        x, y, width, height = cv2.boundingRect(contour)
        if width < 8 or height < 8:
            continue
        box = (x, y, width, height)
        if any(_overlap_ratio(box, token.get("bbox", [0, 0, 0, 0])) >= 0.25 for token in tokens):
            continue

        perimeter = float(cv2.arcLength(contour, True))
        if perimeter <= 0:
            continue
        approximation = cv2.approxPolyDP(contour, 0.035 * perimeter, True)
        vertices = len(approximation)
        circularity = min(1.0, float(4 * np.pi * area / (perimeter * perimeter)))
        aspect_ratio = width / max(1, height)

        if circularity >= 0.72:
            family = "circular_outline"
        elif vertices == 4 and 0.65 <= aspect_ratio <= 1.55:
            family = "quadrilateral_outline"
        elif vertices == 4:
            family = "rectangular_outline"
        elif vertices >= 5:
            family = "polygonal_outline"
        else:
            family = "irregular_closed_shape"

        candidates.append({
            "bbox": [x, y, x + width, y + height],
            "center": [round(x + width / 2, 2), round(y + height / 2, 2)],
            "area_px": round(area, 2),
            "perimeter_px": round(perimeter, 2),
            "aspect_ratio": round(aspect_ratio, 3),
            "circularity": round(circularity, 3),
            "vertex_count": vertices,
            "candidate_family": family,
            "status": "unclassified_shape_candidate",
            "classification_confidence": None,
        })

    # Nested contours can describe the same symbol border. Prefer the outer candidate
    # when one box contains another candidate with nearly the same center.
    candidates.sort(key=lambda item: item["area_px"], reverse=True)
    filtered = []
    for candidate in candidates:
        cx, cy = candidate["center"]
        x1, y1, x2, y2 = candidate["bbox"]
        contained = False
        for existing in filtered:
            ex1, ey1, ex2, ey2 = existing["bbox"]
            if ex1 <= x1 and ey1 <= y1 and ex2 >= x2 and ey2 >= y2:
                ecx, ecy = existing["center"]
                if abs(cx - ecx) <= 3 and abs(cy - ecy) <= 3:
                    contained = True
                    break
        if not contained:
            filtered.append(candidate)

    filtered.sort(key=lambda item: (item["bbox"][1], item["bbox"][0]))
    for index, candidate in enumerate(filtered, start=1):
        candidate["id"] = f"shape-candidate-{index}"

    return {
        "image_size": [image.width, image.height],
        "method": "adaptive_threshold_contour_shape_descriptors",
        "candidates": filtered,
        "limitations": [
            "Shape families are geometric descriptions, not electrical component classes.",
            "Open symbols, line-connected symbols and multi-part symbols may be missed or fragmented.",
            "Text overlap filtering depends on OCR token bounding boxes.",
            "No terminal locations or electrical meaning are inferred.",
        ],
    }
