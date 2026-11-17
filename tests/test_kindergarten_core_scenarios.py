"""Engine-level tests for all six KSW cases, using only a synthetic virtual module."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from edi_ingest.diagnostic_core import _import_core, run_diagnostic_session

CORE = os.environ.get("DIAGNOSTICS_MVP_PATH")
ROOT = Path(__file__).resolve().parents[1]
VIRTUAL_MODULE = ROOT / "benchmarks" / "kindergarten-switchboard" / "diagnostic-core-module.synthetic.yaml"
pytestmark = pytest.mark.skipif(not CORE, reason="DIAGNOSTICS_MVP_PATH is not configured")


class VirtualSwitchboardAdapter:
    """Hidden fault state stays inside this adapter; the core sees only requested readings."""
    adapter_id = "edi-virtual-kindergarten-switchboard"

    def __init__(self, module, mode="Healthy", invalid_first=False):
        self.module = module
        self.mode = mode
        self.invalid_first = invalid_first
        self.calls = []

    def measure(self, request):
        from diag.instruments import MeasurementResult, UNC_PROFILE

        self.calls.append(request.check_id)
        instrument = self.module.instruments[request.instrument_id]
        quantity = self.module.quantities[request.quantity]
        if self.invalid_first and len(self.calls) == 1:
            status, value, message = "instrument_error", None, "synthetic instrument failure"
        else:
            symptom = self.module.symptoms[self.mode][request.quantity][request.net_id]
            lo = symptom.min if symptom.min is not None else symptom.value
            hi = symptom.max if symptom.max is not None else symptom.value
            value = (float(lo) + float(hi)) / 2
            status, message = "valid", None

        profile = instrument.profiles[request.quantity]
        accuracy = profile.accuracy.model_dump() if profile.accuracy else None
        uncertainty = None
        basis = "unknown"
        if accuracy is not None and isinstance(value, (int, float)):
            uncertainty = abs(value) * accuracy["pct"] / 100 + accuracy["abs"]
            basis = UNC_PROFILE

        return MeasurementResult(
            measurement_id=f"virtual-{len(self.calls)}",
            check_id=request.check_id,
            instrument_id=request.instrument_id,
            instrument_profile_version=instrument.version,
            test_point_id=request.test_point_id,
            net_id=request.net_id,
            quantity=request.quantity,
            value=value,
            unit=quantity.unit,
            status=status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            uncertainty=uncertainty,
            uncertainty_basis=basis,
            accuracy=accuracy,
            range=list(profile.range),
            resolution=profile.resolution,
            adapter_id=self.adapter_id,
            message=message,
            common_node_id=request.common_node_id,
        )


def _module():
    _, _, _, dmodule, _, _ = _import_core(CORE)
    return dmodule.load(VIRTUAL_MODULE)


@pytest.mark.parametrize(
    ("scenario_id", "mode"),
    [
        ("KSW-BASE-001", "Healthy"),
        ("KSW-QF4-OPEN-001", "QF4_common_open"),
        ("KSW-QF4-BRANCH-001", "QF4_branch_open"),
        ("KSW-QF9-OBS-001", "QF9_observation_anomaly"),
    ],
)
def test_topology_scenarios_drive_real_core_posterior(scenario_id, mode):
    module = _module()
    adapter = VirtualSwitchboardAdapter(module, mode=mode)
    result = run_diagnostic_session(
        core_root=CORE,
        module_path=VIRTUAL_MODULE,
        adapter=adapter,
        overrides={"policy.selection": "spike"},
        max_steps=100,
    )

    assert result["module"] == module.ref, scenario_id
    assert result["checks_requested"], scenario_id
    assert result["accepted_measurements"], scenario_id
    assert result["mode_posterior"][mode] > 0.5, (scenario_id, result["mode_posterior"])
    assert all(row["allowed"] for row in result["gateway_log"]), scenario_id
    assert all(row["adapter_called"] for row in result["gateway_log"]), scenario_id


def test_invalid_instrument_result_is_rejected_and_not_retried_automatically():
    module = _module()
    adapter = VirtualSwitchboardAdapter(module, invalid_first=True)
    result = run_diagnostic_session(
        core_root=CORE,
        module_path=VIRTUAL_MODULE,
        adapter=adapter,
        overrides={"policy.selection": "spike"},
        max_steps=100,
    )

    assert result["rejected_measurements"]
    rejected = result["rejected_measurements"][0]
    assert rejected["status"] == "instrument_error"
    assert rejected["result"]["value"] is None
    assert adapter.calls.count(adapter.calls[0]) == 1


def test_unknown_ats_point_is_blocked_before_adapter_call():
    _, dins, dmodel, dmodule, dpolicy, dsafety = _import_core(CORE)
    module = dmodule.load(VIRTUAL_MODULE)
    model = dmodel.build(module, dpolicy.load(), {"policy.selection": "spike"})

    class MustNotRun:
        adapter_id = "must-not-run"

        def __init__(self):
            self.calls = 0

        def measure(self, request):
            self.calls += 1
            raise AssertionError("unknown ATS point must be blocked before adapter invocation")

    adapter = MustNotRun()
    gateway = dsafety.SafetyGateway(module, model.catalog, adapter)
    request = dins.MeasurementRequest(
        "dc_voltage@P_ATS_INTERNAL:virtual_meter",
        "dc_voltage",
        "P_ATS_INTERNAL",
        "ATS_INTERNAL",
        "virtual_meter",
        "GND",
    )
    reply = gateway.measure(request)

    assert not reply.allowed
    assert any(v.rule == "base.undeclared_place" for v in reply.verdict.violations)
    assert adapter.calls == 0
