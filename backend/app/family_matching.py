"""Prévia de padrão de vazadores com numeração desconhecida.

Comparação em pixels ilustrativos para todas as geometrias CAD, sem inferir
numeração ou medidas reais. Não dá resultado industrial.
"""
from __future__ import annotations

from .matching import match_visual


def compare_size_family(pieces, photo_contour, circle_candidates, micro_candidates=()):
    if not isinstance(pieces, list) or not (1 <= len(pieces) <= 15):
        raise ValueError("Prévia de família admite de 1 a 15 referências.")
    if len(circle_candidates) + len(micro_candidates) > 140:
        raise ValueError("Candidatos demais para prévia da família.")

    photo_candidates = [
        {**item, "id": "I:" + str(item["id"])}
        for item in circle_candidates
    ] + [
        {**item, "id": "S:" + str(item["id"])}
        for item in micro_candidates
    ]
    comparisons = []
    for item in pieces:
        if not isinstance(item, dict):
            raise ValueError("Molde inválido.")
        cad_features = [
            {
                "id": feature["id"],
                "center": feature["center"],
                "classification": "vazador",
            }
            for feature in item.get("features", [])
            if feature.get("shape") == "circular"
        ]
        if not cad_features:
            continue
        try:
            output = match_visual(
                item["points"], photo_contour,
                cad_features, photo_candidates,
            )
        except (ValueError, TypeError, KeyError, IndexError):
            continue
        comparisons.append({
            "piece_id": str(item.get("id", "?"))[:60],
            "size": str(item.get("size") or item.get("name", "não informada"))[:80],
            "cad_circle_count": len(cad_features),
            "fit_quality": output["fit_quality"],
            "shape_error_relative": output["shape_error_relative"],
            "visual_shape_difference_percent": output["visual_shape_difference_percent"],
            # Contorno CAD projetado, apenas para comparar visualmente com
            # a silhueta vermelha. A escala é ilustrativa, não metrológica.
            "projected_contour": output["projected_contour"],
            "nearby_candidates": len(output["matched"]),
            "projected_circles": [
                {
                    "cad_id": match["cad_id"],
                    "nearest_candidate_id": match["image_id"],
                    "position_px": match["expected_px"],
                }
                for match in output["matched"]
            ] + [
                {
                    "cad_id": feature["cad_id"],
                    "nearest_candidate_id": None,
                    "position_px": feature["position_px"],
                }
                for feature in output["unmatched_cad"]
            ],
        })
    comparisons.sort(key=lambda item: (
        item["shape_error_relative"],
        -item["nearby_candidates"],
    ))
    reliable = [entry for entry in comparisons if entry["fit_quality"] != "baixa"]
    if not comparisons:
        status = "sem_referencia"
    elif not reliable:
        status = "contorno_inconclusivo"
    else:
        # Não eleger numeração: as escalas CAD são normalizadas somente para
        # visualização, então tamanhos distintos podem produzir o mesmo fit.
        status = "padrao_experimental_sem_numero"
    return {
        "status": status,
        "units": "pixels_nao_calibrados",
        "tested_references": len(comparisons),
        "profiles": comparisons,
        "warnings": [
            "Esta é uma prévia de padrão sem determinação de numeração.",
            "Uma sobreposição normalizada por área NÃO mede tamanho real.",
            "Candidato próximo a círculo CAD não confirma que seja vazador.",
            "Não utilizar para aprovação de peças ou percentual de erro de corte.",
        ],
    }
