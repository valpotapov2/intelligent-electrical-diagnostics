from edi_ingest.cli import _print_table_summary


def test_table_summary_prints_cells_and_raw_confidence(capsys):
    page = {
        "table_structures": [{
            "id": "structure-1",
            "row_count": 1,
            "column_count": 2,
            "cells": [
                {"row": 0, "column": 0},
                {"row": 0, "column": 1},
            ],
        }],
        "table_cell_ocr": [{
            "source_structure_id": "structure-1",
            "cells": [
                {"row": 0, "column": 0, "text_raw": "12,5", "mean_confidence": 91.2, "status": "ocr_read"},
                {"row": 0, "column": 1, "text_raw": "", "mean_confidence": None, "status": "ocr_empty"},
            ],
        }],
    }

    _print_table_summary(1, page)
    output = capsys.readouterr().out

    assert "1 rows × 2 columns" in output
    assert "r1 c1: 12,5" in output
    assert "OCR confidence: 91.2" in output
    assert "r1 c2: [empty]" in output
    assert "not verified values" in output
