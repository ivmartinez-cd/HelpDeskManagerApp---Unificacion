import dataclasses

import pytest

from src.modules.sla.application.use_cases.avisar_visitas_en_sucursal_mda import (
    AvisarVisitasEnSucursalMda,
)
from src.modules.sla.domain.entities.incidente_mesa_ayuda import IncidenteMesaAyuda
from src.modules.sla.domain.repositories.avisos_visita_sucursal import ParAvisado
from tests.unit.application.sla.fakes_mesa_ayuda import (
    FakeMesaAyudaQueryGateway,
    build_mesa_ayuda,
)


class FakeRegistro:
    def __init__(self, avisados: set[ParAvisado] | None = None) -> None:
        self.avisados = avisados or set()

    async def ya_avisados(self, pares: list[ParAvisado]) -> set[ParAvisado]:
        return self.avisados & set(pares)

    async def registrar(self, pares: list[ParAvisado]) -> None:
        self.avisados |= set(pares)


class FakeNotificador:
    def __init__(self, falla: bool = False) -> None:
        self.enviados: list[list[int]] = []
        self.falla = falla

    async def avisar(self, incidentes: list[IncidenteMesaAyuda]) -> None:
        if self.falla:
            raise RuntimeError("smtp caído")
        self.enviados.append([i.id_incidente for i in incidentes])


def _con_visita(id_mda: int, id_visita: int) -> IncidenteMesaAyuda:
    return dataclasses.replace(
        build_mesa_ayuda(id_mda), visita_id_incidente=id_visita, visitas_en_sucursal=1
    )


def _use_case(
    incidentes: list[IncidenteMesaAyuda], registro: FakeRegistro, notif: FakeNotificador
) -> AvisarVisitasEnSucursalMda:
    return AvisarVisitasEnSucursalMda(FakeMesaAyudaQueryGateway(incidentes), 428, registro, notif)


async def test_avisa_solo_pares_nuevos_y_una_sola_vez() -> None:
    incidentes = [_con_visita(1, 10), _con_visita(2, 20), build_mesa_ayuda(3)]
    registro, notif = FakeRegistro({(2, 20)}), FakeNotificador()
    uc = _use_case(incidentes, registro, notif)

    assert await uc.execute() == 1
    assert await uc.execute() == 0
    assert notif.enviados == [[1]]


async def test_visita_nueva_en_la_misma_sucursal_vuelve_a_avisar() -> None:
    registro, notif = FakeRegistro({(1, 10)}), FakeNotificador()

    assert await _use_case([_con_visita(1, 11)], registro, notif).execute() == 1


async def test_si_el_mail_falla_no_registra_para_reintentar() -> None:
    registro = FakeRegistro()
    uc = _use_case([_con_visita(1, 10)], registro, FakeNotificador(falla=True))

    with pytest.raises(RuntimeError):
        await uc.execute()
    assert registro.avisados == set()
