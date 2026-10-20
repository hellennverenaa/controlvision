"""Diagnóstico ASSISTIDO, sem classificação física de vazadores."""
import cv2
import numpy as np
import pytest

from app.microholes import inspect_marked_regions
from app.vision import analyze_image


def _scene():
    image = np.zeros((360, 500, 3), np.uint8)
    image[:] = [140, 92, 50]  # tecido azul (BGR)
    cv2.rectangle(image, (105, 55), (395, 295), (232, 231, 232), -1)
    return image


def _inspect(image, points):
    preview = analyze_image(image, mode="holes", piece_tone="light")
    assert preview["status"] == "preview_only"
    return inspect_marked_regions(image, preview["contour"], [
        {"id": f"M{i + 1:02d}", "x": x, "y": y}
        for i, (x, y) in enumerate(points)
    ])


def test_tiny_dark_spots_inside_are_only_contrast_evidence():
    image = _scene()
    for point in [(160, 130), (245, 172), (335, 231)]:
        cv2.circle(image, point, 2, (55, 46, 36), -1)
    outcome = _inspect(image, [(160, 130), (245, 172), (335, 231)])
    assert len(outcome["results"]) == 3
    assert [item["status"] for item in outcome["results"]] == ["contraste_local"] * 3
    assert all("NÃO foi confirmada" in item["evidence"] for item in outcome["results"])
    assert "furo_detectado" not in str(outcome)


def test_no_contrast_does_not_claim_missing_holes():
    image = _scene()
    outcome = _inspect(image, [(150, 150)])
    assert outcome["results"][0]["status"] == "inconclusivo"
    assert "NÃO significa furo ausente" in outcome["results"][0]["evidence"]


def test_click_outside_contour_is_inconclusive():
    image = _scene()
    outcome = _inspect(image, [(28, 190)])
    assert outcome["results"][0]["status"] == "inconclusivo"
    assert "fora" in outcome["results"][0]["evidence"]


def test_marks_limits_and_invalid_points():
    image = _scene()
    preview = analyze_image(image, mode="holes", piece_tone="light")
    for marks in [[], [{"x": -1, "y": 20}], [{"x": float("nan"), "y": 50}], [{}]]:
        with pytest.raises(ValueError):
            inspect_marked_regions(image, preview["contour"], marks)
