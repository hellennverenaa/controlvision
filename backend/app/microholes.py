"""Inspeção LOCAL assistida por marcações humanas: não detecta vazadores sozinha.

Usar para diagnosticar por que furinhos minúsculos não aparecem na segmentação
global. Contraste no pixel não comprova existência de corte passante.
"""
from __future__ import annotations

import cv2
import numpy as np


def inspect_marked_regions(image, outline, marks):
    """Analisa contraste de pequenos pontos ASSINALADOS, sem considerar como furos.

    Coordenadas estão em pixels na imagem original. Não usa referência CAD,
    escala, tolerâncias nem contagem automatizada de furos.
    """
    if image is None or image.ndim != 3:
        raise ValueError("Imagem inválida.")
    if not isinstance(marks, list) or not 1 <= len(marks) <= 60:
        raise ValueError("Envie entre 1 e 60 marcações.")
    contour = np.asarray(outline, dtype=np.float32)
    if contour.ndim != 2 or contour.shape[1] != 2 or len(contour) < 3:
        raise ValueError("Contorno da peça não encontrado.")
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    results = []
    # Raio proporcional à resolução; não "aumenta" o detalhe da câmera.
    ring_radius = max(7, min(21, round(min(w, h) * .014)))
    center_radius = max(1, min(4, round(min(w, h) * .0025)))
    for i, mark in enumerate(marks, 1):
        if not isinstance(mark, dict) or not isinstance(mark.get("x"), (int, float)) or not isinstance(mark.get("y"), (int, float)):
            raise ValueError("Marcação inválida.")
        x, y = float(mark["x"]), float(mark["y"])
        if not np.isfinite([x, y]).all() or not (0 <= x < w and 0 <= y < h):
            raise ValueError("Marcação fora da fotografia.")
        edge_distance = float(cv2.pointPolygonTest(contour, (x, y), True))
        item = {
            "id": str(mark.get("id", f"M{i:02d}"))[:24],
            "position_px": [round(x, 1), round(y, 1)],
            "edge_distance_px": round(edge_distance, 1),
            "status": "inconclusivo",
            "gray_contrast": None,
            "saturation_contrast": None,
            "evidence": "Sem evidência óptica suficiente para confirmar um furo.",
        }
        if edge_distance < 0:
            item["evidence"] = "Marcação fora da silhueta detectada; confira o contorno e o clique."
            results.append(item)
            continue

        xmin, xmax = max(0, int(x) - ring_radius), min(w, int(x) + ring_radius + 1)
        ymin, ymax = max(0, int(y) - ring_radius), min(h, int(y) + ring_radius + 1)
        yy, xx = np.mgrid[ymin:ymax, xmin:xmax]
        radial = np.hypot(xx - x, yy - y)
        # Somente pixels do interior da silhueta da peça, inclusive perto das bordas.
        mask = np.zeros((ymax-ymin, xmax-xmin), np.uint8)
        translated = np.rint(contour - [xmin, ymin]).astype(np.int32)
        cv2.fillPoly(mask, [translated], 1)
        center_pixels = (radial <= center_radius) & (mask > 0)
        ring_pixels = (radial >= max(center_radius + 2, ring_radius * .55)) & (radial <= ring_radius) & (mask > 0)
        if center_pixels.sum() < 1 or ring_pixels.sum() < 12:
            item["evidence"] = "Poucos pixels utilizáveis; margem da peça ou enquadramento prejudica a leitura."
            results.append(item)
            continue
        roi_gray, roi_sat = gray[ymin:ymax, xmin:xmax], hsv[ymin:ymax, xmin:xmax, 1]
        center_gray = float(np.median(roi_gray[center_pixels]))
        surround_gray = float(np.median(roi_gray[ring_pixels]))
        gray_contrast = surround_gray - center_gray
        center_sat = float(np.median(roi_sat[center_pixels]))
        surround_sat = float(np.median(roi_sat[ring_pixels]))
        sat_contrast = center_sat - surround_sat
        bg_mad = float(np.median(np.abs(roi_gray[ring_pixels].astype(float) - surround_gray)))
        item["gray_contrast"] = round(gray_contrast, 1)
        item["saturation_contrast"] = round(sat_contrast, 1)

        # A imagem pode mostrar pigmento, sombra, vazador ou artefato do sensor.
        # Não interpretamos a natureza física, apenas reportamos contraste.
        clear_signal = gray_contrast > max(24, 4 * bg_mad) or sat_contrast > max(55, 5 * bg_mad)
        if clear_signal and edge_distance >= center_radius + 1:
            item["status"] = "contraste_local"
            item["evidence"] = (
                "Existe contraste localizado perto da marcação; pode ser furo, sombra, "
                "textura ou pigmento. A existência de vazador NÃO foi confirmada."
            )
        elif clear_signal:
            item["evidence"] = (
                "Há contraste, mas o ponto está muito próximo da borda para "
                "distinguir com segurança o furo da silhueta."
            )
        elif edge_distance < ring_radius * .4:
            item["evidence"] = "Muito próximo à borda e com contraste fraco; captura inconclusiva."
        else:
            item["evidence"] = "Não há contraste local suficiente nesta resolução; NÃO significa furo ausente."
        results.append(item)
    return {
        "status": "manual_guided_preview",
        "units": "pixels_nao_calibrados",
        "results": results,
        "warnings": [
            "Marcações foram inseridas por uma pessoa, não detectadas automaticamente.",
            "Contraste local não demonstra que há um furo passante.",
            "Sem correspondência CAD, escala métrica ou aprovação de qualidade.",
        ],
    }
