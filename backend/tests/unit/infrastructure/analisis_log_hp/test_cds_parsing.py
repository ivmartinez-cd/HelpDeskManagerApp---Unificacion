"""Parseo puro de las respuestas wsAyC (JSON serializado dentro de strings SOAP)."""

import json

import pytest

from src.modules.analisis_log_hp.domain.entities.cds_incident import CdsReplacement
from src.modules.analisis_log_hp.infrastructure.wsayc import cds_parsing as p


class TestSafeParse:
    def test_none_y_json_invalido_y_json_valido(self) -> None:
        assert p.safe_parse(None) is None
        assert p.safe_parse("no es json") == "no es json"
        assert p.safe_parse('{"a": 1}') == {"a": 1}


class TestParseMachine:
    def test_extrae_id_y_empresa(self) -> None:
        raw = json.dumps({"Machine": {"id": 12, "empresa_id": " 7 "}})
        assert p.parse_machine(raw) == ("12", "7")

    @pytest.mark.parametrize(
        "raw",
        [None, "[]", json.dumps({"Machine": "x"}), json.dumps({"Machine": {"id": None}})],
    )
    def test_sin_machine_valida_devuelve_none(self, raw: str | None) -> None:
        assert p.parse_machine(raw) is None


class TestParseIncidents:
    def test_lista_de_incidentes(self) -> None:
        raw = json.dumps([{"Incident": {"id": "1"}}, {"Incident": "x"}, "basura"])
        assert p.parse_incidents(raw) == [{"id": "1"}]

    def test_un_solo_incidente_como_dict(self) -> None:
        assert p.parse_incidents(json.dumps({"Incident": {"id": "1"}})) == [{"id": "1"}]

    def test_respuesta_no_lista_da_vacio(self) -> None:
        assert p.parse_incidents("texto") == []


class TestParseCounters:
    def test_acepta_envueltos_y_planos(self) -> None:
        raw = json.dumps([{"Counter": {"Contador": "1"}}, {"Contador": "2"}, "x"])
        assert p.parse_counters(raw) == [{"Contador": "1"}, {"Contador": "2"}]

    def test_respuesta_no_lista_da_vacio(self) -> None:
        assert p.parse_counters(None) == []


class TestParseReplacements:
    def test_mapea_articulo_y_cantidad_con_defaults(self) -> None:
        raw = json.dumps([
            {"Replacement": {"Articulo": " Fusor ", "Cantidad": "2"}},
            {"Replacement": {"Articulo": None, "Cantidad": "abc"}},
            {"Replacement": {}},
            {"Otro": {}},
        ])
        assert p.parse_replacements(raw) == [
            CdsReplacement("Fusor", 2),
            CdsReplacement("Desconocido", 1),
            CdsReplacement("Desconocido", 1),
        ]

    def test_respuesta_no_lista_da_vacio(self) -> None:
        assert p.parse_replacements("{}") == []


class TestParseJobs:
    def test_filtra_descripciones_vacias_plantillas_y_cortas(self) -> None:
        raw = json.dumps([
            {"Job": {"Descripcion": "Cambio de fusor"}},
            {"Job": {"Descripcion": "."}},
            {"Job": {"Descripcion": "ab"}},
            {"Job": {"Descripcion": "Fallas: ninguna"}},
            {"Job": {"Descripcion": "Observaciones: x"}},
            {"Job": {}},
            {"Job": "x"},
            "basura",
        ])
        assert p.parse_jobs(raw) == ["Cambio de fusor"]

    def test_respuesta_no_lista_da_vacio(self) -> None:
        assert p.parse_jobs(None) == []
