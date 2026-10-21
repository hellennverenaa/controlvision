"""Sinais ópticos irregulares em regiões CAD: experimento sem confirmação de furos.

Compara contraste não circular em três escalas com janelas da mesma malha.
Não soma candidatos à detecção global, não faz medições nem escolhe tamanho.
"""
from __future__ import annotations

import cv2
import numpy as np


def inspect_irregular_signal(image, body_mask, center, other_centers=()):
    """Procura pequenas descontinuidades sem exigir forma circular.

    Usa black-hat morfológico em escalas 5, 9 e 15 px, comparando o pico
    da vizinhança CAD com regiões locais de mesma dimensão. Não corrige CAD.
    """
    h, w = image.shape[:2]
    cx, cy = float(center[0]), float(center[1])
    result = {
        "status": "inconclusivo",
        "method": "morfologia_multiescala",
        "cad_center_px": [round(cx, 1), round(cy, 1)],
        "analysis_radius_px": 7,
        "bands": [],
        "distinct_band_count": 0,
        "best_peak_px": None,
        "best_peak_distance_px": None,
        "message": "Ainda não há evidência de descontinuidade distinta da trama.",
    }
    if not np.isfinite([cx, cy]).all() or not (0 <= cx < w and 0 <= cy < h):
        result["message"] = "Posição CAD fora da fotografia."
        return result
    # Arredondar um centro fracionário junto à margem pode produzir w/h;
    # evitar indexação fora da imagem nesse caso.
    ox = min(w - 1, max(0, round(cx)))
    oy = min(h - 1, max(0, round(cy)))
    pad = 116
    x0, y0 = max(0, ox - pad), max(0, oy - pad)
    x1, y1 = min(w, ox + pad + 1), min(h, oy + pad + 1)
    sub = image[y0:y1, x0:x1]
    inside = body_mask[y0:y1, x0:x1]
    if sub.size == 0 or inside[oy - y0, ox - x0] == 0:
        result["message"] = "Centro previsto fora da área segmentada como peça."
        return result
    gray = cv2.cvtColor(sub, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), .6)
    gy, gx = np.ogrid[y0:y1, x0:x1]
    area = ((gx - cx)**2 + (gy - cy)**2 <= 7**2) & (inside > 0)
    if np.count_nonzero(area) < 60:
        result["message"] = "Centro muito próximo da borda para análise segura."
        return result
    valid = cv2.erode((inside > 0).astype(np.uint8), np.ones((17, 17), np.uint8))
    xs = np.arange(max(x0 + 10, ox - 108), min(x1 - 10, ox + 109), 11)
    ys = np.arange(max(y0 + 10, oy - 108), min(y1 - 10, oy + 109), 11)
    xx, yy = np.meshgrid(xs, ys)
    radii = np.hypot(xx - cx, yy - cy)
    eligible = ((radii >= 34) & (radii <= 108) & (valid[yy - y0, xx - x0] > 0))
    for other in other_centers:
        eligible &= np.hypot(xx - float(other[0]), yy - float(other[1])) >= 25
    controls_xy = list(zip(xx[eligible].tolist(), yy[eligible].tolist()))
    if len(controls_xy) < 25:
        result["message"] = "Poucas regiões da malha disponíveis como referência."
        return result
    for scale in (5, 9, 15):
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (scale, scale))
        response = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
        response = cv2.GaussianBlur(response.astype(np.float32), (3, 3), .85)
        peak_map = np.where(area, response, -np.inf)
        i, j = np.unravel_index(int(np.argmax(peak_map)), peak_map.shape)
        target = float(peak_map[i, j])
        peak = [int(x0 + j), int(y0 + i)]
        control_max = cv2.dilate(
            response, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        )
        controls = [
            float(control_max[ry - y0, rx - x0]) for rx, ry in controls_xy
        ]
        p95 = float(np.percentile(controls, 95))
        margin = target - p95
        # Limiar EXPLORATÓRIO para destaque de contraste, jamais para
        # confirmar vazadores ou aprovar peças.
        unusual = target >= 14.0 and margin > max(7.0, p95 * .13)
        result["bands"].append({
            "kernel_px": scale,
            "roi_peak_levels": round(target, 1),
            "texture_p95_levels": round(p95, 1),
            "margin_levels": round(margin, 1),
            "reference_count": len(controls),
            "peak_px": peak,
            "peak_distance_px": round(
                float(np.hypot(peak[0] - cx, peak[1] - cy)), 1
            ),
            "unusual_contrast": bool(unusual),
        })
    distinct = [band for band in result["bands"] if band["unusual_contrast"]]
    result["distinct_band_count"] = len(distinct)
    strongest = max(result["bands"], key=lambda band: band["margin_levels"])
    result["best_peak_px"] = strongest["peak_px"]
    result["best_peak_distance_px"] = strongest["peak_distance_px"]
    if distinct:
        result["status"] = "sinal_incomum"
        result["message"] = (
            "Contraste incomum em uma ou mais escalas; pode ser trama, "
            "fibra, sombra ou vazador, sem confirmação física."
        )
    else:
        result["status"] = "sem_destaque"
        result["message"] = (
            "Não houve contraste multiescala suficientemente distinto "
            "da trama; não confirma ausência de furo."
        )
    return result
