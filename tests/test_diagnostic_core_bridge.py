"""Contract smoke test against the pinned, real diagnostics-mvp checkout.

Set DIAGNOSTICS_MVP_PATH to a local checkout of diagnostics-mvp. This test is
skipped in the ordinary ingestion-only environment.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from edi_ingest.diagnostic_core import run_diagnostic_session


CORE = os.environ.get("DIAGNOSTICS_MVP_PATH")
pytestmark = pytest.mark.skipif(not CORE, reason="DIAGNOSTICS_MVP_PATH is not configured")


class HealthyPowerSupplyAdapter:
    adapter_id = "edi-synthetic-healthy-power-supply"

    def __init__(self, module):
        self.module = module
        self.counter = 0

    def measure(self, request):
        from diag.instruments import MeasurementResult, UNC_PROFILE

        self.counter += 1
        quantity = self.module.quantities[request.quantity]
        symptom = self.module.symptoms["Healthy"][request.quantity][request.net_id]
        if quantity.kind == "categorical":
            value = symptom.value
        else:
            lo = symptom.min if symptom.min is not None else symptom.value
            hi = symptom.max if symptom.max is not None else symptom.value
            value = (float(lo) + float(hi)) / 2

        instrument = self.module.instruments[request.instrument_id]
        profile = instrument.profiles[request.quantity]
        accuracy = profile.accuracy.model_dump() if profile.accuracy else None
        uncertainty = None
        basis = "unknown"
        if accuracy is not None and isinstance(value, (int, float)):
            uncertainty = abs(value) * accuracy["pct"] / 100 + accuracy["abs"]
            basis = UNC_PROFILE

        return MeasurementResult(
            measurement_id=f"edi-synthetic-{self.counter}",
            check_id=request.check_id,
            instrument_id=request.instrument_id,
            instrument_profile_version=instrument.version,
            test_point_id=request.test_point_id,
            net_id=request.net_id,
            quantity=request.quantity,
            value=value,
            unit=quantity.unit,
            status="valid",
            timestamp=datetime.now(timezone.utc).isoformat(),
            uncertainty=uncertainty,
            uncertainty_basis=basis,
            accuracy=accuracy,
            range=list(profile.range),
            resolution=profile.resolution,
            adapter_id=self.adapter_id,
            common_node_id=request.common_node_id,
        )


def test_real_core_runs_through_edi_bridge():
    from diag import module as dmodule

    core = Path(CORE).resolve()
    module_path = core / "modules" / "power_supply" / "module.yaml"
    module = dmodule.load(module_path)
    adapter = HealthyPowerSupplyAdapter(module)

    result = run_diagnostic_session(
        core_root=core,
        module_path=module_path,
        adapter=adapter,
        max_steps=100,
    )

    assert result["module"] == module.ref
    assert result["decision"]["action"] in {"conclude", "stop"}
    assert result["checks_requested"]
    assert result["accepted_measurements"]
    assert all(row["allowed"] for row in result["gateway_log"])
    assert all(row["adapter_called"] for row in result["gateway_log"])
    assert result["mode_posterior"]["Healthy"] > 0
