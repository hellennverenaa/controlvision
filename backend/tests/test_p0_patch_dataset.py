"""Teste sintético de patches da IA 2. Nenhuma foto/peça real versionada."""
import json

import cv2
import numpy as np
import pytest

from app.p0_patch_dataset import prepare_patches, validate_annotations


def fixture_data(tmp_path):
    (tmp_path / "cad").mkdir()
    (tmp_path / "fotos").mkdir()
    (tmp_path / "cad" / "sintetico.dxf").write_text("exemplo", encoding="utf-8")
    # Imagem sintética de 100x120, sem padrão de peça industrial.
    img = np.full((100, 120, 3), 180, dtype=np.uint8)
    img[45:55, 45:55] = 20
    cv2.imwrite(str(tmp_path / "fotos" / "sintetica.png"), img)
    manifest = {
        "schema_version": "p0.1", "peca_fisica_id": "PECASINT",
        "material": "sintetico", "cad_revisao": "teste", "revisor": "teste",
        "cad_arquivo": "cad/sintetico.dxf",
        "fotografias": [{"id": "F01", "arquivo": "fotos/sintetica.png",
                         "iluminacao": "outra", "original_sem_overlay": True}],
        "geometrias": [{"cad_feature_id": "V01", "tipo": "vazador",
                        "estado_fisico": "incerto", "verificado_fisicamente": False}]
    }
    annotations = {
        "schema_version": "p0-patches.1", "foto_id": "F01",
        "peca_fisica_id": "PECASINT",
        "pontos": [{"id": "M01", "x": 50, "y": 50, "classe": "vazador_confirmado",
                    "revisado_por_pessoa": True, "existencia_fisica_confirmada": True},
                   {"id": "T01", "x": 80, "y": 50, "classe": "trama_normal_revisada",
                    "revisado_por_pessoa": True, "existencia_fisica_confirmada": False}]
    }
    mp, ap = tmp_path / "manifesto.json", tmp_path / "anotacoes.json"
    mp.write_text(json.dumps(manifest), encoding="utf-8")
    ap.write_text(json.dumps(annotations), encoding="utf-8")
    return mp, ap, annotations, manifest


def test_exports_original_resolution_private(tmp_path):
    mp, ap, _, _ = fixture_data(tmp_path)
    out = tmp_path / "patches"
    assert prepare_patches(mp, ap, out, "F01", 32) == 2
    assert cv2.imread(str(out / "patch_001.png")).shape[:2] == (32, 32)
    assert json.loads((out / "indice.json").read_text())["quantidade"] == 2


def test_rejects_unconfirmed_positive(tmp_path):
    mp, ap, data, manifest = fixture_data(tmp_path)
    data["pontos"][0]["existencia_fisica_confirmada"] = False
    assert any("declaração física" in v for v in validate_annotations(data, manifest, 120, 100, "F01"))


def test_rejects_unreviewed_negative(tmp_path):
    mp, ap, data, manifest = fixture_data(tmp_path)
    data["pontos"][1]["revisado_por_pessoa"] = False
    assert any("revisão humana" in v for v in validate_annotations(data, manifest, 120, 100, "F01"))


def test_rejects_wrong_photo_and_out_of_bounds(tmp_path):
    _, _, data, manifest = fixture_data(tmp_path)
    data["pontos"][0]["x"] = 121
    issues = validate_annotations(data, manifest, 120, 100, "F02")
    assert any("foto_id" in i for i in issues)
    assert any(".x" in i for i in issues)


def test_rejects_border_crops_without_creating_folder(tmp_path):
    mp, ap, data, _ = fixture_data(tmp_path)
    data["pontos"][0]["x"] = 2
    ap.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="borda"):
        prepare_patches(mp, ap, tmp_path / "out", "F01", 32)
    assert not (tmp_path / "out").exists()


def test_rejects_overwriting(tmp_path):
    mp, ap, _, _ = fixture_data(tmp_path)
    out = tmp_path / "patches"
    out.mkdir()
    with pytest.raises(FileExistsError):
        prepare_patches(mp, ap, out, "F01", 32)


def test_rejects_output_outside_private_root(tmp_path):
    mp, ap, _, _ = fixture_data(tmp_path)
    with pytest.raises(ValueError, match="subdiretório"):
        prepare_patches(mp, ap, tmp_path.parent / "outside", "F01", 32)


def test_rejects_invalid_patch_size(tmp_path):
    mp, ap, _, _ = fixture_data(tmp_path)
    with pytest.raises(ValueError, match="par"):
        prepare_patches(mp, ap, tmp_path / "out", "F01", 31)
