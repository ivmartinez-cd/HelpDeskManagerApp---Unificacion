"""Fakes de Siges y OCA y el mundo en memoria de `SincronizarDespachos`."""

from collections.abc import Awaitable, Callable, Sequence

import pytest

from src.modules.insumos.application.use_cases.despachados.sincronizar_despachos import (
    ConfigSincronizacion,
    SincronizarDespachos,
    SincronizarDespachosPorts,
)
from src.modules.insumos.domain.entities.despachados.corrida import (
    OrigenCorrida,
    ResumenCorrida,
)
from src.modules.insumos.domain.entities.despachados.envio_seguido import EnvioSeguido
from src.modules.insumos.domain.value_objects.despachados.despacho_siges import DespachoSiges
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca
from tests.unit.application.insumos._offline_fakes import FakeExclusiveLock
from tests.unit.application.insumos.despachados.fakes_despachados import (
    AHORA,
    CONFIG,
    FakeCalendarioFeriados,
    FakeCorridasDespacho,
    FakeEnviosDespacho,
    FakeHistorialEstados,
    FakeRemitosDespacho,
)


class FakeDespachosSiges:
    def __init__(self, despachos: Sequence[DespachoSiges] = ()) -> None:
        self.despachos = list(despachos)
        self.error: Exception | None = None
        self.llamadas: list[tuple[int, tuple[int, ...]]] = []

    async def listar_despachos_oca(
        self, *, dias_ventana: int, distribuciones: tuple[int, ...]
    ) -> list[DespachoSiges]:
        self.llamadas.append((dias_ventana, distribuciones))
        if self.error is not None:
            raise self.error
        return list(self.despachos)


Respuesta = EstadoOca | None | Exception


class FakeOcaSeguimiento:
    """Responde según `respuestas` (una excepción se lanza); `al_responder` simula lo que
    pasa en HDM mientras OCA contesta (p. ej. un operador cierra una alerta)."""

    def __init__(self, eventos: list[str]) -> None:
        self.respuestas: dict[str, Respuesta] = {}
        self.al_responder: Callable[[str], Awaitable[None]] | None = None
        self._eventos = eventos

    async def consultar_estado_actual(self, guia: str) -> EstadoOca | None:
        self._eventos.append(f"oca {guia}")
        if self.al_responder is not None:
            await self.al_responder(guia)
        respuesta = self.respuestas.get(guia)
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta


class MundoSincronizacion:
    """Todos los puertos de `SincronizarDespachos` en memoria. `eventos` registra en orden
    las consultas a OCA, las pausas, las actualizaciones de envíos, el final de la corrida,
    las confirmaciones y las reversiones."""

    def __init__(self, *, envios: Sequence[EnvioSeguido] = (), candado_libre: bool = True) -> None:
        self.eventos: list[str] = []
        self.siges = FakeDespachosSiges()
        self.oca = FakeOcaSeguimiento(self.eventos)
        self.envios = FakeEnviosDespacho(envios, self.eventos)
        self.remitos = FakeRemitosDespacho(self.envios)
        self.historial = FakeHistorialEstados()
        self.corridas = FakeCorridasDespacho(self.eventos)
        self.feriados = FakeCalendarioFeriados()
        self.candado = FakeExclusiveLock(candado_libre)
        self.ahora = AHORA

    async def confirmar(self) -> None:
        self.eventos.append("confirmar")

    async def revertir(self) -> None:
        self.eventos.append("revertir")

    async def pausar(self, segundos: float) -> None:
        self.eventos.append(f"pausa {segundos}")

    def caso_de_uso(self, config: ConfigSincronizacion = CONFIG) -> SincronizarDespachos:
        ports = SincronizarDespachosPorts(
            siges=self.siges,
            oca=self.oca,
            envios=self.envios,
            remitos=self.remitos,
            historial=self.historial,
            corridas=self.corridas,
            feriados=self.feriados,
            candado=self.candado,
            confirmar=self.confirmar,
            revertir=self.revertir,
            reloj=lambda: self.ahora,
            pausar=self.pausar,
        )
        return SincronizarDespachos(ports, config)

    async def correr(self, origen: OrigenCorrida = OrigenCorrida.PROGRAMADA) -> ResumenCorrida:
        return await self.caso_de_uso().execute(origen)


def mensajes_de_log(caplog: pytest.LogCaptureFixture, texto: str) -> list[str]:
    """Mensajes capturados que contienen `texto`."""
    return [r.getMessage() for r in caplog.records if texto in r.getMessage()]
