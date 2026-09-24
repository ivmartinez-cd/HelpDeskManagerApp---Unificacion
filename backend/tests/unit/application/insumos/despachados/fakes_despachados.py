"""Fakes en memoria de los puertos de Insumos > Despachados y datos de prueba (los de Siges,
OCA y el mundo de `SincronizarDespachos` están en `fakes_sincronizacion.py`).

Calendario de referencia: `AHORA` es el jueves 24/09/2026 a las 12:00 en Argentina; el
lunes 12/10/2026 es feriado.

Los fakes de remitos y de corridas reproducen las reglas de la base de las que depende el
orden del flujo (la FK de remito a envío y el cierre de toda corrida sin terminar): si no,
un caso de uso que las viola pasa los tests unit y falla recién en producción.
"""

from collections.abc import Collection, Sequence
from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from src.modules.insumos.application.use_cases.despachados.sincronizar_despachos import (
    ConfigSincronizacion,
)
from src.modules.insumos.domain.entities.despachados.accion_registrada import (
    AccionNueva,
    AccionRegistrada,
)
from src.modules.insumos.domain.entities.despachados.corrida import (
    Corrida,
    OrigenCorrida,
    ResumenCorrida,
)
from src.modules.insumos.domain.entities.despachados.envio_seguido import (
    CierreAlerta,
    EnvioSeguido,
)
from src.modules.insumos.domain.value_objects.despachados.cambio_estado import CambioEstado
from src.modules.insumos.domain.value_objects.despachados.clasificacion import (
    ClasificacionEnvio,
    ColorSemaforo,
)
from src.modules.insumos.domain.value_objects.despachados.despacho_siges import (
    DespachoSiges,
    IncidenteInsumo,
)
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca

AHORA = datetime(2026, 9, 24, 15, 0, tzinfo=UTC)
HOY = date(2026, 9, 24)
ARGENTINA = ZoneInfo("America/Argentina/Buenos_Aires")
FERIADOS_2026 = frozenset({date(2026, 10, 12)})
GUIA_A = "3867500000000000001"
GUIA_B = "3867500000000000002"
GUIA_C = "3867500000000000003"
USUARIO_ID = UUID("00000000-0000-0000-0000-00000000000a")

CONFIG = ConfigSincronizacion(
    dias_ventana=30,
    distribuciones=(3, 9, 10),
    dias_sin_movimiento=3,
    pausa_segundos=0.3,
    zona_horaria=ARGENTINA,
)

VERDE = ClasificacionEnvio(
    color=ColorSemaforo.VERDE,
    alerta=False,
    abierto=True,
    fecha_limite=None,
    observacion="",
    estado_desconocido=False,
)


def despacho(guia: str = GUIA_A, id_remito: int = 1, **cambios: Any) -> DespachoSiges:
    base = DespachoSiges(
        id_remito=id_remito,
        numero_remito=50000 + id_remito,
        guia=guia,
        id_distribucion=3,
        fecha_remito=date(2026, 9, 23),
        bultos=1,
        cliente="Cliente Test",
        sucursal_cliente="Casa Central",
        entrega_a="Recepción",
        incidentes=(IncidenteInsumo(numero=f"44{id_remito:04d}", numero_cliente=""),),
    )
    return replace(base, **cambios)


def estado_oca(guia: str = GUIA_A, **cambios: Any) -> EstadoOca:
    """En viaje (IdEstado 10, verde) con `FechaEstado` el miércoles 23/09/2026."""
    base = EstadoOca(
        numero_envio=guia,
        operativa="434324",
        orden_retiro="",
        sucursal_actual="Rosario",
        fecha_estado=date(2026, 9, 23),
        estado="En viaje a Centro de Distribución de Destino",
        id_estado=10,
        motivo="Sin Motivo",
        cantidad_paquetes=1,
    )
    return replace(base, **cambios)


def envio(guia: str = GUIA_A, **cambios: Any) -> EnvioSeguido:
    """Envío abierto en verde, con remito del martes 22/09/2026 y sin datos de OCA."""
    base = EnvioSeguido(
        guia=guia,
        id_distribucion=3,
        fecha_remito=date(2026, 9, 22),
        cliente="Cliente Test",
        sucursal_cliente="Casa Central",
        clasificacion=VERDE,
    )
    return replace(base, **cambios)


class FakeEnviosDespacho:
    """`eventos`, si se pasa, anota cada `actualizar` para verificar su orden respecto de las
    confirmaciones; `cierres` guarda lo que se escribió con `registrar_cierre_alerta`."""

    def __init__(
        self, envios: Sequence[EnvioSeguido] = (), eventos: list[str] | None = None
    ) -> None:
        self.envios = {e.guia: e for e in envios}
        self.creados: list[EnvioSeguido] = []
        self.actualizados: list[EnvioSeguido] = []
        self.cierres: list[tuple[str, CierreAlerta]] = []
        self._eventos = [] if eventos is None else eventos

    async def guias_seguidas(self, guias: Collection[str]) -> set[str]:
        return {guia for guia in guias if guia in self.envios}

    async def crear(self, envios: Sequence[EnvioSeguido]) -> None:
        self.creados.extend(envios)
        for nuevo in envios:
            self.envios.setdefault(nuevo.guia, nuevo)

    async def listar_abiertos(self) -> list[EnvioSeguido]:
        abiertos = [e for e in self.envios.values() if e.clasificacion.abierto]
        return sorted(abiertos, key=lambda e: (e.fecha_remito, e.guia))

    async def obtener(self, guia: str) -> EnvioSeguido | None:
        return self.envios.get(guia)

    async def actualizar(self, envio: EnvioSeguido) -> None:
        self._eventos.append(f"actualizar {envio.guia}")
        self.actualizados.append(envio)
        self.envios[envio.guia] = envio

    async def registrar_cierre_alerta(self, guia: str, cierre: CierreAlerta) -> None:
        self.cierres.append((guia, cierre))
        if guia in self.envios:
            self.envios[guia] = replace(self.envios[guia], cierre_alerta=cierre)


class ClaveForaneaVioladaError(Exception):
    """Lo que en la base es un `IntegrityError` por la FK de remito a envío."""


class FakeRemitosDespacho:
    """Con `envios`, rechaza como la FK de la base el remito de una guía sin envío."""

    def __init__(self, envios: FakeEnviosDespacho | None = None) -> None:
        self.guardados: list[DespachoSiges] = []
        self._envios = envios

    async def guardar(self, despachos: Sequence[DespachoSiges]) -> None:
        if self._envios is not None:
            sin_envio = sorted({d.guia for d in despachos} - self._envios.envios.keys())
            if sin_envio:
                raise ClaveForaneaVioladaError(f"remitos de guías sin envío: {sin_envio}")
        self.guardados.extend(despachos)

    async def listar_por_guia(self, guia: str) -> list[DespachoSiges]:
        return [d for d in self.guardados if d.guia == guia]


class FakeHistorialEstados:
    def __init__(self) -> None:
        self.registros: list[tuple[str, EstadoOca, ColorSemaforo]] = []

    async def registrar(self, guia: str, estado: EstadoOca, color: ColorSemaforo) -> None:
        self.registros.append((guia, estado, color))

    async def listar_por_guia(self, guia: str) -> list[CambioEstado]:
        return []


class FakeCorridasDespacho:
    """`iniciadas` guarda cada corrida como se inició y `terminadas` el resumen con que se
    cerró; `ultima()` las combina como la base (con `terminada_en` si ya se cerró).
    `eventos`, si se pasa, anota cada `terminar`."""

    def __init__(self, eventos: list[str] | None = None) -> None:
        self.iniciadas: list[Corrida] = []
        self.terminadas: dict[int, ResumenCorrida] = {}
        self.interrumpidas: list[str] = []
        self.error_al_terminar: Exception | None = None
        self._eventos = [] if eventos is None else eventos

    async def iniciar(self, origen: OrigenCorrida, usuario_nombre: str | None) -> Corrida:
        corrida = Corrida(len(self.iniciadas) + 1, origen, AHORA, usuario_nombre)
        self.iniciadas.append(corrida)
        return corrida

    async def terminar(self, corrida_id: int, resumen: ResumenCorrida) -> None:
        self._eventos.append(f"terminar corrida {corrida_id}")
        if self.error_al_terminar is not None:
            raise self.error_al_terminar
        self.terminadas[corrida_id] = resumen

    async def cerrar_interrumpidas(self, motivo: str) -> int:
        """Como la base: cierra TODA corrida sin terminar, también una recién iniciada."""
        self.interrumpidas.append(motivo)
        colgadas = [c.id for c in self.iniciadas if c.id not in self.terminadas]
        for corrida_id in colgadas:
            self.terminadas[corrida_id] = ResumenCorrida(error=motivo)
        return len(colgadas)

    async def ultima(self) -> Corrida | None:
        if not self.iniciadas:
            return None
        corrida = self.iniciadas[-1]
        resumen = self.terminadas.get(corrida.id)
        if resumen is None:
            return corrida
        return replace(corrida, terminada_en=AHORA, resumen=resumen)

    async def ultima_terminada(self) -> Corrida | None:
        return None


class FakeCalendarioFeriados:
    def __init__(self, feriados: frozenset[date] = FERIADOS_2026) -> None:
        self.feriados = feriados
        self.consultas: list[tuple[date, date]] = []

    async def feriados_entre(self, desde: date, hasta: date) -> frozenset[date]:
        self.consultas.append((desde, hasta))
        return frozenset(f for f in self.feriados if desde <= f <= hasta)


class FakeAccionesDespacho:
    def __init__(self) -> None:
        self.acciones: list[AccionRegistrada] = []

    async def agregar(self, accion: AccionNueva) -> AccionRegistrada:
        registrada = AccionRegistrada(
            id=len(self.acciones) + 1,
            guia=accion.guia,
            tipo=accion.tipo,
            detalle=accion.detalle,
            resultado=accion.resultado,
            cerro_alerta=accion.cerro_alerta,
            usuario_id=accion.usuario_id,
            usuario_nombre=accion.usuario_nombre,
            creada_en=AHORA,
        )
        self.acciones.append(registrada)
        return registrada

    async def listar_por_guia(self, guia: str) -> list[AccionRegistrada]:
        return [a for a in reversed(self.acciones) if a.guia == guia]
