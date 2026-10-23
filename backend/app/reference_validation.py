"""Validação exploratória com furos reais confirmados manualmente.

A marcação humana fornece posição aproximada e declaração de existência
física. NÃO é verdade metrológica nem identifica a numeração.
"""
from __future__ import annotations

from .annotation_comparison import compare_annotations


def validate_confirmed_holes(
    marks, confirmed_ids, circle_candidates, micro_candidates=(), radius_px=12.0
):
    """Calcula recuperação dos furos anotados, sem alegar falsos positivos.

    A comparação é 1:1 e usa exclusivamente detecções automáticas reais.
    Marcas manuais e picos exploratórios das ROIs CAD nunca contam como
    detecções automáticas. Referências não confirmadas não entram na taxa.
    """
    if not isinstance(marks, list) or not isinstance(confirmed_ids, list):
        raise ValueError("Marcações e confirmações devem ser listas.")
    if not all(isinstance(entry, str) for entry in confirmed_ids):
        raise ValueError("IDs confirmados devem ser textos.")
    mark_ids = [mark.get("id") for mark in marks]
    if len(mark_ids) != len(set(mark_ids)) or not all(
        isinstance(value, str) and value for value in mark_ids
    ):
        raise ValueError("IDs de marcações inválidos ou duplicados.")
    if len(confirmed_ids) != len(set(confirmed_ids)):
        raise ValueError("Não é permitido confirmar a mesma marcação duas vezes.")
    if not set(confirmed_ids).issubset(set(mark_ids)):
        raise ValueError("Confirmação sem marcação correspondente.")
    confirmed = [mark for mark in marks if mark["id"] in confirmed_ids]
    report = compare_annotations(
        confirmed, circle_candidates, micro_candidates, radius_px
    )
    total = report["manually_marked"]
    matched = report["nearby_associations"]
    return {
        "status": "experimental" if total else "sem_referencia_confirmada",
        "basis": "posicoes_marcadas_e_existencia_fisica_declarada_pelo_operador",
        "reference_count": total,
        "unverified_mark_count": len(marks) - total,
        "automatically_matched": matched,
        "not_detected_near_reference": total - matched,
        "reference_recovery_percent": round(matched * 100 / total, 1) if total else None,
        "unreviewed_candidate_count": report["unassociated_candidates"],
        "association_radius_px": report["association_radius_px"],
        "references": [
            {
                "mark_id": row["mark_id"],
                "status": "candidato_automatico_proximo"
                if row["associated_candidate_id"] else "sem_candidato_proximo",
                "candidate_id": row["associated_candidate_id"],
                "candidate_type": row["associated_candidate_type"],
                "distance_px": row["associated_distance_px"],
            }
            for row in report["marks"]
        ],
        "warnings": [
            "As posições e a existência física dos vazadores são declaradas pelo operador.",
            "Taxa de recuperação é SOMENTE deste conjunto anotado; não é precisão industrial.",
            "Candidatos não associados não são automaticamente falsos positivos.",
            "Não determina tamanho, erro dimensional em mm ou conformidade de produção.",
            "A referência deixa de valer para outra fotografia até ser marcada novamente.",
        ],
    }
