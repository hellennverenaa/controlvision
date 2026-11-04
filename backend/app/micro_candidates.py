"""Busca exploratória de micropontos ópticos dentro de uma peça.

Não determina se o sinal é um vazador: fibras, tinta, sujeira e pixels
ruidosos podem produzir o mesmo comportamento. Não devolve medidas em mm.
"""
from __future__ import annotations

import cv2
import numpy as np


def find_micro_signals(image: np.ndarray, contour, piece_tone: str, excluded=()):
    """Procura sinais escuros/claros de 1-5 pixels SEM marcações humanas.

    O limiar mínimo é deliberadamente conservador e deve ser revalidado
    para cada família de material/iluminação. Retorna suspeitas, não furos.
    """
    if piece_tone not in {"light", "dark"}:
        raise ValueError("Tom da peça inválido.")
    height, width = image.shape[:2]
    polygon = np.asarray(contour, dtype=np.int32)
    if polygon.ndim != 2 or polygon.shape[1] != 2 or len(polygon) < 3:
        return []
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    fine = cv2.GaussianBlur(gray, (3, 3), .7).astype(np.float32)
    coarse = cv2.GaussianBlur(gray, (17, 17), 3.7).astype(np.float32)
    strength = coarse - fine if piece_tone == "light" else fine - coarse

    mask = np.zeros((height, width), np.uint8)
    cv2.fillPoly(mask, [polygon], 255)
    # Pequeno recuo evita a borda do objeto, que também produz alto contraste.
    safe_mask = cv2.erode(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
    values = strength[safe_mask > 0]
    if values.size < 100:
        return []
    baseline = float(np.median(values))
    deviation = float(np.median(np.abs(values - baseline)))
    threshold = max(18., baseline + 7. * max(1.4826 * deviation, 1.))
    binary = np.uint8((strength > threshold) & (safe_mask > 0))
    num, components, boxes, centers = cv2.connectedComponentsWithStats(binary, 8)
    found = []
    for number in range(1, num):
        x, y, w, h, area = (int(n) for n in boxes[number])
        if not (2 <= area <= 90 and w <= 17 and h <= 17):
            continue
        if not .55 <= w / max(h, 1) <= 1.8:
            continue
        cx, cy = centers[number]
        if any(np.hypot(cx - other["center"][0], cy - other["center"][1]) < 9
               for other in excluded):
            continue
        y1, y2 = max(0, y - 5), min(height, y + h + 5)
        x1, x2 = max(0, x - 5), min(width, x + w + 5)
        yy, xx = np.mgrid[y1:y2, x1:x2]
        radial = np.hypot(xx - cx, yy - cy)
        ring = (radial >= 5) & (radial <= 9) & (safe_mask[y1:y2, x1:x2] > 0)
        if not ring.any():
            continue
        local = strength[y1:y2, x1:x2]
        signal_peak = float(np.max(strength[components == number]))
        surround_signal = float(np.median(np.abs(local[ring])))
        if signal_peak < max(threshold, 3 * surround_signal):
            continue
        found.append({
            "center": [round(float(cx), 1), round(float(cy), 1)],
            "radius_px": round(float(np.sqrt(area / np.pi)), 1),
            "signal_levels": round(signal_peak, 1),
            "kind": "sinal_optico_nao_confirmado",
            "method": "contraste_local_automatico",
        })
    # Elimina candidatos próximos entre si e limita quantos aparecem na UI.
    chosen = []
    for item in sorted(found, key=lambda p: -p["signal_levels"]):
        if any(np.hypot(item["center"][0] - prev["center"][0],
                        item["center"][1] - prev["center"][1]) < 9 for prev in chosen):
            continue
        chosen.append({**item, "id": f"S{len(chosen) + 1:02d}"})
        if len(chosen) >= 60:
            break
    return chosen
