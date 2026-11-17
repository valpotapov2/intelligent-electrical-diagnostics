from __future__ import annotations

import hashlib
import io
from pathlib import Path
from typing import Any

import fitz
from PIL import Image
import pytesseract
from pytesseract import Output

from .geometry import detect_geometry


SUPPORTED_IMAGES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ocr_image(image: Image.Image, page_number: int, lang: str, psm: int) -> dict[str, Any]:
    data = pytesseract.image_to_data(
        image, lang=lang, config=f"--psm {psm}", output_type=Output.DICT
    )
    tokens = []
    for i, raw in enumerate(data["text"]):
        text = str(raw).strip()
        if not text:
            continue
        try:
            confidence = float(data["conf"][i])
        except (TypeError, ValueError):
            confidence = -1.0
        tokens.append({
            "text": text,
            "confidence": confidence if confidence >= 0 else None,
            "bbox": [
                int(data["left"][i]), int(data["top"][i]),
                int(data["left"][i] + data["width"][i]),
                int(data["top"][i] + data["height"][i]),
            ],
            "block_num": int(data["block_num"][i]),
            "par_num": int(data["par_num"][i]),
            "line_num": int(data["line_num"][i]),
        })
    lines: dict[tuple[int, int, int], list[str]] = {}
    for token in tokens:
        key = (token["block_num"], token["par_num"], token["line_num"])
        lines.setdefault(key, []).append(token["text"])
    return {
        "page": page_number,
        "width": image.width,
        "height": image.height,
        "text": "\n".join(" ".join(parts) for parts in lines.values()),
        "tokens": tokens,
    }


def _extract_pdf_vector_primitives(page: fitz.Page) -> dict[str, Any]:
    """Keep native PDF line/rectangle geometry before rasterization; coordinates are PDF points."""
    lines = []
    rectangles = []
    for drawing_index, drawing in enumerate(page.get_drawings(), start=1):
        for item_index, item in enumerate(drawing.get("items", []), start=1):
            kind = item[0]
            primitive_id = f"pdf-path-{drawing_index}-item-{item_index}"
            if kind == "l":
                start, end = item[1], item[2]
                lines.append({
                    "id": primitive_id,
                    "start": [round(start.x, 3), round(start.y, 3)],
                    "end": [round(end.x, 3), round(end.y, 3)],
                    "length_pt": round(start.distance_to(end), 3),
                    "status": "vector_candidate",
                })
            elif kind == "re":
                rect = item[1]
                rectangles.append({
                    "id": primitive_id,
                    "bbox": [round(rect.x0, 3), round(rect.y0, 3), round(rect.x1, 3), round(rect.y1, 3)],
                    "status": "vector_candidate",
                })
    return {
        "coordinate_space": "pdf_points",
        "lines": lines,
        "rectangles": rectangles,
        "note": "Vector primitives are not classified as electrical conductors or component symbols.",
    }


def ingest_document(path: str | Path, lang: str = "rus+eng", dpi: int = 220, psm: int = 11) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    suffix = source.suffix.lower()
    pages = []
    if suffix == ".pdf":
        document = fitz.open(source)
        for index, page in enumerate(document, start=1):
            pixmap = page.get_pixmap(dpi=dpi, alpha=False)
            image = Image.open(io.BytesIO(pixmap.tobytes("png"))).convert("RGB")
            page_result = _ocr_image(image, index, lang, psm)
            page_result["geometry"] = detect_geometry(image)
            page_result["pdf_vector_geometry"] = _extract_pdf_vector_primitives(page)
            page_result["source_page_size"] = [page.rect.width, page.rect.height]
            pages.append(page_result)
    elif suffix in SUPPORTED_IMAGES:
        image = Image.open(source).convert("RGB")
        page_result = _ocr_image(image, 1, lang, psm)
        page_result["geometry"] = detect_geometry(image)
        pages.append(page_result)
    else:
        raise ValueError(f"Unsupported input format: {suffix}")

    return {
        "source": {
            "filename": source.name,
            "media_type": "application/pdf" if suffix == ".pdf" else f"image/{suffix.lstrip('.')}",
            "sha256": sha256_file(source),
        },
        "ocr": {"engine": "tesseract", "language": lang, "pages": pages},
    }
