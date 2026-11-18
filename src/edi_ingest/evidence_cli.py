"""Command-line validation for diagnostic evidence JSON records or snapshots."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .evidence import (
    validate_complete_evidence_snapshot,
    validate_evidence_record,
    validate_evidence_records,
)


def _load_json_value(path: str) -> Any:
    try:
        with Path(path).open(encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON file {path!r}: {exc}") from exc


def _load_json_object(path: str) -> dict[str, Any]:
    value = _load_json_value(path)
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object in {path!r}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate one diagnostic evidence record or a current-state array "
            "against its JSON Schema and diagnostic dependency model."
        )
    )
    parser.add_argument(
        "--record",
        required=True,
        help="Path to one evidence object or an array snapshot",
    )
    parser.add_argument(
        "--dependency-model",
        required=True,
        help="Path to diagnostic dependency-model JSON",
    )
    parser.add_argument(
        "--schema",
        required=True,
        help="Path to diagnostic evidence JSON Schema",
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Require an array snapshot to contain every declared requirement",
    )
    args = parser.parse_args()

    try:
        value = _load_json_value(args.record)
        dependency_model = _load_json_object(args.dependency_model)
        schema = _load_json_object(args.schema)
        if isinstance(value, dict):
            if args.require_complete:
                raise ValueError("--require-complete requires an array snapshot")
            validate_evidence_record(value, dependency_model, schema)
            result = {
                "valid": True,
                "evidence_id": value["evidence_id"],
                "question_id": value["question_id"],
                "evidence_key": value["evidence_key"],
            }
        elif isinstance(value, list):
            if args.require_complete:
                validate_complete_evidence_snapshot(value, dependency_model, schema)
                result = {
                    "valid": True,
                    "record_count": len(value),
                    "complete": True,
                }
            else:
                validate_evidence_records(value, dependency_model, schema)
                result = {
                    "valid": True,
                    "record_count": len(value),
                    "complete": False,
                }
        else:
            raise ValueError("record input must be a JSON object or an array of objects")
    except (ValueError, KeyError) as exc:
        print(f"Invalid evidence record: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
