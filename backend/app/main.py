"""API experimental: não aprova ou reprova peças para produção."""
import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .geometry import read_cad
from .vision import analyze_image

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
async def inspect_preview(file: UploadFile = File(...), mode: str = Form("marks")):
    if mode not in ("marks", "holes"):
        raise HTTPException(422, "Modo inválido: escolha marks ou holes.")
    raw = await file.read(15_000_001)
    if len(raw) > 15_000_000:
        raise HTTPException(413, "Imagem muito grande (limite 15 MB).")
    img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(422, "Imagem inválida.")
    try:
        return analyze_image(img, mode=mode)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
