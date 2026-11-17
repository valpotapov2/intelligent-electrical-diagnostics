from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = Path(os.environ.get("DIAGNOSTICS_CORE_PATH", ROOT / ".deps" / "diagnostics-mvp"))
if not (CORE_PATH / "diag" / "engine.py").is_file():
    pytest.skip("Private diagnostics-mvp checkout is required; see diagnostics/core-integration/README.md",
                allow_module_level=True)

from edi_ingest.diagnostic_core import SCENARIO_MODES, build_model, run_scenario  # noqa: E402
from edi_ingest.diagnostic_core import engine  # noqa: E402

SCENARIOS_PATH = ROOT / "benchmarks" / "kindergarten-switchboard" / "scenarios.v0.1.json"


def test_fixture_is_valid_under_real_core_contract():
    diagnostic_model = build_model()
    assert diagnostic_model.ref == "kindergarten_switchboard_sim@0.1.0"
    assert diagnostic_model.module.schema_version == "1.3"
    assert set(diagnostic_model.module.faults.modes) == {
        "Healthy", "QF4_COMMON_OPEN", "QF4_BRANCH_OPEN", "QF9_ANOMALY"
    }


def test_all_benchmark_scenarios_are_accounted_for():
    source = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    source_ids = {item["id"] for item in source["scenarios"]}
    assert set(SCENARIO_MODES).issubset(source_ids)
    assert "KSW-UNKNOWN-TOPOLOGY-001" in source_ids


@pytest.mark.parametrize(
    ("scenario_id", "expected_mode"),
    [
        ("KSW-BASE-001", "Healthy"),
        ("KSW-QF4-OPEN-001", "QF4_COMMON_OPEN"),
        ("KSW-QF4-BRANCH-001", "QF4_BRANCH_OPEN"),
        ("KSW-QF9-OBS-001", "QF9_ANOMALY"),
    ],
)
def test_real_core_updates_posterior_from_gateway_evidence(scenario_id, expected_mode):
    result = run_scenario(scenario_id)
    assert result["records"], "Core accepted no SafetyGateway-stamped evidence"
    assert all(item["accepted"] for item in result["records"])
    assert result["mode_posterior"][expected_mode] > 0.5
    assert result["gateway_log"]
    assert all(item["allowed"] and item["adapter_called"] for item in result["gateway_log"])


def test_core_does_not_conclude_before_any_evidence():
    diagnostic_model = build_model()
    session = engine.Session(diagnostic_model)
    first = session.step()
    assert first["action"] == "request"
    assert session.records == []


def test_instrument_error_scenario_is_rejected_and_never_becomes_evidence():
    result = run_scenario("KSW-INSTRUMENT-INVALID-001", fail_first=True)
    assert result["adapter_measurements"] >= 1
    assert any(
        item.get("result", {}).get("status") == "instrument_error"
        and item.get("result", {}).get("value") is None
        for item in result["rejected"]
    )
    assert all(item.get("status") != "instrument_error" for item in result["records"])


def test_unknown_ats_internal_logic_is_not_invented_as_a_fault_mode():
    diagnostic_model = build_model()
    session = engine.Session(diagnostic_model, instruments={"ats-internal-logic-probe-not-installed"})
    decision = session.step()
    assert decision["action"] != "request"
    assert decision.get("outcome") != "conclude"
    assert "ats" not in diagnostic_model.module.objects.components
