"""Família com numeração desconhecida: a comparação não pode adivinhar tamanho."""
import math
import pytest
from app.family_matching import compare_size_family

OUTLINE = [[0,0],[110,0],[122,10],[133,40],[91,67],[64,76],[20,70],[-5,35]]
POINTS = [[18,17],[66,14],[105,26]]


def make_piece(size, factor):
    return {
        "id": f"P{size}",
        "size": str(size),
        "name": str(size),
        "points": [[x * factor, y * factor] for x,y in OUTLINE],
        "features": [
            {"id": f"V{index}", "shape":"circular",
             "center":[x * factor,y * factor], "classification":"pendente"}
            for index,(x,y) in enumerate(POINTS)
        ],
    }


def photo_point(point):
    x,y=point
    angle=math.radians(37)
    x,y=x,-y
    return [4*(x*math.cos(angle)-y*math.sin(angle))+250,
            4*(x*math.sin(angle)+y*math.cos(angle))+270]


def test_all_sizes_are_considered_without_claiming_size():
    family=[make_piece(n, 1+0.03*(n-17)) for n in range(17,26)]
    contour=[photo_point(p) for p in OUTLINE]
    candidates=[{"id":f"I{i}","center":photo_point(p)} for i,p in enumerate(POINTS)]
    result=compare_size_family(family,contour,candidates)
    assert result["tested_references"] == 9
    assert result["status"] == "padrao_experimental_sem_numero"
    assert set(item["size"] for item in result["profiles"]) == set(map(str,range(17,26)))
    assert all(item["cad_circle_count"] == 3 for item in result["profiles"])
    assert all(item["nearby_candidates"] == 3 for item in result["profiles"])
    assert all(item["visual_shape_difference_percent"] is not None for item in result["profiles"])
    assert all(0 <= item["visual_shape_difference_percent"] <= 100 for item in result["profiles"])
    # Cada referência exibe também a silhueta CAD projetada, para o
    # operador julgar o alinhamento ANTES de interpretar os furos.
    assert all(len(item["projected_contour"]) == len(OUTLINE) for item in result["profiles"])
    assert all(len(pt) == 2 for item in result["profiles"] for pt in item["projected_contour"])
    assert "selected_size" not in result
    assert "mm" not in result


def test_no_circles_is_not_treated_as_approved():
    family=[make_piece(17,1)]
    result=compare_size_family(family,[photo_point(p) for p in OUTLINE],[])
    assert result["profiles"][0]["nearby_candidates"] == 0


def test_family_size_limit_blocks_large_payloads():
    family=[make_piece(n,1) for n in range(20)]
    with pytest.raises(ValueError):
        compare_size_family(family, [photo_point(p) for p in OUTLINE], [])


def test_low_fit_does_not_claim_valid_size():
    family=[make_piece(17,1)]
    contour=[[0,0],[900,0],[900,14],[0,14]]
    result=compare_size_family(family,contour,[])
    assert result["status"] == "contorno_inconclusivo"
