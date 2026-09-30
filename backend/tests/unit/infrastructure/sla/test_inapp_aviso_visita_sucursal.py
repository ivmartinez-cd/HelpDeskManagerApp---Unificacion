import dataclasses

import pytest

from src.modules.notificaciones.domain.entities.notificacion import NuevaNotificacion
from src.modules.sla.domain.entities.incidente_mesa_ayuda import IncidenteMesaAyuda
from src.modules.sla.infrastructure.inapp_aviso_visita_sucursal import (
    InAppNotificadorVisitaSucursal,
    NotificadoresEnSerie,
)
from tests.unit.application.sla.fakes_mesa_ayuda import build_mesa_ayuda


class FakePublicador:
    def __init__(self) -> None:
        self.publicadas: list[NuevaNotificacion] = []

    async def publicar(self, notificaciones: list[NuevaNotificacion]) -> None:
        self.publicadas.extend(notificaciones)


def _con_visita(id_mda: int, id_visita: int, visitas: int = 1) -> IncidenteMesaAyuda:
    return dataclasses.replace(
        build_mesa_ayuda(id_mda),
        visita_id_incidente=id_visita,
        visita_tecnico="Técnico Uno",
        visita_estado="Asignado",
        visitas_en_sucursal=visitas,
    )


async def test_una_notificacion_por_par_para_la_funcion_de_avisos() -> None:
    publicador = FakePublicador()
    await InAppNotificadorVisitaSucursal(publicador).avisar(
        [_con_visita(10, 20), _con_visita(11, 21, visitas=3)]
    )
    primera, segunda = publicador.publicadas
    assert primera.clave == "sla.visita-sucursal:10:20"
    assert primera.audiencia == "funcion:sla-avisos-mesa-ayuda"
    assert primera.url == "/sla/mesa-de-ayuda"
    assert "Caso 10" in primera.titulo
    assert "Caso 20 derivado a Técnico Uno, Asignado" in primera.cuerpo
    assert "Caso 21 (+2 más)" in segunda.cuerpo


class _Canal:
    def __init__(self, nombre: str, log: list[str], falla: bool = False) -> None:
        self.nombre, self.log, self.falla = nombre, log, falla

    async def avisar(self, incidentes: list[IncidenteMesaAyuda]) -> None:
        if self.falla:
            raise RuntimeError(f"{self.nombre} caído")
        self.log.append(self.nombre)


async def test_en_serie_avisa_por_todos_los_canales_en_orden() -> None:
    log: list[str] = []
    await NotificadoresEnSerie([_Canal("app", log), _Canal("mail", log)]).avisar([])
    assert log == ["app", "mail"]


async def test_en_serie_propaga_el_fallo_de_un_canal() -> None:
    log: list[str] = []
    serie = NotificadoresEnSerie([_Canal("app", log), _Canal("mail", log, falla=True)])
    with pytest.raises(RuntimeError, match="mail caído"):
        await serie.avisar([])
