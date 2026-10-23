"""E1.3: indisponibilidade controlada e predição SAM 2 simulada.

Não instala PyTorch/SAM 2 nem executa pesos reais no CI. O objetivo é
validar integração, contrato e segurança do fluxo opcional.
"""
import asyncio
import base64
from io import BytesIO

import cv2
import numpy as np
import pytest
from fastapi import UploadFile

from app import sam2_optional
from app.main import inspect_preview, segmentation_preview


def image_with_piece():
    image = np.full((350, 470, 3), (130, 80, 55), dtype=np.uint8)
    cv2.rectangle(image, (90, 60), (360, 285), (230, 230, 230), -1)
    return image


def upload(image):
    ok, png = cv2.imencode(".png", image)
    assert ok
    return UploadFile(file=BytesIO(png.tobytes()), filename="foto.png")


def enable_local_fake_checkpoint(monkeypatch, tmp_path, variant="tiny"):
    checkpoint = tmp_path / "sam2.1_hiera_tiny.pt"
    checkpoint.write_bytes(b"test-only-not-real-weights")
    monkeypatch.setenv("CONTROLVISION_SAM2_ENABLED", "1")
    monkeypatch.setenv("CONTROLVISION_SAM2_VARIANT", variant)
    monkeypatch.setenv("CONTROLVISION_SAM2_CHECKPOINT", str(checkpoint))
    monkeypatch.setenv("CONTROLVISION_SAM2_DEVICE", "cpu")
    return checkpoint


def test_disabled_does_not_touch_cv_or_model(monkeypatch):
    monkeypatch.delenv("CONTROLVISION_SAM2_ENABLED", raising=False)
    monkeypatch.setattr(sam2_optional, "analyze_image",
                        lambda *a, **kw: pytest.fail("OpenCV não deveria executar"))
    monkeypatch.setattr(sam2_optional, "_predict_sam2_mask",
                        lambda *a: pytest.fail("Modelo não deveria executar"))
    result = sam2_optional.segment_sam2_optional(image_with_piece())
    assert result["status"] == "indisponivel"
    assert result["mask_png_base64"] is None
    assert result["foreground_pixels"] == 0
    assert not result["prompt_used"]


def test_enabled_without_checkpoint_stays_unavailable(monkeypatch):
    monkeypatch.setenv("CONTROLVISION_SAM2_ENABLED", "1")
    monkeypatch.delenv("CONTROLVISION_SAM2_CHECKPOINT", raising=False)
    result = sam2_optional.segment_sam2_optional(image_with_piece())
    assert result["status"] == "indisponivel"
    assert "Checkpoint" in result["warnings"][0]
    assert result["contour_px"] == []


def test_enabled_with_nonexistent_checkpoint_stays_unavailable(monkeypatch, tmp_path):
    monkeypatch.setenv("CONTROLVISION_SAM2_ENABLED", "1")
    monkeypatch.setenv("CONTROLVISION_SAM2_CHECKPOINT", str(tmp_path / "none.pt"))
    result = sam2_optional.segment_sam2_optional(image_with_piece())
    assert result["status"] == "indisponivel"


def test_invalid_variant_and_device_stay_unavailable(monkeypatch, tmp_path):
    enable_local_fake_checkpoint(monkeypatch, tmp_path, variant="bad")
    result = sam2_optional.segment_sam2_optional(image_with_piece())
    assert result["status"] == "indisponivel"
    monkeypatch.setenv("CONTROLVISION_SAM2_VARIANT", "tiny")
    monkeypatch.setenv("CONTROLVISION_SAM2_DEVICE", "tpu")
    result = sam2_optional.segment_sam2_optional(image_with_piece())
    assert result["status"] == "indisponivel"


def test_missing_dependencies_do_not_fall_back_to_opencv(monkeypatch, tmp_path):
    enable_local_fake_checkpoint(monkeypatch, tmp_path)

    def missing(*args):
        raise ModuleNotFoundError("No module named sam2")

    monkeypatch.setattr(sam2_optional, "_predict_sam2_mask", missing)
    result = sam2_optional.segment_sam2_optional(image_with_piece())
    assert result["status"] == "indisponivel"
    assert result["prompt_used"] is True
    assert result["method"] == "sam2_optional"
    assert result["mask_png_base64"] is None
    assert result["model_version"] is None


def test_baseline_cannot_provide_prompt_is_inconclusive(monkeypatch, tmp_path):
    enable_local_fake_checkpoint(monkeypatch, tmp_path)
    blank = np.full((350, 470, 3), (230, 230, 230), np.uint8)
    result = sam2_optional.segment_sam2_optional(blank)
    assert result["status"] == "inconclusivo"
    assert result["prompt_used"] is False
    assert result["mask_png_base64"] is None


def test_predictor_exception_is_generic_and_private(monkeypatch, tmp_path):
    enable_local_fake_checkpoint(monkeypatch, tmp_path)
    def fail(*args):
        raise RuntimeError("/private/factory/file-with-secrets.pt")
    monkeypatch.setattr(sam2_optional, "_predict_sam2_mask", fail)
    result = sam2_optional.segment_sam2_optional(image_with_piece())
    assert result["status"] == "inconclusivo"
    assert "secrets" not in str(result)
    assert not result["mask_png_base64"]


def test_mock_prediction_uses_bbox_and_fills_external_silhouette(monkeypatch, tmp_path):
    enable_local_fake_checkpoint(monkeypatch, tmp_path)
    observed = {}

    def fake_model(image, box, variant, checkpoint, device):
        observed.update(box=box, variant=variant, device=device)
        mask = np.zeros(image.shape[:2], dtype=np.float32)
        mask[65:282, 96:355] = 1.0
        mask[150:155, 205:212] = 0.0  # furo interno não é alvo E1.3
        return mask

    monkeypatch.setattr(sam2_optional, "_predict_sam2_mask", fake_model)
    result = sam2_optional.segment_sam2_optional(image_with_piece())
    assert result["status"] == "ok"
    assert result["method"] == "sam2_optional"
    assert result["prompt_used"] is True
    assert result["mask_origin"] == "sam2_caixa_derivada_do_contorno_opencv"
    assert result["model_version"].startswith("sam2.1_tiny")
    assert observed["variant"] == "tiny"
    assert observed["device"] == "cpu"
    assert observed["box"][0] <= 96 < observed["box"][2]
    assert observed["box"][1] <= 65 < observed["box"][3]
    png = base64.b64decode(result["mask_png_base64"], validate=True)
    decoded = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    assert decoded.shape == (350, 470)
    assert decoded[153, 209] == 255  # região interna preenchida
    assert decoded[10, 10] == 0
    assert "NÃO são independentes" in result["warnings"][0]


@pytest.mark.parametrize("bad", [
    np.zeros((120, 100), dtype=np.float32),
    np.ones((350, 470), dtype=np.float32),
    np.zeros((350, 470), dtype=np.float32),
    np.full((350, 470), np.nan, dtype=np.float32),
])
def test_bad_mock_prediction_never_produces_ok(monkeypatch, tmp_path, bad):
    enable_local_fake_checkpoint(monkeypatch, tmp_path)
    monkeypatch.setattr(sam2_optional, "_predict_sam2_mask",
                        lambda *args: bad)
    result = sam2_optional.segment_sam2_optional(image_with_piece())
    assert result["status"] == "inconclusivo"
    assert result["mask_png_base64"] is None


def test_optional_route_sam2_unavailable_and_old_route_still_works(monkeypatch):
    monkeypatch.delenv("CONTROLVISION_SAM2_ENABLED", raising=False)
    image = image_with_piece()
    ia = asyncio.run(segmentation_preview(
        file=upload(image), method="sam2", mode="holes", piece_tone="light",
    ))
    assert ia["status"] == "indisponivel"
    old = asyncio.run(inspect_preview(
        file=upload(image), mode="holes", piece_tone="light",
        cad_data=None, cad_family_data=None,
    ))
    assert old["status"] == "preview_only"
    assert len(old["contour"]) >= 3
    assert "mask_png_base64" not in old
