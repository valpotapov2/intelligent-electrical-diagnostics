from __future__ import annotations

import re
from typing import Any

REF_PATTERNS = [
    ("breaker", re.compile(r"\bQF\s*[-:]?\s*\d+\b", re.I)),
    ("contactor", re.compile(r"\bKM\s*[-:]?\s*\d+\b", re.I)),
    ("current_transformer", re.compile(r"\bTA\s*[-:]?\s*\d+\b", re.I)),
    ("busbar", re.compile(r"\b(?:L1|L2|L3|N|PE)\b", re.I)),
    ("ats", re.compile(r"\bАВР\b", re.I)),
]
RATING_RE = re.compile(r"(?<![A-ZА-Я0-9])(?:\d{1,4})\s*[ACВ]?\s*(?:\d{1,2}(?:[.,]\d+)?)?\s*(?:kA|кА)", re.I)


def _normalize_ref(value: str) -> str:
    value = re.sub(r"\s+", "", value.upper())
    return value.replace("АВР", "АВР")


def extract_candidates(ocr_result: dict[str, Any]) -> dict[str, Any]:
    components: dict[str, dict[str, Any]] = {}
    issues = []
    for page in ocr_result.get("pages", []):
        page_no = page["page"]
        for kind, pattern in REF_PATTERNS:
            for match in pattern.finditer(page.get("text", "")):
                label = _normalize_ref(match.group(0))
                key = f"{kind}:{label}"
                components.setdefault(key, {
                    "id": key.replace(":", "_"),
                    "kind": kind,
                    "label": label,
                    "attributes": {},
                    "status": "recognized",
                    "confidence": None,
                    "sources": [{"document_id": "source-1", "page": page_no, "text": match.group(0)}],
                })

        # Keep every OCR token containing an equipment-like code as an unclassified candidate.
        for token in page.get("tokens", []):
            value = token["text"]
            if re.search(r"\b[A-ZА-Я]{2,}\d+[A-ZА-Я0-9-]*\b", value, re.I):
                key = f"label:{value.upper()}"
                components.setdefault(key, {
                    "id": key.replace(":", "_").replace("/", "_"),
                    "kind": "unknown",
                    "label": value,
                    "attributes": {},
                    "status": "ambiguous",
                    "confidence": token.get("confidence"),
                    "sources": [{"document_id": "source-1", "page": page_no, "bbox": token.get("bbox"), "text": value}],
                })
    if not components:
        issues.append({
            "id": "OCR-NO-COMPONENT-CANDIDATES",
            "severity": "medium",
            "description": "OCR did not identify recognizable component references. Review image quality, OCR language and page rendering.",
            "status": "open",
        })
    return {"components": list(components.values()), "connections": [], "circuits": [], "issues": issues}


def build_model(ingested: dict[str, Any], object_name: str = "Unspecified electrical object") -> dict[str, Any]:
    extracted = extract_candidates(ingested["ocr"])
    source = ingested["source"]
    return {
        "schema_version": "0.1",
        "source_documents": [{
            "id": "source-1",
            "kind": "single_line_diagram",
            "filename": source["filename"],
            "media_type": source["media_type"],
            "sha256": source["sha256"],
        }],
        "object": {"name": object_name},
        "components": extracted["components"],
        "connections": extracted["connections"],
        "geometry_candidates": [
            {"page": page["page"], **page.get("geometry", {})}
            for page in ingested["ocr"].get("pages", [])
            if page.get("geometry")
        ],
        "circuits": extracted["circuits"],
        "issues": extracted["issues"] + [{
            "id": "TOPOLOGY-NOT-IMPLEMENTED",
            "severity": "info",
            "description": "Geometric line and intersection candidates are emitted separately. Confirmed electrical wire tracing, terminal attachment, net identity and connection graph construction are not implemented.",
            "status": "open",
        }],
        "extraction": {
            "tool_version": "0.1.0",
            "review_status": "unreviewed",
            "method": "tesseract_ocr_regex_candidates_plus_geometric_line_candidates",
        },
    }
