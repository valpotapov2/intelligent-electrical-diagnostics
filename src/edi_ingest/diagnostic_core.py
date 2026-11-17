"""Bridge to the real diagnostics-mvp engine.

The core is loaded from an explicitly supplied checkout. This repository does not
vendor or reimplement diag.Session, MeasurementRequest, or SafetyGateway.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


def _import_core(core_root: str | Path):
    root = str(Path(core_root).resolve())
    if not (Path(root) / "diag" / "engine.py").is_file():
        raise FileNotFoundError(f"diagnostics-mvp checkout not found at {root!r}")
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        from diag import engine, instruments, model, module, policy, safety
    except Exception as exc:
        raise RuntimeError(f"Cannot import diagnostics-mvp from {root}: {exc}") from exc
    return engine, instruments, model, module, policy, safety


def run_diagnostic_session(
    *,
    core_root: str | Path,
    module_path: str | Path,
    adapter: Any,
    policy_path: str | Path | None = None,
    instruments_at_hand: set[str] | None = None,
    qualified: bool = False,
    max_steps: int = 100,
    overrides: dict | None = None,
) -> dict:
    """Run the actual core decision loop through its safety gateway.

    The adapter only receives MeasurementRequest. Hidden scenario state must
    remain inside the adapter; it must never be added to the engine model or
    passed as an argument to Session.step().
    """
    if max_steps < 1:
        raise ValueError("max_steps must be positive")
    engine, dins, dmodel, dmodule, dpolicy, dsafety = _import_core(core_root)

    module = dmodule.load(module_path)
    policy = dpolicy.load(policy_path) if policy_path else dpolicy.load()
    model = dmodel.build(module, policy, overrides=overrides)
    session = engine.Session(model, instruments_at_hand)
    gateway = dsafety.SafetyGateway(
        module,
        model.catalog,
        adapter,
        qualified=qualified,
    )

    decision = None
    for _ in range(max_steps):
        decision = session.step()
        if decision.get("action") != "request":
            break
        check = decision["check"]
        request = dins.MeasurementRequest(
            check["check_id"],
            check["quantity"],
            check["point"],
            check["net"],
            check["instrument"],
            check.get("common_node"),
        )
        reply = gateway.measure(request)
        session.add_reply(reply, "requested")
    else:
        raise RuntimeError(f"diagnostic core exceeded max_steps={max_steps}")

    return {
        "module": model.ref,
        "policy": model.policy_ref,
        "decision": decision,
        "checks_requested": list(session.requested),
        "accepted_measurements": list(session.records),
        "rejected_measurements": list(session.rejected),
        "mode_posterior": session.mode_posterior(),
        "group_posterior": session.group_posterior(),
        "gateway_log": list(gateway.log),
        "steps": list(session.steps),
    }
