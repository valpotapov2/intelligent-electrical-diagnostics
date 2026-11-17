from PIL import Image

from edi_ingest import table_ocr


def test_read_table_cells_preserves_raw_text_and_confidence(monkeypatch):
    def fake_image_to_data(image, lang, config, output_type):
        return {
            "text": ["12,5", ""],
            "conf": ["87.5", "-1"],
        }

    monkeypatch.setattr(table_ocr.pytesseract, "image_to_data", fake_image_to_data)
    image = Image.new("RGB", (100, 60), "white")
    structures = [{
        "id": "s1",
        "cells": [{
            "row": 0,
            "column": 0,
            "bbox": [5, 5, 50, 30],
            "status": "cell_candidate",
        }],
    }]

    result = table_ocr.read_table_cells(image, structures)
    cell = result[0]["cells"][0]
    assert cell["text_raw"] == "12,5"
    assert cell["tokens"] == [{"text": "12,5", "confidence": 87.5}]
    assert cell["mean_confidence"] == 87.5
    assert cell["status"] == "ocr_read"


def test_read_table_cells_marks_empty_cell_without_inventing_value(monkeypatch):
    def fake_image_to_data(image, lang, config, output_type):
        return {"text": [""], "conf": ["-1"]}

    monkeypatch.setattr(table_ocr.pytesseract, "image_to_data", fake_image_to_data)
    image = Image.new("RGB", (40, 40), "white")
    result = table_ocr.read_table_cells(image, [{
        "id": "s2",
        "cells": [{"row": 0, "column": 0, "bbox": [0, 0, 30, 30]}],
    }])
    cell = result[0]["cells"][0]
    assert cell["text_raw"] == ""
    assert cell["mean_confidence"] is None
    assert cell["status"] == "ocr_empty"
