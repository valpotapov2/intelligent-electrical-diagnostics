from __future__ import annotations

from typing import Any

import cv2
import numpy as np
from PIL import Image


def detect_geometry(image: Image.Image, min_line_length: int = 35, max_line_gap: int = 8) -> dict[str, Any]:
    """Detect orthogonal line and junction candidates; does not assert electrical connectivity."""
    rgb = np.asarray(image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    # Remove small text strokes while preserving long orthogonal drafting lines.
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 31, 12
    )
    scale = max(1, image.width // 1000)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(15, 35 * scale), 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(15, 35 * scale)))
    horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
    vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)

    h_lines = cv2.HoughLinesP(
        horizontal, 1, np.pi / 180, threshold=max(12, min_line_length // 2),
        minLineLength=min_line_length, maxLineGap=max_line_gap
    )
    v_lines = cv2.HoughLinesP(
        vertical, 1, np.pi / 180, threshold=max(12, min_line_length // 2),
        minLineLength=min_line_length, maxLineGap=max_line_gap
    )

    def serialize(lines: np.ndarray | None, orientation: str) -> list[dict[str, Any]]:
        result = []
        if lines is None:
            return result
        for index, line in enumerate(lines[:, 0, :]):
            x1, y1, x2, y2 = (int(value) for value in line)
            result.append({
                "id": f"{orientation}-{index + 1}",
                "orientation": orientation,
                "start": [x1, y1],
                "end": [x2, y2],
                "length_px": round(float(np.hypot(x2 - x1, y2 - y1)), 2),
                "status": "candidate",
            })
        return result

    h_segments = serialize(h_lines, "horizontal")
    v_segments = serialize(v_lines, "vertical")

    # Intersections are candidates only: a drawing crossing may or may not be a junction.
    intersections = cv2.bitwise_and(horizontal, vertical)
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(intersections, 8)
    junctions = []
    for label in range(1, count):
        x, y, width, height, area = (int(v) for v in stats[label])
        if area < 1:
            continue
        cx, cy = centroids[label]
        junctions.append({
            "id": f"junction-candidate-{label}",
            "point": [round(float(cx), 2), round(float(cy), 2)],
            "bbox": [x, y, x + width, y + height],
            "status": "unverified_intersection",
        })

    return {
        "image_size": [image.width, image.height],
        "method": "adaptive_threshold_morphology_hough",
        "horizontal_segments": h_segments,
        "vertical_segments": v_segments,
        "junction_candidates": junctions,
        "limitations": [
            "Detected segments are geometric candidates, not confirmed conductors.",
            "An intersection candidate is not proof of an electrical junction.",
            "Text, symbols, dashed lines and low-resolution scans can create missed or false detections.",
            "No component terminals are attached to line endpoints in this version.",
        ],
    }
