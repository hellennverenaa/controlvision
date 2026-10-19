"""Prévia de correspondência geométrica, SEM medição dimensional.

A escala de sobreposição vem da silhueta fotográfica e NÃO constitui
calibração px/mm. Não usar para aprovação de peças.
"""
from __future__ import annotations

import math
import numpy as np


def _polygon(points):
    arr = np.asarray(points, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] != 2 or len(arr) < 3 or len(arr) > 10000:
        raise ValueError("Contorno inválido ou extenso demais.")
    if not np.isfinite(arr).all():
        raise ValueError("Contorno contém coordenadas inválidas.")
    if np.allclose(arr[0], arr[-1]):
        arr = arr[:-1]
    return arr


def _area(points):
    x, y = points[:, 0], points[:, 1]
    return abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))) / 2


def _sample_outline(points, count=144):
    closed = np.vstack([points, points[0]])
    delta = np.diff(closed, axis=0)
    lengths = np.linalg.norm(delta, axis=1)
    perimeter = float(lengths.sum())
    if perimeter < 1e-6:
        raise ValueError("Contorno degenerado.")
    offsets = np.r_[0., np.cumsum(lengths)]
    targets = np.linspace(0, perimeter, count, endpoint=False)
    indices = np.searchsorted(offsets, targets, side="right") - 1
    indices = np.clip(indices, 0, len(points) - 1)
    ratios = (targets - offsets[indices]) / np.maximum(lengths[indices], 1e-12)
    return closed[indices] + delta[indices] * ratios[:, None]


def _rotation(theta):
    c, s = math.cos(theta), math.sin(theta)
    return np.array([[c, -s], [s, c]], dtype=np.float64)


def _chamfer(projected, target):
    d2 = ((projected[:, None, :] - target[None, :, :]) ** 2).sum(axis=2)
    a, b = np.sqrt(d2.min(axis=1)), np.sqrt(d2.min(axis=0))
    ka, kb = max(1, int(len(a) * .90)), max(1, int(len(b) * .90))
    return float((np.partition(a, ka - 1)[:ka].mean() +
                  np.partition(b, kb - 1)[:kb].mean()) / 2)


def match_visual(cad_contour, photo_contour, cad_features, image_candidates):
    """Sobrepõe por rotação+translação e fator de EXIBIÇÃO, nunca para mm.

    O eixo CAD Y para cima é convertido ao eixo fotográfico Y para baixo.
    Não tenta espelhamento automático nem corrige perspectiva.
    """
    cad = _polygon(cad_contour) * np.array([1., -1.])
    photo = _polygon(photo_contour)
    cad_area, photo_area = _area(cad), _area(photo)
    if cad_area < .1 or photo_area < 100:
        raise ValueError("Contorno insuficiente para correspondência visual.")
    if len(cad_features) > 100 or len(image_candidates) > 100:
        raise ValueError("Muitos pontos para a prévia experimental.")
    cad_s, photo_s = _sample_outline(cad), _sample_outline(photo)
    center_c, center_p = cad_s.mean(axis=0), photo_s.mean(axis=0)
    cad_s -= center_c
    photo_s -= center_p
    # Fator apenas ilustrativo estimado pela área das silhuetas.
    scale_visual = math.sqrt(photo_area / cad_area)
    scaled = cad_s * scale_visual
    trials = []
    for degree in range(0, 360, 10):
        theta = math.radians(degree)
        trials.append((_chamfer(scaled @ _rotation(theta).T, photo_s), theta))
    trials.sort(key=lambda item: item[0])
    finalists = []
    for _, base_angle in trials[:3]:
        for delta in np.arange(-10, 10.01, 1.0):
            theta = base_angle + math.radians(float(delta))
            finalists.append((_chamfer(scaled @ _rotation(theta).T, photo_s), theta))
    error_px, theta = min(finalists, key=lambda item: item[0])
    rotation = _rotation(theta)

    def project(point):
        xy = np.asarray(point, dtype=np.float64) * [1., -1.]
        if xy.shape != (2,) or not np.isfinite(xy).all():
            raise ValueError("Coordenada CAD inválida.")
        return (xy - center_c) * scale_visual @ rotation.T + center_p

    relative_error = error_px / math.sqrt(photo_area)
    reliable_enough = relative_error <= .09
    quality = "baixa" if not reliable_enough else (
        "moderada" if relative_error > .045 else "preliminar")
    expected = []
    for feature in cad_features:
        if feature.get("classification") != "vazador":
            continue
        if feature.get("center") is None:
            raise ValueError("Vazador CAD sem centro definido.")
        expected.append({
            "cad_id": str(feature["id"]),
            "position_px": project(feature["center"]).round(1).tolist(),
        })
    observed = []
    for candidate in image_candidates:
        center = candidate.get("center")
        if not isinstance(center, list) or len(center) != 2 or not np.isfinite(center).all():
            raise ValueError("Candidato fotográfico inválido.")
        observed.append({
            "image_id": str(candidate["id"]),
            "position_px": [float(v) for v in center],
        })

    # Limiar relativo SOMENTE de associação visual, não tolerância da Qualidade.
    threshold_px = max(7., math.sqrt(photo_area) * .045)
    pairs = []
    if reliable_enough:
        for ei, ref in enumerate(expected):
            for oi, detected in enumerate(observed):
                distance = float(np.linalg.norm(
                    np.array(ref["position_px"]) - detected["position_px"]))
                if distance <= threshold_px:
                    pairs.append((distance, ei, oi))
    used_cad, used_image, matches = set(), set(), []
    for _, ei, oi in sorted(pairs):
        if ei in used_cad or oi in used_image:
            continue
        used_cad.add(ei)
        used_image.add(oi)
        matches.append({
            "cad_id": expected[ei]["cad_id"],
            "image_id": observed[oi]["image_id"],
            "expected_px": expected[ei]["position_px"],
            "detected_px": observed[oi]["position_px"],
        })
    return {
        "status": "preview_only",
        "units": "pixels_nao_calibrados",
        "registration": "alinhamento_ilustrativo_por_silhueta",
        "fit_quality": quality,
        "shape_error_relative": round(relative_error, 4),
        "matched": matches,
        "unmatched_cad": [p for i, p in enumerate(expected) if i not in used_cad],
        "unmatched_image": [p for i, p in enumerate(observed) if i not in used_image],
        "projected_contour": [project(p).round(1).tolist() for p in _polygon(cad_contour)],
        "warnings": [
            "Correspondência apenas visual; escala ilustrativa não é calibração.",
            "Pontos não associados podem decorrer de sombra, rabiscos e perspectiva.",
            "Não inferir medidas em mm, conformidade ou defeitos nesta prévia.",
        ],
    }
