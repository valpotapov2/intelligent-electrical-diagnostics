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
