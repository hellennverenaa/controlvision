"""API experimental: não aprova ou reprova peças para produção."""
import cv2
import json
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .geometry import read_cad
from .vision import analyze_image
from .microholes import inspect_marked_regions
from .annotation_comparison import compare_annotations
from .reference_validation import validate_confirmed_holes
from .family_matching import compare_size_family
from .cad_guided import analyze_predicted_regions
from .matching import match_visual

app = FastAPI(title="ControlVision", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "experimental", "release_authorized": False}


@app.post("/api/cad/import")
async def import_cad(file: UploadFile = File(...)):
    name = file.filename or "desconhecido"
    if not name.lower().endswith((".dxf", ".hpgl", ".plt", ".hp2")):
        raise HTTPException(400, "Envie arquivo DXF ou HPGL.")
    raw = await file.read(20_000_001)
    try:
        return {"filename": name, **read_cad(name, raw)}
    except Exception as exc:
        raise HTTPException(422, f"Falha ao interpretar CAD: {exc}") from exc


@app.post("/api/vision/preview")
async def inspect_preview(
    file: UploadFile = File(...),
    mode: str = Form("marks"),
    piece_tone: str = Form("dark"),
    cad_data: str | None = Form(None),
    cad_family_data: str | None = Form(None),
):
    if mode not in ("marks", "holes"):
        raise HTTPException(422, "Modo inválido: escolha marks ou holes.")
    if piece_tone not in ("dark", "light"):
        raise HTTPException(422, "Tom inválido: escolha dark ou light.")
    raw = await file.read(15_000_001)
    if len(raw) > 15_000_000:
        raise HTTPException(413, "Imagem muito grande (limite 15 MB).")
    img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(422, "Imagem inválida.")
    try:
        result = analyze_image(img, mode=mode, piece_tone=piece_tone)
        if result["status"] == "capture_invalid":
            return {**result, "matching": None}
        if cad_family_data is not None:
            if len(cad_family_data) > 2_000_000:
                raise ValueError("Família CAD extensa demais.")
            try:
                family = json.loads(cad_family_data)
                result["family_matching"] = compare_size_family(
                    family, result["contour"],
                    result["candidates"],
                    result.get("micro_candidates", []),
                )
                if mode == "holes":
                    for profile in result["family_matching"]["profiles"]:
                        # Se o contorno não encaixa nem visualmente, não há
                        # justificativa para inspecionar centros CAD projetados.
                        profile["guided_regions"] = (
                            analyze_predicted_regions(
                                img, result["contour"],
                                profile["projected_circles"], piece_tone,
                            ) if profile["fit_quality"] != "baixa" else []
                        )
            except (ValueError, TypeError, KeyError, IndexError) as exc:
                result["family_matching"] = None
                result["warnings"].append(
                    "Comparação experimental da família indisponível: " + str(exc)[:140]
                )
        if cad_data is not None:
            if len(cad_data) > 2_000_000:
                raise ValueError("Geometria CAD extensa demais.")
            try:
                geometry = json.loads(cad_data)
                result["matching"] = match_visual(
                    geometry["contour"],
                    result["contour"],
                    geometry["features"],
                    result["candidates"],
                )
            except (ValueError, TypeError, KeyError, IndexError) as exc:
                result["matching"] = None
                result["warnings"].append(
                    "Prévia de correspondência indisponível: " + str(exc)[:180]
                )
        return result
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/vision/manual-regions")
async def inspect_manual_regions(
    file: UploadFile = File(...),
    marks_json: str = Form(...),
    piece_tone: str = Form("light"),
    physically_confirmed_ids_json: str | None = Form(None),
):
    """Diagnóstico condicionado a anotações humanas. NÃO detecta furos sozinho."""
    if piece_tone not in ("dark", "light"):
        raise HTTPException(422, "Tom inválido.")
    raw = await file.read(15_000_001)
    if len(raw) > 15_000_000:
        raise HTTPException(413, "Imagem excede 15 MB.")
    image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(422, "Imagem inválida.")
    try:
        marks = json.loads(marks_json)
        preview = analyze_image(image, mode="holes", piece_tone=piece_tone)
        if preview["status"] != "preview_only":
            raise ValueError("Contorno não isolado. Não é possível analisar marcas.")
        diagnosis = inspect_marked_regions(
            image, preview["contour"], marks, piece_tone=piece_tone
        )
        diagnosis["annotation_comparison"] = compare_annotations(
            marks,
            preview["candidates"],
            preview.get("micro_candidates", []),
        )
        if physically_confirmed_ids_json is not None:
            ids = json.loads(physically_confirmed_ids_json)
            diagnosis["reference_validation"] = validate_confirmed_holes(
                marks, ids, preview["candidates"],
                preview.get("micro_candidates", []),
            )
        return diagnosis
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        raise HTTPException(422, str(exc)[:200]) from exc
