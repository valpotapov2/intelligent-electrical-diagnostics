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
        if block is None or paragraph is None:
            continue
        box = token.get("bbox")
        if isinstance(box, list) and len(box) == 4:
            groups.setdefault((int(block), int(paragraph)), []).append(box)
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
    horizontal = geometry.get("horizontal_segments", [])
    vertical = geometry.get("vertical_segments", [])
    points: list[tuple[int, int]] = []
    used_h: set[str] = set()
    used_v: set[str] = set()
    for h in horizontal:
        hy = int(h["start"][1])
        hx1, hx2 = sorted((int(h["start"][0]), int(h["end"][0])))
        for v in vertical:
            vx = int(v["start"][0])
            vy1, vy2 = sorted((int(v["start"][1]), int(v["end"][1])))
            if hx1 <= vx <= hx2 and vy1 <= hy <= vy2:
                points.append((vx, hy))
                used_h.add(str(h.get("id")))
                used_v.add(str(v.get("id")))
    if len(points) < 6 or len(used_h) < 3 or len(used_v) < 2:
        return []
    xs, ys = [point[0] for point in points], [point[1] for point in points]
    bbox = _union_box(
        [[min(xs), min(ys), max(xs) + 1, max(ys) + 1]],
        pad=max(8, int(min(width, height) * 0.008)), width=width, height=height
    )
    return [{
        "id": "grid-intersection-region-1",
        "kind": "line_grid_candidate",
        "bbox": bbox,
        "evidence": {
            "intersection_count": len(points),
            "horizontal_segment_count": len(used_h),
            "vertical_segment_count": len(used_v),
        },
        "status": "content_region_candidate",
        "limitations": ["A line grid may be a table, drawing frame, or other orthogonal graphic."],
    }]


def _shape_clusters(shapes: dict[str, Any], width: int, height: int) -> list[dict[str, Any]]:
    candidates = shapes.get("candidates", [])
    if len(candidates) < 3:
        return []
    centers = [item.get("center", [0, 0]) for item in candidates]
    radius = max(36, int(width * 0.075))
    parent = list(range(len(candidates)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for i, (x1, y1) in enumerate(centers):
        for j in range(i + 1, len(centers)):
            x2, y2 = centers[j]
            if (x1 - x2) ** 2 + (y1 - y2) ** 2 <= radius ** 2:
                a, b = find(i), find(j)
                if a != b:
                    parent[b] = a

    groups: dict[int, list[list[int]]] = {}
    for index, item in enumerate(candidates):
        groups.setdefault(find(index), []).append(item["bbox"])
    regions = []
    for index, boxes in enumerate(groups.values(), start=1):
        if len(boxes) < 3:
            continue
        bbox = _union_box(boxes, pad=max(16, int(width * 0.012)), width=width, height=height)
        regions.append({
            "id": f"shape-cluster-{index}",
            "kind": "graphic_shape_cluster",
            "bbox": bbox,
            "evidence": {"shape_candidate_count": len(boxes), "cluster_radius_px": radius},
            "status": "content_region_candidate",
            "limitations": ["Shape density is not evidence of an electrical component or device class."],
        })
    return regions


def propose_content_regions(
    width: int,
    height: int,
    ocr_tokens: list[dict[str, Any]],
    geometry: dict[str, Any],
    shape_candidates: dict[str, Any],
) -> dict[str, Any]:
    """Propose OCR/text, orthogonal-grid, and graphic-density regions without semantic labels."""
    regions = (
        _text_regions(ocr_tokens, width, height)
        + _grid_regions(geometry, width, height)
        + _shape_clusters(shape_candidates, width, height)
    )
    regions.sort(key=lambda item: (item["bbox"][1], item["bbox"][0], item["kind"]))
    return {
        "method": "ocr_blocks_line_intersections_and_shape_density",
        "coordinate_space": "source_page_pixels",
        "regions": regions,
        "limitations": [
            "Proposals are geometric/content candidates, not verified equipment or table classifications.",
            "OCR text blocks depend on the whole-page OCR segmentation.",
            "Grid intersections can belong to drawing frames or non-table graphics.",
            "Shape clusters can merge unrelated nearby graphics and are not electrical objects.",
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
