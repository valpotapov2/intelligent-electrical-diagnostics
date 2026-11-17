from edi_ingest.extract import build_model, extract_candidates


def test_extracts_component_references_and_keeps_unknown_topology():
    ocr = {
        "pages": [{
            "page": 1,
            "text": "QF1 QF2 KM1 TA1 АВР L1 L2 L3 N PE",
            "tokens": [],
        }]
    }
    result = extract_candidates(ocr)
    labels = {item["label"] for item in result["components"]}
    assert {"QF1", "QF2", "KM1", "TA1", "АВР", "L1", "L2", "L3", "N", "PE"} <= labels
    assert result["connections"] == []
    assert result["circuits"] == []


def test_model_marks_topology_as_not_implemented():
    ingested = {
        "source": {"filename": "sample.png", "media_type": "image/png", "sha256": "abc"},
        "ocr": {"pages": [{"page": 1, "text": "QF1", "tokens": []}]},
    }
    model = build_model(ingested, "Test panel")
    assert model["object"]["name"] == "Test panel"
    assert any(issue["id"] == "TOPOLOGY-NOT-IMPLEMENTED" for issue in model["issues"])
    assert model["components"][0]["sources"][0]["page"] == 1
