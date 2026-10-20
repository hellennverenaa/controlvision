"""Proximidade de anotações humanas não equivale a confirmação de furos."""
import pytest

from app.annotation_comparison import compare_annotations


def test_um_dos_tres_com_vinte_e_tres_candidatos():
    marks = [
        {"id": "M01", "x": 802.6, "y": 600.3},
        {"id": "M02", "x": 794.9, "y": 725.1},
        {"id": "M03", "x": 184.3, "y": 640.6},
    ]
    auto = [{"id": f"I{i}", "center": [250+i, 550+i]} for i in range(1, 23)]
    auto.append({"id": "I23", "center": [184.6, 639.6]})
    result = compare_annotations(marks, auto)
    assert result["manually_marked"] == 3
    assert result["nearby_associations"] == 1
    assert result["without_nearby_candidate"] == 2
    assert result["unassociated_candidates"] == 22
    assert result["marks"][2]["associated_candidate_id"] == "I23"
    assert result["marks"][2]["associated_distance_px"] == 1.0
    assert result["status"] == "diagnostico_nao_metrologico"


def test_uma_suspeita_nao_pode_ser_duplicada_em_dois_cliques():
    marks = [{"id": "M01", "x": 50, "y": 50}, {"id": "M02", "x": 53, "y": 51}]
    candidates = [{"id": "S01", "center": [51, 51]}]
    result = compare_annotations(marks, [], candidates)
    assert result["nearby_associations"] == 1
    assert result["unassociated_candidates"] == 0


def test_sem_candidatos_reporta_distancia_indisponivel():
    res = compare_annotations([{"id": "M01", "x": 10, "y": 15}], [])
    assert res["nearby_associations"] == 0
    assert res["marks"][0]["nearest_distance_px"] is None


def test_raio_nao_e_tolerancia_aceita_valores_finitos():
    with pytest.raises(ValueError):
        compare_annotations([], [], radius_px=float("inf"))
    with pytest.raises(ValueError):
        compare_annotations([{"id": "M01", "x": float("nan"), "y": 4}], [])
