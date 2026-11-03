"""Diagnóstico SEM download/instalação de pré-requisitos para SAM 2.1 (E2.1).

Executar na pasta backend: python -m app.sam2_preflight
Este módulo não importa torch, torchvision ou sam2, não lê pesos e não
habilita IA. Confere configurações e metadados disponíveis no ambiente local.
"""
from __future__ import annotations

from importlib import metadata, util
import json
import os
from pathlib import Path
import re
import sys
from typing import Mapping


# Correspondência publicada oficialmente por facebookresearch/sam2.
SAM2_VARIANTS = {
    "tiny": {
        "config": "configs/sam2.1/sam2.1_hiera_t.yaml",
        "checkpoint": "sam2.1_hiera_tiny.pt",
    },
    "small": {
        "config": "configs/sam2.1/sam2.1_hiera_s.yaml",
        "checkpoint": "sam2.1_hiera_small.pt",
    },
    "base_plus": {
        "config": "configs/sam2.1/sam2.1_hiera_b+.yaml",
        "checkpoint": "sam2.1_hiera_base_plus.pt",
    },
    "large": {
        "config": "configs/sam2.1/sam2.1_hiera_l.yaml",
        "checkpoint": "sam2.1_hiera_large.pt",
    },
}


def _installed_version(dist_name: str) -> str | None:
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return None


def _module_present(name: str) -> bool:
    try:
        return util.find_spec(name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def _version_at_least(installed: str | None, minimum: tuple[int, ...]) -> bool:
    if not installed:
        return False
    matched = re.match(r"^(\d+)\.(\d+)(?:\.(\d+))?", installed)
    if not matched:
        return False
    parts = tuple(int(x or "0") for x in matched.groups())
    return parts >= minimum


def inspect_sam2_environment(
    *,
    environ: Mapping[str, str] | None = None,
    installed_version=None,
    module_present=None,
    python_version: tuple[int, int] | None = None,
    platform: str | None = None,
) -> dict:
    """Pré-verificação estática, sem carregar modelos ou consultar GPU real.

    Permite injetar probes em testes; não confundir prontidão estática com
    inferência comprovada nem estimativa de desempenho.
    """
    env = os.environ if environ is None else environ
    version = _installed_version if installed_version is None else installed_version
    present = _module_present if module_present is None else module_present
    python = sys.version_info[:2] if python_version is None else python_version
    system = sys.platform if platform is None else platform
    enabled = env.get("CONTROLVISION_SAM2_ENABLED") == "1"
    variant = env.get("CONTROLVISION_SAM2_VARIANT", "tiny")
    checkpoint = env.get("CONTROLVISION_SAM2_CHECKPOINT", "").strip()
    device = env.get("CONTROLVISION_SAM2_DEVICE", "cpu").lower()

    issues: list[str] = []
    warnings: list[str] = []

    if python < (3, 10):
        issues.append("Python 3.10+ necessário.")
    if not system.startswith("linux"):
        warnings.append("SAM 2 é recomendado oficialmente em Linux; em Windows, usar WSL.")
    if variant not in SAM2_VARIANTS:
        issues.append("Variante não suportada: tiny, small, base_plus ou large.")
    if device not in ("cpu", "cuda"):
        issues.append("Dispositivo inválido: escolha cpu ou cuda.")

    expected = SAM2_VARIANTS.get(variant)
    if not checkpoint:
        issues.append("Informe o caminho local do checkpoint oficial.")
        checkpoint_found = False
    else:
        checkpoint_found = Path(checkpoint).is_file()
        if not checkpoint_found:
            issues.append("Checkpoint não encontrado no caminho informado.")
        if expected and Path(checkpoint).name != expected["checkpoint"]:
            issues.append("Nome de checkpoint não corresponde à variante/configuração SAM 2.1 selecionada.")

    packages = {}
    for package, distribution, minimum in (
        ("torch", "torch", (2, 5, 1)),
        ("torchvision", "torchvision", (0, 20, 1)),
    ):
        detected = version(distribution)
        available = bool(present(package))
        compatible = available and _version_at_least(detected, minimum)
        packages[package] = {"installed": available, "version": detected,
                             "meets_documented_minimum": compatible}
        if not compatible:
            issues.append(f"{distribution} ausente ou anterior ao mínimo recomendado.")
    detected_sam2 = version("SAM-2")
    sam2_available = bool(present("sam2")) and detected_sam2 is not None
    packages["sam2"] = {"installed": sam2_available, "version": detected_sam2,
                        "meets_documented_minimum": sam2_available}
    if not sam2_available:
        issues.append("Pacote oficial SAM-2 não encontrado no ambiente Python atual.")

    if device == "cpu":
        warnings.append("CPU é opção experimental: inferência pode ser lenta ou incompatível com certos kernels.")
    elif device == "cuda":
        warnings.append("CUDA selecionado: GPU/driver/VRAM NÃO foram verificados (nenhum torch importado).")
    warnings.append(
        "Nome e existência de .pt NÃO verificam integridade/autenticidade; carregar somente pesos oficiais confiáveis."
    )
    warnings.append(
        "Compatibilidade exata torch/torchvision/CUDA e custo de memória/tempo só serão validados em E2.2."
    )
    if not enabled:
        warnings.insert(0, "SAM 2 permanece desativado até CONTROLVISION_SAM2_ENABLED=1.")

    return {
        "stage": "E2.1",
        "status": "desativado" if not enabled else ("prerequisitos_presentes" if not issues else "pendente"),
        "enabled": enabled,
        "ready_for_static_trial": bool(enabled and not issues),
        "model": "SAM 2.1",
        "variant": variant,
        "config": expected["config"] if expected else None,
        "expected_checkpoint_filename": expected["checkpoint"] if expected else None,
        "checkpoint_found": checkpoint_found,
        "device": device,
        "python": f"{python[0]}.{python[1]}",
        "platform": system,
        "packages": packages,
        "issues": issues,
        "warnings": warnings,
        "license": "Apache-2.0 (código e checkpoints, conforme README oficial)",
        "model_executed": False,
        "gpu_verified": False,
        "performance_measured": False,
    }


def main() -> None:
    report = inspect_sam2_environment()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # Um diagnóstico incompleto é resultado normal, não falha do backend.
    # CI deve testar o contrato da saída, não exigir pesos instalados.


if __name__ == "__main__":
    main()
