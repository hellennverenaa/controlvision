"""Segmentação preliminar de contornos e pontos internos em imagens.

Resultados apenas em pixels. Contornos escuros desenhados NÃO equivalem a furos.
Nenhuma medição dimensional, alinhamento ou decisão de qualidade aqui.
"""
from __future__ import annotations

import cv2
import numpy as np


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


def analyze_image(image: np.ndarray, mode: str = "marks") -> dict:
    """Localiza silhueta e possíveis círculos; não relaciona posição ao CAD."""
    if mode not in {"marks", "holes"}:
        raise ValueError("Modo de detecção inválido.")
    if image is None or image.ndim != 3:
        raise ValueError("Imagem inválida.")
    height, width = image.shape[:2]
    if width * height > 20_000_000:
        raise ValueError("Imagem muito grande: limite de 20 megapixels.")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    smooth = cv2.GaussianBlur(gray, (3, 3), 0)
    _, black = cv2.threshold(smooth, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, hierarchy = cv2.findContours(black, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("Nenhum contorno encontrado: revise luz e fundo.")
    outer_id = max(range(len(contours)), key=lambda n: cv2.contourArea(contours[n]))
    outer = contours[outer_id]
    area = cv2.contourArea(outer)
    if area < 50:
        raise ValueError("Contorno pequeno demais.")
    polygon = cv2.approxPolyDP(outer, 1.5, True).reshape(-1, 2).tolist()
    if mode == "holes":
        # Um furo claro dentro de material escuro cria um contorno filho
        # diretamente ligado à região escura principal.
        parent_ids = hierarchy[0, :, 3].tolist() if hierarchy is not None else []
        candidates = _circular_candidates(contours, outer, area, mode, parent_ids, outer_id)
        advice = ("Aberturas claras internas são candidatas. Só funciona bem se o "
                  "material contrastar com o fundo/iluminação; confirme cada ponto.")
    else:
        # Marcas de caneta são componentes escuros, NÃO vazadores físicos.
        candidates = _circular_candidates(contours, outer, area, mode)
        advice = ("Marcas escuras circulares são apenas pontos desenhados, "
                  "não furos ou vazadores físicos. Rabiscos e texturas podem atrapalhar.")
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
        "warnings": [
            advice,
            "Nenhuma associação espacial com o CAD foi realizada.",
            "Sem calibração, tolerâncias ou resultado dimensional.",
        ],
    }
