"""Caracterización: port de `tests/soap-normalize.test.ts` del legacy (lo que
aplica con zeep: el desenvuelto de node-soap no existe acá, zeep entrega el
string) + el mapeo de filas reales de wsAyC (claves relevadas el 2026-09-25)."""

import json

from src.modules.reporte_incidentes.domain.entities.incidente import Empresa
from src.modules.reporte_incidentes.infrastructure.wsayc import parsing
from src.modules.reporte_incidentes.infrastructure.wsayc.parsing_incidentes import incidentes


def test_parse_json_valido_vacio_e_invalido() -> None:
    assert parsing.parse_json('[{"id":"1"}]', "op") == [{"id": "1"}]
    assert parsing.parse_json("   ", "op") is None
    assert parsing.parse_json("no-json", "op") is None


def test_elegir_toma_el_primer_valor_no_vacio_y_lo_recorta() -> None:
    assert parsing.elegir({"Nombre": "  ACME  "}, ("Nombre",)) == "ACME"
    assert parsing.elegir({"nombre": "x"}, ("Nombre",)) == "x"
    assert parsing.elegir({"NOMBRE": "y"}, ("Nombre",)) == "y"
    assert parsing.elegir({"a": "   ", "b": "2"}, ("a", "b")) == "2"
    assert parsing.elegir({"a": "   "}, ("a", "b")) is None


def test_desenvolver_la_fila_bajo_su_clave() -> None:
    assert parsing.desenvolver({"Incident": {"id": "1"}}, "Incident") == {"id": "1"}
    assert parsing.desenvolver({"id": "1"}, "Incident") == {"id": "1"}
    assert parsing.desenvolver({"Incident": "plano"}, "Incident") == {"Incident": "plano"}


def test_fecha_iso() -> None:
    assert parsing.fecha_iso("23/06/2026 10:30:00") == "2026-06-23"
    assert parsing.fecha_iso("01/12/2025") == "2025-12-01"
    assert parsing.fecha_iso("01/01/1900") == parsing.fecha_iso("1900-01-01") == ""
    assert parsing.fecha_iso("2026-06-23T12:00:00Z") == "2026-06-23"
    assert parsing.fecha_iso(None) == parsing.fecha_iso("") == ""


def test_es_vacio_detecta_los_vacios_del_servicio() -> None:
    assert all(parsing.es_vacio(v) for v in (None, " ", "-", "  , . - "))
    assert not parsing.es_vacio("abc") and not parsing.es_vacio("0")


def test_empresas_activas_por_fecha_de_restriccion() -> None:
    hoy = "20260925"
    fila = {"id": "7", "Nombre": "ACME", "FechaRestriccionServicio": "19990101"}
    assert parsing.empresa_activa(fila, hoy) == Empresa("7", "ACME")
    assert parsing.empresa_activa({**fila, "FechaRestriccionServicio": "20261231"}, hoy)
    assert parsing.empresa_activa({**fila, "FechaRestriccionServicio": "20250101"}, hoy) is None
    assert parsing.empresa_activa({"Nombre": "sin id"}, hoy) is None


def test_trabajos_sin_vacios_y_en_orden_cronologico() -> None:
    raw = json.dumps([
        {"Instance": {"Tareas": "cambio fusor", "Estado": "Finalizado", "Fecha": "02/06/2026"}},
        {"Instance": {"Tareas": " ", "Observaciones": "-", "Estado": " ", "Fecha": " "}},
        {"Instance": {"Tareas": "-", "Observaciones": "no imprime", "Estado": "Pendiente"}},
    ])
    trabajos = parsing.trabajos(raw)
    assert [t.estado for t in trabajos] == ["Pendiente", "Finalizado"]
    assert trabajos[0].descripcion == "" and trabajos[0].observ == "no imprime"


def test_detalle_de_getincidentbyid() -> None:
    raw = json.dumps({"Incident": {"Causa": "Desgaste", "Tecnico": "J. Perez", "Tipo": "Visita"}})
    detalle = parsing.detalle(raw)
    assert detalle.causa == "Desgaste"
    assert (detalle.tecnico, detalle.tipo_trabajo) == ("J. Perez", "Visita")


def test_incidente_del_listado_con_numero_verificado() -> None:
    raw = json.dumps([{"Incident": {
        "id": "99", "NroIncidente": "2026060001", "Fecha": "10/06/2026 09:00:00",
        "Sucursal": "Central", "NroSerie": "ABC123", "EstadoWeb": "Resuelto", "Estado": "Cerrado",
        "Motivo": " ", "Articulo": "Impresora X", "Tipo": "Correctivo", "FechaCierre": "01/01/1900",
    }}])
    inc = incidentes(raw, Empresa("1001", "ACME"))[0]
    assert (inc.id, inc.numero, inc.fecha) == ("99", "2026060001-5", "2026-06-10")
    assert (inc.estado, inc.descripcion, inc.maquina) == ("Resuelto", "Impresora X", "ABC123")
    assert inc.fecha_cierre is None and inc.empresa_nombre == "ACME"
