"""Executor opcional SAM 2 para a silhueta da peça (ControlVision E1.3).

Desligado por padrão. Não instala pacotes, não baixa modelos e não modifica
o detector OpenCV, o CAD, os vazadores nem a rota de inspeção existente.
Este módulo só importa torch/SAM 2 depois de validar a configuração local.
"""
from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
from threading import Lock
from time import perf_counter

import cv2
import numpy as np

from .segmentation_contract import build_segmentation_result
from .vision import analyze_image


# Nomes de configurações da distribuição oficial facebookresearch/sam2.
MODEL_CONFIGS = {
    "tiny": "configs/sam2.1/sam2.1_hiera_t.yaml",
    "small": "configs/sam2.1/sam2.1_hiera_s.yaml",
    "base_plus": "configs/sam2.1/sam2.1_hiera_b+.yaml",
    "large": "configs/sam2.1/sam2.1_hiera_l.yaml",
}
_PREDICT_LOCK = Lock()


@lru_cache(maxsize=1)
def _load_predictor(variant: str, checkpoint: str, device: str):
    """Carrega pesos locais uma vez, sem downloads e sem import em startup."""
    import torch
    from sam2.build_sam import build_sam2
    from sam2.sam2_image_predictor import SAM2ImagePredictor

    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("cuda_indisponivel")
    predictor = SAM2ImagePredictor(
        build_sam2(MODEL_CONFIGS[variant], checkpoint, device=device)
    )
    return torch, predictor


def _predict_sam2_mask(image: np.ndarray, bbox: list[int], variant: str,
                       checkpoint: str, device: str) -> np.ndarray:
    """Uma predição por caixa, sem marcações de furo ou retreinamento."""
    # O predictor mantém estado por imagem; serializar a inferência evita
    # cruzamento entre uploads em duas requisições simultâneas.
    with _PREDICT_LOCK:
        torch, predictor = _load_predictor(variant, checkpoint, device)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        with torch.inference_mode():
            predictor.set_image(rgb)
            masks, _scores, _logits = predictor.predict(
                box=np.asarray(bbox, dtype=np.float32),
                multimask_output=False,
            )
        if len(masks) != 1:
            raise ValueError("Quantidade inesperada de máscaras SAM 2.")
        return np.asarray(masks[0])


def _response(image: np.ndarray, started: float, *, status: str,
              reason: str, prompt_used: bool = False) -> dict:
    height, width = image.shape[:2]
    return build_segmentation_result(
        method="sam2_optional",
        image_size_px=(width, height),
        status=status,
        mask=None,
        contour_px=[],
        elapsed_ms=(perf_counter() - started) * 1000,
        warnings=[reason, "Nenhuma máscara de IA foi obtida; o OpenCV padrão não foi substituído."],
        mask_origin="sam2_caixa_derivada_do_contorno_opencv",
        prompt_used=prompt_used,
    )


def segment_sam2_optional(image: np.ndarray, *, mode: str = "holes",
                          piece_tone: str = "light") -> dict:
    """Retorna contrato v1, inclusive em falhas de configuração/inferência.

    A caixa vem do contorno OpenCV e é um prompt automático. Portanto uma
    eventual máscara SAM 2 NÃO é resultado independente do baseline.
    """
    if image is None or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Imagem inválida.")
    if mode not in ("holes", "marks") or piece_tone not in ("light", "dark"):
        raise ValueError("Modo ou tom inválido.")
    height, width = image.shape[:2]
    if width * height > 20_000_000:
        raise ValueError("Imagem excede 20 megapixels.")
    started = perf_counter()
    if os.getenv("CONTROLVISION_SAM2_ENABLED") != "1":
        return _response(
            image, started, status="indisponivel",
            reason="SAM 2 desativado. Defina CONTROLVISION_SAM2_ENABLED=1 apenas em laboratório."
        )

    variant = os.getenv("CONTROLVISION_SAM2_VARIANT", "tiny")
    if variant not in MODEL_CONFIGS:
        return _response(
            image, started, status="indisponivel",
            reason="Variante SAM 2 não suportada (tiny, small, base_plus, large)."
        )
    checkpoint = os.getenv("CONTROLVISION_SAM2_CHECKPOINT", "").strip()
    if not checkpoint or not Path(checkpoint).is_file():
        return _response(
            image, started, status="indisponivel",
            reason="Checkpoint SAM 2 não configurado ou inexistente no computador."
        )
    device = os.getenv("CONTROLVISION_SAM2_DEVICE", "cpu").lower()
    if device not in ("cpu", "cuda"):
        return _response(
            image, started, status="indisponivel",
            reason="Dispositivo SAM 2 inválido. Use cpu ou cuda."
        )

    # E1.3: usa o contorno já existente exclusivamente para montar o prompt
    # (caixa delimitadora). A caixa não contém informação dos vazadores.
    try:
        preview = analyze_image(image, mode=mode, piece_tone=piece_tone)
    except ValueError:
        return _response(
            image, started, status="inconclusivo",
            reason="OpenCV não conseguiu fornecer um contorno inicial para a caixa SAM 2."
        )
    if preview["status"] != "preview_only" or len(preview["contour"]) < 3:
        return _response(
            image, started, status="inconclusivo",
            reason="Sem silhueta inicial confiável para a caixa SAM 2."
        )
    x, y, bw, bh = cv2.boundingRect(np.asarray(preview["contour"], dtype=np.int32))
    box = [x, y, min(width - 1, x + bw - 1), min(height - 1, y + bh - 1)]
    if bw < 8 or bh < 8:
        return _response(
            image, started, status="inconclusivo",
            reason="Contorno inicial pequeno demais para inferência assistida."
        )

    try:
        prediction = _predict_sam2_mask(image, box, variant, checkpoint, device)
    except (ImportError, ModuleNotFoundError):
        return _response(
            image, started, status="indisponivel",
            reason="Dependências locais ausentes: instale torch e SAM 2 em ambiente de teste separado.",
            prompt_used=True,
        )
    except Exception:
        # Não devolver paths, stacktrace ou detalhes privados ao navegador.
        return _response(
            image, started, status="inconclusivo",
            reason="Execução do SAM 2 falhou neste ambiente. Consulte o log local do servidor.",
            prompt_used=True,
        )

    # Conferir shape antes de binarizar, sem redimensionar silenciosamente.
    if (prediction.shape != (height, width) or
            not np.issubdtype(prediction.dtype, np.number)
            and prediction.dtype != np.dtype(bool)):
        return _response(
            image, started, status="inconclusivo",
            reason="SAM 2 retornou máscara com dimensões ou tipo inválidos.",
            prompt_used=True,
        )
    if not np.isfinite(prediction).all():
        return _response(
            image, started, status="inconclusivo",
            reason="SAM 2 retornou valores não finitos.",
            prompt_used=True,
        )

    binary = (prediction > 0.5).astype(np.uint8) * 255
    contours, _hierarchy = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return _response(
            image, started, status="inconclusivo",
            reason="SAM 2 não isolou uma região da peça.",
            prompt_used=True,
        )
    outer = max(contours, key=cv2.contourArea)
    area = float(cv2.contourArea(outer))
    ox, oy, ow, oh = cv2.boundingRect(outer)
    if (area < .01 * width * height or area > .90 * width * height
            or ox <= 1 or oy <= 1 or ox + ow >= width - 1
            or oy + oh >= height - 1):
        return _response(
            image, started, status="inconclusivo",
            reason="Máscara SAM 2 não isolou uma peça interna plausível; revisar o recorte.",
            prompt_used=True,
        )

    # Para comparar com o baseline: usar SOMENTE silhueta externa preenchida.
    polygon = cv2.approxPolyDP(outer, 1.5, True).reshape(-1, 2)
    if len(polygon) < 3:
        return _response(
            image, started, status="inconclusivo",
            reason="Contorno SAM 2 insuficiente para comparação.",
            prompt_used=True,
        )
    filled = np.zeros((height, width), dtype=np.uint8)
    cv2.fillPoly(filled, [polygon.astype(np.int32)], 255)
    return build_segmentation_result(
        method="sam2_optional",
        image_size_px=(width, height),
        status="ok",
        mask=filled,
        contour_px=polygon.tolist(),
        elapsed_ms=(perf_counter() - started) * 1000,
        warnings=[
            "Máscara SAM 2 assistida por caixa automática originada do OpenCV; "
            "os dois métodos NÃO são independentes nesta etapa.",
            "Silhueta externa aproximada e preenchida; vazadores internos não são classificados.",
            "Modelo não validado em fotos reais. Tempo não inclui upload nem codificação PNG.",
        ],
        mask_origin="sam2_caixa_derivada_do_contorno_opencv",
        prompt_used=True,
        model_version=f"sam2.1_{variant}:{Path(checkpoint).name}",
    )
