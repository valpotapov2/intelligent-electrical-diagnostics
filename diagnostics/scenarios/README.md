# Offline scenario runner

This is a **graph-level benchmark adapter**, not the diagnostic engine and not an implementation of `MeasurementRequest`, `MeasurementResult`, `InstrumentAdapter`, `SafetyGateway` or `Session`. The pilot plan calls for integration through those existing contracts; this adapter deliberately stops before that integration.

## Run

```bash
pip install -e ".[dev]"
edi-scenarios
```

Write a report with `edi-scenarios --output artifacts/kindergarten-switchboard-report.json`.

The runner validates scenario references, applies declared graph-edge removals or synthetic non-numeric observations, computes disconnected downstream loads, rejects instrument-error results as measurements, reports undocumented ATS internals as insufficient model, and unconditionally blocks live measurement and operation.

A passing result means only that the expected affected-load set matches the graph calculation. It does not prove that the diagnostic engine identifies a physical cause, that the SVG matches the as-built installation, or that any live test is safe.

The next integration step is to adapt these inputs to the actual diagnostic-core contracts after their current code/API is located and reviewed. Do not create a parallel inference engine here.
