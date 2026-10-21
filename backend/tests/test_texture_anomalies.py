"""A malha regular não deve virar vazadores; traços podem gerar indícios."""
import cv2
import numpy as np

from app.texture_anomalies import inspect_irregular_signal


def make_mesh(with_slit=False):
    photo = np.full((380, 520, 3), (150, 105, 60), np.uint8)
    cv2.rectangle(photo, (40, 30), (480, 350), (230, 230, 232), -1)
    for y in range(45, 345, 10):
        for x in range(55, 470, 10):
            cv2.circle(photo, (x, y), 1, (157, 157, 157), -1)
    center = [250, 190]
    if with_slit:
        # Furo alongado/traço de orientação livre, não circular.
        cv2.line(photo, (245, 188), (255, 193), (25, 25, 25), 2)
    mask = np.zeros((380, 520), np.uint8)
    cv2.rectangle(mask, (40, 30), (480, 350), 255, -1)
    return photo, mask, center


def test_textura_regular_nao_e_sinal_irregular_incomum():
    photo, mask, center = make_mesh()
    result = inspect_irregular_signal(photo, mask, center)
    assert result["status"] == "sem_destaque"
    assert result["distinct_band_count"] == 0
    assert len(result["bands"]) == 3


def test_traco_pequeno_alongado_pode_se_destacar_sem_exigir_circulo():
    photo, mask, center = make_mesh(with_slit=True)
    result = inspect_irregular_signal(photo, mask, center)
    assert result["status"] == "sinal_incomum"
    assert result["distinct_band_count"] >= 1
    assert result["best_peak_distance_px"] <= 7
    assert any(
        band["unusual_contrast"] for band in result["bands"]
        if band["kernel_px"] in (9, 15)
    )
    assert "furo_confirmado" not in str(result)


def test_pequeno_traco_rotacionado_mantem_indicio():
    photo, mask, center = make_mesh(with_slit=True)
    transform = cv2.getRotationMatrix2D(tuple(center), 87, 1)
    rotated = cv2.warpAffine(
        photo, transform, (photo.shape[1], photo.shape[0]),
        borderValue=(150, 105, 60)
    )
    result = inspect_irregular_signal(rotated, mask, center)
    assert result["status"] == "sinal_incomum"


def test_centro_fora_da_imagem_e_inconclusivo():
    photo, mask, _ = make_mesh()
    result = inspect_irregular_signal(photo, mask, [-20, 90])
    assert result["status"] == "inconclusivo"
    assert not result["bands"]


def test_centro_fora_da_peca_nao_gera_deteccao():
    photo, mask, _ = make_mesh()
    result = inspect_irregular_signal(photo, mask, [510, 45])
    assert result["status"] == "inconclusivo"
    assert result["distinct_band_count"] == 0
