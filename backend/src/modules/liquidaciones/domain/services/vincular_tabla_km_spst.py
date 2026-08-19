"""Propuesta de vínculo Tabla KM ↔ SPST por coincidencia de localidad/zona.

Resuelve el caso en que la Tabla KM de un prestador se importó antes de que
existiera el SPST correspondiente: sin `TablaKm.spst_id`, `resolver_zona`
(`motor_reglas/_resolucion.py`) nunca puede devolver una zona distinta de la
genérica, aunque el tarifario de esa zona ya esté cargado y mapeado."""

import unicodedata
from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.entities.spst import Spst
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm


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


def proponer_vinculos_spst(
    filas: list[TablaKm], spsts: list[Spst]
) -> list[PropuestaVinculoSpst]:
    """Solo filas sin `spst_id`. Propone el único SPST del prestador cuya zona
    (o localidad, si no tiene zona) — normalizada sin acentos — sea substring de
    la localidad del cliente o viceversa. Ambiguo (más de un candidato) o sin
    texto para comparar = sin propuesta, queda para vínculo manual."""
    candidatos = [
        (s, _normalizar(s.zona or s.localidad or "")) for s in spsts if s.zona or s.localidad
    ]
    return [_proponer_una(fila, candidatos) for fila in filas if fila.spst_id is None]


def _proponer_una(
    fila: TablaKm, candidatos: list[tuple[Spst, str]]
) -> PropuestaVinculoSpst:
    localidad = _normalizar(fila.localidad_cliente or "")
    match = _match_unico(localidad, candidatos) if localidad else None
    return PropuestaVinculoSpst(
        tabla_km_id=fila.id,
        empresa_nombre=fila.empresa_nombre,
        sucursal_nombre=fila.sucursal_nombre,
        localidad_cliente=fila.localidad_cliente,
        spst_id=match.id if match else None,
        spst_nombre=match.nombre if match else None,
    )


def _match_unico(localidad: str, candidatos: list[tuple[Spst, str]]) -> Spst | None:
    coincidencias = [
        s for s, texto in candidatos if texto and (texto in localidad or localidad in texto)
    ]
    return coincidencias[0] if len(coincidencias) == 1 else None
