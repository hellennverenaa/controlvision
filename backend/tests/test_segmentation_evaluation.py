"""E1.6 — métricas reprodutíveis e API sem publicação de imagens reais."""
import asyncio
from io import BytesIO

import cv2
import numpy as np
import pytest
from fastapi import HTTPException, UploadFile

from app.main import segmentation_evaluate
from app.segmentation_contract import build_segmentation_result
from app.segmentation_evaluation import (
    score_binary_silhouette, read_reviewed_reference,
    evaluate_methods_against_reference, evaluate_segmentation,
)


def mask_of_piece():
    image = np.zeros((160, 200), np.uint8)
    cv2.rectangle(image, (45, 35), (155, 125), 255, -1)
    return image


def sample_photo():
    photo = np.full((160, 200, 3), (125, 80, 45), np.uint8)
    photo[35:126, 45:156] = (238, 238, 238)
    return photo


def png(image):
    okay, buffer = cv2.imencode(".png", image)
    assert okay
    return buffer.tobytes()


def upload(image, filename="reference.png"):
    return UploadFile(file=BytesIO(png(image)), filename=filename)


def successful_result(image, method="opencv_baseline"):
    contour = [[45, 35], [155, 35], [155, 125], [45, 125]]
    return build_segmentation_result(
        method=method,
        image_size_px=(image.shape[1], image.shape[0]),
        status="ok", mask=image, contour_px=contour, elapsed_ms=22.125,
        warnings=[], mask_origin="teste", prompt_used=method != "opencv_baseline",
    )


def unavailable_result(image):
    return build_segmentation_result(
        method="sam2_optional", image_size_px=(image.shape[1], image.shape[0]),
        status="indisponivel", mask=None, contour_px=[], elapsed_ms=0.4,
        warnings=["SAM 2 desativado."], mask_origin="teste",
    )


def test_identical_masks_perfect_iou_dice_and_zero_boundary_error():
    mask = mask_of_piece()
    m = score_binary_silhouette(mask, mask.copy())
    assert m == {
        "iou": 1.0, "dice": 1.0,
        "boundary_mean_px": 0.0, "boundary_p95_px": 0.0,
    }


def test_translated_mask_reduces_scores_and_increases_boundary_error():
    reference = mask_of_piece()
    shifted = np.zeros_like(reference)
    cv2.rectangle(shifted, (51, 35), (161, 125), 255, -1)
    m = score_binary_silhouette(reference, shifted)
    assert 0 < m["iou"] < m["dice"] < 1
    assert m["boundary_mean_px"] > 0
    assert m["boundary_p95_px"] > 0
    assert set(m) == {"iou", "dice", "boundary_mean_px", "boundary_p95_px"}


def test_disjoint_silhouettes_have_zero_overlap_but_positive_edge_error():
    a = np.zeros((100, 200), np.uint8)
    b = np.zeros_like(a)
    a[20:50, 20:50] = 255
    b[20:50, 120:150] = 255
    m = score_binary_silhouette(a, b)
    assert m["iou"] == 0
    assert m["dice"] == 0
    assert m["boundary_p95_px"] > 40


@pytest.mark.parametrize("bad", [
    np.zeros((160, 200), np.uint8),
    np.full((160, 200), 255, np.uint8),
    np.full((160, 200), 128, np.uint8),
    np.zeros((160, 200, 3), np.uint8),
    np.zeros((160, 200), np.float32),
    np.zeros((170, 200), np.uint8),
])
def test_rejects_invalid_prediction_or_dimension(bad):
    with pytest.raises(ValueError):
        score_binary_silhouette(mask_of_piece(), bad)


def test_reference_png_requires_correct_shape_and_gray_binary():
    reference = mask_of_piece()
    assert np.array_equal(read_reviewed_reference(
        png(reference), image_shape=reference.shape, filename="reference.png",
    ), reference)
    with pytest.raises(ValueError, match="mesmas dimensões"):
        read_reviewed_reference(png(reference), image_shape=(165, 200), filename="reference.png")
    with pytest.raises(ValueError, match="somente pixels"):
        read_reviewed_reference(png(reference // 255 * 180), image_shape=reference.shape,
                                filename="reference.png")
    with pytest.raises(ValueError, match="escala de cinza"):
        read_reviewed_reference(png(cv2.cvtColor(reference, cv2.COLOR_GRAY2BGR)),
                                image_shape=reference.shape, filename="reference.png")
    with pytest.raises(ValueError, match="PNG"):
        read_reviewed_reference(png(reference), image_shape=reference.shape, filename="reference.jpg")
    with pytest.raises(ValueError, match="PNG"):
        read_reviewed_reference(b"invalid", image_shape=reference.shape, filename="reference.png")


def test_unavailable_sam2_is_not_measured_or_zero_score():
    reference = mask_of_piece()
    report = evaluate_methods_against_reference(
        reference,
        opencv_result=successful_result(reference),
        sam2_result=unavailable_result(reference),
    )
    assert report["status"] == "experimental"
    assert report["units"] == "pixels_nao_calibrados"
    assert report["reference"]["human_review_declared"]
    assert report["reference"]["image_size_px"] == [200, 160]
    assert report["methods"]["opencv"]["evaluation_status"] == "avaliado"
    assert report["methods"]["opencv"]["metrics"]["iou"] == 1.0
    assert report["methods"]["opencv"]["elapsed_ms"] == 22.12
    assert report["methods"]["sam2"]["evaluation_status"] == "nao_medido"
    assert report["methods"]["sam2"]["metrics"] is None
    assert report["methods"]["sam2"]["segmentation_status"] == "indisponivel"
    assert report["methods"]["sam2"]["elapsed_ms"] == 0.4


def test_invalid_segmentation_mask_is_not_measured():
    reference = mask_of_piece()
    result = successful_result(reference)
    result["mask_png_base64"] = "invalid"
    evaluation = evaluate_segmentation(reference, result)
    assert evaluation["evaluation_status"] == "nao_medido"
    assert evaluation["metrics"] is None
    assert evaluation["reason"]


def test_api_requires_confirmation_before_processing():
    with pytest.raises(HTTPException) as error:
        asyncio.run(segmentation_evaluate(
            file=upload(sample_photo(), "foto.png"),
            reference_mask=upload(mask_of_piece()),
            reference_reviewed=False, mode="holes", piece_tone="light",
        ))
    assert error.value.status_code == 422
    assert "revisão humana" in error.value.detail


def test_api_evaluates_baseline_and_reports_disabled_sam2(monkeypatch):
    monkeypatch.delenv("CONTROLVISION_SAM2_ENABLED", raising=False)
    image = sample_photo()
    result = asyncio.run(segmentation_evaluate(
        file=upload(image, "foto.png"),
        reference_mask=upload(mask_of_piece()),
        reference_reviewed=True, mode="holes", piece_tone="light",
    ))
    assert result["status"] == "experimental"
    assert result["reference"]["human_review_declared"]
    assert result["methods"]["opencv"]["segmentation_status"] == "ok"
    assert result["methods"]["opencv"]["evaluation_status"] == "avaliado"
    assert 0.9 < result["methods"]["opencv"]["metrics"]["iou"] <= 1
    assert result["methods"]["sam2"]["evaluation_status"] == "nao_medido"
    assert result["methods"]["sam2"]["metrics"] is None


def test_api_rejects_non_binary_reference_without_fallback():
    gray = mask_of_piece()
    gray[60, 60] = 128
    with pytest.raises(HTTPException) as error:
        asyncio.run(segmentation_evaluate(
            file=upload(sample_photo(), "foto.png"),
            reference_mask=upload(gray),
            reference_reviewed=True, mode="holes", piece_tone="light",
        ))
    assert error.value.status_code == 422
    assert "somente pixels" in error.value.detail


def test_api_rejects_different_resolution_reference():
    with pytest.raises(HTTPException) as error:
        asyncio.run(segmentation_evaluate(
            file=upload(sample_photo(), "foto.png"),
            reference_mask=upload(mask_of_piece()[:100]),
            reference_reviewed=True, mode="holes", piece_tone="light",
        ))
    assert error.value.status_code == 422
    assert "mesmas dimensões" in error.value.detail
