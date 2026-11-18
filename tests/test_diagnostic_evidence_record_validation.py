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


def test_batch_validator_accepts_distinct_current_state_requirements():
    from edi_ingest.evidence import validate_evidence_records

    first, second = DEPENDENCIES["questions"][:2]
    records = [
        valid_record(),
        {
            "evidence_id": "ev-integration-2",
            "question_id": second["id"],
            "evidence_key": second["required_evidence"][0],
            "state": "unknown",
            "observations": [],
        },
    ]

    validate_evidence_records(records, DEPENDENCIES, SCHEMA)


def test_batch_validator_rejects_duplicate_evidence_ids():
    from edi_ingest.evidence import validate_evidence_records

    first = valid_record()
    second_question = DEPENDENCIES["questions"][1]
    second = {
        "evidence_id": first["evidence_id"],
        "question_id": second_question["id"],
        "evidence_key": second_question["required_evidence"][0],
        "state": "unknown",
        "observations": [],
    }

    with pytest.raises(ValueError, match="duplicate evidence_id"):
        validate_evidence_records([first, second], DEPENDENCIES, SCHEMA)


def test_batch_validator_rejects_duplicate_current_state_requirement():
    from edi_ingest.evidence import validate_evidence_records

    first = valid_record()
    second = dict(first, evidence_id="ev-integration-duplicate")

    with pytest.raises(ValueError, match="duplicate current-state requirement"):
        validate_evidence_records([first, second], DEPENDENCIES, SCHEMA)


def test_batch_validator_rejects_invalid_record_with_index():
    from edi_ingest.evidence import validate_evidence_records

    first = valid_record()
    second = dict(valid_record(), evidence_id="ev-invalid", state="healthy")

    with pytest.raises(ValueError, match="index 1"):
        validate_evidence_records([first, second], DEPENDENCIES, SCHEMA)


def test_batch_validator_rejects_empty_batch():
    from edi_ingest.evidence import validate_evidence_records

    with pytest.raises(ValueError, match="must not be empty"):
        validate_evidence_records([], DEPENDENCIES, SCHEMA)


def complete_unknown_snapshot():
    records = []
    for question in DEPENDENCIES["questions"]:
        for index, evidence_key in enumerate(question["required_evidence"]):
            records.append(
                {
                    "evidence_id": f"ev-{question['id']}-{index}",
                    "question_id": question["id"],
                    "evidence_key": evidence_key,
                    "state": "unknown",
                    "observations": [],
                }
            )
    return records


def test_complete_snapshot_accepts_all_declared_requirements_as_unknown():
    from edi_ingest.evidence import validate_complete_evidence_snapshot

    records = complete_unknown_snapshot()
    assert len(records) == 276

    validate_complete_evidence_snapshot(records, DEPENDENCIES, SCHEMA)


def test_complete_snapshot_rejects_missing_requirement_even_when_remaining_records_valid():
    from edi_ingest.evidence import validate_complete_evidence_snapshot

    records = complete_unknown_snapshot()[:-1]

    with pytest.raises(ValueError, match="1 requirements missing"):
        validate_complete_evidence_snapshot(records, DEPENDENCIES, SCHEMA)


def test_complete_snapshot_rejects_duplicate_requirement_declaration():
    from edi_ingest.evidence import validate_complete_evidence_snapshot

    model = dict(DEPENDENCIES)
    model["questions"] = [
        dict(DEPENDENCIES["questions"][0]),
        *DEPENDENCIES["questions"][1:],
    ]
    model["questions"][0]["required_evidence"] = [
        *model["questions"][0]["required_evidence"],
        model["questions"][0]["required_evidence"][0],
    ]

    with pytest.raises(ValueError, match="duplicate declared requirement"):
        validate_complete_evidence_snapshot(
            complete_unknown_snapshot(), model, SCHEMA
        )
