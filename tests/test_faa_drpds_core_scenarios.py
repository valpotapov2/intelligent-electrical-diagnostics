"""Real diagnostic-core tests using a synthetic-only DRPDS module."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from edi_ingest.diagnostic_core import _import_core, run_diagnostic_session

CORE = os.environ.get("DIAGNOSTICS_MVP_PATH")
ROOT = Path(__file__).resolve().parents[1]
VIRTUAL_MODULE = ROOT / "benchmarks" / "faa-drpds" / "diagnostic-core-module.synthetic.yaml"
pytestmark = pytest.mark.skipif(not CORE, reason="DIAGNOSTICS_MVP_PATH is not configured")


class VirtualDrpdsAdapter:
    """Hidden fault state stays in the adapter; the core receives requested readings only."""
    adapter_id = "edi-virtual-faa-drpds"

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
    ("mode",),
    [
        ("Healthy",),
        ("Critical_A_path_loss",),
        ("Critical_B_path_loss",),
        ("Dual_critical_path_loss",),
        ("SATS_output_loss",),
        ("Essential_feed_loss",),
        ("Source_1_evidence_loss",),
        ("Source_2_evidence_loss",),
        ("SWGR_1_section_evidence_loss",),
        ("SWGR_2_section_evidence_loss",),
        ("Generator_bus_evidence_loss",),
        ("Standby_transfer_evidence_loss",),
    ],
)
def test_synthetic_drpds_mode_updates_real_core_posterior(mode):
    module = _module()
    adapter = VirtualDrpdsAdapter(module, mode=mode)
    result = run_diagnostic_session(
        core_root=CORE,
        module_path=VIRTUAL_MODULE,
        adapter=adapter,
        overrides={"policy.selection": "spike", "policy.max_checks": 12},
        max_steps=100,
    )

    assert result["module"] == module.ref
    assert result["checks_requested"]
    assert result["accepted_measurements"]
    assert result["mode_posterior"][mode] > 0.5, {"mode": mode, "posterior": result["mode_posterior"], "requested_points": list(result["checks_requested"]), "accepted_points": list(result["accepted_measurements"]), "decision": result["decision"]}
    assert all(row["allowed"] for row in result["gateway_log"])
    assert all(row["adapter_called"] for row in result["gateway_log"])


def test_invalid_instrument_result_is_rejected_without_automatic_retry():
    module = _module()
    adapter = VirtualDrpdsAdapter(module, invalid_first=True)
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


def test_unknown_sats_internal_point_is_blocked_before_adapter_call():
    _, dins, dmodel, dmodule, dpolicy, dsafety = _import_core(CORE)
    module = dmodule.load(VIRTUAL_MODULE)
    model = dmodel.build(module, dpolicy.load(), {"policy.selection": "spike"})

    class MustNotRun:
        adapter_id = "must-not-run"

        def __init__(self):
            self.calls = 0

        def measure(self, request):
            self.calls += 1
            raise AssertionError("undeclared SATS internal point must be blocked")

    adapter = MustNotRun()
    gateway = dsafety.SafetyGateway(module, model.catalog, adapter)
    request = dins.MeasurementRequest(
        "dc_voltage@P_SATS_INTERNAL:virtual_meter",
        "dc_voltage",
        "P_SATS_INTERNAL",
        "SATS_INTERNAL",
        "virtual_meter",
        "GND",
    )
    reply = gateway.measure(request)

    assert not reply.allowed
    assert any(v.rule == "base.undeclared_place" for v in reply.verdict.violations)
    assert adapter.calls == 0
