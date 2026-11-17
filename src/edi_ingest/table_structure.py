from __future__ import annotations

from typing import Any

import cv2
import numpy as np
from PIL import Image


def _projection_groups(values: np.ndarray, threshold: float, offset: int, merge_gap: int = 4) -> list[int]:
    indices = np.flatnonzero(values >= threshold).tolist()
    groups: list[list[int]] = []
    for index in indices:
        if not groups or index - groups[-1][-1] > merge_gap:
            groups.append([index])
        else:
            groups[-1].append(index)
    return [offset + int(round(sum(group) / len(group))) for group in groups]


def extract_table_structures(
    image: Image.Image,
    proposals: dict[str, Any],
) -> list[dict[str, Any]]:
    """Recover row/column rules and cell boxes from table-region proposals.

    The proposal is deliberately expanded left/up: the current grid detector
    often sees only the dense numeric columns and misses the table's first
    column and header. Returned lines/cells remain geometric candidates.
    """
    page_width, page_height = image.size
    gray = cv2.cvtColor(np.asarray(image.convert("RGB")), cv2.COLOR_RGB2GRAY)
    structures = []

    for proposal in proposals.get("regions", []):
        if proposal.get("kind") != "table_candidate":
            continue
        x1, y1, x2, y2 = [int(value) for value in proposal["bbox"]]
        proposal_width, proposal_height = x2 - x1, y2 - y1
        left = max(0, x1 - int(proposal_width * 0.22))
        top = max(0, y1 - int(proposal_height * 0.25))
        right = min(page_width, x2 + int(proposal_width * 0.04))
        bottom = min(page_height, y2)
        if right - left < 60 or bottom - top < 40:
            continue

        roi = gray[top:bottom, left:right]
        binary = cv2.adaptiveThreshold(
            roi, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 31, 12
        )
        horizontal_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (max(25, roi.shape[1] // 10), 1)
        )
        horizontal_mask = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
        row_projection = (horizontal_mask > 0).sum(axis=1)
        row_positions = _projection_groups(
            row_projection, roi.shape[1] * 0.55, top, merge_gap=4
        )
        if len(row_positions) < 3:
            continue

        first_row, last_row = row_positions[0], row_positions[-1]
        vertical_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (1, max(20, (last_row - first_row) // 5))
        )
        vertical_mask = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
        local_top, local_bottom = first_row - top, last_row - top + 1
        column_projection = (vertical_mask[local_top:local_bottom] > 0).sum(axis=0)
        column_positions = _projection_groups(
            column_projection, (local_bottom - local_top) * 0.45, left, merge_gap=4
        )
        if len(column_positions) < 3:
            continue

        cells = []
        for row_index, (row_top, row_bottom) in enumerate(zip(row_positions, row_positions[1:])):
            for column_index, (column_left, column_right) in enumerate(zip(column_positions, column_positions[1:])):
                if row_bottom > row_top and column_right > column_left:
                    cells.append({
                        "row": row_index,
                        "column": column_index,
                        "bbox": [column_left, row_top, column_right, row_bottom],
                        "status": "cell_candidate",
                    })

        structures.append({
            "id": f"structure-{proposal.get('id', len(structures) + 1)}",
            "source_region_id": proposal.get("id"),
            "kind": "table_structure_candidate",
            "bbox": [column_positions[0], first_row, column_positions[-1], last_row],
            "row_boundaries": row_positions,
            "column_boundaries": column_positions,
            "row_count": len(row_positions) - 1,
            "column_count": len(column_positions) - 1,
            "cells": cells,
            "status": "structure_candidate",
            "limitations": [
                "Line projections can miss broken, faint, or merged cell borders.",
                "Cell coordinates do not establish row labels, column meaning, or OCR correctness.",
            ],
        })
    return structures
