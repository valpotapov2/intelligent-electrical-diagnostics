from PIL import Image, ImageDraw

from edi_ingest.content_regions import propose_content_regions, run_content_region_ocr


def test_text_blocks_become_source_coordinate_regions():
    result = propose_content_regions(
        400, 300,
        [
            {"text": "QF1", "bbox": [100, 50, 125, 62], "block_num": 2, "par_num": 1},
            {"text": "16A", "bbox": [130, 50, 150, 62], "block_num": 2, "par_num": 1},
        ],
        {"horizontal_segments": [], "vertical_segments": []},
        {"candidates": []},
    )
    region = result["regions"][0]
    assert region["kind"] == "ocr_text_block"
    assert region["bbox"] == [88, 38, 162, 74]


def test_line_grid_requires_multiple_intersections():
    geometry = {
        "horizontal_segments": [
            {"id": "h1", "start": [10, 20], "end": [100, 20]},
            {"id": "h2", "start": [10, 40], "end": [100, 40]},
            {"id": "h3", "start": [10, 60], "end": [100, 60]},
        ],
        "vertical_segments": [
            {"id": "v1", "start": [30, 10], "end": [30, 70]},
            {"id": "v2", "start": [70, 10], "end": [70, 70]},
        ],
    }
    result = propose_content_regions(120, 90, [], geometry, {"candidates": []})
    grid = next(item for item in result["regions"] if item["kind"] == "line_grid_candidate")
    assert grid["evidence"]["intersection_count"] == 6
    assert grid["bbox"][0] <= 22 and grid["bbox"][2] >= 78


def test_shape_density_groups_nearby_candidates_without_naming_them():
    shapes = {"candidates": [
        {"center": [40, 40], "bbox": [30, 30, 50, 50]},
        {"center": [70, 45], "bbox": [60, 35, 80, 55]},
        {"center": [90, 70], "bbox": [80, 60, 100, 80]},
    ]}
    result = propose_content_regions(300, 200, [], {}, shapes)
    cluster = next(item for item in result["regions"] if item["kind"] == "graphic_shape_cluster")
    assert cluster["evidence"]["shape_candidate_count"] == 3
    assert cluster["status"] == "content_region_candidate"


def test_content_region_ocr_maps_boxes_to_page_coordinates():
    image = Image.new("RGB", (240, 160), "white")
    ImageDraw.Draw(image).text((55, 45), "QF1", fill="black")
    proposals = {"regions": [{
        "id": "test",
        "kind": "ocr_text_block",
        "bbox": [40, 30, 120, 80],
        "status": "content_region_candidate",
    }]}
    result = run_content_region_ocr(image, proposals, lang="eng", psm=6, scale=2)
    assert len(result) == 1
    for token in result[0]["tokens"]:
        x1, y1, x2, y2 = token["bbox"]
        assert 40 <= x1 <= x2 <= 120
        assert 30 <= y1 <= y2 <= 80


def test_page_frame_grid_is_rejected():
    geometry = {
        "horizontal_segments": [
            {"id": f"h{i}", "start": [4, y], "end": [396, y]}
            for i, y in enumerate([4, 100, 200, 296])
        ],
        "vertical_segments": [
            {"id": f"v{i}", "start": [x, 4], "end": [x, 296]}
            for i, x in enumerate([4, 130, 260, 396])
        ],
    }
    result = propose_content_regions(400, 300, [], geometry, {"candidates": []})
    assert not [item for item in result["regions"] if item["kind"] == "line_grid_candidate"]


def test_shape_chain_does_not_merge_into_one_long_region():
    shapes = {"candidates": [
        {"center": [30, 40], "bbox": [20, 30, 40, 50]},
        {"center": [65, 40], "bbox": [55, 30, 75, 50]},
        {"center": [100, 40], "bbox": [90, 30, 110, 50]},
        {"center": [135, 40], "bbox": [125, 30, 145, 50]},
        {"center": [170, 40], "bbox": [160, 30, 180, 50]},
    ]}
    result = propose_content_regions(240, 160, [], {}, shapes)
    clusters = [item for item in result["regions"] if item["kind"] == "graphic_shape_cluster"]
    assert all(item["bbox"][2] - item["bbox"][0] <= 110 for item in clusters)


def test_table_candidate_requires_grid_and_repeated_text_bands():
    geometry = {
        "horizontal_segments": [
            {"id": "h1", "start": [10, 20], "end": [100, 20]},
            {"id": "h2", "start": [10, 40], "end": [100, 40]},
            {"id": "h3", "start": [10, 60], "end": [100, 60]},
        ],
        "vertical_segments": [
            {"id": "v1", "start": [30, 10], "end": [30, 70]},
            {"id": "v2", "start": [70, 10], "end": [70, 70]},
        ],
    }
    tokens = [
        {"text": f"c{i}", "bbox": [20 + (i % 2) * 40, 22 + (i // 2) * 8, 28 + (i % 2) * 40, 29 + (i // 2) * 8]}
        for i in range(8)
    ]
    result = propose_content_regions(120, 90, tokens, geometry, {"candidates": []})
    tables = [item for item in result["regions"] if item["kind"] == "table_candidate"]
    assert len(tables) == 1
    assert tables[0]["evidence"]["text_token_count"] == 8
