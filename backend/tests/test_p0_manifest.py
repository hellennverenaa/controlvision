"""Testes apenas com metadados sintéticos; sem fotos/CAD industriais."""
from pathlib import Path

from app.p0_manifest import validate_manifest


def sample():
    return {
        "schema_version": "p0.1",
        "peca_fisica_id": "EXEMPLO-SINTETICO",
        "material": "malha_sintetica",
        "cad_revisao": "R0",
        "revisor": "revisor_exemplo",
        "cad_arquivo": "cad/exemplo.dxf",
        "fotografias": [
            {"id": "F01", "arquivo": "fotos/frontal.jpg",
             "iluminacao": "frontal", "original_sem_overlay": True}
        ],
        "geometrias": [
            {"cad_feature_id": "V01", "tipo": "vazador",
             "estado_fisico": "incerto", "verificado_fisicamente": False}
        ],
    }


def test_valid_structure_does_not_require_private_files(tmp_path: Path):
    assert validate_manifest(sample(), tmp_path) == []


def test_not_physically_verified_cannot_claim_open(tmp_path: Path):
    d = sample()
    d["geometrias"][0]["estado_fisico"] = "aberto"
    assert any("sem revisão física" in e for e in validate_manifest(d, tmp_path))


def test_duplicate_feature_is_rejected(tmp_path: Path):
    d = sample()
    d["geometrias"].append(dict(d["geometrias"][0]))
    assert any("único" in e for e in validate_manifest(d, tmp_path))


def test_private_path_cannot_escape(tmp_path: Path):
    d = sample()
    d["cad_arquivo"] = "../fora.dxf"
    assert any("relativo" in e for e in validate_manifest(d, tmp_path))


def test_requires_existing_files_if_requested(tmp_path: Path):
    assert any("não encontrado" in e for e in validate_manifest(sample(), tmp_path, require_files=True))


def test_verified_open_is_structurally_valid(tmp_path: Path):
    d = sample()
    d["geometrias"][0].update(estado_fisico="aberto", verificado_fisicamente=True)
    assert validate_manifest(d, tmp_path) == []


def test_invalid_photo_overlay(tmp_path: Path):
    d = sample()
    d["fotografias"][0]["original_sem_overlay"] = False
    assert any("original_sem_overlay" in e for e in validate_manifest(d, tmp_path))
