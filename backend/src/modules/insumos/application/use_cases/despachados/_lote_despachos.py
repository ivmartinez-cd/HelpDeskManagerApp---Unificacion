"""Los dos pasos de una corrida de Despachados: incorporar las guías que despachó Siges y
consultar en OCA el estado de los envíos abiertos.

Los errores de Siges y de OCA (`ExternalServiceError`) no cortan la corrida: el gateway ya
logueó el detalle, acá queda una línea con la guía y el error en el envío o en el resumen.
Cualquier otro error sí la corta (lo maneja `SincronizarDespachos`).
"""

import logging
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from src.modules.insumos.application.use_cases.despachados._contexto_corrida import (
    armar_contexto,
)
from src.modules.insumos.application.use_cases.despachados.puertos_sincronizacion import (
    ConfigSincronizacion,
    SincronizarDespachosPorts,
)
from src.modules.insumos.domain.entities.despachados.corrida import ResumenCorrida
from src.modules.insumos.domain.services.despachados.seguimiento import (
    MomentoConsulta,
    ResultadoConsulta,
    aplicar_consulta,
    nuevo_envio,
    registrar_error,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import (
    ContextoClasificacion,
)
from src.modules.insumos.domain.value_objects.despachados.despacho_siges import DespachoSiges
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)


@dataclass
class AvanceCorrida:
    """Lo que la corrida lleva hecho; si se corta, se guarda lo que llegó a hacer."""

    envios_nuevos: int = 0
    consultas_ok: int = 0
    consultas_error: int = 0
    error: str | None = None

    def agregar_error(self, mensaje: str) -> None:
        self.error = mensaje if self.error is None else f"{self.error}; {mensaje}"

    def a_resumen(self) -> ResumenCorrida:
        return ResumenCorrida(
            envios_nuevos=self.envios_nuevos,
            consultas_ok=self.consultas_ok,
            consultas_error=self.consultas_error,
            error=self.error,
        )


class LoteDespachos:
    """Una corrida: se crea una instancia por corrida (acumula el avance)."""

    def __init__(self, ports: SincronizarDespachosPorts, config: ConfigSincronizacion) -> None:
        self._ports = ports
        self._config = config
        self.avance = AvanceCorrida()

    async def ejecutar(self) -> None:
        contexto = await armar_contexto(self._ports, self._config)
        await self._incorporar(contexto)
        await self._consultar_abiertos(contexto)

    async def _incorporar(self, contexto: ContextoClasificacion) -> None:
        """Alta de las guías nuevas y alta/actualización de todos los remitos leídos."""
        despachos = await self._leer_siges()
        if despachos is None:
            return
        por_guia = _agrupar_por_guia(despachos)
        seguidas = await self._ports.envios.guias_seguidas(por_guia.keys())
        nuevos = [
            nuevo_envio(grupo, contexto) for guia, grupo in por_guia.items() if guia not in seguidas
        ]
        await self._ports.envios.crear(nuevos)
        await self._ports.remitos.guardar(despachos)
        await self._ports.confirmar()
        self.avance.envios_nuevos = len(nuevos)

    async def _leer_siges(self) -> list[DespachoSiges] | None:
        """None si Siges no respondió: igual se consultan en OCA los envíos abiertos."""
        try:
            return await self._ports.siges.listar_despachos_oca(
                dias_ventana=self._config.dias_ventana,
                distribuciones=self._config.distribuciones,
            )
        except ExternalServiceError as exc:
            logger.warning(
                "Despachados: no se pudo leer Siges (%s); se consultan igual los envíos abiertos",
                exc.message,
            )
            self.avance.agregar_error(f"No se pudo leer Siges: {exc.message}")
            return None

    async def _consultar_abiertos(self, contexto: ContextoClasificacion) -> None:
        """De a una guía, con una pausa entre consulta y consulta a OCA."""
        abiertos = await self._ports.envios.listar_abiertos()
        for indice, envio in enumerate(abiertos):
            if indice:
                await self._ports.pausar(self._config.pausa_segundos)
            await self._consultar(envio.guia, contexto)

    async def _consultar(self, guia: str, contexto: ContextoClasificacion) -> None:
        try:
            estado = await self._ports.oca.consultar_estado_actual(guia)
        except ExternalServiceError as exc:
            await self._registrar_fallo(guia, exc.message, contexto)
            return
        await self._aplicar(guia, estado, contexto)

    async def _registrar_fallo(
        self, guia: str, mensaje: str, contexto: ContextoClasificacion
    ) -> None:
        logger.warning(
            "Despachados: falló la consulta a OCA de la guía %s (%s); se sigue con la próxima",
            guia,
            mensaje,
        )
        self.avance.consultas_error += 1
        envio = await self._ports.envios.obtener(guia)
        if envio is None:
            return
        con_error = registrar_error(envio, mensaje, self._momento(contexto))
        await self._ports.envios.actualizar(con_error)
        await self._ports.confirmar()

    async def _aplicar(
        self, guia: str, estado: EstadoOca | None, contexto: ContextoClasificacion
    ) -> None:
        """Relee el envío justo antes de aplicar la respuesta: el listado de abiertos es de
        antes de la primera consulta y un operador pudo cerrar la alerta entretanto."""
        envio = await self._ports.envios.obtener(guia)
        if envio is None:
            logger.warning("Despachados: la guía %s dejó de estar seguida durante la corrida", guia)
            return
        resultado = aplicar_consulta(envio, estado, self._momento(contexto))
        if resultado.cambio_estado and estado is not None:
            color = resultado.envio.clasificacion.color
            await self._ports.historial.registrar(guia, estado, color)
        _avisar_estado_desconocido(resultado)
        await self._ports.envios.actualizar(resultado.envio)
        await self._ports.confirmar()
        self.avance.consultas_ok += 1

    def _momento(self, contexto: ContextoClasificacion) -> MomentoConsulta:
        return MomentoConsulta(ahora=self._ports.reloj(), contexto=contexto)


def _agrupar_por_guia(despachos: Sequence[DespachoSiges]) -> dict[str, list[DespachoSiges]]:
    por_guia: defaultdict[str, list[DespachoSiges]] = defaultdict(list)
    for despacho in despachos:
        por_guia[despacho.guia].append(despacho)
    return dict(por_guia)


def _avisar_estado_desconocido(resultado: ResultadoConsulta) -> None:
    """Un estado fuera del catálogo del semáforo queda en amarillo/naranja "Estado nuevo,
    revisar": el log es para que alguien lo sume a las reglas."""
    envio = resultado.envio
    estado = envio.estado_oca
    if estado is None or not envio.clasificacion.estado_desconocido:
        return
    logger.warning(
        "Despachados: la guía %s tiene un estado de OCA fuera del catálogo (IdEstado %s, "
        "estado %r, motivo %r); revisar y sumarlo a las reglas del semáforo",
        envio.guia,
        estado.id_estado,
        estado.estado,
        estado.motivo,
    )
