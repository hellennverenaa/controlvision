"""Contrato de máscaras independente de IA e regressão do fluxo OpenCV."""
import asyncio
import base64
from io import BytesIO

import cv2
import numpy as np
import pytest
from fastapi import HTTPException, UploadFile

from app.main import segmentation_preview
from app.segmentation_contract import (
    SCHEMA_VERSION, build_segmentation_result, segment_opencv_baseline
)
from app.vision import analyze_image


def photo_with_light_piece():
    image = np.full((360, 480, 3), (135, 85, 50), dtype=np.uint8)
    cv2.rectangle(image, (90, 60), (380, 290), (235, 235, 235), -1)
    return image


def test_mask_binary_png_matches_original_resolution():
    image = photo_with_light_piece()
    result = segment_opencv_baseline(image)
    assert result["schema_version"] == SCHEMA_VERSION
    assert result["status"] == "ok"
    assert result["method"] == "opencv_baseline"
    assert result["image_size_px"] == [480, 360]
    assert result["mask_origin"] == "poligono_externo_preenchido_do_opencv_atual"
    assert result["model_version"] is None
    assert result["prompt_used"] is False
    assert result["calibrated"] is False
    assert result["requires_human_review"] is True
    assert result["units"] == "pixels_nao_calibrados"
    assert result["elapsed_ms"] >= 0
    assert result["foreground_pixels"] > 60000
    encoded = base64.b64decode(result["mask_png_base64"], validate=True)
    decoded = cv2.imdecode(np.frombuffer(encoded, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    assert decoded.shape == (360, 480)
    assert decoded.dtype == np.uint8
    assert set(np.unique(decoded).tolist()) == {0, 255}
    assert decoded[180, 230] == 255
    assert decoded[20, 20] == 0


def test_baseline_no_leak_into_main_image_analyzer():
    image = photo_with_light_piece()
    before = analyze_image(image, mode="holes", piece_tone="light")
    result = segment_opencv_baseline(image)
    after = analyze_image(image, mode="holes", piece_tone="light")
    assert before == after
    assert result["contour_px"] == before["contour"]


def test_invalid_capture_is_inconclusive_without_false_empty_mask():
    image = np.full((360, 480, 3), 245, np.uint8)
    result = segment_opencv_baseline(image)
    assert result["status"] == "inconclusivo"
    assert result["mask_png_base64"] is None
    assert result["contour_px"] == []
    assert result["foreground_pixels"] == 0
    assert result["warnings"]


@pytest.mark.parametrize("bad_mask", [
    np.full((360, 480), 128, dtype=np.uint8),
    np.full((360, 480), 255, dtype=np.uint8),
    np.zeros((360, 480), dtype=np.uint8),
    np.zeros((380, 480), dtype=np.uint8),
    np.zeros((360, 480), dtype=np.float32),
])
def test_contract_rejects_invalid_masks(bad_mask):
    with pytest.raises(ValueError):
        build_segmentation_result(
            method="opencv_baseline", image_size_px=(480, 360), status="ok",
            mask=bad_mask, contour_px=[[90, 60], [380, 60], [380, 290]],
            elapsed_ms=12.0, warnings=[], mask_origin="test"
        )


def test_contract_rejects_inconclusive_with_mask():
    with pytest.raises(ValueError):
        build_segmentation_result(
            method="future_sam2", image_size_px=(480, 360),
            status="inconclusivo", mask=np.zeros((360, 480), np.uint8),
            contour_px=[], elapsed_ms=0, warnings=[], mask_origin="test"
        )


def _upload(image=None, raw=None):
    if raw is None:
        success, buffer = cv2.imencode(".png", image)
        assert success
        raw = buffer.tobytes()
    return UploadFile(file=BytesIO(raw), filename="foto.png")


def test_optional_endpoint_returns_same_contract_without_changing_main_route():
    res = asyncio.run(segmentation_preview(
        file=_upload(photo_with_light_piece()),
        method="opencv", mode="holes", piece_tone="light"
    ))
    assert res["schema_version"] == SCHEMA_VERSION
    assert res["status"] == "ok"
    assert res["method"] == "opencv_baseline"


def test_optional_endpoint_rejects_unavailable_model_explicitly():
    with pytest.raises(HTTPException) as error:
        asyncio.run(segmentation_preview(file=_upload(raw=b"ignored"), method="sam2"))
    assert error.value.status_code == 422
    assert "indisponível" in error.value.detail


def test_optional_endpoint_rejects_invalid_image():
    with pytest.raises(HTTPException) as error:
        asyncio.run(segmentation_preview(file=_upload(raw=b"not image"), method="opencv", mode="holes", piece_tone="light"))
    assert error.value.status_code == 422


def test_optional_endpoint_rejects_oversized_image():
    with pytest.raises(HTTPException) as error:
        asyncio.run(segmentation_preview(file=_upload(raw=b"x" * 15_000_001), method="opencv", mode="holes", piece_tone="light"))
    assert error.value.status_code == 413
