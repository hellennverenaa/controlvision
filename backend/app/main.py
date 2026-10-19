"""API experimental: não aprova ou reprova peças para produção."""
import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .geometry import read_cad

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
async def inspect_preview(file: UploadFile = File(...)):
    raw = await file.read(15_000_001)
    img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(422, "Imagem inválida.")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise HTTPException(422, "Nenhum contorno encontrado; reveja a iluminação.")
    biggest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(biggest) < 50:
        raise HTTPException(422, "Contorno pequeno demais.")
    outline = cv2.approxPolyDP(biggest, 1.5, True).reshape(-1, 2).tolist()
    # Coordenadas em pixels: não representa inspeção dimensional calibrada.
    return {
        "status": "preview_only", "units": "pixels", "contour": outline,
        "contour_area_px2": round(cv2.contourArea(biggest), 2),
        "image_size": [img.shape[1], img.shape[0]],
        "detected_regions": len(contours),
        "warnings": ["Sem calibração nem correspondência dimensional com o CAD."]
    }
