"""Validation for diagnostic evidence records and their model references.

Successful validation confirms only that records conform to the data contract
and point to declared requirements. It is not a diagnostic conclusion.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


def validate_evidence_reference(
    record: Mapping[str, Any],
    dependency_model: Mapping[str, Any],
) -> None:
    """Raise ValueError unless the record points to a declared question/evidence key."""
    if not isinstance(record, Mapping):
        raise ValueError("evidence record must be an object")
    if not isinstance(dependency_model, Mapping):
        raise ValueError("dependency model must be an object")

    question_id = record.get("question_id")
    evidence_key = record.get("evidence_key")
    if not isinstance(question_id, str) or not question_id:
        raise ValueError("question_id must be a non-empty string")
    if not isinstance(evidence_key, str) or not evidence_key:
        raise ValueError("evidence_key must be a non-empty string")

    questions = dependency_model.get("questions")
    if not isinstance(questions, list):
        raise ValueError("dependency model must contain a questions array")

    matches = [
        question
        for question in questions
        if isinstance(question, Mapping) and question.get("id") == question_id
    ]
    if not matches:
        raise ValueError(f"unknown diagnostic question_id: {question_id}")
    if len(matches) != 1:
        raise ValueError(f"ambiguous diagnostic question_id: {question_id}")

    required_evidence = matches[0].get("required_evidence")
    if not isinstance(required_evidence, list):
        raise ValueError(f"question {question_id} has no valid required_evidence array")
    if evidence_key not in required_evidence:
        raise ValueError(
            f"evidence_key {evidence_key!r} is not declared for question {question_id}"
        )


def validate_evidence_record(
    record: Mapping[str, Any],
    dependency_model: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> None:
    """Validate one record's JSON Schema shape and model references."""
    if not isinstance(schema, Mapping):
        raise ValueError("evidence schema must be an object")

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(
        validator.iter_errors(record),
        key=lambda error: (list(map(str, error.absolute_path)), error.message),
    )
    if errors:
        error = errors[0]
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        raise ValueError(f"invalid evidence record at {location}: {error.message}")

    validate_evidence_reference(record, dependency_model)


def validate_evidence_records(
    records: Sequence[Mapping[str, Any]],
    dependency_model: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> None:
    """Validate a current-state batch and reject duplicate record identities.

    A batch is a snapshot, not an event history: it may contain at most one
    record for each (question_id, evidence_key), and evidence_id values must
    be unique within that batch.
    """
    if isinstance(records, (str, bytes)) or not isinstance(records, Sequence):
        raise ValueError("evidence records must be an array")
    if not records:
        raise ValueError("evidence records array must not be empty")

    seen_ids: set[str] = set()
    seen_requirements: set[tuple[str, str]] = set()
    for index, record in enumerate(records):
        try:
            validate_evidence_record(record, dependency_model, schema)
        except ValueError as exc:
            raise ValueError(f"invalid evidence record at index {index}: {exc}") from exc

        evidence_id = record["evidence_id"]
        identity = (record["question_id"], record["evidence_key"])
        if evidence_id in seen_ids:
            raise ValueError(f"duplicate evidence_id in batch: {evidence_id}")
        if identity in seen_requirements:
            raise ValueError(
                "duplicate current-state requirement in batch: "
                f"question_id={identity[0]}, evidence_key={identity[1]}"
            )
        seen_ids.add(evidence_id)
        seen_requirements.add(identity)


def validate_complete_evidence_snapshot(
    records: Sequence[Mapping[str, Any]],
    dependency_model: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> None:
    """Validate a snapshot containing exactly one record for every declared requirement.

    Requirements with state="unknown" are valid entries. Completeness means
    every model requirement has an explicit record; it does not mean evidence
    has been acquired or that any equipment condition has been established.
    """
    validate_evidence_records(records, dependency_model, schema)

    questions = dependency_model.get("questions")
    if not isinstance(questions, list):
        raise ValueError("dependency model must contain a questions array")

    expected: set[tuple[str, str]] = set()
    for index, question in enumerate(questions):
        if not isinstance(question, Mapping):
            raise ValueError(f"invalid dependency question at index {index}")
        question_id = question.get("id")
        required_evidence = question.get("required_evidence")
        if not isinstance(question_id, str) or not question_id:
            raise ValueError(f"invalid question id at dependency index {index}")
        if not isinstance(required_evidence, list):
            raise ValueError(
                f"question {question_id} has no valid required_evidence array"
            )
        for evidence_key in required_evidence:
            if not isinstance(evidence_key, str) or not evidence_key:
                raise ValueError(
                    f"question {question_id} contains an invalid evidence key"
                )
            identity = (question_id, evidence_key)
            if identity in expected:
                raise ValueError(
                    "duplicate declared requirement in dependency model: "
                    f"question_id={question_id}, evidence_key={evidence_key}"
                )
            expected.add(identity)

    actual = {(record["question_id"], record["evidence_key"]) for record in records}
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if unexpected:
        raise ValueError(f"snapshot contains undeclared requirements: {unexpected!r}")
    if missing:
        preview = missing[:10]
        suffix = " ..." if len(missing) > len(preview) else ""
        raise ValueError(
            f"incomplete evidence snapshot: {len(missing)} requirements missing: "
            f"{preview!r}{suffix}"
        )
