import json
from pathlib import Path
import pytest
from edi_ingest.scenario_runner import run_benchmark, run_scenario, _index_model

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "benchmarks/kindergarten-switchboard/electrical-object-model.v0.1.json"
SCENARIOS = ROOT / "benchmarks/kindergarten-switchboard/scenarios.v0.1.json"

@pytest.fixture
def benchmark():
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    ids, edges, circuits = _index_model(model)
    return model, scenarios, ids, edges, circuits

def test_all_scenarios_have_expected_graph_scope():
    report = run_benchmark(MODEL, SCENARIOS)
    assert report["scenario_count"] == 6
    assert report["passed"] == 6
    assert report["failed"] == 0
    assert report["execution_mode"] == "offline_simulation_only"

def test_qf4_common_feeder_disconnects_both_downstream_loads(benchmark):
    model, scenarios, _, edges, circuits = benchmark
    case = next(x for x in scenarios["scenarios"] if x["id"] == "KSW-QF4-OPEN-001")
    result = run_scenario(case, model, edges, circuits)
    assert result["affected_load_ids"] == ["load-plan-4", "load-plan-5"]

def test_qf4_branch_disconnects_only_attic_load(benchmark):
    model, scenarios, _, edges, circuits = benchmark
    case = next(x for x in scenarios["scenarios"] if x["id"] == "KSW-QF4-BRANCH-001")
    result = run_scenario(case, model, edges, circuits)
    assert result["affected_load_ids"] == ["load-plan-5"]

def test_instrument_error_is_not_recorded_as_measurement(benchmark):
    model, scenarios, _, edges, circuits = benchmark
    case = next(x for x in scenarios["scenarios"] if x["id"] == "KSW-INSTRUMENT-INVALID-001")
    result = run_scenario(case, model, edges, circuits)
    assert result["status"] == "measurement_rejected"
    assert result["observations"][0]["value"] is None
    assert result["observations"][0]["is_physical_measurement"] is False

def test_unknown_ats_topology_returns_insufficient_model(benchmark):
    model, scenarios, _, edges, circuits = benchmark
    case = next(x for x in scenarios["scenarios"] if x["id"] == "KSW-UNKNOWN-TOPOLOGY-001")
    assert run_scenario(case, model, edges, circuits)["status"] == "insufficient_model"

def test_runner_never_allows_live_actions():
    report = run_benchmark(MODEL, SCENARIOS)
    assert all(not x["safety_gateway"]["live_measurement_allowed"] for x in report["results"])
    assert all(not x["safety_gateway"]["live_operation_allowed"] for x in report["results"])

def test_non_offline_mode_is_rejected(tmp_path):
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    scenarios["execution_mode"] = "live"
    path = tmp_path / "scenarios.json"
    path.write_text(json.dumps(scenarios), encoding="utf-8")
    with pytest.raises(ValueError, match="offline_simulation_only"):
        run_benchmark(MODEL, path)
