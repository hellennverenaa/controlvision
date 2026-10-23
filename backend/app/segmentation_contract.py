"""Contrato experimental de segmentação, compartilhável entre OpenCV e futura IA.

Saída padronizada de máscara da SILHUETA externa, sem análise de
vazadores e sem qualquer inferência de medidas físicas ou conformidade.
"""
from __future__ import annotations

import base64
import math
from time import perf_counter

import cv2
import numpy as np

from .vision import analyze_image


SCHEMA_VERSION = "1.0"
STATUS_VALUES = {"ok", "inconclusivo", "indisponivel"}


def build_segmentation_result(
    *,
    method: str,
    image_size_px: tuple[int, int],
    status: str,
    mask: np.ndarray | None,
    contour_px: list,
    elapsed_ms: float,
    warnings: list[str],
    mask_origin: str,
    prompt_used: bool = False,
    model_version: str | None = None,
) -> dict:
    """Valida e serializa uma máscara 8-bit binária em PNG/base64.

    O mesmo contrato deverá ser usado por OpenCV, SAM 2 e qualquer modelo
    posterior. O status inconclusivo NÃO permite fabricar máscara vazia
    como se fosse uma segmentação bem-sucedida.
    """
    if not method or not isinstance(method, str):
        raise ValueError("Método de segmentação inválido.")
    if status not in STATUS_VALUES:
        raise ValueError("Status de segmentação inválido.")
    if len(image_size_px) != 2:
        raise ValueError("Dimensões da imagem inválidas.")
    width, height = image_size_px
    if (not isinstance(width, int) or not isinstance(height, int)
            or not 0 < width * height <= 20_000_000):
        raise ValueError("Dimensões da imagem inválidas.")
    if not math.isfinite(elapsed_ms) or elapsed_ms < 0:
        raise ValueError("Tempo de processamento inválido.")
    if not isinstance(warnings, list) or not all(isinstance(x, str) for x in warnings):
        raise ValueError("Avisos inválidos.")
    if not isinstance(contour_px, list):
        raise ValueError("Contorno inválido.")
    png_base64 = None
    foreground_pixels = 0
    if status == "ok":
        if (not isinstance(mask, np.ndarray) or mask.shape != (height, width)
                or mask.dtype != np.uint8):
            raise ValueError("Máscara deve ser uint8, com dimensões originais.")
        if not np.isin(mask, [0, 255]).all():
            raise ValueError("Máscara deve conter exclusivamente 0 ou 255.")
        foreground_pixels = int(np.count_nonzero(mask))
        if not foreground_pixels or foreground_pixels == width * height:
            raise ValueError("Máscara sem peça isolada.")
        if len(contour_px) < 3:
            raise ValueError("Contorno externo insuficiente.")
        encoded, buffer = cv2.imencode(".png", mask)
        if not encoded:
            raise ValueError("Falha ao codificar máscara em PNG.")
        png_base64 = base64.b64encode(buffer.tobytes()).decode("ascii")
    else:
        if mask is not None or contour_px:
            raise ValueError("Resultado inconclusivo não pode conter segmentação.")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "method": method,
        "model_version": model_version,
        "prompt_used": bool(prompt_used),
        "image_size_px": [width, height],
        "mask_mime_type": "image/png",
        "mask_png_base64": png_base64,
        "mask_origin": mask_origin,
        "contour_px": contour_px,
        "foreground_pixels": foreground_pixels,
        "elapsed_ms": round(float(elapsed_ms), 2),
        "units": "pixels_nao_calibrados",
        "calibrated": False,
        "requires_human_review": True,
        "warnings": warnings,
    }


def segment_opencv_baseline(
    image: np.ndarray,
    *,
    mode: str = "holes",
    piece_tone: str = "light",
) -> dict:
    """Adapta a saída atual do OpenCV, SEM modificar o detector existente.

    Máscara: preenchimento da silhueta externa poligonal já retornada pelo
    OpenCV. Pequenos recortes e furos INTERNOS não são mascarados nesta fase;
    não é máscara original exata da limiarização nem medição de vazadores.
    """
    if image is None or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Imagem inválida.")
    height, width = image.shape[:2]
    started = perf_counter()
    preview = analyze_image(image, mode=mode, piece_tone=piece_tone)
    elapsed_ms = (perf_counter() - started) * 1000
    if preview["status"] != "preview_only":
        return build_segmentation_result(
            method="opencv_baseline",
            image_size_px=(width, height),
            status="inconclusivo",
            mask=None,
            contour_px=[],
            elapsed_ms=elapsed_ms,
            warnings=list(preview.get("warnings", [])),
            mask_origin="contorno_externo_opencv_aproximado",
        )

    contour = preview["contour"]
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.fillPoly(mask, [np.asarray(contour, dtype=np.int32)], 255)
    # O tempo inclui também a codificação em PNG, medido à parte pela API
    # futuramente quando as duas abordagens estiverem lado a lado.
    return build_segmentation_result(
        method="opencv_baseline",
        image_size_px=(width, height),
        status="ok",
        mask=mask,
        contour_px=contour,
        elapsed_ms=elapsed_ms,
        warnings=[
            *preview.get("warnings", []),
            "Máscara do baseline é o polígono externo aproximado e preenchido; "
            "não representa a máscara binária bruta, vazadores ou furos internos.",
            "Tempo informado mede a análise OpenCV, não upload nem serialização PNG.",
        ],
        mask_origin="poligono_externo_preenchido_do_opencv_atual",
    )
