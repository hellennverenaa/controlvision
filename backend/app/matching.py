"""Prévia de correspondência geométrica, SEM medição dimensional.

A escala de sobreposição vem da silhueta fotográfica e NÃO constitui
calibração px/mm. Não usar para aprovação de peças.
"""
from __future__ import annotations

import math
import numpy as np
from shapely.geometry import Polygon


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



def _refine_rigid_outline(scaled_cad, centered_photo, initial_theta, max_shift_px):
    """Refina rotação/translação da projeção usando APENAS contornos.

    Não altera a escala do CAD. Limita o deslocamento para evitar esconder
    deformações reais com um alinhamento visual exagerado.
    """
    translation = np.zeros(2, dtype=np.float64)
    theta = float(initial_theta)
    original_error = _chamfer(scaled_cad @ _rotation(theta).T, centered_photo)
    error = original_error
    # Busca local determinística, sem pontos internos, sem scaling adicional.
    stages = (
        (max(2., max_shift_px * .32), math.radians(1.)),
        (max(1., max_shift_px * .14), math.radians(.35)),
        (.4, math.radians(.12)),
    )
    for step_px, step_theta in stages:
        deltas = [
            (dx * step_px, dy * step_px, 0.)
            for dx, dy in ((-1,0),(1,0),(0,-1),(0,1),
                           (-1,-1),(-1,1),(1,-1),(1,1))
        ]
        deltas.extend(((0., 0., -step_theta), (0., 0., step_theta)))
        for _ in range(7):
            best = None
            for dx, dy, dtheta in deltas:
                shift = translation + np.array([dx, dy])
                if float(np.linalg.norm(shift)) > max_shift_px:
                    continue
                angle = theta + dtheta
                candidate = _chamfer(scaled_cad @ _rotation(angle).T + shift,
                                     centered_photo)
                if candidate < error - 1e-5 and (best is None or candidate < best[0]):
                    best = (candidate, angle, shift)
            if best is None:
                break
            error, theta, translation = best
    return theta, translation, original_error, error


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
    _, theta = min(finalists, key=lambda item: item[0])
    # A etapa anterior fixa os centros pela média do perímetro. Nas peças
    # de malha, rebarbas e pontas deslocam essa média mesmo quando a forma
    # principal se encaixa. Refinamos pequenas translações e rotações.
    max_translation = min(35., max(4., math.sqrt(photo_area) * .06))
    theta_refined, shift, initial_error_px, error_px = _refine_rigid_outline(
        scaled, photo_s, theta, max_translation
    )

    def project_at(point, angle, offset):
        xy = np.asarray(point, dtype=np.float64) * [1., -1.]
        if xy.shape != (2,) or not np.isfinite(xy).all():
            raise ValueError("Coordenada CAD inválida.")
        return (xy - center_c) * scale_visual @ _rotation(angle).T + center_p + offset

    # Mantemos o ajuste de origem se uma melhoria na média dos contornos
    # fizer o encaixe das SILHUETAS piorar. Nenhum vazador é referência.
    def silhouette_difference(angle, offset):
        a = Polygon([project_at(p, angle, offset) for p in _polygon(cad_contour)])
        b = Polygon(photo)
        if not (a.is_valid and b.is_valid):
            return None
        union = a.union(b).area
        return 100 * (1. - a.intersection(b).area / union) if union > 0 else None

    shape_before = silhouette_difference(theta, np.zeros(2))
    shape_after = silhouette_difference(theta_refined, shift)
    if (shape_before is not None and shape_after is not None
            and shape_after > shape_before + .25):
        # Por segurança, não trocar um bom encaixe por melhor Chamfer local.
        theta_refined = theta
        shift = np.zeros(2)
        error_px = initial_error_px

    def project(point):
        return project_at(point, theta_refined, shift)

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
    # Apenas índice de diferença DE FORMA 2D, após escala de visualização.
    # Não representa percentagem de erro dimensional nem tolerância metrológica.
    overlay_difference_percent = None
    if reliable_enough:
        silhouette_a = Polygon([project(p) for p in _polygon(cad_contour)])
        silhouette_b = Polygon(photo)
        if silhouette_a.is_valid and silhouette_b.is_valid:
            union = silhouette_a.union(silhouette_b).area
            if union > 0:
                overlay_difference_percent = round(
                    100 * (1 - silhouette_a.intersection(silhouette_b).area / union), 2
                )
    return {
        "status": "preview_only",
        "units": "pixels_nao_calibrados",
        "registration": "alinhamento_ilustrativo_por_silhueta",
        "registration_refinement": {
            "method": "rotacao_e_translacao_limitadas_pelo_contorno",
            "translation_px": np.round(shift, 1).tolist(),
            "translation_magnitude_px": round(float(np.linalg.norm(shift)), 1),
            "rotation_adjustment_deg": round(
                float(math.degrees(theta_refined - theta)), 2
            ),
            "initial_chamfer_px": round(initial_error_px, 2),
            "refined_chamfer_px": round(error_px, 2),
            "scale_changed_during_refinement": False,
        },
        "fit_quality": quality,
        "shape_error_relative": round(relative_error, 4),
        "visual_shape_difference_percent": overlay_difference_percent,
        "matched": matches,
        "unmatched_cad": [p for i, p in enumerate(expected) if i not in used_cad],
        "unmatched_image": [p for i, p in enumerate(observed) if i not in used_image],
        "projected_contour": [project(p).round(1).tolist() for p in _polygon(cad_contour)],
        "warnings": [
            "Correspondência apenas visual; escala ilustrativa não é calibração.",
            "Refino limitado usa apenas o contorno externo; centros internos não são utilizados.",
            "Pontos não associados podem decorrer de sombra, rabiscos e perspectiva.",
            "Diferença percentual visual usa normalização de escala e não representa erro de corte.",
            "Não inferir medidas em mm, conformidade ou defeitos nesta prévia.",
        ],
    }
