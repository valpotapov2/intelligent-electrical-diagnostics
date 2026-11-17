from __future__ import annotations

from typing import Any

from PIL import Image
import pytesseract
from pytesseract import Output


def _union_box(boxes: list[list[int]], pad: int, width: int, height: int) -> list[int]:
    return [
        max(0, min(box[0] for box in boxes) - pad),
        max(0, min(box[1] for box in boxes) - pad),
        min(width, max(box[2] for box in boxes) + pad),
        min(height, max(box[3] for box in boxes) + pad),
    ]


def _text_regions(tokens: list[dict[str, Any]], width: int, height: int) -> list[dict[str, Any]]:
    groups: dict[tuple[int, int], list[list[int]]] = {}
    for token in tokens:
        block, paragraph = token.get("block_num"), token.get("par_num")
        box = token.get("bbox")
        if block is None or paragraph is None or not isinstance(box, list) or len(box) != 4:
            continue
        x1, y1, x2, y2 = (int(value) for value in box)
        if 0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height:
            groups.setdefault((int(block), int(paragraph)), []).append([x1, y1, x2, y2])
    regions = []
    for (block, paragraph), boxes in groups.items():
        if len(boxes) < 2:
            continue
        bbox = _union_box(boxes, pad=12, width=width, height=height)
        if bbox[2] - bbox[0] >= 35 and bbox[3] - bbox[1] >= 12:
            regions.append({
                "id": f"text-block-{block}-{paragraph}",
                "kind": "ocr_text_block",
                "bbox": bbox,
                "evidence": {"token_count": len(boxes), "block_num": block, "par_num": paragraph},
                "status": "content_region_candidate",
            })
    return regions


def _grid_regions(geometry: dict[str, Any], width: int, height: int) -> list[dict[str, Any]]:
    """Find bounded local groups of line intersections; discard page-frame-sized groups."""
    points: list[tuple[int, int, str, str]] = []
    for h in geometry.get("horizontal_segments", []):
        hy = int(h["start"][1])
        hx1, hx2 = sorted((int(h["start"][0]), int(h["end"][0])))
        for v in geometry.get("vertical_segments", []):
            vx = int(v["start"][0])
            vy1, vy2 = sorted((int(v["start"][1]), int(v["end"][1])))
            if hx1 <= vx <= hx2 and vy1 <= hy <= vy2:
                points.append((vx, hy, str(h.get("id")), str(v.get("id"))))
    if len(points) < 6:
        return []

    # A detected segment can span unrelated drawing areas. Connect only
    # neighboring intersections along that segment, using its local spacing.
    # This preserves ordinary grids while preventing one long line from
    # chaining otherwise separate regions across the page.
    parent = list(range(len(points)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(first: int, second: int) -> None:
        a, b = find(first), find(second)
        if a != b:
            parent[b] = a

    def connect_local_neighbors(
        members_by_segment: dict[str, list[int]], axis: int, axis_length: int
    ) -> None:
        for members in members_by_segment.values():
            ordered = sorted(members, key=lambda index: points[index][axis])
            gaps = [
                points[right][axis] - points[left][axis]
                for left, right in zip(ordered, ordered[1:])
            ]
            positive_gaps = [gap for gap in gaps if gap > 0]
            if not positive_gaps:
                continue
            max_gap = min(1.6 * float(sorted(positive_gaps)[len(positive_gaps) // 2]), axis_length * 0.25)
            for left, right, gap in zip(ordered, ordered[1:], gaps):
                if gap <= max_gap:
                    union(left, right)

    by_horizontal: dict[str, list[int]] = {}
    by_vertical: dict[str, list[int]] = {}
    for index, (_, _, horizontal_id, vertical_id) in enumerate(points):
        by_horizontal.setdefault(horizontal_id, []).append(index)
        by_vertical.setdefault(vertical_id, []).append(index)

    connect_local_neighbors(by_horizontal, axis=0, axis_length=width)
    connect_local_neighbors(by_vertical, axis=1, axis_length=height)

    groups: dict[int, list[int]] = {}
    for index in range(len(points)):
        groups.setdefault(find(index), []).append(index)

    regions = []
    for group_index, indices in enumerate(groups.values(), start=1):
        if len(indices) < 6:
            continue
        selected = [points[index] for index in indices]
        xs, ys = [point[0] for point in selected], [point[1] for point in selected]
        raw = [min(xs), min(ys), max(xs) + 1, max(ys) + 1]
        box_w, box_h = raw[2] - raw[0], raw[3] - raw[1]
        # A candidate occupying most of the sheet is almost certainly a drawing frame/network.
        if box_w > width * 0.85 or box_h > height * 0.75:
            continue
        if box_w * box_h > width * height * 0.45:
            continue
        if raw[0] <= width * 0.015 and raw[1] <= height * 0.015:
            continue
        bbox = _union_box([raw], pad=max(8, int(min(width, height) * 0.008)), width=width, height=height)
        regions.append({
            "id": f"grid-component-{group_index}",
            "kind": "line_grid_candidate",
            "bbox": bbox,
            "evidence": {
                "intersection_count": len(selected),
                "horizontal_segment_count": len({point[2] for point in selected}),
                "vertical_segment_count": len({point[3] for point in selected}),
            },
            "status": "content_region_candidate",
            "limitations": ["A bounded line grid may still be a table, symbol group, or other orthogonal graphic."],
        })
    return regions


def _shape_clusters(shapes: dict[str, Any], width: int, height: int) -> list[dict[str, Any]]:
    """Use bounded neighborhoods rather than transitive chain-link clustering."""
    candidates = shapes.get("candidates", [])
    if len(candidates) < 3:
        return []
    radius = max(28, int(min(width, height) * 0.045))
    centers = [item.get("center", [0, 0]) for item in candidates]
    assigned: set[int] = set()
    groups: list[list[int]] = []
    for seed in range(len(candidates)):
        if seed in assigned:
            continue
        sx, sy = centers[seed]
        members = [seed]
        for index, (x, y) in enumerate(centers):
            if index == seed or index in assigned:
                continue
            if (x - sx) ** 2 + (y - sy) ** 2 <= radius ** 2:
                members.append(index)
        if len(members) >= 3:
            groups.append(members)
            assigned.update(members)

    regions = []
    for group_index, indices in enumerate(groups, start=1):
        boxes = [candidates[index]["bbox"] for index in indices]
        bbox = _union_box(boxes, pad=max(12, int(width * 0.008)), width=width, height=height)
        box_w, box_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        if box_w > width * 0.32 or box_h > height * 0.30:
            continue
        if box_w * box_h > width * height * 0.10:
            continue
        regions.append({
            "id": f"shape-cluster-{group_index}",
            "kind": "graphic_shape_cluster",
            "bbox": bbox,
            "evidence": {"shape_candidate_count": len(boxes), "seed_radius_px": radius},
            "status": "content_region_candidate",
            "limitations": ["A local shape cluster is not evidence of an electrical component or device class."],
        })
    return regions


def _table_regions(
    tokens: list[dict[str, Any]], grid_regions: list[dict[str, Any]], width: int, height: int
) -> list[dict[str, Any]]:
    """Promote bounded grid candidates only when OCR text occupies repeated row-like bands."""
    result = []
    for grid in grid_regions:
        x1, y1, x2, y2 = grid["bbox"]
        inside = [token for token in tokens
                  if x1 <= (token["bbox"][0] + token["bbox"][2]) / 2 <= x2
                  and y1 <= (token["bbox"][1] + token["bbox"][3]) / 2 <= y2]
        if len(inside) < 8:
            continue
        row_centers = sorted((token["bbox"][1] + token["bbox"][3]) / 2 for token in inside)
        bands: list[list[float]] = []
        tolerance = max(5, int((y2 - y1) * 0.035))
        for center in row_centers:
            if not bands or center - bands[-1][-1] > tolerance:
                bands.append([center])
            else:
                bands[-1].append(center)
        if len(bands) < 3:
            continue
        result.append({
            "id": f"table-{grid['id']}",
            "kind": "table_candidate",
            "bbox": [x1, y1, x2, y2],
            "evidence": {
                "text_token_count": len(inside),
                "text_row_band_count": len(bands),
                "grid_intersection_count": grid["evidence"]["intersection_count"],
            },
            "status": "content_region_candidate",
            "limitations": ["Repeated text bands and line intersections are only table evidence; cell structure is not yet reconstructed."],
        })
    return result


def propose_content_regions(
    width: int,
    height: int,
    ocr_tokens: list[dict[str, Any]],
    geometry: dict[str, Any],
    shape_candidates: dict[str, Any],
) -> dict[str, Any]:
    """Propose text, bounded grid, table-like, and local shape regions without semantic claims."""
    grids = _grid_regions(geometry, width, height)
    regions = (
        _text_regions(ocr_tokens, width, height)
        + grids
        + _table_regions(ocr_tokens, grids, width, height)
        + _shape_clusters(shape_candidates, width, height)
    )
    regions.sort(key=lambda item: (item["bbox"][1], item["bbox"][0], item["kind"]))
    return {
        "method": "ocr_blocks_bounded_line_grid_text_bands_and_local_shape_density",
        "coordinate_space": "source_page_pixels",
        "regions": regions,
        "limitations": [
            "Proposals are content candidates, not verified equipment or table classifications.",
            "OCR text blocks depend on whole-page OCR segmentation.",
            "Line-grid components may still be non-table graphics.",
            "Shape neighborhoods are seed-centered and may omit nearby candidates outside the radius.",
            "No electrical class, terminal, connectivity, or topology is inferred.",
        ],
    }


def run_content_region_ocr(
    image: Image.Image,
    proposals: dict[str, Any],
    lang: str = "rus+eng",
    psm: int = 11,
    scale: int = 3,
) -> list[dict[str, Any]]:
    """Run enlarged OCR over content proposals and map boxes to source-page pixels."""
    results = []
    for region in proposals.get("regions", []):
        x1, y1, x2, y2 = region["bbox"]
        crop = image.crop((x1, y1, x2, y2))
        resized = crop.resize((crop.width * scale, crop.height * scale))
        data = pytesseract.image_to_data(
            resized, lang=lang, config=f"--psm {psm}", output_type=Output.DICT
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
            tokens.append({
                "text": value,
                "confidence": confidence if confidence >= 0 else None,
                "bbox": [
                    x1 + int(data["left"][index] / scale),
                    y1 + int(data["top"][index] / scale),
                    x1 + int((data["left"][index] + data["width"][index]) / scale),
                    y1 + int((data["top"][index] + data["height"][index]) / scale),
                ],
            })
        results.append({
            **region,
            "scale": scale,
            "psm": psm,
            "tokens": tokens,
            "text": " ".join(token["text"] for token in tokens),
        })
    return results
