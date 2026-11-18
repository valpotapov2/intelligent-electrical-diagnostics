"""Command-line validation for one diagnostic evidence JSON record."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .evidence import validate_evidence_record


def _load_json_object(path: str) -> dict[str, Any]:
    try:
        with Path(path).open(encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON file {path!r}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object in {path!r}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate one diagnostic evidence record against its JSON Schema "
            "and diagnostic dependency model."
        )
    )
    parser.add_argument("--record", required=True, help="Path to one evidence-record JSON object")
    parser.add_argument("--dependency-model", required=True, help="Path to diagnostic dependency-model JSON")
    parser.add_argument("--schema", required=True, help="Path to diagnostic evidence JSON Schema")
    args = parser.parse_args()

    try:
        record = _load_json_object(args.record)
        dependency_model = _load_json_object(args.dependency_model)
        schema = _load_json_object(args.schema)
        validate_evidence_record(record, dependency_model, schema)
    except ValueError as exc:
        print(f"Invalid evidence record: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "valid": True,
                "evidence_id": record["evidence_id"],
                "question_id": record["question_id"],
                "evidence_key": record["evidence_key"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
