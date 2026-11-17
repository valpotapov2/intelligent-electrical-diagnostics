from PIL import Image, ImageDraw

from edi_ingest.table_structure import extract_table_structures


def test_table_structure_recovers_rows_columns_and_cells_from_expanded_region():
    image = Image.new("RGB", (320, 220), "white")
    draw = ImageDraw.Draw(image)
    xs = [40, 95, 150, 205, 260]
    ys = [40, 70, 100, 130, 160]
    for y in ys:
        draw.line((xs[0], y, xs[-1], y), fill="black", width=2)
    for x in xs:
        draw.line((x, ys[0], x, ys[-1]), fill="black", width=2)

    proposals = {"regions": [{
        "id": "table-test",
        "kind": "table_candidate",
        # Deliberately clipped on the left and top, like the real proposal.
        "bbox": [80, 60, 280, 180],
    }]}
    result = extract_table_structures(image, proposals)

    assert len(result) == 1
    structure = result[0]
    assert structure["row_count"] == 4
    assert structure["column_count"] == 4
    assert len(structure["cells"]) == 16
    assert structure["bbox"][0] <= 40
    assert structure["bbox"][1] <= 40
    assert structure["status"] == "structure_candidate"


def test_no_structure_without_table_proposal():
    image = Image.new("RGB", (100, 100), "white")
    assert extract_table_structures(image, {"regions": []}) == []
