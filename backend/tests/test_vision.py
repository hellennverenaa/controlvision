"""Testes sintéticos: detectar candidatos não equivale a medir vazadores."""
import cv2
import numpy as np
import pytest

from app.vision import analyze_image


def test_circulos_desenhados_aparecem_como_marcas_nao_vazadores():
    image = np.full((400, 450, 3), 245, dtype=np.uint8)
    cv2.rectangle(image, (100, 70), (320, 340), (10, 10, 10), 4)
    for point in [(160, 130), (230, 130), (160, 210), (230, 210), (160, 290), (230, 290)]:
        cv2.circle(image, point, 7, (0, 0, 0), -1)
    result = analyze_image(image, mode="marks")
    assert result["status"] == "preview_only"
    assert result["units"] == "pixels"
    assert result["candidate_count"] == 6
    assert all(p["kind"] == "marca_escura" for p in result["candidates"])
    assert "não furos" in result["warnings"][0]


def test_aberturas_claras_dentro_de_peca_escura():
    image = np.full((390, 450, 3), 250, dtype=np.uint8)
    cv2.rectangle(image, (80, 50), (360, 340), (25, 25, 25), -1)
    for center in [(125, 105), (210, 105), (295, 105), (125, 260), (210, 260), (295, 260)]:
        cv2.circle(image, center, 11, (250, 250, 250), -1)
    result = analyze_image(image, mode="holes")
    assert result["candidate_count"] == 6
    assert all(p["kind"] == "abertura_clara" for p in result["candidates"])


def test_sem_marcacoes_nao_inventa_vazadores():
    image = np.full((300, 300, 3), 255, dtype=np.uint8)
    cv2.rectangle(image, (60, 70), (250, 230), (0, 0, 0), -1)
    result = analyze_image(image, mode="holes")
    assert result["candidate_count"] == 0


def test_modo_invalido_e_bloqueado():
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    with pytest.raises(ValueError):
        analyze_image(image, mode="cad_match")
