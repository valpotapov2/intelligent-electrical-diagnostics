import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schema" / "diagnostic-evidence.schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())


def record(state, observations=None, **extra):
    return {
        "evidence_id": "ev-1",
        "question_id": "DQ-SWGR-COMMERCIAL-RETURN",
        "evidence_key": "restored_commercial_source_identity_and_source_side_measurement_quality_timestamp",
        "state": state,
        "observations": observations or [],
        **extra,
    }


def observation(observation_id, *, quality="valid", value=480):
    return {
        "observation_id": observation_id,
        "source": {"kind": "measurement", "ref": f"meter-event:{observation_id}"},
        "observed_at": "2026-11-18T10:00:00Z",
        "value": value,
        "unit": "V",
        "quality": quality,
    }


def assert_valid(item):
    errors = list(VALIDATOR.iter_errors(item))
    assert not errors, [error.message for error in errors]


def assert_invalid(item):
    assert list(VALIDATOR.iter_errors(item))


def test_all_five_evidence_states_have_valid_examples():
    assert_valid(record("unknown"))
    assert_valid(record("unavailable", reason="Source record could not be retrieved", checked_at="2026-11-18T10:05:00Z"))
    assert_valid(record("stale", [observation("old")], freshness_basis="Site-approved source freshness rule"))
    assert_valid(record("contradicted", [observation("a", value=480), observation("b", value=0)], reason="Independent source records disagree"))
    assert_valid(record("observed", [observation("current", quality="uncertain")]))


def test_unknown_cannot_contain_an_observation():
    assert_invalid(record("unknown", [observation("unexpected")]))


def test_unavailable_requires_attempt_time_and_reason():
    assert_invalid(record("unavailable"))
    assert_invalid(record("unavailable", reason="No response"))


def test_stale_requires_observation_and_explicit_freshness_basis():
    assert_invalid(record("stale"))
    assert_invalid(record("stale", [observation("old")]))


def test_contradicted_requires_two_observations_and_reason():
    assert_invalid(record("contradicted", [observation("only-one")], reason="Conflict"))
    assert_invalid(record("contradicted", [observation("a"), observation("b")]))


def test_observed_requires_an_observation_but_does_not_require_valid_quality():
    assert_invalid(record("observed"))
    assert_valid(record("observed", [observation("invalid", quality="invalid")]))


def test_observation_requires_provenance_timestamp_and_quality():
    item = record("observed", [observation("ok")])
    del item["observations"][0]["source"]
    assert_invalid(item)


def test_unknown_state_is_not_a_health_or_diagnosis_value():
    assert set(SCHEMA["properties"]["state"]["enum"]) == {
        "unknown",
        "unavailable",
        "stale",
        "contradicted",
        "observed",
    }
    assert "diagnosis" not in SCHEMA["properties"]
    assert "health" not in SCHEMA["properties"]
