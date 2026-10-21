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


def test_foto_real_21_outubro_duas_marcas_proximas_mas_semterceira():
    """Regressão das coordenadas reportadas na validação experimental.

    As coordenadas são recortes do relatório do operador, não fotos no
    repositório. Não é medida metrológica nem confirmação de vazadores.
    """
    marks = [
        {"id": "M01", "x": 823.7, "y": 595.1},
        {"id": "M02", "x": 800.6, "y": 708.4},
        {"id": "M03", "x": 241.9, "y": 641.2},
    ]
    candidates = [
        ("I15", 374, 507.5), ("I14", 259.5, 513.5),
        ("I13", 180.5, 569.5), ("I12", 316.5, 574),
        ("I11", 275.5, 577.5), ("I10", 309, 578.5),
        ("I09", 326.5, 588.5), ("I08", 824.5, 592.5),
        ("I07", 286.5, 602.5), ("I06", 304.5, 612.5),
        ("I05", 353.5, 613.5), ("I04", 241.8, 638.5),
        ("I03", 349.5, 646.5), ("I02", 342, 651.5),
        ("I01", 310, 660.5),
    ]
    circles = [{"id": id, "center": [x, y]} for id, x, y in candidates]
    result = compare_annotations(marks, circles)
    assert result["nearby_associations"] == 2
    assert result["without_nearby_candidate"] == 1
    assert result["unassociated_candidates"] == 13
    assert result["marks"][0]["associated_candidate_id"] == "I08"
    assert result["marks"][0]["associated_distance_px"] == 2.7
    assert result["marks"][1]["associated_candidate_id"] is None
    assert result["marks"][1]["nearest_distance_px"] == 118.3
    assert result["marks"][2]["associated_candidate_id"] == "I04"
    assert result["marks"][2]["associated_distance_px"] == 2.7
