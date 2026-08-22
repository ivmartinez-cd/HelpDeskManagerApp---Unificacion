"""Emparejado de incidente CD con la lectura de contador más relevante
(port de find_counter_for_incident del legacy)."""

import pytest

from src.modules.analisis_log_hp.domain.services.cds_counter_matching import (
    find_counter_for_incident,
)


def _lectura(fecha: str, valor: str, tipo: str = "Lectura") -> dict[str, str]:
    return {"FechaToma": fecha, "Contador": valor, "TipoToma": tipo}


class TestFindCounterForIncident:
    def test_prioriza_informe_tecnico_dentro_de_la_ventana(self) -> None:
        lecturas = [
            _lectura("10/03/2026", "900"),
            _lectura("12/03/2026", "1000", tipo="Informe S. Tecnico"),
            _lectura("14/03/2026", "1100"),
        ]
        contador = find_counter_for_incident(
            lecturas, "11/03/2026 10:00:00", "15/03/2026 10:00:00"
        )
        assert contador == "1000"

    def test_entre_varios_informes_tecnicos_elige_el_mas_reciente(self) -> None:
        lecturas = [
            _lectura("12/03/2026", "1000", tipo="Informe S. Tecnico"),
            _lectura("13/03/2026", "1050", tipo="Informe S. Tecnico"),
        ]
        contador = find_counter_for_incident(
            lecturas, "11/03/2026 10:00:00", "15/03/2026 10:00:00"
        )
        assert contador == "1050"

    def test_sin_informe_tecnico_usa_la_lectura_mas_reciente_antes_del_cierre(self) -> None:
        lecturas = [
            _lectura("10/03/2026", "900"),
            _lectura("14/03/2026", "1100"),
            _lectura("20/03/2026", "1300"),
        ]
        contador = find_counter_for_incident(
            lecturas, "11/03/2026 10:00:00", "15/03/2026 10:00:00"
        )
        assert contador == "1100"

    def test_sin_fecha_de_cierre_usa_ventana_de_30_dias(self) -> None:
        lecturas = [
            _lectura("05/04/2026", "1200"),
            _lectura("20/04/2026", "1500"),
        ]
        contador = find_counter_for_incident(lecturas, "11/03/2026 10:00:00", None)
        assert contador == "1200"

    def test_lectura_con_fecha_y_hora_tambien_se_parsea(self) -> None:
        lecturas = [_lectura("12/03/2026 08:00:00", "1000")]
        contador = find_counter_for_incident(
            lecturas, "11/03/2026 10:00:00", "15/03/2026 10:00:00"
        )
        assert contador == "1000"

    @pytest.mark.parametrize(
        "lecturas",
        [
            [],
            [{"FechaToma": "12/03/2026", "Contador": ""}],
            [{"FechaToma": "fecha rota", "Contador": "10"}],
        ],
    )
    def test_sin_lecturas_utiles_devuelve_none(self, lecturas: list[dict[str, str]]) -> None:
        assert find_counter_for_incident(lecturas, "11/03/2026 10:00:00", None) is None

    def test_fecha_de_incidente_invalida_devuelve_none(self) -> None:
        lecturas = [_lectura("12/03/2026", "1000")]
        assert find_counter_for_incident(lecturas, "no es fecha", None) is None

    def test_todas_las_lecturas_posteriores_al_cierre_devuelve_none(self) -> None:
        lecturas = [_lectura("20/03/2026", "1300")]
        contador = find_counter_for_incident(
            lecturas, "11/03/2026 10:00:00", "15/03/2026 10:00:00"
        )
        assert contador is None
