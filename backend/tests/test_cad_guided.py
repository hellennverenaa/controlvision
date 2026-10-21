"""Testes sintéticos para a inspeção visual guiada pelos centros CAD."""
import cv2
import numpy as np
import pytest
from app.cad_guided import analyze_predicted_regions


def scene():
    img = np.zeros((460, 620, 3), np.uint8)
    img[:] = (140, 75, 40)
    vertices = np.array([[120, 80], [500, 80], [515, 390], [100, 375]], np.int32)
    cv2.fillPoly(img, [vertices], (235, 235, 235))
    return img, vertices.astype(float).tolist()


def positions():
    return [
        {"cad_id": "V01", "position_px": [170., 180.]},
        {"cad_id": "V02", "position_px": [300., 270.]},
        {"cad_id": "V03", "position_px": [465., 225.]},
    ]


def test_tres_pontos_com_contraste_local_nao_sao_confirmados():
    img, poly = scene()
    for point in positions():
        x, y = map(int, point["position_px"])
        cv2.circle(img, (x, y), 2, (40, 40, 40), -1)
    outcome = analyze_predicted_regions(img, poly, positions())
    assert len(outcome) == 3
    assert all(item["status"] == "sinal_suspeito" for item in outcome)
    assert all(item["best_signal_levels"] > 16 for item in outcome)
    assert "confirmar" not in str(outcome).lower() or all(
        "Não confirma" in item["message"] for item in outcome
    )


def test_peca_lisa_nao_inventa_tres_furos():
    img, poly = scene()
    outcome = analyze_predicted_regions(img, poly, positions())
    assert len(outcome) == 3
    assert all(item["status"] == "inconclusivo" for item in outcome)
    assert all(item["best_signal_px"] is None for item in outcome)


def test_trama_periodica_e_ambigua_nao_furo():
    img, poly = scene()
    for y in range(246, 295, 10):
        for x in range(276, 326, 10):
            cv2.circle(img, (x, y), 2, (35, 35, 35), -1)
    outcome = analyze_predicted_regions(img, poly, [positions()[1]])[0]
    assert outcome["status"] == "textura_ambigua"
    assert outcome["optical_peaks"] > 3
    assert "Não é possível" in outcome["message"]


def test_ponto_projetado_fora_da_foto_inconclusivo():
    img, poly = scene()
    out = analyze_predicted_regions(
        img, poly, [{"cad_id": "V04", "position_px": [-11, 20]}])
    assert out[0]["status"] == "inconclusivo"
    assert out[0]["best_signal_px"] is None


def test_coordenadas_invalidas_sao_rejeitadas():
    img, poly = scene()
    with pytest.raises(ValueError):
        analyze_predicted_regions(
            img, poly, [{"cad_id": "V01", "position_px": [float("nan"), 200]}])
