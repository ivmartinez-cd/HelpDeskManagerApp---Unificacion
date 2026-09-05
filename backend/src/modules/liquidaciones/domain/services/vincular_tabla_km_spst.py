"""Propuesta de vínculo Tabla KM ↔ SPST por coincidencia de localidad/cobertura,
con la provincia como segundo criterio.

Resuelve el caso en que la Tabla KM de un prestador se importó antes de que
existiera el SPST correspondiente: sin `TablaKm.spst_id`, `resolver_tarifario`
(`motor_reglas/_resolucion.py`) nunca puede matchear un tarifario específico
de ese SPST, aunque ya esté cargado.

Orden: primero localidad del cliente contra zona de cobertura/localidad del
SPST (substring, sin acentos); si eso no da un único candidato, provincia del
cliente contra provincia del SPST (igualdad exacta normalizada). Caso real que
motivó el segundo criterio (INFOMAC, 2026-09-04): "Cipolletti" no es substring
de "Gral. Roca / Neuquén", pero la fila dice Río Negro y el único SPST de Río
Negro es Gral. Roca. Sigue siendo una propuesta: la confirma el dry-run."""

import unicodedata
from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.entities.spst import Spst
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm

CRITERIO_LOCALIDAD = "localidad"
CRITERIO_PROVINCIA = "provincia"


def _normalizar(texto: str) -> str:
    sin_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return sin_acentos.strip().lower()


@dataclass(frozen=True)
class PropuestaVinculoSpst:
    tabla_km_id: UUID
    empresa_nombre: str
    sucursal_nombre: str
    localidad_cliente: str | None
    spst_id: UUID | None
    spst_nombre: str | None
    # Cómo se llegó al SPST propuesto: `CRITERIO_LOCALIDAD` (zona/localidad del
    # SPST contra localidad del cliente) o `CRITERIO_PROVINCIA` (único SPST de
    # esa provincia — proxy más débil: la provincia no siempre coincide con la
    # zona tarifaria, ej. Plottier/Neuquén factura por Gral. Roca). `None` = sin
    # propuesta.
    criterio: str | None = None


def proponer_vinculos_spst(filas: list[TablaKm], spsts: list[Spst]) -> list[PropuestaVinculoSpst]:
    """Solo filas sin `spst_id`. Propone el único SPST del prestador cuya
    `zona_cobertura` (o localidad, si no tiene cobertura cargada) — normalizada
    sin acentos — sea substring de la localidad del cliente o viceversa.
    Ambiguo (más de un candidato) o sin texto para comparar = sin propuesta,
    queda para vínculo manual."""
    candidatos = [
        (s, _normalizar(s.zona_cobertura or s.localidad or ""))
        for s in spsts
        if s.zona_cobertura or s.localidad
    ]
    por_provincia: dict[str, list[Spst]] = {}
    for s in spsts:
        if s.provincia:
            por_provincia.setdefault(_normalizar(s.provincia), []).append(s)
    return [
        _proponer_una(fila, candidatos, por_provincia) for fila in filas if fila.spst_id is None
    ]


def _proponer_una(
    fila: TablaKm, candidatos: list[tuple[Spst, str]], por_provincia: dict[str, list[Spst]]
) -> PropuestaVinculoSpst:
    localidad = _normalizar(fila.localidad_cliente or "")
    match = _match_unico(localidad, candidatos) if localidad else None
    criterio = CRITERIO_LOCALIDAD if match else None
    if match is None:
        match = _match_provincia(fila.provincia_cliente, por_provincia)
        criterio = CRITERIO_PROVINCIA if match else None
    return PropuestaVinculoSpst(
        tabla_km_id=fila.id,
        empresa_nombre=fila.empresa_nombre,
        sucursal_nombre=fila.sucursal_nombre,
        localidad_cliente=fila.localidad_cliente,
        spst_id=match.id if match else None,
        spst_nombre=match.nombre if match else None,
        criterio=criterio,
    )


def _match_unico(localidad: str, candidatos: list[tuple[Spst, str]]) -> Spst | None:
    coincidencias = [
        s for s, texto in candidatos if texto and (texto in localidad or localidad in texto)
    ]
    return coincidencias[0] if len(coincidencias) == 1 else None


def _match_provincia(
    provincia_cliente: str | None, por_provincia: dict[str, list[Spst]]
) -> Spst | None:
    if not provincia_cliente:
        return None
    coincidencias = por_provincia.get(_normalizar(provincia_cliente), [])
    return coincidencias[0] if len(coincidencias) == 1 else None
