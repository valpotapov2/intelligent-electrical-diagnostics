import json
from pathlib import Path

import pytest

from edi_ingest.evidence import validate_evidence_reference


ROOT = Path(__file__).resolve().parents[1]
DEPENDENCIES = json.loads(
    (ROOT / "diagnostics" / "scenarios" / "faa-drpds-diagnostic-dependencies.v0.1.json")
    .read_text(encoding="utf-8")
)


def test_every_declared_question_evidence_key_is_linkable():
    for question in DEPENDENCIES["questions"]:
        for evidence_key in question["required_evidence"]:
            validate_evidence_reference(
                {
                    "question_id": question["id"],
                    "evidence_key": evidence_key,
                },
                DEPENDENCIES,
            )


def test_rejects_unknown_question_id():
    with pytest.raises(ValueError, match="unknown diagnostic question_id"):
        validate_evidence_reference(
            {"question_id": "DQ-NOT-DECLARED", "evidence_key": "anything"},
            DEPENDENCIES,
        )


def test_rejects_evidence_key_declared_under_another_question():
    first, second = DEPENDENCIES["questions"][:2]
    foreign_key = first["required_evidence"][0]
    assert foreign_key not in second["required_evidence"]

    with pytest.raises(ValueError, match="not declared for question"):
        validate_evidence_reference(
            {"question_id": second["id"], "evidence_key": foreign_key},
            DEPENDENCIES,
        )


@pytest.mark.parametrize(
    "record",
    [
        {},
        {"question_id": "", "evidence_key": "key"},
        {"question_id": "DQ-SOURCE-AVAILABILITY", "evidence_key": ""},
        {"question_id": None, "evidence_key": "key"},
    ],
)
def test_rejects_missing_or_invalid_reference_fields(record):
    with pytest.raises(ValueError):
        validate_evidence_reference(record, DEPENDENCIES)


def test_rejects_dependency_model_without_questions():
    with pytest.raises(ValueError, match="questions array"):
        validate_evidence_reference(
            {"question_id": "DQ-SOURCE-AVAILABILITY", "evidence_key": "key"},
            {},
        )
