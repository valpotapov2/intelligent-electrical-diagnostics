"""Regression checks for source-grounded kindergarten switchboard metadata."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "benchmarks" / "kindergarten-switchboard" / "electrical-object-model.v0.1.json"


def test_breaker_markings_are_preserved_without_unsupported_pole_count():
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    breakers = {item["label"]: item for item in model["components"] if item["kind"] == "breaker"}

    expected = {
        "QF1": "3C25",
        "QF2": "3C25",
        "QF3": "3C25",
        "QF4": "3C32",
        "QF5": "3C10",
        "QF6": "3C10",
        "QF7": "1C10",
        "QF8": "1C10",
        "QF9": "3C80",
        "QF10": "3C10",
    }
    assert set(breakers) == set(expected)
    for tag, marking in expected.items():
        attributes = breakers[tag]["attributes"]
        assert attributes["marking"] == marking
        assert "poles" not in attributes


def test_circuit_source_bounds_cover_their_traced_feeder_geometry():
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    edges = model["connections"]
    for circuit in model["circuits"]:
        related = [
            edge for edge in edges
            if (edge["from"] == circuit["protective_device_id"] and edge["to"] == circuit["cable_id"])
            or (edge["from"] == circuit["cable_id"] and edge["to"] in circuit["load_ids"])
            or (edge["to"] == circuit["protective_device_id"] and edge["from"] == "bus-l123")
        ]
        boxes = [source["bbox"] for edge in related for source in edge["sources"] if "bbox" in source]
        assert boxes, circuit["id"]
        expected = [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]
        assert circuit["sources"][0]["bbox"] == expected, circuit["id"]
        x1, y1, x2, y2 = circuit["sources"][0]["bbox"]
        assert x2 > x1 and y2 > y1, circuit["id"]


def test_incoming_side_omission_is_explicitly_recorded():
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    issue = next(item for item in model["issues"] if item["id"] == "SVG-005")
    assert issue["status"] == "open"
    assert "1QF" in issue["description"] and "2QF" in issue["description"]
    assert "outgoing feeders QF1–QF10 only" in issue["description"]
    assert set(issue["related_ids"]) == {
        "supply-1", "supply-2", "ats", "contactor-km1", "contactor-km2"
    }
