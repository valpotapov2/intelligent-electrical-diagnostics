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


def test_faa_ups_roles_are_separated_without_inventing_site_instances():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    questions = {item["id"]: item for item in model["questions"]}
    graph_components = {item["id"]: item for item in graph["components"]}

    reserve = questions["DQ-UPS-1-BYPASS-RESERVE"]
    ups2 = questions["DQ-UPS-2-OUTPUT-PATH"]
    ups3 = questions["DQ-UPS-3-OUTPUT-PATH"]

    assert set(reserve["component_refs"]) <= set(graph_components)
    assert set(ups2["component_refs"]) <= set(graph_components)
    assert set(ups3["component_refs"]) <= set(graph_components)
    assert graph_components["UPS-GROUP"]["attributes"]["ups_1_role"] == "bypass_source_for_ups_2_and_ups_3"
    assert graph_components["UPS-GROUP"]["attributes"]["ups_2_output"] == "critical_bus_A"
    assert graph_components["UPS-GROUP"]["attributes"]["ups_3_output"] == "critical_bus_B"
    assert "documented_bypass_path_state_for_the_relevant_UPS" in reserve["required_evidence"]
    assert "documented_UPS_2_to_Critical_Bus_A_assignment" in ups2["required_evidence"]
    assert "documented_UPS_3_to_Critical_Bus_B_assignment" in ups3["required_evidence"]
    assert "verify the installed site's" in ups2["applicability"]
    assert "verify the installed site's" in ups3["applicability"]


def test_faa_pdu_input_feeder_and_pair_questions_respect_grouped_source_boundary():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    questions = {item["id"]: item for item in model["questions"]}
    components = {item["id"]: item for item in graph["components"]}
    pdu = components["PDU-GROUP"]["attributes"]

    input_question = questions["DQ-PDU-INPUT-CONDITION"]
    feeder = questions["DQ-PDU-OUTGOING-FEEDER"]
    pair = questions["DQ-PDU-MAINTENANCE-PAIR"]

    for question in (input_question, feeder, pair):
        assert set(question["component_refs"]) <= set(components)
    assert pdu["typical_count"] == 8
    assert pdu["hcf_count"] == 6
    assert pdu["input"] == "480/277 V three-wire"
    assert pdu["output"] == "208/120 V four-wire"
    assert pdu["paired_for_maintenance"] is True
    assert pdu["each_pdu_feeds_two_sats"] is True
    assert "specific_PDU_identity_and_documented_upstream_bus_assignment" in input_question["required_evidence"]
    assert "documented_PDU_to_SATS_input_assignment" in feeder["required_evidence"]
    assert "documented_identity_of_the_PDU_maintenance_pair" in pair["required_evidence"]
    assert "individual pair map" in pair["applicability"]
    assert "aggregate_PDU_and_SATS_counts" in pair["cannot_conclude_from"]


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



def test_faa_sats_dual_input_and_transfer_questions_respect_grouped_source_boundary():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    questions = {item["id"]: item for item in model["questions"]}
    components = {item["id"]: item for item in graph["components"]}
    dual = questions["DQ-SATS-DUAL-INPUT-AVAILABILITY"]
    transfer = questions["DQ-SATS-AUTO-TRANSFER"]
    umbrella = questions["DQ-SATS-SOURCE-SELECTION"]

    for question in (dual, transfer, umbrella):
        assert set(question["component_refs"]) <= set(components)
    assert dual["prerequisites"] == ["DQ-PDU-OUTGOING-FEEDER"]
    assert transfer["prerequisites"] == ["DQ-SATS-DUAL-INPUT-AVAILABILITY"]
    assert set(umbrella["prerequisites"]) == {
        "DQ-SATS-DUAL-INPUT-AVAILABILITY", "DQ-SATS-AUTO-TRANSFER"
    }
    assert "documented_source_A_PDU_and_feeder_assignment_to_SATS_input" in dual["required_evidence"]
    assert "documented_source_B_PDU_and_feeder_assignment_to_SATS_input" in dual["required_evidence"]
    assert "selected_source_state_before_and_after_event" in transfer["required_evidence"]
    assert "SATS_output_continuity_and_quality_evidence" in transfer["required_evidence"]
    assert "sensing thresholds" in transfer["applicability"]
    assert "individual_feeder_mapping" in dual["cannot_conclude_from"]
    assert "SATS-GROUP" in components
    assert "PDU-GROUP" in components
