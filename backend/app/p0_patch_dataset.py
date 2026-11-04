"""Recortes de referência para P0/IA2, exclusivamente offline e sem treinamento."""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import cv2
import numpy as np

from .p0_manifest import validate_manifest

LABELS = {"vazador_confirmado", "trama_normal_revisada"}
MAX_POINTS = 300


def validate_annotations(data, manifest, image_width, image_height, photo_id):
    """Confere apenas integridade declarada, NÃO veracidade física dos rótulos."""
    issues = []
    if not isinstance(data, dict) or data.get("schema_version") != "p0-patches.1":
        return ["schema_version inválido: esperado p0-patches.1"]
    if data.get("foto_id") != photo_id:
        issues.append("foto_id não corresponde à fotografia selecionada")
    if data.get("peca_fisica_id") != manifest.get("peca_fisica_id"):
        issues.append("peca_fisica_id não corresponde ao manifesto")
    points = data.get("pontos")
    if not isinstance(points, list) or not points or len(points) > MAX_POINTS:
        return issues + ["pontos: fornecer de 1 a 300 anotações"]
    ids = set()
    for i, point in enumerate(points):
        name = f"pontos[{i}]"
        if not isinstance(point, dict):
            issues.append(f"{name}: deve ser objeto")
            continue
        pid = point.get("id")
        if not isinstance(pid, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,30}", pid) or pid in ids:
            issues.append(f"{name}: id inválido/duplicado")
        else:
            ids.add(pid)
        if point.get("classe") not in LABELS:
            issues.append(f"{name}: classe inválida")
        if point.get("revisado_por_pessoa") is not True:
            issues.append(f"{name}: requer revisão humana explícita")
        if point.get("classe") == "vazador_confirmado" and point.get("existencia_fisica_confirmada") is not True:
            issues.append(f"{name}: vazador exige declaração física positiva")
        # Áreas de trama são negativos VISUAIS revisados, não prova absoluta de ausência física.
        if point.get("classe") == "trama_normal_revisada" and point.get("existencia_fisica_confirmada") is True:
            issues.append(f"{name}: negativo não pode declarar confirmação de vazador")
        for key, limit in (("x", image_width), ("y", image_height)):
            val = point.get(key)
            if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val) or val < 0 or val >= limit:
                issues.append(f"{name}.{key}: coordenada fora da imagem")
    return issues


def prepare_patches(manifest_path: Path, annotations_path: Path, output_dir: Path,
                    photo_id: str, patch_size: int = 64):
    """Grava somente crops e índice privados; saída nunca é score de defeito."""
    if patch_size < 16 or patch_size > 512 or patch_size % 2:
        raise ValueError("patch_size deve ser par entre 16 e 512")
    root = manifest_path.resolve().parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    issues = validate_manifest(manifest, root, require_files=True)
    if issues:
        raise ValueError("; ".join(issues))
    selected = [p for p in manifest["fotografias"] if p["id"] == photo_id]
    if len(selected) != 1:
        raise ValueError("foto_id desconhecida ou ambígua")
    photo = selected[0]
    if photo["original_sem_overlay"] is not True:
        raise ValueError("é necessária fotografia original sem overlay")
    img_path = (root / photo["arquivo"]).resolve()
    img = cv2.imdecode(np.fromfile(str(img_path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("não foi possível decodificar a fotografia")
    h, w = img.shape[:2]
    if h < patch_size or w < patch_size:
        raise ValueError("foto menor que o recorte pedido")
    annotations = json.loads(annotations_path.read_text(encoding="utf-8"))
    issues = validate_annotations(annotations, manifest, w, h, photo_id)
    if issues:
        raise ValueError("; ".join(issues))
    half = patch_size // 2
    crops = []
    for p in annotations["pontos"]:
        # Recorte centrado em pixels originais, sem resize/interpolação.
        cx, cy = int(round(p["x"])), int(round(p["y"]))
        left, top = cx - half, cy - half
        if left < 0 or top < 0 or left + patch_size > w or top + patch_size > h:
            raise ValueError(f"{p['id']}: recorte ultrapassa a borda da foto")
        crops.append((p, img[top:top+patch_size, left:left+patch_size].copy()))
    if output_dir.exists():
        raise FileExistsError("diretório de saída já existe; não sobrescrever dataset anterior")
    # Saída obrigatoriamente irmã do manifesto, para evitar publicar no repositório.
    destination = output_dir.resolve()
    if not destination.is_relative_to(root) or destination == root:
        raise ValueError("saída deve ser subdiretório da pasta privada do ensaio")
    destination.mkdir(mode=0o700, parents=True)
    records = []
    for index, (p, crop) in enumerate(crops, start=1):
        filename = f"patch_{index:03d}.png"
        encoded, buffer = cv2.imencode(".png", crop)
        if not encoded:
            raise ValueError("erro ao codificar recorte")
        (destination / filename).write_bytes(buffer.tobytes())
        records.append({"arquivo": filename, "id_anotacao": p["id"],
                        "classe_declarada": p["classe"],
                        "centro_px": [p["x"], p["y"]],
                        "revisado_por_pessoa": True})
    (destination / "indice.json").write_text(json.dumps({
        "schema_version": "p0-patches.1",
        "foto_id": photo_id,
        "peca_fisica_id": manifest["peca_fisica_id"],
        "tamanho_px": patch_size,
        "quantidade": len(records),
        "itens": records,
        "aviso": "Rótulos declarados por humanos; sem treinamento, calibração ou veredito."
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(records)


def main():
    parser = argparse.ArgumentParser(description="Extrai patches de anotações humanas privadas; não treina IA.")
    parser.add_argument("manifesto", type=Path)
    parser.add_argument("anotacoes", type=Path)
    parser.add_argument("--foto-id", default="F01")
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--tamanho", type=int, default=64)
    args = parser.parse_args()
    try:
        n = prepare_patches(args.manifesto, args.anotacoes, args.saida, args.foto_id, args.tamanho)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERRO: {exc}")
        return 1
    print(f"{n} recortes privados exportados. NÃO há modelo treinado nem detecção validada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
