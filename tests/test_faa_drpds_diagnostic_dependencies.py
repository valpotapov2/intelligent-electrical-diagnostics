import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "diagnostics" / "scenarios" / "faa-drpds-diagnostic-dependencies.v0.1.json"
GRAPH_PATH = ROOT / "examples" / "objects" / "faa-drpds.generic.json"


def test_faa_dependency_model_references_existing_graph_components():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    component_ids = {item["id"] for item in graph["components"]}
    assert model["source_model"] == "examples/objects/faa-drpds.generic.json"
    assert model["execution_mode"] == "architecture_only"
    assert model["semantics"]["not_a_measurement_plan"] is True
    assert model["semantics"]["not_a_site_as_built_model"] is True
    assert model["questions"]
    for question in model["questions"]:
        assert question["component_refs"]
        assert set(question["component_refs"]) <= component_ids
        assert question["sources"]
        assert question["required_evidence"]
        assert question["cannot_conclude_from"]


def test_faa_dependency_model_prerequisites_resolve_and_are_acyclic():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    questions = {item["id"]: item for item in model["questions"]}
    assert len(questions) == len(model["questions"])
    for question in questions.values():
        assert set(question["prerequisites"]) <= set(questions)

    visiting = set()
    visited = set()

    def visit(question_id):
        if question_id in visiting:
            raise AssertionError(f"dependency cycle at {question_id}")
        if question_id in visited:
            return
        visiting.add(question_id)
        for prerequisite in questions[question_id]["prerequisites"]:
            visit(prerequisite)
        visiting.remove(question_id)
        visited.add(question_id)

    for question_id in questions:
        visit(question_id)


def test_faa_dependency_model_does_not_claim_physical_measurement_values():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    serialized = json.dumps(model).lower()
    assert '"value":' not in serialized
    assert "terminal_number" not in serialized
    assert "measurement_limit" not in serialized


def test_faa_control_power_is_an_explicit_prerequisite_where_relevant():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    questions = {item["id"]: item for item in model["questions"]}
    control = questions["DQ-CONTROL-POWER"]
    assert control["component_refs"] == ["DC125"]
    assert "DC_bus_state" in control["required_evidence"]
    assert "battery_subsystem_state" in control["required_evidence"]
    assert "DQ-CONTROL-POWER" in questions["DQ-SWGR-STANDBY-TRANSFER"]["prerequisites"]
    assert "DQ-CONTROL-POWER" in questions["DQ-PMCS-TRUSTWORTHINESS"]["prerequisites"]
    assert "DQ-CONTROL-POWER" not in questions["DQ-SWGR-SECTION-SUPPLY"]["prerequisites"]


def test_faa_loadbank_test_path_is_architecture_only_and_not_synthetic():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    question = next(item for item in model["questions"] if item["id"] == "DQ-LOADBANK-TEST-PATH")
    component_ids = {item["id"] for item in graph["components"]}
    assert set(question["component_refs"]) <= component_ids
    assert set(question["component_refs"]) == {"PSG", "UPS-SWBD", "LOADBANK-SWBD", "LOADBANK"}
    assert "load_bank_switchboard_interlock_state" in question["required_evidence"]
    assert "load_bank_nonresponse_without_source_and_interlock_evidence" in question["cannot_conclude_from"]
    assert "does not define or authorize a test procedure" in question["applicability"]
    assert "load testing" in " ".join(model["global_constraints"]).lower()
