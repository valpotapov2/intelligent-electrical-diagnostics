import json
from pathlib import Path

from edi_ingest.evidence_cli import main


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schema" / "diagnostic-evidence.schema.json"
DEPENDENCIES = (
    ROOT
    / "diagnostics"
    / "scenarios"
    / "faa-drpds-diagnostic-dependencies.v0.1.json"
)


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")
    return str(path)


def valid_record():
    model = json.loads(DEPENDENCIES.read_text(encoding="utf-8"))
    question = model["questions"][0]
    return {
        "evidence_id": "cli-ev-1",
        "question_id": question["id"],
        "evidence_key": question["required_evidence"][0],
        "state": "unknown",
        "observations": [],
    }


def test_cli_validates_record_and_prints_machine_readable_result(tmp_path, monkeypatch, capsys):
    record_path = write_json(tmp_path / "record.json", valid_record())
    monkeypatch.setattr(
        "sys.argv",
        [
            "edi-evidence-validate",
            "--record",
            record_path,
            "--dependency-model",
            str(DEPENDENCIES),
            "--schema",
            str(SCHEMA),
        ],
    )

    assert main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output == {
        "valid": True,
        "evidence_id": "cli-ev-1",
        "question_id": valid_record()["question_id"],
        "evidence_key": valid_record()["evidence_key"],
    }


def test_cli_returns_nonzero_and_explains_invalid_record(tmp_path, monkeypatch, capsys):
    record = valid_record()
    record["state"] = "healthy"
    record_path = write_json(tmp_path / "record.json", record)
    monkeypatch.setattr(
        "sys.argv",
        [
            "edi-evidence-validate",
            "--record",
            record_path,
            "--dependency-model",
            str(DEPENDENCIES),
            "--schema",
            str(SCHEMA),
        ],
    )

    assert main() == 2
    captured = capsys.readouterr()
    assert "Invalid evidence record:" in captured.err
    assert captured.out == ""


def test_cli_validates_current_state_array(tmp_path, monkeypatch, capsys):
    model = json.loads(DEPENDENCIES.read_text(encoding="utf-8"))
    first = valid_record()
    question = model["questions"][1]
    second = {
        "evidence_id": "cli-ev-2",
        "question_id": question["id"],
        "evidence_key": question["required_evidence"][0],
        "state": "unknown",
        "observations": [],
    }
    record_path = write_json(tmp_path / "snapshot.json", [first, second])
    monkeypatch.setattr(
        "sys.argv",
        [
            "edi-evidence-validate",
            "--record",
            record_path,
            "--dependency-model",
            str(DEPENDENCIES),
            "--schema",
            str(SCHEMA),
        ],
    )

    assert main() == 0
    assert json.loads(capsys.readouterr().out) == {"valid": True, "record_count": 2}


def test_cli_rejects_duplicate_requirement_in_snapshot(tmp_path, monkeypatch, capsys):
    first = valid_record()
    second = dict(first, evidence_id="cli-ev-duplicate")
    record_path = write_json(tmp_path / "snapshot.json", [first, second])
    monkeypatch.setattr(
        "sys.argv",
        [
            "edi-evidence-validate",
            "--record",
            record_path,
            "--dependency-model",
            str(DEPENDENCIES),
            "--schema",
            str(SCHEMA),
        ],
    )

    assert main() == 2
    assert "duplicate current-state requirement" in capsys.readouterr().err
