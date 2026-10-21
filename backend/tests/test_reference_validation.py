"""Referências físicas anotadas não podem ser confundidas com candidatos automáticos."""
import pytest

from app.reference_validation import validate_confirmed_holes


def test_tres_vazadores_fisicos_dois_com_candidato_um_nao():
    marks=[
        {"id":"M01","x":823.7,"y":594.7},
        {"id":"M02","x":821.8,"y":717.6},
        {"id":"M03","x":236.2,"y":633.1},
    ]
    circles=[
        {"id":"I08","center":[824.5,592.5]},
        {"id":"I04","center":[241.8,638.5]},
        {"id":"I01","center":[300,600]},
        {"id":"I02","center":[290,580]},
    ]
    report=validate_confirmed_holes(marks,["M01","M02","M03"],circles)
    assert report["reference_count"]==3
    assert report["automatically_matched"]==2
    assert report["not_detected_near_reference"]==1
    assert report["reference_recovery_percent"]==66.7
    assert report["unreviewed_candidate_count"]==2
    assert report["references"][1]["status"]=="sem_candidato_proximo"
    assert report["references"][0]["candidate_id"]=="I08"
    assert "false_positive_count" not in report
    assert "approved" not in report


def test_sem_confirmacao_fisica_nao_calcula_taxa():
    marks=[{"id":"M01","x":10,"y":10}]
    circles=[{"id":"I01","center":[10,10]}]
    report=validate_confirmed_holes(marks,[],circles)
    assert report["status"]=="sem_referencia_confirmada"
    assert report["reference_recovery_percent"] is None
    assert report["unverified_mark_count"]==1
    assert report["automatically_matched"]==0


def test_um_candidato_nao_pode_ser_contado_em_duas_referencias():
    marks=[{"id":"M01","x":10,"y":10},{"id":"M02","x":11,"y":12}]
    circles=[{"id":"I01","center":[10,11]}]
    report=validate_confirmed_holes(marks,["M01","M02"],circles)
    assert report["automatically_matched"]==1
    assert report["not_detected_near_reference"]==1
    assert report["reference_recovery_percent"]==50.0


def test_apenas_confirmados_entram_na_taxa():
    marks=[
        {"id":"M01","x":10,"y":10},
        {"id":"M02","x":50,"y":50},
    ]
    circles=[{"id":"I01","center":[10,10]}]
    report=validate_confirmed_holes(marks,["M01"],circles)
    assert report["reference_count"]==1
    assert report["unverified_mark_count"]==1
    assert report["reference_recovery_percent"]==100.0


@pytest.mark.parametrize("ids", [["M99"],["M01","M01"],[123]])
def test_confirmacao_invalida_rejeitada(ids):
    marks=[{"id":"M01","x":10,"y":10}]
    with pytest.raises(ValueError):
        validate_confirmed_holes(marks,ids,[])


def test_marcacoes_duplicadas_rejeitadas():
    marks=[{"id":"M01","x":10,"y":10},{"id":"M01","x":20,"y":20}]
    with pytest.raises(ValueError):
        validate_confirmed_holes(marks,["M01"],[])
