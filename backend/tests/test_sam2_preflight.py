"""E2.1 — verificação estática do ambiente SAM 2 sem torch, download ou GPU."""
import json

from app import sam2_preflight
from app.sam2_preflight import SAM2_VARIANTS, inspect_sam2_environment


def _probes(versions=None):
    versions = versions if versions is not None else {
        "torch": "2.5.1+cu121",
        "torchvision": "0.20.1+cu121",
        "SAM-2": "1.0",
    }

    def installed(name):
        return versions.get(name)

    def exists(name):
        return installed("SAM-2" if name == "sam2" else name) is not None

    return installed, exists


def _env(tmp_path, *, variant="tiny", filename="sam2.1_hiera_tiny.pt",
         enabled="1", device="cpu"):
    checkpoint = tmp_path / filename
    checkpoint.write_bytes(b"dummy-do-not-load")
    return {
        "CONTROLVISION_SAM2_ENABLED": enabled,
        "CONTROLVISION_SAM2_VARIANT": variant,
        "CONTROLVISION_SAM2_CHECKPOINT": str(checkpoint),
        "CONTROLVISION_SAM2_DEVICE": device,
    }


def test_variants_agree_with_official_sam2_1_config_and_filenames():
    assert SAM2_VARIANTS == {
        "tiny": {"config": "configs/sam2.1/sam2.1_hiera_t.yaml",
                 "checkpoint": "sam2.1_hiera_tiny.pt"},
        "small": {"config": "configs/sam2.1/sam2.1_hiera_s.yaml",
                  "checkpoint": "sam2.1_hiera_small.pt"},
        "base_plus": {"config": "configs/sam2.1/sam2.1_hiera_b+.yaml",
                      "checkpoint": "sam2.1_hiera_base_plus.pt"},
        "large": {"config": "configs/sam2.1/sam2.1_hiera_l.yaml",
                  "checkpoint": "sam2.1_hiera_large.pt"},
    }


def test_disabled_does_not_claim_model_is_ready(tmp_path):
    installed, present = _probes()
    result = inspect_sam2_environment(
        environ=_env(tmp_path, enabled="0"), installed_version=installed,
        module_present=present, python_version=(3, 11), platform="linux",
    )
    assert result["status"] == "desativado"
    assert result["enabled"] is False
    assert not result["ready_for_static_trial"]
    assert result["model_executed"] is False
    assert result["performance_measured"] is False


def test_static_prerequisites_present_do_not_promise_inference(tmp_path):
    installed, present = _probes()
    result = inspect_sam2_environment(
        environ=_env(tmp_path), installed_version=installed,
        module_present=present, python_version=(3, 11), platform="linux",
    )
    assert result["status"] == "prerequisitos_presentes"
    assert result["ready_for_static_trial"] is True
    assert result["expected_checkpoint_filename"] == "sam2.1_hiera_tiny.pt"
    assert result["checkpoint_found"] is True
    assert result["issues"] == []
    assert result["license"].startswith("Apache-2.0")
    assert result["packages"]["torch"]["meets_documented_minimum"] is True
    assert not result["model_executed"]
    assert not result["gpu_verified"]


def test_missing_weights_never_returns_ready(tmp_path):
    installed, present = _probes()
    result = inspect_sam2_environment(
        environ={"CONTROLVISION_SAM2_ENABLED": "1"},
        installed_version=installed, module_present=present,
        python_version=(3, 11), platform="linux",
    )
    assert result["status"] == "pendente"
    assert not result["checkpoint_found"]
    assert not result["ready_for_static_trial"]
    assert any("checkpoint" in issue.lower() for issue in result["issues"])


def test_mismatched_variant_checkpoint_rejected_without_loading(tmp_path):
    installed, present = _probes()
    result = inspect_sam2_environment(
        environ=_env(tmp_path, variant="large"), installed_version=installed,
        module_present=present, python_version=(3, 11), platform="linux",
    )
    assert result["status"] == "pendente"
    assert any("não corresponde" in issue for issue in result["issues"])
    assert result["config"].endswith("_l.yaml")
    assert result["expected_checkpoint_filename"] == "sam2.1_hiera_large.pt"


def test_invalid_variant_and_device_are_explicit(tmp_path):
    installed, present = _probes()
    result = inspect_sam2_environment(
        environ=_env(tmp_path, variant="invented", device="tpu"),
        installed_version=installed, module_present=present,
        python_version=(3, 12), platform="linux",
    )
    assert result["status"] == "pendente"
    assert result["config"] is None
    assert any("Variante" in x for x in result["issues"])
    assert any("Dispositivo" in x for x in result["issues"])


def test_python_and_package_minima_verified_without_torch_import(tmp_path):
    installed, present = _probes({
        "torch": "2.4.0",
        "torchvision": "0.19.1",
        "SAM-2": None,
    })
    result = inspect_sam2_environment(
        environ=_env(tmp_path), installed_version=installed,
        module_present=present, python_version=(3, 9), platform="win32",
    )
    assert result["status"] == "pendente"
    assert len(result["issues"]) >= 4
    assert any("Python 3.10+" in x for x in result["issues"])
    assert result["packages"]["torch"]["meets_documented_minimum"] is False
    assert result["packages"]["torchvision"]["meets_documented_minimum"] is False
    assert result["packages"]["sam2"]["installed"] is False
    assert any("WSL" in x for x in result["warnings"])


def test_cuda_only_reported_as_unverified_not_falsely_approved(tmp_path):
    installed, present = _probes()
    result = inspect_sam2_environment(
        environ=_env(tmp_path, device="cuda"), installed_version=installed,
        module_present=present, python_version=(3, 11), platform="linux",
    )
    assert result["device"] == "cuda"
    assert result["gpu_verified"] is False
    assert any("NÃO foram verificados" in msg for msg in result["warnings"])


def test_command_prints_safe_json_and_does_not_load_checkpoint(tmp_path, monkeypatch, capsys):
    env = _env(tmp_path, enabled="0")
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    sam2_preflight.main()
    stdout = capsys.readouterr().out
    report = json.loads(stdout)
    assert report["status"] == "desativado"
    assert report["model_executed"] is False
    assert str(tmp_path) not in stdout  # nunca expor path absoluto configurado
    assert "checkpoint_found" in report
