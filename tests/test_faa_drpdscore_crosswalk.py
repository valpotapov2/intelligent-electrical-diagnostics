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
        "Source_1_evidence_loss",
        "Source_2_evidence_loss",
        "SWGR_1_section_evidence_loss",
        "SWGR_2_section_evidence_loss",
        "Generator_bus_evidence_loss",
        "Standby_transfer_evidence_loss",
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
    assert "measurementrequest" not in json.dumps(crosswalk["mappings"]).lower()
    assert "terminal_number" not in serialized
    assert '"value":' not in serialized
    assert "not evidence that the synthetic mode diagnoses" in " ".join(crosswalk["constraints"]).lower()
    assert "unmapped questions" in " ".join(crosswalk["constraints"]).lower()


def test_faa_ups_role_questions_are_explicitly_uncovered_by_synthetic_core():
    crosswalk = json.loads(CROSSWALK_PATH.read_text(encoding="utf-8"))
    mappings = {item["question_id"]: item for item in crosswalk["mappings"]}
    for question_id in (
        "DQ-UPS-1-BYPASS-RESERVE",
        "DQ-UPS-2-OUTPUT-PATH",
        "DQ-UPS-3-OUTPUT-PATH",
    ):
        assert mappings[question_id]["coverage"] == "none"
        assert mappings[question_id]["synthetic_modes"] == []


def test_faa_pdu_questions_are_explicitly_uncovered_by_synthetic_core():
    crosswalk = json.loads(CROSSWALK_PATH.read_text(encoding="utf-8"))
    mappings = {item["question_id"]: item for item in crosswalk["mappings"]}
    for question_id in (
        "DQ-PDU-INPUT-CONDITION",
        "DQ-PDU-OUTGOING-FEEDER",
        "DQ-PDU-MAINTENANCE-PAIR",
    ):
        assert mappings[question_id]["coverage"] == "none"
        assert mappings[question_id]["synthetic_modes"] == []


def test_faa_loadbank_question_is_explicitly_uncovered_by_synthetic_core():
    crosswalk = json.loads(CROSSWALK_PATH.read_text(encoding="utf-8"))
    mapping = next(item for item in crosswalk["mappings"] if item["question_id"] == "DQ-LOADBANK-TEST-PATH")
    assert mapping["coverage"] == "none"
    assert mapping["synthetic_modes"] == []
    assert "load-bank" in mapping["rationale"].lower()



def test_faa_sats_input_and_transfer_questions_are_uncovered_by_synthetic_core():
    crosswalk = json.loads(CROSSWALK_PATH.read_text(encoding="utf-8"))
    mappings = {item["question_id"]: item for item in crosswalk["mappings"]}
    for question_id in ("DQ-SATS-DUAL-INPUT-AVAILABILITY", "DQ-SATS-AUTO-TRANSFER"):
        assert mappings[question_id]["coverage"] == "none"
        assert mappings[question_id]["synthetic_modes"] == []
