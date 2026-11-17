import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CROSSWALK_PATH = ROOT / "diagnostics" / "scenarios" / "faa-drpds-core-crosswalk.v0.1.json"
DEPENDENCIES_PATH = ROOT / "diagnostics" / "scenarios" / "faa-drpds-diagnostic-dependencies.v0.1.json"
MODULE_PATH = ROOT / "benchmarks" / "faa-drpds" / "diagnostic-core-module.synthetic.yaml"


def test_faa_core_crosswalk_covers_every_architecture_question_once():
    crosswalk = json.loads(CROSSWALK_PATH.read_text(encoding="utf-8"))
    dependencies = json.loads(DEPENDENCIES_PATH.read_text(encoding="utf-8"))
    question_ids = {item["id"] for item in dependencies["questions"]}
    mappings = crosswalk["mappings"]
    mapped_ids = [item["question_id"] for item in mappings]

    assert crosswalk["execution_mode"] == "test_traceability_only"
    assert crosswalk["semantics"]["executable_mapping"] is False
    assert crosswalk["semantics"]["physical_equivalence"] is False
    assert set(mapped_ids) == question_ids
    assert len(mapped_ids) == len(set(mapped_ids))
    assert all(item["rationale"] for item in mappings)
    assert all(item["coverage"] in {"partial", "none"} for item in mappings)


def test_faa_core_crosswalk_modes_exist_in_synthetic_module():
    crosswalk = json.loads(CROSSWALK_PATH.read_text(encoding="utf-8"))
    module_text = MODULE_PATH.read_text(encoding="utf-8")
    known_modes = {
        "Healthy",
        "Critical_A_path_loss",
        "Critical_B_path_loss",
        "Dual_critical_path_loss",
        "SATS_output_loss",
        "Essential_feed_loss",
    }

    for mapping in crosswalk["mappings"]:
        assert set(mapping["synthetic_modes"]) <= known_modes
        if mapping["coverage"] == "none":
            assert mapping["synthetic_modes"] == []
        else:
            assert mapping["synthetic_modes"]
    assert "synthetic software-only" in module_text.lower()


def test_faa_core_crosswalk_does_not_claim_execution_or_physical_measurements():
    crosswalk = json.loads(CROSSWALK_PATH.read_text(encoding="utf-8"))
    serialized = json.dumps(crosswalk).lower()
    assert crosswalk["semantics"]["field_measurement_plan"] is False
    assert "measurementrequest" not in serialized
    assert "terminal_number" not in serialized
    assert '"value":' not in serialized
    assert all("not" in item["rationale"].lower() or item["coverage"] == "partial"
               for item in crosswalk["mappings"])
