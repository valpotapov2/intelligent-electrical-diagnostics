import json
from pathlib import Path

import pytest

from edi_ingest.evidence import validate_evidence_record


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads(
    (ROOT / "schema" / "diagnostic-evidence.schema.json").read_text(encoding="utf-8")
)
DEPENDENCIES = json.loads(
    (
        ROOT
        / "diagnostics"
        / "scenarios"
        / "faa-drpds-diagnostic-dependencies.v0.1.json"
    ).read_text(encoding="utf-8")
)


def valid_record():
    question = DEPENDENCIES["questions"][0]
    return {
        "evidence_id": "ev-integration-1",
        "question_id": question["id"],
        "evidence_key": question["required_evidence"][0],
        "state": "unknown",
        "observations": [],
    }


def test_combined_validator_accepts_schema_and_declared_reference():
    validate_evidence_record(valid_record(), DEPENDENCIES, SCHEMA)


def test_combined_validator_rejects_schema_violation_before_reference_check():
    record = valid_record()
    record["state"] = "healthy"

    with pytest.raises(ValueError, match="invalid evidence record"):
        validate_evidence_record(record, DEPENDENCIES, SCHEMA)


def test_combined_validator_rejects_unknown_question():
    record = valid_record()
    record["question_id"] = "DQ-NOT-DECLARED"

    with pytest.raises(ValueError, match="unknown diagnostic question_id"):
        validate_evidence_record(record, DEPENDENCIES, SCHEMA)


def test_combined_validator_rejects_key_borrowed_from_another_question():
    first, second = DEPENDENCIES["questions"][:2]
    record = valid_record()
    record["question_id"] = second["id"]
    record["evidence_key"] = first["required_evidence"][0]

    with pytest.raises(ValueError, match="not declared for question"):
        validate_evidence_record(record, DEPENDENCIES, SCHEMA)


def test_combined_validator_rejects_duplicate_question_ids_in_model():
    record = valid_record()
    model = dict(DEPENDENCIES)
    model["questions"] = [
        *DEPENDENCIES["questions"],
        dict(DEPENDENCIES["questions"][0]),
    ]

    with pytest.raises(ValueError, match="ambiguous diagnostic question_id"):
        validate_evidence_record(record, model, SCHEMA)


def test_combined_validator_does_not_turn_observation_quality_into_diagnosis():
    record = valid_record()
    record.update(
        {
            "state": "observed",
            "observations": [
                {
                    "observation_id": "obs-1",
                    "source": {"kind": "operator_record", "ref": "record:1"},
                    "observed_at": "2026-11-18T10:00:00Z",
                    "quality": "invalid",
                }
            ],
        }
    )

    validate_evidence_record(record, DEPENDENCIES, SCHEMA)
