"""Offline bridge to the pinned diagnostics-mvp engine.

The simulator keeps the hidden scenario state. diag.Session receives only
MeasurementRequest/MeasurementResult through the real SafetyGateway.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = Path(os.environ.get("DIAGNOSTICS_CORE_PATH", ROOT / ".deps" / "diagnostics-mvp"))
if not (CORE_ROOT / "diag" / "engine.py").is_file():
    raise RuntimeError(
        "Private diagnostics-mvp checkout missing. See diagnostics/core-integration/README.md"
    )
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from diag import engine, instruments, model, module, policy, safety  # noqa: E402

MODULE_PATH = ROOT / "diagnostics" / "core-integration" / "kindergarten-simulation.module.yaml"
SCENARIO_MODES = {
    "KSW-BASE-001": "Healthy",
    "KSW-QF4-OPEN-001": "QF4_COMMON_OPEN",
    "KSW-QF4-BRANCH-001": "QF4_BRANCH_OPEN",
    "KSW-QF9-OBS-001": "QF9_ANOMALY",
    "KSW-INSTRUMENT-INVALID-001": "Healthy",
}
READINGS = {
    "Healthy": {"qf4_common_code": 1.0, "qf4_branch_code": 1.0, "qf9_code": 1.0},
    "QF4_COMMON_OPEN": {"qf4_common_code": 0.0, "qf4_branch_code": 0.0, "qf9_code": 1.0},
    "QF4_BRANCH_OPEN": {"qf4_common_code": 1.0, "qf4_branch_code": 0.0, "qf9_code": 1.0},
    "QF9_ANOMALY": {"qf4_common_code": 1.0, "qf4_branch_code": 1.0, "qf9_code": 0.0},
}


class ScenarioAdapter:
    """InstrumentAdapter implementation for tests; never receives commands for real devices."""

    adapter_id = "kindergarten-scenario-simulator"

    def __init__(self, hidden_mode: str, fail_first: bool = False):
        self._hidden_mode = hidden_mode
        self._fail_first = fail_first
        self.measurement_number = 0

    def measure(self, request: instruments.MeasurementRequest) -> instruments.MeasurementResult:
        self.measurement_number += 1
        failed = self._fail_first and self.measurement_number == 1
        status = instruments.INSTRUMENT_ERROR if failed else instruments.VALID
        value = None if failed else READINGS[self._hidden_mode][request.quantity]
        return instruments.MeasurementResult(
            measurement_id=f"sim-{self._hidden_mode}-{self.measurement_number}",
            check_id=request.check_id,
            instrument_id=request.instrument_id,
            instrument_profile_version=1,
            test_point_id=request.test_point_id,
            net_id=request.net_id,
            quantity=request.quantity,
            value=value,
            unit="sim-code",
            status=status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            uncertainty_basis=instruments.UNC_UNKNOWN,
            range=[0.0, 1.0],
            resolution=0.01,
            adapter_id=self.adapter_id,
            message="Injected simulator instrument error" if failed else None,
        )


def build_model():
    """Use the same loader, policy and model builder as diagnostics-mvp's harness.runner."""
    parsed = module.load(MODULE_PATH)
    return model.build(parsed, policy.load())


def run_scenario(scenario_id: str, *, fail_first: bool = False, instruments_available=None) -> dict:
    if scenario_id not in SCENARIO_MODES:
        raise ValueError(f"No core simulation mode is defined for {scenario_id}")
    diagnostic_model = build_model()
    session = engine.Session(diagnostic_model, instruments=instruments_available)
    adapter = ScenarioAdapter(SCENARIO_MODES[scenario_id], fail_first=fail_first)
    gateway = safety.SafetyGateway(
        diagnostic_model.module, diagnostic_model.catalog, adapter, qualified=True
    )
    decision = session.step()
    while decision["action"] == "request":
        check = decision["check"]
        request = instruments.MeasurementRequest(
            check["check_id"], check["quantity"], check["point"], check["net"],
            check["instrument"], check.get("common_node"),
        )
        session.add_reply(gateway.measure(request), "kindergarten-simulation")
        decision = session.step()
    return {
        "decision": decision,
        "mode_posterior": session.mode_posterior(),
        "group_posterior": session.group_posterior(),
        "records": list(session.records),
        "rejected": list(session.rejected),
        "gateway_log": list(gateway.log),
        "adapter_measurements": adapter.measurement_number,
    }
