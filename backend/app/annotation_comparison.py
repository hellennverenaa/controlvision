"""Diagnóstico de proximidade entre anotações humanas e candidatos de imagem.

Não é avaliação de erro dimensional, detecção de furos ou desempenho
metrológico: marcações humanas podem ter erro de localização.
"""
from __future__ import annotations

import math


def compare_annotations(marks, circle_candidates, micro_candidates=(), radius_px=12.0):
    """Associação um-para-um por distância em pixels; raio apenas exploratório."""
    if not math.isfinite(radius_px) or radius_px <= 0:
        raise ValueError("Raio de diagnóstico inválido.")
    if len(marks) > 60 or len(circle_candidates) + len(micro_candidates) > 200:
        raise ValueError("Limite de candidatos excedido.")

    points = []
    for kind, collection in (("circulo", circle_candidates), ("microponto", micro_candidates)):
        for item in collection:
            center = item.get("center")
            if not isinstance(center, (list, tuple)) or len(center) != 2:
                raise ValueError("Candidato inválido.")
            x, y = float(center[0]), float(center[1])
            if not (math.isfinite(x) and math.isfinite(y)):
                raise ValueError("Coordenada do candidato inválida.")
            points.append((str(item.get("id", "?")), kind, x, y))

    edges = []
    closest = []
    for index, mark in enumerate(marks):
        x, y = float(mark["x"]), float(mark["y"])
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError("Marcação inválida.")
        distances = sorted(
            (math.hypot(x-px, y-py), pindex)
            for pindex, (_, _, px, py) in enumerate(points)
        )
        closest.append(distances[0] if distances else None)
        edges.extend((dist, index, pindex) for dist, pindex in distances if dist <= radius_px)

    assigned_marks, assigned_points = {}, set()
    for distance, mark_i, candidate_i in sorted(edges):
        if mark_i in assigned_marks or candidate_i in assigned_points:
            continue
        assigned_marks[mark_i] = (distance, candidate_i)
        assigned_points.add(candidate_i)

    results = []
    for i, mark in enumerate(marks):
        best = closest[i]
        matched = assigned_marks.get(i)
        nearest = points[best[1]] if best else None
        paired = points[matched[1]] if matched else None
        results.append({
            "mark_id": str(mark.get("id", f"M{i+1:02d}"))[:24],
            "nearest_candidate_id": nearest[0] if nearest else None,
            "nearest_candidate_type": nearest[1] if nearest else None,
            "nearest_distance_px": round(best[0], 1) if best else None,
            "associated_candidate_id": paired[0] if paired else None,
            "associated_candidate_type": paired[1] if paired else None,
            "associated_distance_px": round(matched[0], 1) if matched else None,
            "status": "candidato_proximo" if matched else "sem_candidato_proximo",
        })
    return {
        "status": "diagnostico_nao_metrologico",
        "association_radius_px": radius_px,
        "manually_marked": len(marks),
        "nearby_associations": len(assigned_marks),
        "without_nearby_candidate": len(marks) - len(assigned_marks),
        "unassociated_candidates": len(points) - len(assigned_points),
        "marks": results,
        "warnings": [
            "A associação indica somente proximidade de pixels com anotações humanas.",
            "Candidatos sem anotação NÃO são necessariamente falsos positivos.",
            "Não representa taxa de acerto industrial, erro dimensional ou aprovação.",
        ],
    }
