from PIL import Image, ImageDraw

from edi_ingest.geometry import detect_geometry


def test_detects_orthogonal_line_candidates_and_intersection():
    image = Image.new("RGB", (640, 420), "white")
    draw = ImageDraw.Draw(image)
    draw.line((80, 210, 560, 210), fill="black", width=4)
    draw.line((320, 60, 320, 360), fill="black", width=4)

    result = detect_geometry(image, min_line_length=40)
    assert result["horizontal_segments"]
    assert result["vertical_segments"]
    assert result["junction_candidates"]
    assert all(item["status"] == "unverified_intersection" for item in result["junction_candidates"])


def test_empty_image_returns_no_false_segments():
    image = Image.new("RGB", (320, 240), "white")
    result = detect_geometry(image)
    assert result["horizontal_segments"] == []
    assert result["vertical_segments"] == []
    assert result["junction_candidates"] == []
