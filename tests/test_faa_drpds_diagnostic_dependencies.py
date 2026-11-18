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
    assert umbrella["prerequisites"] == ["DQ-SATS-DUAL-INPUT-AVAILABILITY"]
    assert "DQ-SATS-AUTO-TRANSFER" not in umbrella["prerequisites"]
    assert "documented_source_A_PDU_and_feeder_assignment_to_SATS_input" in dual["required_evidence"]
    assert "documented_source_B_PDU_and_feeder_assignment_to_SATS_input" in dual["required_evidence"]
    assert "selected_source_state_before_and_after_event" in transfer["required_evidence"]
    assert "SATS_output_continuity_and_quality_evidence" in transfer["required_evidence"]
    assert "sensing thresholds" in transfer["applicability"]
    assert "aggregate_PDU_to_SATS_relationship_without_individual_feeder_mapping" in dual["cannot_conclude_from"]
    assert "SATS-GROUP" in components
    assert "PDU-GROUP" in components


def test_faa_cdp_incoming_and_branch_questions_respect_grouped_source_boundary():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    questions = {item["id"]: item for item in model["questions"]}
    components = {item["id"]: item for item in graph["components"]}
    incoming = questions["DQ-CDP-INCOMING-PATH"]
    branch = questions["DQ-CDP-OUTGOING-BRANCH"]
    umbrella = questions["DQ-CDP-OUTGOING-CIRCUIT"]

    for question in (incoming, branch, umbrella):
        assert set(question["component_refs"]) <= set(components)
    assert incoming["prerequisites"] == ["DQ-SATS-SOURCE-SELECTION"]
    assert branch["prerequisites"] == ["DQ-CDP-INCOMING-PATH"]
    assert umbrella["prerequisites"] == ["DQ-CDP-INCOMING-PATH", "DQ-CDP-OUTGOING-BRANCH"]
    assert "specific_CDP_identity_and_documented_SATS_output_assignment" in incoming["required_evidence"]
    assert "current_site_drawing_for_the_SATS_to_CDP_incoming_path" in incoming["required_evidence"]
    assert "documented_branch_to_critical_load_assignment" in branch["required_evidence"]
    assert "outgoing_protective_device_state_and_measurement_validity" in branch["required_evidence"]
    assert "aggregate_SATS_to_CDP_relationship_without_individual_assignment" in incoming["cannot_conclude_from"]
    assert "aggregate_CDP_to_critical_loads_relationship_without_individual_branch_mapping" in branch["cannot_conclude_from"]
    assert "maintenance isolation" in incoming["applicability"]
    assert "CDP-GROUP" in components



def test_faa_pmcs_diagnostic_chain_is_decomposed_without_inventing_signal_topology():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    questions = {item["id"]: item for item in model["questions"]}
    components = {item["id"] for item in graph["components"]}
    channel = questions["DQ-PMCS-MEASUREMENT-CHANNEL"]
    plc = questions["DQ-PMCS-PLC-ACQUISITION"]
    comms = questions["DQ-PMCS-COMMS-OWS-FRESHNESS"]
    umbrella = questions["DQ-PMCS-TRUSTWORTHINESS"]

    assert set(channel["component_refs"] + plc["component_refs"] + comms["component_refs"] + umbrella["component_refs"]) <= components
    assert channel["prerequisites"] == []
    assert plc["prerequisites"] == ["DQ-PMCS-MEASUREMENT-CHANNEL"]
    assert comms["prerequisites"] == ["DQ-PMCS-PLC-ACQUISITION"]
    assert set(umbrella["prerequisites"]) == {
        "DQ-CONTROL-POWER",
        "DQ-PMCS-MEASUREMENT-CHANNEL",
        "DQ-PMCS-PLC-ACQUISITION",
        "DQ-PMCS-COMMS-OWS-FRESHNESS",
    }
    assert "independent_physical_or_electrical_cross_check" in umbrella["required_evidence"]
    assert "PMCS screen indication alone" in umbrella["applicability"]


def test_faa_pmcs_decomposition_is_uncovered_by_synthetic_core():
    crosswalk_path = ROOT / "diagnostics" / "scenarios" / "faa-drpds-core-crosswalk.v0.1.json"
    crosswalk = json.loads(crosswalk_path.read_text(encoding="utf-8"))
    mappings = {item["question_id"]: item for item in crosswalk["mappings"]}
    for question_id in (
        "DQ-PMCS-MEASUREMENT-CHANNEL",
        "DQ-PMCS-PLC-ACQUISITION",
        "DQ-PMCS-COMMS-OWS-FRESHNESS",
    ):
        assert mappings[question_id]["coverage"] == "none"
        assert mappings[question_id]["synthetic_modes"] == []


def test_faa_generator_diagnostic_chain_localizes_start_output_connection_and_capacity():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    questions = {item["id"]: item for item in model["questions"]}
    components = {item["id"] for item in graph["components"]}
    start = questions["DQ-GENERATOR-START-READINESS"]
    output = questions["DQ-GENERATOR-ELECTRICAL-OUTPUT"]
    connection = questions["DQ-GENERATOR-SYNCHRONIZATION-CONNECTION"]
    capacity = questions["DQ-GENERATOR-CAPACITY-RESERVE"]
    umbrella = questions["DQ-GENERATOR-AVAILABILITY"]
    for question in (start, output, connection, capacity, umbrella):
        assert set(question["component_refs"]) <= components
    assert start["prerequisites"] == []
    assert output["prerequisites"] == ["DQ-GENERATOR-START-READINESS"]
    assert connection["prerequisites"] == ["DQ-GENERATOR-ELECTRICAL-OUTPUT"]
    assert capacity["prerequisites"] == ["DQ-GENERATOR-SYNCHRONIZATION-CONNECTION"]
    assert set(umbrella["prerequisites"]) == {
        "DQ-GENERATOR-START-READINESS",
        "DQ-GENERATOR-ELECTRICAL-OUTPUT",
        "DQ-GENERATOR-SYNCHRONIZATION-CONNECTION",
        "DQ-GENERATOR-CAPACITY-RESERVE",
    }
    assert "historical_typical_unit_count_as_a_site_specific_capacity_threshold" in capacity["cannot_conclude_from"]


def test_faa_generator_decomposition_is_not_claimed_by_synthetic_bus_fixture():
    crosswalk_path = ROOT / "diagnostics" / "scenarios" / "faa-drpds-core-crosswalk.v0.1.json"
    crosswalk = json.loads(crosswalk_path.read_text(encoding="utf-8"))
    mappings = {item["question_id"]: item for item in crosswalk["mappings"]}
    for question_id in (
        "DQ-GENERATOR-START-READINESS",
        "DQ-GENERATOR-ELECTRICAL-OUTPUT",
        "DQ-GENERATOR-SYNCHRONIZATION-CONNECTION",
        "DQ-GENERATOR-CAPACITY-RESERVE",
    ):
        assert mappings[question_id]["coverage"] == "none"
        assert mappings[question_id]["synthetic_modes"] == []
    assert mappings["DQ-GENERATOR-AVAILABILITY"]["coverage"] == "partial"
    assert mappings["DQ-GENERATOR-AVAILABILITY"]["synthetic_modes"] == ["Generator_bus_evidence_loss"]


def test_faa_swgr_transfer_chain_separates_mode_permissives_and_breaker_execution():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    questions = {item["id"]: item for item in model["questions"]}
    components = {item["id"] for item in graph["components"]}
    mode = questions["DQ-SWGR-CONTROL-MODE"]
    permissives = questions["DQ-SWGR-TRANSFER-PERMISSIVES"]
    actuation = questions["DQ-SWGR-BREAKER-ACTUATION"]
    umbrella = questions["DQ-SWGR-STANDBY-TRANSFER"]
    for question in (mode, permissives, actuation, umbrella):
        assert set(question["component_refs"]) <= components
    assert mode["prerequisites"] == []
    assert set(permissives["prerequisites"]) == {"DQ-SOURCE-AVAILABILITY", "DQ-TRANSFORMER-INPUT-OUTPUT", "DQ-GENERATOR-AVAILABILITY"}
    assert set(actuation["prerequisites"]) == {
        "DQ-SWGR-CONTROL-MODE", "DQ-SWGR-TRANSFER-PERMISSIVES", "DQ-CONTROL-POWER"
    }
    assert set(umbrella["prerequisites"]) == {
        "DQ-SOURCE-AVAILABILITY", "DQ-TRANSFORMER-INPUT-OUTPUT", "DQ-GENERATOR-AVAILABILITY", "DQ-CONTROL-POWER",
        "DQ-SWGR-CONTROL-MODE", "DQ-SWGR-TRANSFER-PERMISSIVES", "DQ-SWGR-BREAKER-ACTUATION"
    }
    assert "AUTO_LOCAL_MANUAL_selector_state_and_timestamp" in mode["required_evidence"]
    assert "event_context_and_permissive_state_at_command_time" in permissives["required_evidence"]
    assert "independent_electrical_state_of_relevant_section_or_path" in actuation["required_evidence"]
    assert "auxiliary_contact_alone_as_proof_of_primary_contact_condition" in actuation["cannot_conclude_from"]


def test_faa_swgr_transfer_decomposition_is_not_claimed_by_synthetic_fixture():
    crosswalk_path = ROOT / "diagnostics" / "scenarios" / "faa-drpds-core-crosswalk.v0.1.json"
    crosswalk = json.loads(crosswalk_path.read_text(encoding="utf-8"))
    mappings = {item["question_id"]: item for item in crosswalk["mappings"]}
    for question_id in (
        "DQ-SWGR-CONTROL-MODE",
        "DQ-SWGR-TRANSFER-PERMISSIVES",
        "DQ-SWGR-BREAKER-ACTUATION",
    ):
        assert mappings[question_id]["coverage"] == "none"
        assert mappings[question_id]["synthetic_modes"] == []


def test_faa_transformer_input_output_diagnostic_is_source_backed_and_site_bounded():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    questions = {item["id"]: item for item in model["questions"]}
    components = {item["id"] for item in graph["components"]}
    transformer = questions["DQ-TRANSFORMER-INPUT-OUTPUT"]
    source = questions["DQ-SOURCE-AVAILABILITY"]

    assert set(transformer["component_refs"]) <= components
    assert transformer["prerequisites"] == ["DQ-SOURCE-AVAILABILITY"]
    assert "transformer_input_state_and_measurement_channel_validity" in transformer["required_evidence"]
    assert "transformer_output_state_and_measurement_channel_validity" in transformer["required_evidence"]
    assert "documented_transformer_protection_or_condition_indication_when_available" in transformer["required_evidence"]
    assert source["prerequisites"] == []
    assert "transformer_input_output_evidence" not in source["required_evidence"]
    assert "source_side_measurement_identity_quality_and_timestamp" in source["required_evidence"]
    assert "physical_commercial_source_loss_or_out_of_documented_condition" in source["distinguishes"]
    assert "assumed_primary_voltage_transformer_rating_or_impedance" in transformer["cannot_conclude_from"]
    assert "480/277 V" in transformer["applicability"]
    assert "site-specific" in transformer["applicability"]


def test_faa_transformer_decomposition_is_not_claimed_by_synthetic_core():
    crosswalk_path = ROOT / "diagnostics" / "scenarios" / "faa-drpds-core-crosswalk.v0.1.json"
    crosswalk = json.loads(crosswalk_path.read_text(encoding="utf-8"))
    mappings = {item["question_id"]: item for item in crosswalk["mappings"]}
    assert mappings["DQ-TRANSFORMER-INPUT-OUTPUT"]["coverage"] == "none"
    assert mappings["DQ-TRANSFORMER-INPUT-OUTPUT"]["synthetic_modes"] == []



def test_faa_commercial_source_independence_is_documented_but_site_verification_is_required():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    questions = {item["id"]: item for item in model["questions"]}
    components = {item["id"] for item in graph["components"]}
    independence = questions["DQ-COMMERCIAL-SOURCE-INDEPENDENCE"]

    assert set(independence["component_refs"]) == {"U1", "U2"}
    assert set(independence["component_refs"]) <= components
    assert independence["prerequisites"] == []
    assert "current_site_one_line_or_utility_records_showing_upstream_source_origins_when_available" in independence["required_evidence"]
    assert "documented_shared_upstream_supply_dependency" in independence["distinguishes"]
    assert "U1_and_U2_labels_alone_as_proof_of_independent_upstream_sources" in independence["cannot_conclude_from"]
    assert "historical FAA reference describes two independent" in independence["applicability"]


def test_faa_source_and_transformer_path_are_separate_stages_before_swgr_supply():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    questions = {item["id"]: item for item in model["questions"]}
    source = questions["DQ-SOURCE-AVAILABILITY"]
    transformer = questions["DQ-TRANSFORMER-INPUT-OUTPUT"]
    section = questions["DQ-SWGR-SECTION-SUPPLY"]

    assert source["prerequisites"] == []
    assert transformer["prerequisites"] == ["DQ-SOURCE-AVAILABILITY"]
    assert set(section["prerequisites"]) == {"DQ-SOURCE-AVAILABILITY", "DQ-TRANSFORMER-INPUT-OUTPUT"}
    assert "transformer_input_state_and_measurement_channel_validity" in transformer["required_evidence"]
    assert "transformer_output_state_and_measurement_channel_validity" in transformer["required_evidence"]
    assert "physical_source_loss" not in transformer["distinguishes"]


def test_faa_essential_distribution_is_localized_by_feeder_mcc_and_load_evidence():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    questions = {item["id"]: item for item in model["questions"]}
    feeder = questions["DQ-ESSENTIAL-SWBD-FEEDER"]
    mcc = questions["DQ-ESSENTIAL-MCC-CONTROL"]
    load = questions["DQ-ESSENTIAL-LOAD-RESPONSE"]
    shed = questions["DQ-ESSENTIAL-LOAD-SHED-RESTORE"]
    umbrella = questions["DQ-ESSENTIAL-FEED"]

    assert feeder["prerequisites"] == ["DQ-SWGR-SECTION-SUPPLY"]
    assert mcc["prerequisites"] == ["DQ-ESSENTIAL-SWBD-FEEDER"]
    assert load["prerequisites"] == ["DQ-ESSENTIAL-MCC-CONTROL"]
    assert umbrella["prerequisites"] == [
        "DQ-ESSENTIAL-SWBD-FEEDER",
        "DQ-ESSENTIAL-MCC-CONTROL",
        "DQ-ESSENTIAL-LOAD-RESPONSE",
    ]
    assert shed["prerequisites"] == ["DQ-GENERATOR-CAPACITY-RESERVE"]
    assert "site_specific_load_priority_or_shed_restore_criteria" in shed["required_evidence"]
    assert "historical_typical_generator_count_as_a_site_specific_threshold" in shed["cannot_conclude_from"]

    crosswalk_path = ROOT / "diagnostics" / "scenarios" / "faa-drpds-core-crosswalk.v0.1.json"
    crosswalk = json.loads(crosswalk_path.read_text(encoding="utf-8"))
    mappings = {item["question_id"]: item for item in crosswalk["mappings"]}
    for question_id in (
        "DQ-ESSENTIAL-SWBD-FEEDER",
        "DQ-ESSENTIAL-MCC-CONTROL",
        "DQ-ESSENTIAL-LOAD-RESPONSE",
        "DQ-ESSENTIAL-LOAD-SHED-RESTORE",
    ):
        assert mappings[question_id]["coverage"] == "none"
        assert mappings[question_id]["synthetic_modes"] == []


def test_faa_ups_supply_switchgear_input_and_outgoing_feeder_are_separate_stages():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    questions = {item["id"]: item for item in model["questions"]}
    incoming = questions["DQ-UPS-SWGR-INPUT"]
    feeder = questions["DQ-UPS-SWGR-FEEDER"]

    assert incoming["prerequisites"] == ["DQ-SWGR-SECTION-SUPPLY"]
    assert feeder["prerequisites"] == ["DQ-UPS-SWGR-INPUT"]
    for question_id in (
        "DQ-UPS-CONVERSION-PATH",
        "DQ-UPS-BYPASS-PATH",
        "DQ-UPS-DC-BATTERY",
    ):
        assert questions[question_id]["prerequisites"] == ["DQ-UPS-SWGR-FEEDER"]
    assert set(questions["DQ-UPS-HEALTH"]["prerequisites"]) == {
        "DQ-UPS-SWGR-FEEDER",
        "DQ-UPS-CONVERSION-PATH",
        "DQ-UPS-BYPASS-PATH",
        "DQ-UPS-DC-BATTERY",
    }

    assert "site_documented_UPS_SWGR_incoming_source_and_connection_identity" in incoming["required_evidence"]
    assert "assumed_number_or_source_pairing_of_UPS_SWGR_incomers" in incoming["cannot_conclude_from"]
    assert "specific_UPS_and_outgoing_feeder_assignment_from_current_site_records" in feeder["required_evidence"]
    assert "aggregate_UPS_SWGR_node_as_proof_of_individual_feeder_mapping" in feeder["cannot_conclude_from"]

    crosswalk_path = ROOT / "diagnostics" / "scenarios" / "faa-drpds-core-crosswalk.v0.1.json"
    crosswalk = json.loads(crosswalk_path.read_text(encoding="utf-8"))
    mappings = {item["question_id"]: item for item in crosswalk["mappings"]}
    for question_id in ("DQ-UPS-SWGR-INPUT", "DQ-UPS-SWGR-FEEDER"):
        assert mappings[question_id]["coverage"] == "none"
        assert mappings[question_id]["synthetic_modes"] == []


def test_faa_ups_internal_conversion_bypass_and_battery_stages_are_separate():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    questions = {item["id"]: item for item in model["questions"]}
    conversion = questions["DQ-UPS-CONVERSION-PATH"]
    bypass = questions["DQ-UPS-BYPASS-PATH"]
    battery = questions["DQ-UPS-DC-BATTERY"]
    health = questions["DQ-UPS-HEALTH"]

    for question in (conversion, bypass, battery):
        assert question["prerequisites"] == ["DQ-UPS-SWGR-FEEDER"]
        assert question["sources"]
        assert question["required_evidence"]
        assert question["cannot_conclude_from"]
    assert set(conversion["component_refs"]) == {"UPS-GROUP"}
    assert "rectifier_operating_state_and_available_alarm_or_event_evidence" in conversion["required_evidence"]
    assert "inverter_operating_state_and_available_alarm_or_event_evidence" in conversion["required_evidence"]
    assert "UPS_output_present_as_proof_that_inverter_is_supplying_the_load" in bypass["cannot_conclude_from"]
    assert "battery_test_results_and_event_history" in battery["required_evidence"]
    assert "charger_state_and_available_alarm_evidence_when_present" in battery["required_evidence"]
    assert "Evaluate the UPS DC bus" in battery["applicability"]
    assert set(health["prerequisites"]) == {
        "DQ-UPS-SWGR-FEEDER",
        "DQ-UPS-CONVERSION-PATH",
        "DQ-UPS-BYPASS-PATH",
        "DQ-UPS-DC-BATTERY",
    }
    assert questions["DQ-UPS-1-BYPASS-RESERVE"]["prerequisites"] == ["DQ-UPS-BYPASS-PATH"]
    assert questions["DQ-UPS-2-OUTPUT-PATH"]["prerequisites"] == ["DQ-UPS-HEALTH"]
    assert questions["DQ-UPS-3-OUTPUT-PATH"]["prerequisites"] == ["DQ-UPS-HEALTH"]

    crosswalk_path = ROOT / "diagnostics" / "scenarios" / "faa-drpds-core-crosswalk.v0.1.json"
    crosswalk = json.loads(crosswalk_path.read_text(encoding="utf-8"))
    mappings = {item["question_id"]: item for item in crosswalk["mappings"]}
    for question_id in (
        "DQ-UPS-CONVERSION-PATH",
        "DQ-UPS-BYPASS-PATH",
        "DQ-UPS-DC-BATTERY",
    ):
        assert mappings[question_id]["coverage"] == "none"
        assert mappings[question_id]["synthetic_modes"] == []


def test_faa_pdu_input_conversion_and_internal_protection_are_separate_stages():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    questions = {item["id"]: item for item in model["questions"]}
    incoming = questions["DQ-PDU-INPUT-SUPPLY"]
    conversion = questions["DQ-PDU-VOLTAGE-CONVERSION"]
    protection = questions["DQ-PDU-INTERNAL-PROTECTION"]
    umbrella = questions["DQ-PDU-INPUT-CONDITION"]
    outgoing = questions["DQ-PDU-OUTGOING-FEEDER"]

    assert incoming["prerequisites"] == ["DQ-CRITICAL-BUS"]
    assert conversion["prerequisites"] == ["DQ-PDU-INPUT-SUPPLY"]
    assert protection["prerequisites"] == ["DQ-PDU-INPUT-SUPPLY"]
    assert set(umbrella["prerequisites"]) == {
        "DQ-PDU-INPUT-SUPPLY",
        "DQ-PDU-VOLTAGE-CONVERSION",
        "DQ-PDU-INTERNAL-PROTECTION",
    }
    assert outgoing["prerequisites"] == ["DQ-PDU-INPUT-CONDITION"]
    assert "historical_480_277_to_208_120_V_reference_as_installed_site_rating" in conversion["cannot_conclude_from"]
    assert "assumed_transformer_or_conversion_technology_inside_the_PDU" in conversion["cannot_conclude_from"]
    assert "outgoing_feeder_protection_state_as_proof_of_PDU_main_protection_state" in protection["cannot_conclude_from"]
    assert "outgoing-feeder protective device belongs to DQ-PDU-OUTGOING-FEEDER" in protection["applicability"]
    assert "internal_switching_device_identity_and_state_when_documented" in protection["required_evidence"]
    assert "switching_command_and_feedback_state_when_present_and_documented" in protection["required_evidence"]
    assert "assessed only when the installed design documents one" in protection["applicability"]

    crosswalk_path = ROOT / "diagnostics" / "scenarios" / "faa-drpds-core-crosswalk.v0.1.json"
    crosswalk = json.loads(crosswalk_path.read_text(encoding="utf-8"))
    mappings = {item["question_id"]: item for item in crosswalk["mappings"]}
    for question_id in ("DQ-PDU-INPUT-SUPPLY", "DQ-PDU-VOLTAGE-CONVERSION", "DQ-PDU-INTERNAL-PROTECTION"):
        assert mappings[question_id]["coverage"] == "none"
        assert mappings[question_id]["synthetic_modes"] == []
