"""Apply del cálculo de distancias PST↔sucursal (paso 2 de 2, ver
`preview_calcular_distancias.py` para el paso 1 — separados porque juntos
superaban el tamaño máximo de archivo, §4). Materializa la propuesta del
preview en tabla_km sin volver a llamar a Google."""

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    CalcularDistanciasPorts,
    maps_url_ida_vuelta,
    validar_prestador_para_distancias,
)
from src.modules.liquidaciones.domain.entities.calculo_km_preview import (
    ACCION_ACTUALIZAR,
    PreviewFila,
)
from src.modules.liquidaciones.domain.errors import PreviewNoEncontradoError
from src.modules.liquidaciones.domain.services.vincular_tabla_km_spst import (
    proponer_vinculos_spst,
)


@dataclass(frozen=True)
class AplicarDistanciasResultado:
    creadas: int
    actualizadas: int
    # Filas existentes con km ya cargado que se saltearon por `solo_sin_km`.
    omitidas: int = 0


class AplicarCalcularDistancias:
    def __init__(self, ports: CalcularDistanciasPorts) -> None:
        self._ports = ports

    async def execute(
        self, preview_id: UUID, *, solo_sin_km: bool = False
    ) -> AplicarDistanciasResultado:
        """`solo_sin_km`: completa solo las filas sin km de referencia (nuevas o con
        `kms_a_facturar` 0) y no pisa las que la TL ya negoció — modo de la pasada
        masiva 2026-09-05, donde 706 filas tenían km medido ≠ facturado."""
        preview = await self._ports.previews.get_by_id(preview_id)
        if preview is None:
            raise PreviewNoEncontradoError(preview_id)
        await validar_prestador_para_distancias(self._ports.prestadores, preview.prestador_id)
        resultado = await self._aplicar_filas(preview.prestador_id, preview.filas, solo_sin_km)
        await self._ports.previews.delete(preview_id)
        if resultado.creadas:
            # Las filas nuevas nacen sin SPST (el cálculo de distancias no lo
            # sabe) — sin esto quedarían sin zona/tarifa hasta que alguien lo
            # notara a mano. Mismo criterio "único candidato" del botón manual.
            await self._vincular_spst_nuevas(preview.prestador_id)
        return resultado

    async def _aplicar_filas(
        self, prestador_id: UUID, filas: Sequence[PreviewFila], solo_sin_km: bool
    ) -> AplicarDistanciasResultado:
        creadas = actualizadas = omitidas = 0
        for fila in filas:
            if solo_sin_km and _ya_tiene_km(fila):
                omitidas += 1
                continue
            c, a = await self._aplicar_fila(prestador_id, fila)
            creadas += c
            actualizadas += a
        return AplicarDistanciasResultado(creadas, actualizadas, omitidas)

    async def _vincular_spst_nuevas(self, prestador_id: UUID) -> None:
        filas = await self._ports.tabla_km.list_by_prestador(prestador_id)
        spsts = await self._ports.spsts.list_by_prestador(prestador_id)
        for propuesta in proponer_vinculos_spst(filas, spsts):
            if propuesta.spst_id is not None:
                await self._ports.tabla_km.update_vinculo_spst(
                    propuesta.tabla_km_id, spst_id=propuesta.spst_id
                )

    async def _aplicar_fila(self, prestador_id: UUID, fila: PreviewFila) -> tuple[int, int]:
        base = (fila.latitud_base, fila.longitud_base)
        url = maps_url_ida_vuelta(
            base,
            (fila.latitud_destino, fila.longitud_destino),
            domicilio=fila.domicilio,
            localidad=fila.localidad,
            provincia=fila.provincia,
        )
        if fila.accion == ACCION_ACTUALIZAR and fila.tabla_km_id is not None:
            actualizada = await self._ports.tabla_km.update_distancias(
                fila.tabla_km_id,
                kms_ida=fila.kms_ida,
                kms_vuelta=fila.kms_vuelta,
                kms_recorrido=fila.kms_total,
                aplica_viatico=fila.aplica_viatico,
                kms_a_facturar=fila.kms_a_facturar,
                url_maps=url,
                latitud_destino=fila.latitud_destino,
                longitud_destino=fila.longitud_destino,
                coords_origen=fila.coords_origen,
                siges_sucursal_id=fila.siges_sucursal_id,
                id_costo_servicios=fila.id_costo_servicios,
            )
            return (0, 1) if actualizada else (0, 0)
        await self._crear_fila(prestador_id, fila, url)
        return 1, 0

    async def _crear_fila(self, prestador_id: UUID, fila: PreviewFila, url: str) -> None:
        await self._ports.tabla_km.create(
            prestador_id=prestador_id,
            spst_id=None,
            empresa_nombre=fila.empresa_nombre,
            sucursal_nombre=fila.sucursal_nombre,
            observaciones=None,
            domicilio_cliente=fila.domicilio,
            localidad_cliente=fila.localidad,
            provincia_cliente=fila.provincia,
            kms_recorrido=fila.kms_total,
            umbral_viatico=fila.umbral_viatico,
            aplica_viatico=fila.aplica_viatico,
            kms_a_facturar=fila.kms_a_facturar,
            url_maps=url,
            latitud_destino=fila.latitud_destino,
            longitud_destino=fila.longitud_destino,
            kms_ida=fila.kms_ida,
            kms_vuelta=fila.kms_vuelta,
            coords_origen=fila.coords_origen,
            siges_sucursal_id=fila.siges_sucursal_id,
            id_costo_servicios=fila.id_costo_servicios,
        )


def _ya_tiene_km(fila: PreviewFila) -> bool:
    return fila.accion == ACCION_ACTUALIZAR and (fila.kms_a_facturar_actual or 0) > 0
