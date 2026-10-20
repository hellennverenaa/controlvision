"""Segmentação preliminar de contornos e pontos internos em imagens.

Resultados apenas em pixels. Contornos escuros desenhados NÃO equivalem a furos.
Nenhuma medição dimensional, alinhamento ou decisão de qualidade aqui.
"""
from __future__ import annotations

import cv2
import numpy as np

from .micro_candidates import find_micro_signals


def _center(contour):
    moments = cv2.moments(contour)
    if moments["m00"]:
        return moments["m10"] / moments["m00"], moments["m01"] / moments["m00"]
    (x, y), _ = cv2.minEnclosingCircle(contour)
    return x, y


def _circular_candidates(contours, outer, outer_area, mode, parents=None, outer_index=None):
    """Contornos circulares pequenos dentro da silhueta principal."""
    found = []
    for idx, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        # Evita objetos enormes (região interna do desenho) e ruído subpixel.
        if area < 12 or area > outer_area * .025:
            continue
        if parents is not None and parents[idx] != outer_index:
            continue
        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter else 0
        if circularity < .62:
            continue
        (cx, cy), radius = cv2.minEnclosingCircle(contour)
        if radius < 2.3:
            continue
        x, y, w, h = cv2.boundingRect(contour)
        if not h or not .60 <= w / h <= 1.65:
            continue
        # Somente interior; excluir irregularidades da borda externa.
        margin = max(2, min(7, int(radius * .5)))
        if cv2.pointPolygonTest(outer, (float(cx), float(cy)), True) <= margin:
            continue
        found.append({
            "id": f"I{len(found)+1:02d}",
            "center": [round(cx, 1), round(cy, 1)],
            "radius_px": round(radius, 1),
            "circularity": round(float(circularity), 2),
            "area_px2": round(area, 1),
            "kind": "marca_escura" if mode == "marks" else "abertura_clara",
        })
    return sorted(found, key=lambda item: (item["center"][1], item["center"][0]))[:100]




def _light_piece_mask(image: np.ndarray) -> np.ndarray:
    """Máscara para peça clara sobre fundo colorido/mais escuro.

    Heurística de protótipo, não segmentador universal. Uma superfície
    de cor parecida com a peça pode impedir a identificação.
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, (0, 0, 135), (179, 90, 255))


def _invalid_capture(width, height, regions, reason):
    return {
        "status": "capture_invalid", "mode": "holes", "units": "pixels",
        "contour": [], "contour_area_px2": 0,
        "image_size": [width, height], "detected_regions": regions,
        "candidates": [], "candidate_count": 0,
        "warnings": [
            reason,
            "Nenhum vazador nem diferença dimensional foi medido.",
            "Tente mudar o fundo, a iluminação ou o tom da peça.",
        ],
    }

def analyze_image(image: np.ndarray, mode: str = "marks", piece_tone: str = "dark") -> dict:
    """Localiza silhueta e possíveis círculos; não relaciona posição ao CAD."""
    if mode not in {"marks", "holes"}:
        raise ValueError("Modo de detecção inválido.")
    if piece_tone not in {"dark", "light"}:
        raise ValueError("Tom da peça inválido (dark/light).")
    if image is None or image.ndim != 3:
        raise ValueError("Imagem inválida.")
    height, width = image.shape[:2]
    if width * height > 20_000_000:
        raise ValueError("Imagem muito grande: limite de 20 megapixels.")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    smooth = cv2.GaussianBlur(gray, (3, 3), 0)
    polarity = cv2.THRESH_BINARY if mode == "holes" and piece_tone == "light" else cv2.THRESH_BINARY_INV
    _, mask = cv2.threshold(smooth, 0, 255, polarity + cv2.THRESH_OTSU)
    if mode == "holes" and piece_tone == "light":
        # Usa cromaticidade: mais robusto para material claro sobre tecido azul.
        # Não conclui nada sobre furos se a silhueta não for isolada.
        mask = _light_piece_mask(image)
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        if mode == "holes":
            return _invalid_capture(width, height, 0, "Captura inconclusiva: nenhuma silhueta isolada.")
        raise ValueError("Nenhum contorno encontrado: revise luz e fundo.")
    if mode == "holes" and piece_tone == "light":
        # Rejeitar componentes encostados nas bordas, como a mesa e faixas claras.
        valid_ids = []
        for index, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)
            if hierarchy is not None and hierarchy[0, index, 3] != -1:
                continue
            if x <= 2 or y <= 2 or x + w >= width - 2 or y + h >= height - 2:
                continue
            if .025 * width * height <= area <= .80 * width * height:
                valid_ids.append(index)
        if not valid_ids:
            return _invalid_capture(width, height, len(contours),
                "Captura inconclusiva: não foi possível distinguir a peça clara do fundo.")
        outer_id = max(valid_ids, key=lambda index: cv2.contourArea(contours[index]))
    else:
        outer_id = max(range(len(contours)), key=lambda n: cv2.contourArea(contours[n]))
    outer = contours[outer_id]
    area = cv2.contourArea(outer)
    if area < 50:
        raise ValueError("Contorno pequeno demais.")
    polygon = cv2.approxPolyDP(outer, 1.5, True).reshape(-1, 2).tolist()
    # Na prática, fundo e mesa podem gerar um contorno muito maior que a peça.
    # Não reportar pontos externos ao objeto como "furos" quando isto ocorrer.
    x, y, w, h = cv2.boundingRect(outer)
    touches_border = x <= 2 or y <= 2 or x + w >= width - 2 or y + h >= height - 2
    suspicious_size = area < width * height * .025 or area > width * height * .80
    if mode == "holes" and (touches_border or suspicious_size):
        return {
            "status": "capture_invalid",
            "mode": mode, "units": "pixels",
            "contour": [],
            "contour_area_px2": round(area, 2),
            "image_size": [width, height],
            "detected_regions": len(contours),
            "candidates": [], "candidate_count": 0,
            "warnings": [
                "Captura inconclusiva: a segmentação parece incluir o fundo ou não isola a peça.",
                "Tente apoiar a peça em superfície de maior contraste ou mudar o tom selecionado.",
                "Não foi realizada associação ao CAD nem inspeção dimensional.",
            ],
        }
    if mode == "holes":
        # Um furo claro dentro de material escuro cria um contorno filho
        # diretamente ligado à região escura principal.
        parent_ids = hierarchy[0, :, 3].tolist() if hierarchy is not None else []
        candidates = _circular_candidates(contours, outer, area, mode, parent_ids, outer_id)
        advice = ("Aberturas internas são candidatas, não furos validados. "
                  "Furinhos menores que poucos pixels podem não ser detectados; "
                  "zero candidatos NÃO significa zero vazadores.")
    else:
        # Marcas de caneta são componentes escuros, NÃO vazadores físicos.
        candidates = _circular_candidates(contours, outer, area, mode)
        advice = ("Marcas escuras circulares são apenas pontos desenhados, "
                  "não furos ou vazadores físicos. Rabiscos e texturas podem atrapalhar.")
    # Segunda estratégia exclusiva para furos minúsculos em material claro:
    # procura variações de contraste de poucos pixels sem exigir círculos fechados.
    # São sinais suspeitos, separados dos candidatos circulares clássicos.
    micro_candidates = (
        find_micro_signals(image, polygon, piece_tone, excluded=candidates)
        if mode == "holes" and piece_tone == "light" else []
    )
    # Qualidade de triagem: muitos sinais em uma só peça sugerem textura,
    # iluminação ou limiar mal ajustado. Não descartar os sinais brutos, mas
    # não oferecer a contagem como evidência de vazadores identificados.
    micro_density = (
        len(micro_candidates) * 10_000 / area if area > 0 else 0.
    )
    excessive_micro = (
        len(micro_candidates) >= 12 and micro_density >= 2.0
    )
    micro_signal_quality = (
        "excesso_de_textura" if excessive_micro else "exploratorio"
    )
    return {
        "status": "preview_only",
        "mode": mode,
        "units": "pixels",
        "contour": polygon,
        "contour_area_px2": round(area, 2),
        "image_size": [width, height],
        "detected_regions": len(contours),
        "candidates": candidates,
        "candidate_count": len(candidates),
        "micro_candidates": micro_candidates,
        "micro_candidate_count": len(micro_candidates),
        "micro_signal_quality": micro_signal_quality,
        "micro_signals_per_10000_px2": round(micro_density, 2),
        "warnings": [
            advice,
            "Excesso de micropontos: provável influência da textura/iluminação; a contagem não é confiável."
            if excessive_micro else
            "Micropontos são sinais ópticos suspeitos, não vazadores confirmados.",
            "Nenhuma associação espacial com o CAD foi realizada.",
            "Sem calibração, tolerâncias ou resultado dimensional.",
        ],
    }
