from __future__ import annotations

from typing import Any

import cv2
import numpy as np
from PIL import Image


def _merge_axis_segments(
    lines: np.ndarray | None, orientation: str, axis_tolerance: int, gap_tolerance: int
) -> list[dict[str, Any]]:
    """Collapse duplicate/overlapping Hough fragments into stable axis-aligned segments."""
    if lines is None:
        return []
    raw = []
    for line in np.asarray(lines).reshape(-1, 4):
        x1, y1, x2, y2 = (int(value) for value in line)
        if orientation == "horizontal":
            axis = int(round((y1 + y2) / 2))
            start, end = sorted((x1, x2))
        else:
            axis = int(round((x1 + x2) / 2))
            start, end = sorted((y1, y2))
        if end > start:
            raw.append((axis, start, end))

    raw.sort()
    clusters: list[list[tuple[int, int, int]]] = []
    for segment in raw:
        axis, start, end = segment
        matching = next(
            (
                cluster for cluster in reversed(clusters)
                if abs(axis - round(sum(item[0] for item in cluster) / len(cluster))) <= axis_tolerance
                and start <= max(item[2] for item in cluster) + gap_tolerance
            ),
            None,
        )
        if matching is None:
            clusters.append([segment])
        else:
            matching.append(segment)

    merged = []
    for cluster in clusters:
        axis = int(round(sum(item[0] for item in cluster) / len(cluster)))
        intervals = sorted((item[1], item[2]) for item in cluster)
        start, end = intervals[0]
        for next_start, next_end in intervals[1:]:
            if next_start <= end + gap_tolerance:
                end = max(end, next_end)
            else:
                merged.append((axis, start, end))
                start, end = next_start, next_end
        merged.append((axis, start, end))

    result = []
    for index, (axis, start, end) in enumerate(sorted(merged), start=1):
        if orientation == "horizontal":
            p1, p2 = [start, axis], [end, axis]
        else:
            p1, p2 = [axis, start], [axis, end]
        result.append({
            "id": f"{orientation}-{index}",
            "orientation": orientation,
            "start": p1,
            "end": p2,
            "length_px": float(end - start),
            "status": "candidate",
        })
    return result


def detect_geometry(image: Image.Image, min_line_length: int = 35, max_line_gap: int = 8) -> dict[str, Any]:
    """Detect orthogonal line and intersection candidates, never confirmed connectivity."""
    rgb = np.asarray(image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
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

    h_segments = _merge_axis_segments(h_lines, "horizontal", axis_tolerance=4, gap_tolerance=max_line_gap + 3)
    v_segments = _merge_axis_segments(v_lines, "vertical", axis_tolerance=4, gap_tolerance=max_line_gap + 3)

    # Intersections are calculated from normalized segments, not raw raster overlap.
    # This still cannot distinguish a true junction from a bridge/crossover convention.
    junctions = []
    for h in h_segments:
        y = h["start"][1]
        hx1, hx2 = h["start"][0], h["end"][0]
        for v in v_segments:
            x = v["start"][0]
            vy1, vy2 = v["start"][1], v["end"][1]
            if hx1 <= x <= hx2 and vy1 <= y <= vy2:
                junctions.append({
                    "id": f"junction-candidate-{len(junctions) + 1}",
                    "point": [x, y],
                    "status": "unverified_intersection",
                    "evidence": {"horizontal_segment": h["id"], "vertical_segment": v["id"]},
                })

    return {
        "image_size": [image.width, image.height],
        "method": "adaptive_threshold_morphology_hough_axis_merge",
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
