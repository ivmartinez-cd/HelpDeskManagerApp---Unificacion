"""GetCdsIncidents: incidentes CD de los últimos 12 meses (tope 15), ordenados
del más nuevo al más viejo, enriquecidos con contador, repuestos y tareas."""

from datetime import datetime, timedelta

from src.modules.analisis_log_hp.application.use_cases.get_cds_incidents import GetCdsIncidents
from tests.unit.application.analisis_log_hp.fake_gateways import FakeCdsGateway

_FMT = "%d/%m/%Y %H:%M:%S"


def _inc(id: str, dias_atras: int, **extra: str) -> dict[str, str]:
    fecha = (datetime.now() - timedelta(days=dias_atras)).strftime(_FMT)
    return {
        "id": id, "NroIncidente": f"N{id}", "Fecha": fecha, "Tipo": "Correctivo",
        "Estado": "Cerrado", "Motivo": "Atasco", **extra,
    }


class TestGetCdsIncidents:
    async def test_equipo_inexistente_devuelve_lista_vacia(self) -> None:
        assert await GetCdsIncidents(FakeCdsGateway(machine=None)).execute("x") == []

    async def test_filtra_12_meses_ordena_y_enriquece(self) -> None:
        gw = FakeCdsGateway(
            incidents=[_inc("1", 30), _inc("2", 400), _inc("3", 5), {"Fecha": "rota"}, {}],
            counters=[{"FechaToma": (datetime.now() - timedelta(days=4)).strftime("%d/%m/%Y"),
                       "Contador": "5000", "TipoToma": "Lectura"}],
        )
        result = await GetCdsIncidents(gw).execute(" abc ")

        assert gw.serial == "ABC"
        assert [i.id for i in result] == ["3", "1"]
        mas_nuevo = result[0]
        assert mas_nuevo.numero_incidente == "N3"
        assert mas_nuevo.contador == "5000"
        assert mas_nuevo.repuestos[0].articulo == "rep-3"
        assert mas_nuevo.tareas_realizadas == ["tarea-3"]
        assert (mas_nuevo.tipo, mas_nuevo.estado, mas_nuevo.motivo) == (
            "Correctivo", "Cerrado", "Atasco"
        )

    async def test_tope_de_15_incidentes(self) -> None:
        gw = FakeCdsGateway(incidents=[_inc(str(i), i) for i in range(20)])
        result = await GetCdsIncidents(gw).execute("s")
        assert len(result) == 15
        assert len(gw.detail_calls) == 15

    async def test_falla_del_detalle_deja_repuestos_y_tareas_vacios(self) -> None:
        gw = FakeCdsGateway(incidents=[_inc("1", 1)], details_error=RuntimeError("soap"))
        result = await GetCdsIncidents(gw).execute("s")
        assert (result[0].repuestos, result[0].tareas_realizadas) == ([], [])

    async def test_incidente_sin_id_no_consulta_detalle_y_usa_defaults(self) -> None:
        fecha = (datetime.now() - timedelta(days=1)).strftime(_FMT)
        gw = FakeCdsGateway(incidents=[{"Fecha": fecha}])
        result = await GetCdsIncidents(gw).execute("s")
        assert gw.detail_calls == []
        inc = result[0]
        assert (inc.id, inc.tipo, inc.estado, inc.motivo) == (
            "", "Desconocido", "Desconocido", "Sin motivo"
        )
        assert inc.contador is None
