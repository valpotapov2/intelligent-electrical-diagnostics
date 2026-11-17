import json
from pathlib import Path

from edi_ingest.scenario_runner import run_benchmark

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "examples/objects/faa-drpds.generic.json"
SCENARIOS = ROOT / "benchmarks/faa-drpds/scenarios.v0.1.json"


def test_faa_drpds_scenarios_have_expected_graph_scope():
    report = run_benchmark(MODEL, SCENARIOS)
    assert report["scenario_count"] == 8
    assert report["passed"] == 8
    assert report["failed"] == 0
    assert report["diagnostic_capability"] == "graph_reachability_only"


def test_loss_of_one_critical_bus_path_keeps_alternate_path_reachable():
    report = run_benchmark(MODEL, SCENARIOS)
    result = next(x for x in report["results"] if x["scenario_id"] == "DRPDS-CRITICAL-A-LOSS-001")
    assert result["affected_load_ids"] == []


def test_loss_of_both_critical_paths_affects_only_critical_load_group():
    report = run_benchmark(MODEL, SCENARIOS)
    result = next(x for x in report["results"] if x["scenario_id"] == "DRPDS-CRITICAL-BOTH-LOSS-001")
    assert result["affected_load_ids"] == ["CRIT-LOADS"]


def test_loss_of_both_essential_feeds_affects_only_essential_load_group():
    report = run_benchmark(MODEL, SCENARIOS)
    result = next(x for x in report["results"] if x["scenario_id"] == "DRPDS-ESSENTIAL-BOTH-FEEDS-LOSS-001")
    assert result["affected_load_ids"] == ["ESS-LOADS"]


def test_unknown_sats_and_ups_detail_is_reported_as_insufficient_model():
    report = run_benchmark(MODEL, SCENARIOS)
    by_id = {x["scenario_id"]: x for x in report["results"]}
    assert by_id["DRPDS-UNKNOWN-SATS-DETAIL-001"]["status"] == "insufficient_model"
    assert by_id["DRPDS-UNKNOWN-UPS-UNIT-001"]["status"] == "insufficient_model"
    assert "индивидуальных ID SATS" in by_id["DRPDS-UNKNOWN-SATS-DETAIL-001"]["explanation"]


def test_instrument_error_is_not_a_physical_measurement():
    report = run_benchmark(MODEL, SCENARIOS)
    result = next(x for x in report["results"] if x["scenario_id"] == "DRPDS-INSTRUMENT-ERROR-001")
    assert result["status"] == "measurement_rejected"
    assert result["observations"][0]["value"] is None
    assert result["observations"][0]["is_physical_measurement"] is False


def test_all_faa_drpds_scenarios_block_live_actions():
    report = run_benchmark(MODEL, SCENARIOS)
    assert all(not x["safety_gateway"]["live_measurement_allowed"] for x in report["results"])
    assert all(not x["safety_gateway"]["live_operation_allowed"] for x in report["results"])


def test_unknown_edge_reference_is_rejected(tmp_path):
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    scenarios["scenarios"][1]["injection"]["edge_id"] = "DOES-NOT-EXIST"
    bad = tmp_path / "bad-scenarios.json"
    bad.write_text(json.dumps(scenarios), encoding="utf-8")
    try:
        run_benchmark(MODEL, bad)
    except ValueError as exc:
        assert "unknown edge_id" in str(exc)
    else:
        raise AssertionError("Unknown edge reference must be rejected")
