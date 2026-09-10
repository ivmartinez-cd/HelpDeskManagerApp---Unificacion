"""Traduce un `DiffIncidentes` a filas de `ModificacionPrestador` y las persiste
— colaborador de `_reconciliar_liquidacion.py`, separado por el límite de
tamaño de archivo (§4). Se llama ANTES de aplicar el diff (`update_cobrados`/
`delete_by_ids`), momento en el que el valor anterior todavía existe — por eso
recibe `locales` (para resolver `numero_incidente` de una baja: `diff.bajas`
solo trae el `incidente_id`, que después de borrar deja de servir para mostrarle
algo a la TL).

Guard de reenvío masivo: si el prestador reenvía toda la liquidación, un evento
por campo por incidente sería ruido — por encima de `_UMBRAL_RESUMEN` de
incidentes tocados se registra un único evento resumen en vez de N×M filas
(mismo criterio que `_UMBRAL_BAJAS_MASIVAS` en `_reconciliar_liquidacion.py`)."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.modificacion_prestador import (
    TIPO_ALTA,
    TIPO_BAJA,
    TIPO_MODIFICACION,
    ModificacionPrestador,
)
from src.modules.liquidaciones.domain.repositories.modificacion_prestador_repository import (
    ModificacionPrestadorRepository,
)
from src.modules.liquidaciones.domain.services.reconciliar_incidentes import DiffIncidentes
from src.modules.liquidaciones.domain.value_objects.campo_modificado import CampoModificado
from src.modules.liquidaciones.domain.value_objects.incidente_importado import IncidenteImportado

_UMBRAL_RESUMEN = 20


async def registrar_modificaciones(
    repo: ModificacionPrestadorRepository,
    liquidacion_id: UUID,
    diff: DiffIncidentes,
    locales: Sequence[Incidente],
) -> None:
    incidentes_tocados = len(diff.altas) + len(diff.bajas) + len(diff.modificaciones)
    if incidentes_tocados == 0:
        return
    if incidentes_tocados > _UMBRAL_RESUMEN:
        await repo.bulk_create([_resumen(liquidacion_id, incidentes_tocados)])
        return
    await repo.bulk_create(_filas(liquidacion_id, diff, locales))


def _filas(
    liquidacion_id: UUID, diff: DiffIncidentes, locales: Sequence[Incidente]
) -> list[ModificacionPrestador]:
    numero_por_id = {i.id: i.numero_incidente for i in locales}
    filas = [_alta(liquidacion_id, alta) for alta in diff.altas]
    filas += [
        _baja(liquidacion_id, numero_por_id.get(incidente_id, str(incidente_id)))
        for incidente_id in diff.bajas
    ]
    for modificado in diff.modificaciones:
        filas += [
            _campo(liquidacion_id, modificado.numero_incidente, campo)
            for campo in modificado.campos
        ]
    return filas


def _base(liquidacion_id: UUID, numero_incidente: str, tipo_cambio: str) -> dict[str, object]:
    return {
        "id": uuid.uuid4(),
        "liquidacion_id": liquidacion_id,
        "numero_incidente": numero_incidente,
        "tipo_cambio": tipo_cambio,
        "detectada_en": datetime.now(UTC),
        "vista_en": None,
    }


def _alta(liquidacion_id: UUID, alta: IncidenteImportado) -> ModificacionPrestador:
    return ModificacionPrestador(
        **_base(liquidacion_id, alta.numero_incidente, TIPO_ALTA),
        campo=None,
        valor_anterior=None,
        valor_nuevo=None,
    )


def _baja(liquidacion_id: UUID, numero_incidente: str) -> ModificacionPrestador:
    return ModificacionPrestador(
        **_base(liquidacion_id, numero_incidente, TIPO_BAJA),
        campo=None,
        valor_anterior=None,
        valor_nuevo=None,
    )


def _campo(
    liquidacion_id: UUID, numero_incidente: str, campo: CampoModificado
) -> ModificacionPrestador:
    return ModificacionPrestador(
        **_base(liquidacion_id, numero_incidente, TIPO_MODIFICACION),
        campo=campo.campo,
        valor_anterior=campo.valor_anterior,
        valor_nuevo=campo.valor_nuevo,
    )


def _resumen(liquidacion_id: UUID, cantidad: int) -> ModificacionPrestador:
    return ModificacionPrestador(
        **_base(liquidacion_id, "-", TIPO_MODIFICACION),
        campo="resumen",
        valor_anterior=None,
        valor_nuevo=f"{cantidad} incidentes modificados en un reenvío masivo",
    )
