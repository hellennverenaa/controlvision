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
    assert all(item["max_local_signal_levels"] is not None for item in outcome)
    assert all(item["threshold_levels"] is not None for item in outcome)
    assert all(item["noise_sigma_levels"] is not None for item in outcome)
    assert all(item["max_local_signal_levels"] < item["threshold_levels"] for item in outcome)


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


def test_registro_dos_limiares_mesmo_sem_picos():
    img, poly = scene()
    output = analyze_predicted_regions(img, poly, positions())
    assert len(output) == 3
    for point in output:
        assert point["status"] == "inconclusivo"
        assert point["max_local_signal_levels"] is not None
        assert point["threshold_levels"] > point["max_local_signal_levels"]
        assert "limiar" in point["message"].lower()


def test_pico_bruto_nao_confirma_furo_e_registra_distancia():
    img, poly = scene()
    # Sinal local de contraste claro, no lugar previsto pelo CAD.
    center = positions()[1]["position_px"]
    cv2.circle(img, tuple(map(int, center)), 2, (70, 70, 70), -1)
    result = analyze_predicted_regions(img, poly, [positions()[1]])[0]
    assert result["raw_peak_px"] is not None
    assert result["raw_peak_distance_px"] <= 3
    assert result["contrast_margin_levels"] is not None
    assert result["signal_at_cad_center_levels"] is not None
    assert result["status"] in ("sinal_suspeito", "inconclusivo")
    assert "furo_confirmado" not in str(result)


def test_pico_bruto_em_regiao_lisa_nao_cria_vazadores():
    img, poly = scene()
    result = analyze_predicted_regions(img, poly, [positions()[1]])[0]
    assert result["status"] == "inconclusivo"
    assert result["raw_peak_px"] is not None
    assert result["contrast_margin_levels"] < 0
    assert result["best_signal_px"] is None
    assert result["optical_peaks"] == 0



def test_compara_sinal_isolado_com_controles_da_mesma_peca():
    img, poly = scene()
    # Tecido uniforme mais um sinal escuro excepcional na posição CAD.
    cv2.circle(img, (300, 270), 2, (30, 30, 30), -1)
    out = analyze_predicted_regions(img, poly, [positions()[1]])[0]
    assert out["texture_reference_window_count"] >= 30
    assert out["texture_target_peak_levels"] > out["texture_reference_p90_levels"]
    assert out["texture_peak_excess_p90_levels"] > 10
    assert out["texture_distinctiveness"] == "contraste_incomum_na_regiao"
    assert out["status"] in ("sinal_suspeito", "inconclusivo")


def test_peca_lisa_nao_classifica_percentil_100_como_furo():
    img, poly = scene()
    out = analyze_predicted_regions(img, poly, [positions()[1]])[0]
    assert out["texture_reference_window_count"] >= 30
    assert out["texture_peak_percentile"] == 100
    assert out["texture_distinctiveness"] == "sem_destaque_frente_a_trama"
    assert out["optical_peaks"] == 0


def test_trama_regular_nao_e_automaticamente_vazador():
    img, poly = scene()
    for y in range(105, 367, 12):
        for x in range(140, 487, 12):
            cv2.circle(img, (x, y), 2, (90, 90, 90), -1)
    out = analyze_predicted_regions(img, poly, [positions()[1]])[0]
    assert out["texture_reference_window_count"] >= 30
    assert out["texture_distinctiveness"] == "sem_destaque_frente_a_trama"
    assert out["status"] != "furo_confirmado"


def test_guiado_cad_inclui_diagnostico_sem_alterar_contagem_de_picos():
    img, poly = scene()
    center = positions()[1]["position_px"]
    cv2.line(img, (294, 268), (305, 271), (30, 30, 30), 2)
    out = analyze_predicted_regions(img, poly, positions())
    assert len(out) == 3
    for item in out:
        investigation = item["irregular_texture"]
        assert investigation["method"] == "morfologia_multiescala"
        assert investigation["status"] in ("sem_destaque", "sinal_incomum", "inconclusivo")
        assert "furo_confirmado" not in str(investigation)
        assert "candidate_count" not in investigation
    assert out[1]["irregular_texture"]["status"] == "sinal_incomum"
