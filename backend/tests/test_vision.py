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


def test_peca_clara_com_furos_escuros_em_fundo_escuro():
    image = np.full((400, 470, 3), 40, dtype=np.uint8)
    cv2.rectangle(image, (85, 55), (365, 340), (235, 235, 235), -1)
    for center in [(140, 110), (225, 190), (312, 275)]:
        cv2.circle(image, center, 12, (40, 40, 40), -1)
    result = analyze_image(image, mode="holes", piece_tone="light")
    assert result["status"] == "preview_only"
    assert result["candidate_count"] == 3
    assert all(p["kind"] == "abertura_clara" for p in result["candidates"])


def test_fundo_confundido_com_peca_bloqueia_vazadores():
    # Escuro em quase toda a imagem = fundo selecionado, não peça isolada.
    image = np.full((360, 460, 3), 24, dtype=np.uint8)
    for p in [(105, 110), (230, 230), (345, 195)]:
        cv2.circle(image, p, 8, (250, 250, 250), -1)
    result = analyze_image(image, mode="holes", piece_tone="dark")
    assert result["status"] == "capture_invalid"
    assert result["candidate_count"] == 0
    assert result["contour"] == []
    assert "inconclusiva" in result["warnings"][0].lower()


def test_tom_invalido():
    with pytest.raises(ValueError):
        analyze_image(np.zeros((100, 100, 3), dtype=np.uint8), mode="holes", piece_tone="alien")


def test_peca_clara_em_fundo_azul_segmenta_silhueta_sem_inventar_furos():
    # Cores geradas sinteticamente: branco com contraste de cromaticidade azul.
    image = np.zeros((335, 447, 3), dtype=np.uint8)
    image[:] = [128, 88, 65]  # fundo azul em BGR
    poly = np.array([[126, 90], [166, 65], [305, 56], [354, 81],
                     [351, 173], [357, 211], [316, 231], [259, 220],
                     [139, 178], [125, 154]], dtype=np.int32)
    cv2.fillPoly(image, [poly], (200, 205, 211))
    result = analyze_image(image, mode="holes", piece_tone="light")
    assert result["status"] == "preview_only"
    assert len(result["contour"]) >= 3
    assert result["candidate_count"] == 0
    assert "NÃO" in result["warnings"][0] or "zero" in result["warnings"][0]


def test_claro_no_fundo_claro_nao_compara():
    image = np.full((340, 440, 3), 245, dtype=np.uint8)
    result = analyze_image(image, mode="holes", piece_tone="light")
    assert result["status"] == "capture_invalid"
    assert result["contour"] == []


def test_peca_clara_aninhada_em_tecido_azul_e_borda_branca():
    """Caso das fotos reais reduzidas: piso claro conectado às bordas,
    tecido azul isolando a peça clara como contorno interno."""
    image = np.full((300, 525, 3), (243, 243, 243), dtype=np.uint8)
    cv2.rectangle(image, (25, 0), (495, 299), (140, 85, 55), -1)
    piece = np.asarray([
        (140, 75), (220, 40), (334, 66), (360, 145),
        (332, 207), (208, 205), (125, 165)
    ], np.int32)
    cv2.fillPoly(image, [piece], (229, 230, 232))
    result = analyze_image(image, mode="holes", piece_tone="light")
    assert result["status"] == "preview_only"
    assert 18000 <= result["contour_area_px2"] <= 40000
    assert result["candidate_count"] == 0
    assert result["micro_candidate_count"] == 0
    assert any("Fotografia reduzida" in warning for warning in result["warnings"])


def test_cor_branca_fora_da_peca_nao_deve_ser_contorno_principal():
    """Outra orientação: a peça branca interna deve prevalecer sobre a
    mesa branca que aparece nas margens da imagem."""
    image = np.full((300, 525, 3), (245, 245, 245), dtype=np.uint8)
    cv2.rectangle(image, (20, 2), (499, 299), (135, 82, 50), -1)
    cv2.rectangle(image, (171, 39), (350, 256), (231, 229, 233), -1)
    result = analyze_image(image, mode="holes", piece_tone="light")
    assert result["status"] == "preview_only"
    assert 35000 <= result["contour_area_px2"] <= 41000
    box = cv2.boundingRect(np.asarray(result["contour"], dtype=np.int32))
    assert abs(box[0] - 171) < 5
    assert abs(box[1] - 39) < 5
