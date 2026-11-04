"""Validação offline de metadados do ensaio P0 (sem abrir/enviar fotografias)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_STATUS = {"aberto", "ausente_ou_incompleto", "deslocado", "incerto"}
ALLOWED_LIGHTING = {"frontal", "contraluz", "outra"}
ALLOWED_FEATURE = {"vazador", "recorte"}


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _local_file(value, root: Path, label: str, issues: list[str], require_files: bool):
    if not _nonempty(value):
        issues.append(f"{label}: caminho obrigatório")
        return
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() in (".", ""):
        issues.append(f"{label}: use caminho relativo sem '..'")
        return
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        issues.append(f"{label}: caminho fora do diretório privado")
        return
    if require_files and not resolved.is_file():
        issues.append(f"{label}: arquivo não encontrado")


def validate_manifest(data: object, root: Path, *, require_files=False) -> list[str]:
    """Valida estrutura/identificadores, nunca a presença física de um vazador."""
    issues: list[str] = []
    if not isinstance(data, dict):
        return ["raiz: JSON deve ser um objeto"]
    if data.get("schema_version") != "p0.1":
        issues.append("schema_version: esperado p0.1")
    for field in ("peca_fisica_id", "material", "cad_revisao", "revisor"):
        if not _nonempty(data.get(field)):
            issues.append(f"{field}: obrigatório")
    _local_file(data.get("cad_arquivo"), root, "cad_arquivo", issues, require_files)
    photos = data.get("fotografias")
    if not isinstance(photos, list) or not photos:
        issues.append("fotografias: lista não vazia obrigatória")
    else:
        photo_ids: set[str] = set()
        for index, photo in enumerate(photos):
            label = f"fotografias[{index}]"
            if not isinstance(photo, dict):
                issues.append(f"{label}: objeto obrigatório")
                continue
            photo_id = photo.get("id")
            if not _nonempty(photo_id) or photo_id in photo_ids:
                issues.append(f"{label}.id: obrigatório e único")
            else:
                photo_ids.add(photo_id)
            _local_file(photo.get("arquivo"), root, f"{label}.arquivo", issues, require_files)
            if photo.get("iluminacao") not in ALLOWED_LIGHTING:
                issues.append(f"{label}.iluminacao: valor inválido")
            if photo.get("original_sem_overlay") is not True:
                issues.append(f"{label}.original_sem_overlay: deve ser true")
    features = data.get("geometrias")
    if not isinstance(features, list) or not features:
        issues.append("geometrias: lista não vazia obrigatória")
    else:
        seen: set[str] = set()
        for index, item in enumerate(features):
            label = f"geometrias[{index}]"
            if not isinstance(item, dict):
                issues.append(f"{label}: objeto obrigatório")
                continue
            feature_id = item.get("cad_feature_id")
            if not _nonempty(feature_id) or feature_id in seen:
                issues.append(f"{label}.cad_feature_id: obrigatório e único")
            else:
                seen.add(feature_id)
            if item.get("tipo") not in ALLOWED_FEATURE:
                issues.append(f"{label}.tipo: inválido")
            if item.get("estado_fisico") not in ALLOWED_STATUS:
                issues.append(f"{label}.estado_fisico: inválido")
            if item.get("verificado_fisicamente") not in (True, False):
                issues.append(f"{label}.verificado_fisicamente: booleano obrigatório")
            if item.get("verificado_fisicamente") is True and item.get("estado_fisico") == "incerto":
                issues.append(f"{label}: confirmação física não pode ter estado incerto")
            if item.get("verificado_fisicamente") is False and item.get("estado_fisico") != "incerto":
                issues.append(f"{label}: sem revisão física, use estado incerto")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida metadados P0 offline; nunca atesta furos.")
    parser.add_argument("manifest", type=Path, help="JSON privado do ensaio")
    parser.add_argument("--require-files", action="store_true",
                        help="também verifica se caminhos relativos existem")
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"Manifesto inválido: {exc}")
        return 2
    issues = validate_manifest(data, args.manifest.parent, require_files=args.require_files)
    if issues:
        for issue in issues:
            print("ERRO:", issue)
        return 1
    print("Estrutura P0 válida. NÃO significa vazadores validados nem captura adequada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
