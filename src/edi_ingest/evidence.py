"""Validation for diagnostic evidence records and their model references.

Successful validation confirms only that a record conforms to the data contract
and points to a declared requirement. It is not a diagnostic conclusion.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


def validate_evidence_reference(
    record: Mapping[str, Any],
    dependency_model: Mapping[str, Any],
) -> None:
    """Raise ValueError unless the record points to a declared question/evidence key.

    The question identifier and evidence key are matched exactly. This function
    does not validate observation payloads, freshness, quality, or diagnosis.
    """
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
    """Validate one evidence record's JSON Schema shape and model references.

    Raises ValueError with the first deterministic schema or reference error.
    JSON Schema validation and cross-file reference validation remain distinct
    checks, but callers can now invoke them through one integration boundary.
    """
    if not isinstance(schema, Mapping):
        raise ValueError("evidence schema must be an object")

    validator = Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )
    errors = sorted(
        validator.iter_errors(record),
        key=lambda error: (list(map(str, error.absolute_path)), error.message),
    )
    if errors:
        error = errors[0]
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        raise ValueError(f"invalid evidence record at {location}: {error.message}")

    validate_evidence_reference(record, dependency_model)
