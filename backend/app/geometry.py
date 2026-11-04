"""Leitores CAD experimentais. Nunca usar para liberar produção."""
from __future__ import annotations
from collections import Counter
from io import StringIO
import math
import re

import ezdxf
from ezdxf.path import make_path
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import polygonize, unary_union


def _pts(points):
    out = [(float(p[0]), float(p[1])) for p in points]
    if len(out) > 1 and math.dist(out[0], out[-1]) < 1e-6:
        out.pop()
    return out


def _flatten(entities, warnings, depth=0):
    if depth > 10:
        warnings.append("Profundidade de bloco INSERT ultrapassada.")
        return
    for entity in entities:
        if entity.dxftype() == "INSERT":
            try:
                yield from _flatten(entity.virtual_entities(), warnings, depth + 1)
            except Exception as exc:
                warnings.append(f"Bloco não expandido: {exc}")
        else:
            yield entity


def _polygons(paths, warnings):
    segments = []
    for raw in paths:
        closed = len(raw) >= 3 and math.dist(raw[0], raw[-1]) <= 0.12
        coords = _pts(raw)
        if len(coords) < 2:
            continue
        if closed:
            coords.append(coords[0])
        try:
            segments.append(LineString(coords))
        except Exception:
            warnings.append("Segmento degenerado ignorado.")
    if not segments:
        return []
    # Costura polilinhas/linhas conectadas sem depender das camadas CAD.
    polygons = list(polygonize(unary_union(segments)))
    return [p for p in polygons if p.is_valid and p.area > .1]


def _outline(poly):
    return [[round(x, 4), round(y, 4)] for x, y in list(poly.exterior.coords)[:-1]]


def _assemble(paths, labels, warnings, kind, units):
    polygons = _polygons(paths, warnings)
    rings = []
    seen = set()
    for poly in polygons:
        for border in [poly.exterior, *poly.interiors]:
            try:
                ring = Polygon(border)
                if not ring.is_valid or ring.area < .1:
                    continue
                key = tuple(round(v, 3) for v in ring.bounds) + (round(ring.area, 2),)
                if key not in seen:
                    rings.append(ring)
                    seen.add(key)
            except Exception:
                continue
    rings.sort(key=lambda r: -r.area)

    def is_inside(child, parent):
        return parent is not child and parent.area > child.area and parent.contains(child.representative_point())

    roots = [r for r in rings if r.area >= 100 and not any(is_inside(r, other) for other in rings)]
    # O HPGL Lectra inclui moldura do encaixe que não é uma peça.
    if kind == "HPGL" and len(roots) == 1 and len(rings) > 5:
        frame = roots[0]
        if frame.area > 300_000 and sum(is_inside(r, frame) for r in rings) > 4:
            roots = [r for r in rings if r is not frame and r.area >= 100
                     and not any(other is not frame and is_inside(r, other) for other in rings)]
            warnings.append("Moldura HPGL removida por heurística. Confirmar visualmente.")
    pieces = []
    for index, ring in enumerate(roots, 1):
        children = [r for r in rings if is_inside(r, ring)]
        features = []
        for child in children:
            if any(is_inside(child, other) for other in children):
                continue
            # Fechamento interno = candidato, não confirmação de vazador.
            circularity = 4 * math.pi * child.area / (child.length * child.length) if child.length else 0
            circular = circularity >= 0.90
            center = child.centroid
            features.append({
                "id": f"V{len(features)+1:02d}",
                "points": _outline(child),
                "center": [round(center.x, 4), round(center.y, 4)],
                "shape": "circular" if circular else "recorte",
                "suggestion": "Possível vazador circular" if circular else "Recorte/marca interna: revisar",
                "classification": "pendente",
            })
        possible_labels = [text for text, x, y in labels if ring.buffer(.2).covers(Point(x, y))]
        name = next((label for label in possible_labels if 0 < len(label) < 70), None)
        pieces.append({
            "id": f"P{index:03d}",
            "name": name or f"Peça {index:03d}",
            "size": name if name and re.fullmatch(r"\d{2}", name) else None,
            "points": _outline(ring),
            "features": features,
            "bbox": [round(v, 3) for v in ring.bounds],
            "area_mm2": round(ring.area, 2),
            "reviewed": False,
        })
    if not pieces:
        warnings.append("Nenhuma peça identificada. Revisar fechamento dos contornos.")
    warnings.append("Todas as peças e vazadores exigem confirmação humana antes da medição.")
    return {
        "format": kind,
        "units": units,
        "pieces": pieces,
        "count": len(pieces),
        "requires_review": True,
        "warnings": list(dict.fromkeys(warnings)),
    }


def parse_dxf(data: bytes):
    try:
        content = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        content = data.decode("cp1252")
    # ezdxf.read() espera linhas de texto com newline normalizado.
    document = ezdxf.read(StringIO(content.replace("\r\n", "\n")))
    warnings, labels, paths = [], [], []
    ignored = Counter()
    for entity in _flatten(document.modelspace(), warnings):
        kind = entity.dxftype()
        if kind in {"TEXT", "MTEXT"}:
            try:
                text = (entity.dxf.text if kind == "TEXT" else entity.text).strip()
                position = entity.dxf.insert
                labels.append((text, float(position.x), float(position.y)))
            except Exception:
                pass
        elif kind in {"LWPOLYLINE", "POLYLINE", "LINE", "ARC", "CIRCLE", "ELLIPSE", "SPLINE"}:
            try:
                coords = _pts(make_path(entity).flattening(.07))
                closed = kind == "CIRCLE" or (kind in {"LWPOLYLINE", "POLYLINE", "SPLINE"} and bool(
                    getattr(entity, "closed", getattr(entity, "is_closed", False))
                ))
                if closed and coords:
                    coords.append(coords[0])
                paths.append(coords)
            except Exception as exc:
                warnings.append(f"Geometria {kind} ignorada: {exc}")
        else:
            ignored[kind] += 1
    unit_code = int(document.header.get("$INSUNITS", 0))
    if unit_code != 4:
        warnings.append(f"DXF com INSUNITS={unit_code}: confirmar escala antes de medir.")
    result = _assemble(paths, labels, warnings, "DXF", "mm" if unit_code == 4 else "não confirmada")
    result["ignored_entities"] = dict(ignored)
    return result


def parse_hpgl(data: bytes):
    text = data.decode("latin1").replace("\r", "\n")
    cursor = (0., 0.)
    paths, labels, warnings = [], [], []
    active = []
    absolute = True
    pen_down = False

    def finish_path():
        nonlocal active
        if len(active) > 1:
            paths.append(active)
        active = []

    for raw in re.split(r"[;\x1c]+", text):
        token = raw.strip()
        if len(token) < 2:
            continue
        kind, value = token[:2].upper(), token[2:].strip()
        if kind == "LB":
            name = value.split("\x03")[0].strip()
            if name:
                labels.append((name, *cursor))
            continue
        if kind == "PA":
            absolute = True
        elif kind == "PR":
            absolute = False
            warnings.append("Coordenadas relativas PR: confirmar interpretação.")
        elif kind not in {"PU", "PD"}:
            continue
        if kind == "PU":
            finish_path()
            pen_down = False
        if kind == "PD":
            pen_down = True
        nums = re.findall(r"-?\d+(?:\.\d+)?", value)
        if len(nums) % 2:
            warnings.append("HPGL possui coordenadas incompletas.")
            continue
        for index in range(0, len(nums), 2):
            point = (float(nums[index]) / 40., float(nums[index+1]) / 40.)
            if not absolute:
                point = (cursor[0] + point[0], cursor[1] + point[1])
            if pen_down:
                if not active:
                    active = [cursor]
                active.append(point)
            cursor = point
    finish_path()
    warnings.append("HPGL: 40 unidades/mm é hipótese de exportação; confirmar no CAD.")
    return _assemble(paths, labels, warnings, "HPGL", "mm presumido")


def read_cad(filename: str, content: bytes):
    if len(content) > 20_000_000:
        raise ValueError("Arquivo supera limite do protótipo: 20 MB.")
    name = filename.lower()
    if name.endswith(".dxf"):
        return parse_dxf(content)
    if name.endswith((".hpgl", ".plt", ".hp2")):
        return parse_hpgl(content)
    raise ValueError("Formato não suportado: use DXF, HPGL ou PLT.")
