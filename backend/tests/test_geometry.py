import ezdxf
from app.geometry import read_cad


def test_dxf_contour_and_internal_circle(tmp_path):
    doc = ezdxf.new("R2013")
    doc.header["$INSUNITS"] = 4
    m = doc.modelspace()
    m.add_lwpolyline([(0,0),(100,0),(100,50),(0,50)], close=True, dxfattribs={"layer":"7"})
    m.add_circle((25,25), 5, dxfattribs={"layer":"3"})
    file = tmp_path / "teste.dxf"
    doc.saveas(file)
    result = read_cad(file.name, file.read_bytes())
    assert result["count"] == 1
    assert len(result["pieces"][0]["features"]) == 1
    assert result["pieces"][0]["features"][0]["classification"] == "pendente"


def test_open_polylines_form_one_piece(tmp_path):
    doc = ezdxf.new("R2013")
    m = doc.modelspace()
    m.add_lwpolyline([(0,0),(50,0),(50,40)])
    m.add_lwpolyline([(50,40),(0,40),(0,0)])
    file = tmp_path / "aberto.dxf"
    doc.saveas(file)
    assert read_cad(file.name, file.read_bytes())["count"] == 1


def test_hpgl_converts_plotter_units_to_mm():
    data = b"IN;PA;PU0,0;PD4000,0,4000,2000,0,2000,0,0;PU;"
    parsed = read_cad("teste.hpgl", data)
    assert parsed["count"] == 1
    assert abs(parsed["pieces"][0]["area_mm2"] - 5000) < .1


def test_invalid_extension():
    try:
        read_cad("malware.exe", b"1234")
        assert False
    except ValueError:
        pass


def test_hole_is_displayed_as_candidate_not_confirmed(tmp_path):
    doc = ezdxf.new("R2013")
    doc.header["$INSUNITS"] = 4
    model = doc.modelspace()
    model.add_lwpolyline([(0, 0), (120, 0), (120, 90), (0, 90)], close=True)
    model.add_circle((24, 45), 1.7)
    file = tmp_path / "peca.dxf"
    doc.saveas(file)
    piece = read_cad(file.name, file.read_bytes())["pieces"][0]
    assert len(piece["features"]) == 1
    feature = piece["features"][0]
    assert feature["shape"] == "circular"
    assert feature["classification"] == "pendente"
    assert abs(feature["center"][0] - 24) < .1
    assert abs(feature["center"][1] - 45) < .1
    assert "vazador" in feature["suggestion"].lower()
