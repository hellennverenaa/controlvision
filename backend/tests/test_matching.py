"""Testes sintéticos de associação visual, SEM validação dimensional."""
import math
import pytest

from app.matching import match_visual


CAD = [[0, 0], [110, 0], [122, 10], [133, 40],
       [91, 67], [64, 76], [20, 70], [-5, 35]]
HOLES = [[18, 17], [66, 14], [105, 26],
         [95, 51], [55, 54], [24, 49]]
FEATURES = [
    {"id": f"V{i+1}", "center": point, "classification": "vazador"}
    for i, point in enumerate(HOLES)
]


def camera_projection(point, degrees):
    angle = math.radians(degrees)
    x, y = point[0], -point[1]
    return [3.4 * (math.cos(angle) * x - math.sin(angle) * y) + 300,
            3.4 * (math.sin(angle) * x + math.cos(angle) * y) + 250]


@pytest.mark.parametrize("angle", [0, 47, 90, 179, 257, 320])
def test_identifica_seis_pontos_em_diversas_orientacoes(angle):
    image_contour = [camera_projection(p, angle) for p in CAD]
    candidates = [{"id": f"I{i+1}", "center": camera_projection(p, angle)}
                  for i, p in enumerate(HOLES)]
    result = match_visual(CAD, image_contour, FEATURES, candidates)
    assert result["fit_quality"] == "preliminar"
    assert len(result["matched"]) == 6
    assert result["unmatched_cad"] == []
    assert result["unmatched_image"] == []
    assert result["units"] == "pixels_nao_calibrados"
    assert "mm" not in result


def test_ponto_ausente_e_extra_ficam_separados():
    angle = 83
    image_contour = [camera_projection(p, angle) for p in CAD]
    candidates = [{"id": f"I{i+1}", "center": camera_projection(p, angle)}
                  for i, p in enumerate(HOLES[:-1])]
    candidates.append({"id": "I99", "center": [999, 888]})
    result = match_visual(CAD, image_contour, FEATURES, candidates)
    assert len(result["matched"]) == 5
    assert [v["cad_id"] for v in result["unmatched_cad"]] == ["V6"]
    assert [v["image_id"] for v in result["unmatched_image"]] == ["I99"]


def test_sem_candidatos_na_imagem():
    image_contour = [camera_projection(p, 45) for p in CAD]
    result = match_visual(CAD, image_contour, FEATURES, [])
    assert len(result["matched"]) == 0
    assert len(result["unmatched_cad"]) == 6
    assert not result["unmatched_image"]


def test_contornos_invalidos_nao_passam():
    with pytest.raises(ValueError):
        match_visual([[0, 0]], CAD, [], [])
