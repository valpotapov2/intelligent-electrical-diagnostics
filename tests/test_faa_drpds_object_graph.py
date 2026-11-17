"""Structural integrity checks for the generic FAA DRPDS object graph."""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "electrical-object-model.schema.json"
MODEL_PATH = ROOT / "examples" / "objects" / "faa-drpds.generic.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_faa_drpds_graph_matches_electrical_object_schema():
    schema = load_json(SCHEMA_PATH)
    model = load_json(MODEL_PATH)

    errors = sorted(
        Draft202012Validator(schema).iter_errors(model),
        key=lambda error: list(error.absolute_path),
    )
    assert not errors, "\n".join(
        f"{list(error.absolute_path)}: {error.message}" for error in errors
    )


def test_faa_drpds_graph_has_unique_component_ids_and_resolved_edges():
    model = load_json(MODEL_PATH)
    component_ids = [component["id"] for component in model["components"]]

    assert len(component_ids) == len(set(component_ids))

    known_ids = set(component_ids)
    for edge in model["connections"]:
        assert edge["from"] in known_ids, edge["id"]
        assert edge["to"] in known_ids, edge["id"]
        assert edge["sources"], edge["id"]


def test_faa_drpds_power_control_and_test_paths_are_distinguished():
    model = load_json(MODEL_PATH)
    types = {edge["id"]: edge["connection_type"] for edge in model["connections"]}

    assert all(types[f"E{i:02d}"] == "power" for i in range(1, 29))
    assert all(types[f"E{i}"] == "control_monitoring" for i in range(29, 33))
    assert types["E33"] == "auxiliary_power"
    assert all(types[f"E{i}"] == "test_power" for i in range(34, 37))


def test_faa_drpds_source_pages_are_numeric_and_provenance_is_resolvable():
    model = load_json(MODEL_PATH)
    document_ids = {document["id"] for document in model["source_documents"]}

    for collection in ("components", "connections", "circuits"):
        for item in model[collection]:
            for source in item.get("sources", []):
                assert source["document_id"] in document_ids, item["id"]
                if source.get("page") is not None:
                    assert isinstance(source["page"], int), item["id"]
                    assert source["page"] >= 1, item["id"]
