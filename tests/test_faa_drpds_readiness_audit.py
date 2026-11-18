"""FAA DRPDS architecture readiness and crosswalk invariants."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "diagnostics" / "scenarios"


def test_faa_readiness_question_and_crosswalk_inventory():
    model = json.loads((SCENARIOS / "faa-drpds-diagnostic-dependencies.v0.1.json").read_text(encoding="utf-8"))
    crosswalk = json.loads((SCENARIOS / "faa-drpds-core-crosswalk.v0.1.json").read_text(encoding="utf-8"))
    graph = json.loads((ROOT / "examples" / "objects" / "faa-drpds.generic.json").read_text(encoding="utf-8"))

    question_ids = [question["id"] for question in model["questions"]]
    mapping_ids = [mapping["question_id"] for mapping in crosswalk["mappings"]]
    component_ids = {component["id"] for component in graph["components"]}
    assert len(question_ids) == len(set(question_ids))
    assert len(mapping_ids) == len(set(mapping_ids))
    assert set(question_ids) == set(mapping_ids)
    assert model["execution_mode"] == "architecture_only"
    assert len(question_ids) == 51
    assert len(graph["components"]) == 29
    assert len(graph["connections"]) == 36
    assert len(graph["issues"]) == 5

    for question in model["questions"]:
        assert set(question["component_refs"]) <= component_ids
        assert set(question["prerequisites"]) <= set(question_ids)
        assert question["id"] not in question["prerequisites"]

    seen, visiting = set(), set()
    prerequisites = {question["id"]: question["prerequisites"] for question in model["questions"]}

    def visit(question_id):
        assert question_id not in visiting, "Diagnostic prerequisite cycle"
        if question_id in seen:
            return
        visiting.add(question_id)
        for prerequisite in prerequisites[question_id]:
            visit(prerequisite)
        visiting.remove(question_id)
        seen.add(question_id)

    for question_id in question_ids:
        visit(question_id)


def test_faa_readiness_coverage_never_implies_physical_diagnosis():
    crosswalk = json.loads((SCENARIOS / "faa-drpds-core-crosswalk.v0.1.json").read_text(encoding="utf-8"))
    mappings = crosswalk["mappings"]
    assert sum(item["coverage"] == "partial" for item in mappings) == 7
    assert sum(item["coverage"] == "none" for item in mappings) == 44
    assert all(item["coverage"] in {"none", "partial"} for item in mappings)
    assert all(not item["synthetic_modes"] for item in mappings if item["coverage"] == "none")
    assert all(item["synthetic_modes"] for item in mappings if item["coverage"] == "partial")
    by_id = {item["question_id"]: item for item in mappings}
    for question_id in (
        "DQ-PDU-INPUT-SUPPLY",
        "DQ-PDU-VOLTAGE-CONVERSION",
        "DQ-PDU-INTERNAL-PROTECTION",
    ):
        assert by_id[question_id]["coverage"] == "none"
        assert by_id[question_id]["synthetic_modes"] == []
