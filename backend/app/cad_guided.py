"""Diagnóstico óptico em regiões sugeridas por uma sobreposição CAD ilustrativa.

NÃO é detector validado de vazadores. Uma região pode conter fibras, pigmento
ou sombra e nem todo furo verdadeiro coincide com o CAD projetado. Preserva
também a detecção global para inspecionar sinais deslocados e extras.
"""
from __future__ import annotations

import cv2
import numpy as np

from .texture_anomalies import inspect_irregular_signal


def analyze_predicted_regions(image, photo_contour, centers, piece_tone="light"):
    """Analisa sinais em ROIs dos centros CAD projetados, sem alterar o alinhamento.

    Os resultados não são mm, não confirmam furos e não alteram as detecções
    globais. Todos os pontos recebem um diagnóstico, inclusive os inconclusivos.
    """
    if piece_tone not in ("light", "dark"):
        raise ValueError("Tom inválido.")
    if image is None or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Imagem inválida.")
    if not isinstance(centers, list) or len(centers) > 30:
        raise ValueError("Quantidade de centros inválida.")
    h, w = image.shape[:2]
    polygon = np.asarray(photo_contour, dtype=np.float32)
    if polygon.ndim != 2 or polygon.shape[1] != 2 or polygon.shape[0] < 3:
        raise ValueError("Contorno da foto inválido.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    smooth = cv2.GaussianBlur(gray, (3, 3), 0.7).astype(np.float32)
    background = cv2.GaussianBlur(gray, (17, 17), 3.7).astype(np.float32)
    signal = (background - smooth) if piece_tone == "light" else (smooth - background)
    body = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(body, [np.rint(polygon).astype(np.int32)], 255)
    # Região pequena apenas para buscar evidência perto do centro previsto.
    # A escala fotográfica foi normalizada pelo CAD em outro módulo e não
    # serve para medir distância física ou aplicar tolerância industrial.
    body_area = max(1., float(cv2.contourArea(polygon)))
    radius = min(26, max(13, round(np.sqrt(body_area) * .032)))
    # Comparação experimental com a malha vizinha: em vez de diminuir o
    # limiar para encontrar três pontos, medimos quão incomum é o contraste
    # perto do centro CAD em relação a janelas SEMELHANTES do próprio tecido.
    # A distribuição mede raridade óptica, NÃO probabilidade de existir furo.
    texture_radius = 8
    texture_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (2 * texture_radius + 1,) * 2
    )
    texture_max = cv2.dilate(signal, texture_kernel)
    texture_inside = cv2.erode(body, texture_kernel)
    cad_centers = np.asarray(
        [item["position_px"] for item in centers], dtype=np.float64
    ) if centers else np.empty((0, 2))
    output = []
    for number, item in enumerate(centers, 1):
        center = item.get("position_px")
        if not isinstance(center, list) or len(center) != 2:
            raise ValueError("Centro projetado inválido.")
        x, y = (float(center[0]), float(center[1]))
        if not np.isfinite([x, y]).all():
            raise ValueError("Centro projetado não finito.")
        result = {
            "cad_id": str(item.get("cad_id", f"V{number}"))[:50],
            "position_px": [round(x, 1), round(y, 1)],
            "roi_radius_px": radius,
            "status": "inconclusivo",
            "optical_peaks": 0,
            "best_signal_px": None,
            "best_signal_levels": None,
            "distance_to_projected_center_px": None,
            "max_local_signal_levels": None,
            "threshold_levels": None,
            "noise_sigma_levels": None,
            # O pico mais forte SEM limiar serve exclusivamente de diagnóstico.
            # Pode ser trama/ruído. Não gera candidato nem muda o status.
            "raw_peak_px": None,
            "raw_peak_distance_px": None,
            "contrast_margin_levels": None,
            "signal_at_cad_center_levels": None,
            "texture_window_radius_px": texture_radius,
            "texture_reference_window_count": 0,
            "texture_reference_median_levels": None,
            "texture_reference_p90_levels": None,
            "texture_target_peak_levels": None,
            "texture_peak_percentile": None,
            "texture_peak_excess_p90_levels": None,
            "texture_distinctiveness": "comparacao_indisponivel",
            "irregular_texture": None,
            "message": "Região inconclusiva; ausência de sinal não significa vazador ausente.",
        }
        if not (0 <= x < w and 0 <= y < h):
            result["message"] = "Centro CAD projetado fora da fotografia."
            output.append(result)
            continue
        # Diagnóstico INDEPENDENTE: não exige círculos e não produz
        # candidatos globais nem validação física. Conserva os filtros originais.
        other_centers = [
            other["position_px"] for other in centers if other is not item
        ]
        result["irregular_texture"] = inspect_irregular_signal(
            image, body, [x, y], other_centers
        )
        # Janelas de controle entre 35 e 115 pixels do centro previsto,
        # completamente internas à peça. Evita os outros centros CAD para
        # não contaminar a referência com possíveis vazadores conhecidos.
        cx, cy = int(round(x)), int(round(y))
        if 0 <= cx < w and 0 <= cy < h and texture_inside[cy, cx]:
            grid_x = np.arange(max(0, cx - 115), min(w, cx + 116), 8)
            grid_y = np.arange(max(0, cy - 115), min(h, cy + 116), 8)
            gx, gy = np.meshgrid(grid_x, grid_y)
            radii = np.hypot(gx - x, gy - y)
            valid = ((radii >= 35) & (radii <= 115) &
                     (texture_inside[gy, gx] > 0))
            for ocx, ocy in cad_centers:
                valid &= np.hypot(gx - ocx, gy - ocy) >= 22
            controls = texture_max[gy[valid], gx[valid]]
            if controls.size >= 30:
                target = float(texture_max[cy, cx])
                result["texture_reference_window_count"] = int(controls.size)
                result["texture_reference_median_levels"] = round(
                    float(np.median(controls)), 1
                )
                result["texture_reference_p90_levels"] = round(
                    float(np.percentile(controls, 90)), 1
                )
                result["texture_target_peak_levels"] = round(target, 1)
                result["texture_peak_percentile"] = round(
                    float(np.mean(controls <= target) * 100), 1
                )
                difference = target - float(np.percentile(controls, 90))
                result["texture_peak_excess_p90_levels"] = round(
                    difference, 1
                )
                result["texture_distinctiveness"] = (
                    "contraste_incomum_na_regiao"
                    if target >= 18. and difference > 10.
                    else "sem_destaque_frente_a_trama"
                )
        x0, x1 = max(0, int(x) - radius), min(w, int(x) + radius + 1)
        y0, y1 = max(0, int(y) - radius), min(h, int(y) + radius + 1)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        eligible = (np.hypot(xx - x, yy - y) <= radius) & (body[y0:y1, x0:x1] > 0)
        if int(eligible.sum()) < 50:
            result["message"] = "Região muito próxima de borda ou parcialmente fora da peça."
            output.append(result)
            continue
        roi = signal[y0:y1, x0:x1]
        values = roi[eligible]
        median = float(np.median(values))
        mad = float(np.median(np.abs(values - median)))
        # Regra experimental de contraste local. Uma trama uniforme também
        # pode produzir picos; múltiplos picos tornam o resultado ambíguo.
        noise_sigma = 1.4826 * mad
        threshold = max(16., median + 5. * max(1., noise_sigma))
        result["max_local_signal_levels"] = round(float(np.max(values)), 1)
        result["threshold_levels"] = round(threshold, 1)
        result["noise_sigma_levels"] = round(noise_sigma, 1)
        result["contrast_margin_levels"] = round(
            result["max_local_signal_levels"] - result["threshold_levels"], 1
        )
        # Pixel mais contrastado, independentemente do limiar; identificar
        # distância ao centro previsto SEM interpretá-lo como furo.
        masked_signal = np.where(eligible, roi, -np.inf)
        raw_index = np.unravel_index(int(np.argmax(masked_signal)), roi.shape)
        raw_y, raw_x = int(raw_index[0]) + y0, int(raw_index[1]) + x0
        result["raw_peak_px"] = [raw_x, raw_y]
        result["raw_peak_distance_px"] = round(
            float(np.hypot(raw_x - x, raw_y - y)), 1
        )
        ix, iy = min(w-1, max(0, int(round(x)))), min(h-1, max(0, int(round(y))))
        result["signal_at_cad_center_levels"] = round(float(signal[iy, ix]), 1)
        peaks_mask = ((roi > threshold) &
                      (roi >= cv2.dilate(roi, np.ones((5, 5), np.uint8))) &
                      eligible)
        py, px = np.where(peaks_mask)
        peaks = [
            (float(roi[i, j]), float(np.hypot(j + x0 - x, i + y0 - y)),
             int(j + x0), int(i + y0))
            for i, j in zip(py, px)
        ]
        result["optical_peaks"] = len(peaks)
        if not peaks:
            if result["max_local_signal_levels"] < result["threshold_levels"]:
                result["message"] = (
                    "Maior contraste observado ficou abaixo do limiar exigido pelo filtro. "
                    "A posição do pico bruto ajuda a investigar a imagem, mas pode ser trama "
                    "ou ruído; não comprova furo ausente."
                )
            else:
                result["message"] = (
                    "Houve contraste na região, mas nenhum pico isolado passou pelos critérios locais. "
                    "Não é possível determinar se há um vazador."
                )
            output.append(result)
            continue
        peak = min(peaks, key=lambda p: (-p[0], p[1]))
        result["best_signal_px"] = [peak[2], peak[3]]
        result["best_signal_levels"] = round(peak[0], 1)
        result["distance_to_projected_center_px"] = round(peak[1], 1)
        if len(peaks) > 3:
            result["status"] = "textura_ambigua"
            result["message"] = (
                "Múltiplos sinais na região; a textura pode imitar vazadores. "
                "Não é possível isolar um furo com confiança."
            )
        else:
            result["status"] = "sinal_suspeito"
            result["message"] = (
                "Contraste localizado perto do centro projetado; pode ser "
                "vazador, trama, pigmento ou sombra. Não confirma furo."
            )
        output.append(result)
    return output
