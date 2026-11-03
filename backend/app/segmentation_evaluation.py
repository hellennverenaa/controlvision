"""E1.6 — métricas experimentais de SILHUETA com referência humana revisada.

Nenhuma sobreposição CAD, anotação de furo ou máscara OpenCV conta como
verdade-terreno. A referência é um PNG binário revisado pelo operador e
independente das predições que serão avaliadas.
"""
from __future__ import annotations

import base64
import math

import cv2
import numpy as np

MAX_EVALUATION_PIXELS = 8_000_000
QUALITY_METRICS = ("iou", "dice", "boundary_mean_px", "boundary_p95_px")


def _validated_binary(mask: np.ndarray, *, expected_shape: tuple[int, int] | None = None):
    if not isinstance(mask, np.ndarray) or mask.dtype != np.uint8 or mask.ndim != 2:
        raise ValueError("A máscara deve ser PNG em escala de cinza de 8 bits.")
    h, w = mask.shape
    if h <= 0 or w <= 0 or h * w > MAX_EVALUATION_PIXELS:
        raise ValueError("Máscara excede o limite experimental de 8 megapixels.")
    if expected_shape is not None and mask.shape != expected_shape:
        raise ValueError("Máscara de referência e fotografia precisam ter as mesmas dimensões.")
    if not np.isin(mask, (0, 255)).all():
        raise ValueError("Máscara deve ter somente pixels 0 (fundo) e 255 (peça), sem cinza.")
    n = int(np.count_nonzero(mask))
    if not 0 < n < mask.size:
        raise ValueError("A referência deve conter peça e fundo, ambos não vazios.")
    return mask


def read_reviewed_reference(raw: bytes, *, image_shape: tuple[int, int],
                            filename: str) -> np.ndarray:
    """Aceita somente PNG monocanal uint8, sem interpolação ou redimensionamento."""
    if not filename.lower().endswith(".png") or not raw.startswith(
        b"\x89PNG\r\n\x1a\n"
    ):
        raise ValueError("Envie uma máscara de referência PNG, não foto ou JPEG.")
    # Verifica dimensões do IHDR antes de alocar memória para decodificar PNG.
    if len(raw) < 33 or raw[12:16] != b"IHDR":
        raise ValueError("Cabeçalho PNG inválido.")
    width = int.from_bytes(raw[16:20], "big")
    height = int.from_bytes(raw[20:24], "big")
    if (height, width) != image_shape:
        raise ValueError("Máscara PNG deve ter as mesmas dimensões da fotografia original.")
    if width * height > MAX_EVALUATION_PIXELS:
        raise ValueError("Avaliação limitada a 8 megapixels nesta etapa.")
    decoded = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if decoded is None:
        raise ValueError("Não foi possível decodificar o PNG de referência.")
    return _validated_binary(decoded, expected_shape=image_shape)


def decode_predicted_mask(segmentation: dict, *, image_shape: tuple[int, int]) -> np.ndarray:
    """Confere novamente a máscara binária fornecida pelo contrato E1.1."""
    if segmentation.get("status") != "ok":
        raise ValueError("Segmentação indisponível não pode ser avaliada.")
    if segmentation.get("mask_mime_type") != "image/png":
        raise ValueError("Segmentação sem PNG.")
    if segmentation.get("image_size_px") != [image_shape[1], image_shape[0]]:
        raise ValueError("Resolução de segmentação não corresponde à referência.")
    data = segmentation.get("mask_png_base64")
    if not isinstance(data, str):
        raise ValueError("Segmentação informou sucesso, mas não tem máscara.")
    try:
        raw = base64.b64decode(data, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError("Máscara de segmentação PNG/base64 inválida.") from exc
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Máscara de segmentação não é PNG.")
    decoded = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    return _validated_binary(decoded, expected_shape=image_shape)


def _edge(mask: np.ndarray) -> np.ndarray:
    binary = (mask > 0).astype(np.uint8)
    eroded = cv2.erode(binary, np.ones((3, 3), dtype=np.uint8))
    return (binary != eroded)


def score_binary_silhouette(reference: np.ndarray, predicted: np.ndarray) -> dict:
    """IoU, Dice e distâncias simétricas entre bordas, em pixels.

    A média é calculada nas distâncias de borda A->B e B->A; o p95
    é o percentil 95 da união dessas amostras (simétrico, não Hausdorff).
    Pixels NÃO são milímetros e estas métricas não geram tolerância de corte.
    """
    reference = _validated_binary(reference)
    predicted = _validated_binary(predicted, expected_shape=reference.shape)
    a, b = reference != 0, predicted != 0
    intersection = int(np.count_nonzero(a & b))
    count_a = int(np.count_nonzero(a))
    count_b = int(np.count_nonzero(b))
    union = count_a + count_b - intersection
    edges_a, edges_b = _edge(reference), _edge(predicted)
    if not edges_a.any() or not edges_b.any():
        raise ValueError("Bordas insuficientes para cálculo.")

    # O distanceTransform encontra distância ao pixel ZERO. Onde há borda,
    # o mapa contém zero; cada borda contrária amostra sua distância.
    distance_to_a = cv2.distanceTransform(
        np.where(edges_a, 0, 255).astype(np.uint8),
        cv2.DIST_L2, cv2.DIST_MASK_PRECISE,
    )
    distance_to_b = cv2.distanceTransform(
        np.where(edges_b, 0, 255).astype(np.uint8),
        cv2.DIST_L2, cv2.DIST_MASK_PRECISE,
    )
    distances = np.concatenate((
        distance_to_b[edges_a],
        distance_to_a[edges_b],
    ))
    return {
        "iou": round(intersection / union, 6),
        "dice": round(2 * intersection / (count_a + count_b), 6),
        "boundary_mean_px": round(float(distances.mean()), 3),
        "boundary_p95_px": round(float(np.percentile(distances, 95)), 3),
    }


def evaluate_segmentation(reference: np.ndarray, result: dict) -> dict:
    """Erro/indisponibilidade não vira zero de IoU, Dice ou borda."""
    elapsed = result.get("elapsed_ms")
    elapsed_ms = (round(float(elapsed), 2) if isinstance(elapsed, (int, float))
                  and not isinstance(elapsed, bool) and math.isfinite(elapsed)
                  and elapsed >= 0 else None)
    response = {
        "method": str(result.get("method", "desconhecido")),
        "segmentation_status": result.get("status"),
        "evaluation_status": "nao_medido",
        "metrics": None,
        "elapsed_ms": elapsed_ms,
        "prompt_used": bool(result.get("prompt_used", False)),
        "model_version": result.get("model_version"),
        "reason": None,
    }
    if result.get("status") != "ok":
        response["reason"] = "Segmentação indisponível/inconclusiva, sem máscara para avaliação."
        return response
    try:
        mask = decode_predicted_mask(result, image_shape=reference.shape)
        response["metrics"] = score_binary_silhouette(reference, mask)
        response["evaluation_status"] = "avaliado"
    except ValueError:
        response["reason"] = "A máscara do método não passou pela validação; qualidade não medida."
    return response


def evaluate_methods_against_reference(reference: np.ndarray, *,
                                       opencv_result: dict,
                                       sam2_result: dict) -> dict:
    """Uma captura, uma referência revisada e os dois resultados separadamente."""
    reference = _validated_binary(reference)
    h, w = reference.shape
    return {
        "status": "experimental",
        "units": "pixels_nao_calibrados",
        "reference": {
            "human_review_declared": True,
            "source": "png_binario_externo_revisado_pelo_operador",
            "image_size_px": [w, h],
            "foreground_pixels": int(np.count_nonzero(reference)),
        },
        "methods": {
            "opencv": evaluate_segmentation(reference, opencv_result),
            "sam2": evaluate_segmentation(reference, sam2_result),
        },
        "warnings": [
            "Confirmação de revisão humana é declarada pelo operador, não verificável automaticamente.",
            "IoU e Dice avaliam silhueta externa, NÃO vazadores nem diferenças dimensionais.",
            "Distâncias são em pixels, SEM calibração física ou tolerâncias industriais.",
            "Tempos refletem a análise de cada método, não upload, rede ou serialização.",
            "O SAM 2, quando habilitado, usa prompt de caixa derivado do OpenCV; métodos não são independentes.",
            "Uma fotografia isolada não demonstra generalização nem acurácia industrial.",
        ],
    }
