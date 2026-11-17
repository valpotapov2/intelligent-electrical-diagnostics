from PIL import Image

from edi_ingest.roi import propose_regions, run_roi_ocr


def test_region_proposals_are_bounded_and_cover_page_zones():
    regions = propose_regions(1000, 800)
    assert {item["id"] for item in regions} == {
        "top_left", "top_right", "middle_left", "middle_right", "bottom_full"
    }
    for item in regions:
        x1, y1, x2, y2 = item["bbox"]
        assert 0 <= x1 < x2 <= 1000
        assert 0 <= y1 < y2 <= 800


def test_roi_ocr_maps_boxes_to_source_coordinates():
    image = Image.new("RGB", (320, 240), "white")
    result = run_roi_ocr(image, lang="eng", psm=11, scale=2)
    assert result["coordinate_space"] == "source_page_pixels"
    assert len(result["regions"]) == 5
    for region in result["regions"]:
        x1, y1, x2, y2 = region["bbox"]
        for token in region["tokens"]:
            tx1, ty1, tx2, ty2 = token["bbox"]
            assert x1 <= tx1 <= tx2 <= x2
            assert y1 <= ty1 <= ty2 <= y2
