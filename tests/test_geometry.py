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
    assert len(result["junction_candidates"]) == 1
    assert result["junction_candidates"][0]["point"] == [320, 210]
    assert all(item["status"] == "unverified_intersection" for item in result["junction_candidates"])


def test_hough_duplicates_are_merged_into_one_segment_per_axis():
    image = Image.new("RGB", (640, 420), "white")
    draw = ImageDraw.Draw(image)
    draw.line((80, 210, 560, 210), fill="black", width=5)
    result = detect_geometry(image, min_line_length=40)
    assert len(result["horizontal_segments"]) == 1
    assert result["vertical_segments"] == []
    assert result["horizontal_segments"][0]["length_px"] >= 475


def test_nearby_but_non_intersecting_lines_do_not_create_junction():
    image = Image.new("RGB", (640, 420), "white")
    draw = ImageDraw.Draw(image)
    draw.line((80, 180, 560, 180), fill="black", width=4)
    draw.line((320, 240, 320, 360), fill="black", width=4)
    result = detect_geometry(image, min_line_length=40)
    assert result["horizontal_segments"]
    assert result["vertical_segments"]
    assert result["junction_candidates"] == []


def test_empty_image_returns_no_false_segments():
    image = Image.new("RGB", (320, 240), "white")
    result = detect_geometry(image)
    assert result["horizontal_segments"] == []
    assert result["vertical_segments"] == []
    assert result["junction_candidates"] == []


def test_native_pdf_vector_primitives_are_preserved():
    import fitz

    from edi_ingest.ingest import _extract_pdf_vector_primitives

    document = fitz.open()
    page = document.new_page(width=300, height=200)
    page.draw_line((20, 40), (250, 40), color=(0, 0, 0), width=1)
    page.draw_rect((30, 70, 120, 130), color=(0, 0, 0), width=1)

    result = _extract_pdf_vector_primitives(page)
    assert result["coordinate_space"] == "pdf_points"
    assert len(result["lines"]) >= 1
    assert len(result["rectangles"]) >= 1
    assert result["lines"][0]["start"] == [20.0, 40.0]
    assert result["lines"][0]["end"] == [250.0, 40.0]
