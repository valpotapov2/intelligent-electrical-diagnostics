from PIL import Image, ImageDraw

from edi_ingest.symbols import detect_symbol_candidates


def test_detects_circle_and_quadrilateral_as_unclassified_shapes():
    image = Image.new("RGB", (500, 300), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((70, 80, 130, 140), outline="black", width=4)
    draw.rectangle((250, 75, 330, 145), outline="black", width=4)

    result = detect_symbol_candidates(image)
    families = {item["candidate_family"] for item in result["candidates"]}
    assert "circular_outline" in families
    assert "rectangular_outline" in families
    assert all(item["status"] == "unclassified_shape_candidate" for item in result["candidates"])
    assert all(item["classification_confidence"] is None for item in result["candidates"])


def test_ocr_text_box_suppresses_overlapping_shape_candidate():
    image = Image.new("RGB", (300, 180), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((80, 60, 170, 120), outline="black", width=4)

    result = detect_symbol_candidates(image, ocr_tokens=[{"bbox": [70, 50, 180, 130]}])
    assert result["candidates"] == []


def test_blank_image_has_no_shape_candidates():
    image = Image.new("RGB", (300, 180), "white")
    result = detect_symbol_candidates(image)
    assert result["candidates"] == []
