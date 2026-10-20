"""Sinais ópticos muito pequenos: candidatos exploratórios, nunca confirmação."""
import cv2
import numpy as np

from app.vision import analyze_image


def _scene():
    height, width = 600, 850
    image = np.zeros((height, width, 3), np.uint8)
    image[:] = (140, 80, 50)  # tecido azul em BGR
    shape = np.asarray([[170, 90], [680, 120], [710, 460], [190, 480]], np.int32)
    cv2.fillPoly(image, [shape], (233, 232, 232))
    return image


def test_pequenos_pontos_sem_circulos_grandes_sao_sinais_separados():
    image = _scene()
    expected = [(245, 195), (580, 250), (285, 350)]
    for center in expected:
        cv2.circle(image, center, 1, (155, 155, 155), -1)
    result = analyze_image(image, mode="holes", piece_tone="light")
    assert result["status"] == "preview_only"
    assert result["micro_candidate_count"] == 3
    actual = [item["center"] for item in result["micro_candidates"]]
    assert all(any(np.hypot(a[0]-x, a[1]-y) <= 3 for a in actual) for x, y in expected)
    assert all(item["kind"] == "sinal_optico_nao_confirmado" for item in result["micro_candidates"])


def test_peca_lisa_nao_inventa_micropontos():
    result = analyze_image(_scene(), mode="holes", piece_tone="light")
    assert result["micro_candidate_count"] == 0


def test_ruido_leve_nao_gera_pontos_em_massa():
    rng = np.random.default_rng(44)
    image = _scene()
    noise = rng.normal(0, 2.5, (*image.shape[:2], 1))
    image = np.clip(image.astype(float) + noise, 0, 255).astype(np.uint8)
    result = analyze_image(image, mode="holes", piece_tone="light")
    assert result["micro_candidate_count"] <= 2


def test_não_considera_pontos_no_tecido_como_vazadores():
    image = _scene()
    for xy in [(25, 35), (90, 200), (760, 280)]:
        cv2.circle(image, xy, 2, (255, 255, 255), -1)
    result = analyze_image(image, mode="holes", piece_tone="light")
    assert result["micro_candidate_count"] == 0


def test_multimodal_nao_mistura_detectores():
    image = _scene()
    cv2.circle(image, (380, 280), 10, (30, 30, 30), -1)
    result = analyze_image(image, mode="holes", piece_tone="light")
    # Um círculo grande é candidato do método tradicional, não deve
    # ser contabilizado novamente no detector de micropontos.
    assert result["candidate_count"] >= 1
    assert all(np.hypot(item["center"][0]-380, item["center"][1]-280) >= 9
               for item in result["micro_candidates"])
