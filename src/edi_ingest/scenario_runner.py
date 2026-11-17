from __future__ import annotations
import argparse
import json
from collections import deque
from pathlib import Path
from typing import Any

def _load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return value

def _index_model(model: dict[str, Any]):
    component_by_id = {}
    for item in model.get("components", []):
        component_id = item.get("id")
        if not isinstance(component_id, str) or not component_id:
            raise ValueError("Every component must have a non-empty id")
        if component_id in component_by_id:
            raise ValueError(f"Duplicate component id: {component_id}")
        component_by_id[component_id] = item
    edge_by_id = {}
    for item in model.get("connections", []):
        edge_id = item.get("id")
        if not isinstance(edge_id, str) or not edge_id:
            raise ValueError("Every connection must have a non-empty id")
        if edge_id in edge_by_id:
            raise ValueError(f"Duplicate connection id: {edge_id}")
        if item.get("from") not in component_by_id or item.get("to") not in component_by_id:
            raise ValueError(f"Connection {edge_id} has a dangling endpoint")
        edge_by_id[edge_id] = item
    circuit_by_id = {item["id"]: item for item in model.get("circuits", [])}
    return set(component_by_id), edge_by_id, circuit_by_id

def _source_ids(model, scenario=None):
    configured = (scenario or {}).get("source_component_ids")
    if configured is None:
        configured = model.get("object", {}).get("supply", {}).get("diagnostic_source_ids")
    if configured is None:
        configured = ["bus-l123"]
    if not isinstance(configured, list) or not configured:
        raise ValueError("source_component_ids must be a non-empty list")
    return configured

def _reachable_loads(model, edge_by_id, removed_edge_ids=None, source_ids=None):
    removed = set(removed_edge_ids or [])
    adjacency = {}
    for edge_id, edge in edge_by_id.items():
        if edge_id not in removed:
            adjacency.setdefault(edge["from"], []).append(edge["to"])
    component_ids = {item.get("id") for item in model.get("components", [])}
    starts = set(source_ids or ["bus-l123"])
    missing = starts - component_ids
    if missing:
        raise ValueError(f"Unknown diagnostic source component(s): {sorted(missing)}")
    visited, queue = set(starts), deque(starts)
    while queue:
        for neighbour in adjacency.get(queue.popleft(), []):
            if neighbour not in visited:
                visited.add(neighbour)
                queue.append(neighbour)
    return {item["id"] for item in model.get("components", [])
            if item.get("kind") == "load" and item["id"] not in visited}

def _validate_references(scenarios, component_ids, edge_by_id, circuit_by_id):
    seen = set()
    for scenario in scenarios.get("scenarios", []):
        scenario_id = scenario.get("id")
        if not isinstance(scenario_id, str) or not scenario_id or scenario_id in seen:
            raise ValueError(f"Missing or duplicate scenario id: {scenario_id!r}")
        seen.add(scenario_id)
        injection = scenario.get("injection", {})
        edge_ids = list(injection.get("edge_ids", []))
        if injection.get("edge_id"):
            edge_ids.append(injection["edge_id"])
        for edge_id in edge_ids:
            if edge_id not in edge_by_id:
                raise ValueError(f"{scenario_id}: unknown edge_id {edge_id}")
        target_id = injection.get("target_id")
        if target_id and target_id not in component_ids and target_id not in circuit_by_id:
            raise ValueError(f"{scenario_id}: unknown target_id {target_id}")
        source_ids = scenario.get("source_component_ids")
        if source_ids is not None:
            missing = set(source_ids) - component_ids
            if missing:
                raise ValueError(f"{scenario_id}: unknown source component(s) {sorted(missing)}")
        for key in ("affected_load_ids", "unaffected_reference_load_ids"):
            for load_id in scenario.get("expected", {}).get(key, []):
                if load_id not in component_ids:
                    raise ValueError(f"{scenario_id}: unknown {key} reference {load_id}")

def run_scenario(scenario, model, edge_by_id, circuit_by_id):
    injection = scenario.get("injection", {})
    injection_type = injection.get("type")
    sources = _source_ids(model, scenario)
    affected, observations = set(), []
    status = "simulated_topology_evaluation"
    explanation = "Только виртуальная проверка графа; фактическое состояние объекта не установлено."
    if injection_type in ("open_edge", "open_edges"):
        removed = injection.get("edge_ids", [])
        if injection.get("edge_id"):
            removed = [*removed, injection["edge_id"]]
        if not removed:
            raise ValueError(f"{scenario['id']}: open_edges requires at least one edge id")
        affected = (_reachable_loads(model, edge_by_id, removed, sources)
                    - _reachable_loads(model, edge_by_id, source_ids=sources))
        status = "simulated_open_edges" if len(removed) > 1 else "simulated_open_edge"
        explanation = f"В цифровом графе исключены связи: {', '.join(removed)}."
    elif injection_type == "synthetic_observation":
        target_id = injection["target_id"]
        circuit = circuit_by_id.get(target_id)
        observations.append({"kind":"synthetic","target_id":target_id,
            "quantity":injection.get("quantity"),"condition":injection.get("condition"),
            "is_physical_measurement":False})
        if circuit is not None:
            affected = set(circuit.get("load_ids", []))
        status = "synthetic_observation_recorded"
        explanation = ("Записано условное наблюдение; числовое измерение и причина неисправности не создавались. "
                       "Само наблюдение не доказывает причинную связь с отказом нагрузки.")
    elif injection_type == "measurement_result":
        observations.append({"kind":"instrument_error","target_id":injection.get("target_id"),
            "instrument_status":injection.get("instrument_status"),"value":None,
            "is_physical_measurement":False})
        status = "measurement_rejected"
        explanation = "Результат прибора со статусом error не принят как измерение."
    elif injection_type == "question":
        status = "insufficient_model"
        missing = injection.get("missing_prerequisites", [])
        explanation = "Недостаточно данных для ответа: " + (
            "; ".join(missing) if missing else "требуется дополнительная схема или спецификация."
        )
    elif injection_type == "none":
        status = "baseline"
    else:
        raise ValueError(f"Unsupported injection type: {injection_type!r}")
    expected = set(scenario.get("expected", {}).get("affected_load_ids", []))
    return {"scenario_id":scenario["id"],"title":scenario.get("title"),"status":status,
        "affected_load_ids":sorted(affected),"expected_affected_load_ids":sorted(expected),
        "affected_scope_matches":affected == expected,"observations":observations,
        "explanation":explanation,"execution_mode":"offline_simulation_only",
        "diagnostic_capability":"graph_reachability_only",
        "safety_gateway":{"live_measurement_allowed":False,"live_operation_allowed":False,
        "decision":"blocked","reason":"Runner не подключает приборы и не разрешает действия на реальном объекте."}}

def run_benchmark(model_path, scenarios_path):
    model, scenarios = _load_json(model_path), _load_json(scenarios_path)
    if scenarios.get("execution_mode") != "offline_simulation_only":
        raise ValueError("Only offline_simulation_only benchmark mode is supported")
    component_ids, edges, circuits = _index_model(model)
    _validate_references(scenarios, component_ids, edges, circuits)
    results = [run_scenario(item, model, edges, circuits) for item in scenarios.get("scenarios", [])]
    return {"benchmark_id":scenarios.get("benchmark_id"),"module_id":scenarios.get("module_id"),
        "execution_mode":"offline_simulation_only","diagnostic_capability":"graph_reachability_only",
        "scenario_count":len(results),"passed":sum(x["affected_scope_matches"] for x in results),
        "failed":sum(not x["affected_scope_matches"] for x in results),"results":results}

def main():
    parser = argparse.ArgumentParser(description="Run offline graph-level electrical scenarios.")
    parser.add_argument("--model", default="benchmarks/kindergarten-switchboard/electrical-object-model.v0.1.json")
    parser.add_argument("--scenarios", default="benchmarks/kindergarten-switchboard/scenarios.v0.1.json")
    parser.add_argument("--output", help="Optional JSON report path")
    args = parser.parse_args()
    report = run_benchmark(args.model, args.scenarios)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    if report["failed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
