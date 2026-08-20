"""Matching de sucursales de Tabla KM ↔ Siges (Fase 1 del plan de matching +
geovalidación): N1 determinístico auto-vinculable (decisión 0.4.a) y
propuestas N2 difusas para confirmación humana (siempre, sin excepción).

N0 (igualdad con `normalizar_nombre`, existente) no se toca acá — sigue
siendo responsabilidad de `RefrescarDatosSiges`. Estos casos de uso operan
sobre las filas que YA pasaron por N0 y siguen sin vínculo."""

from dataclasses import dataclass, field
from uuid import UUID

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    validar_prestador_vinculado_siges,
)
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.repositories.matching_descarte_repository import (
    MatchingDescarteRepository,
)
from src.modules.liquidaciones.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCatalogoGateway,
    SigesSucursalCliente,
)
from src.modules.liquidaciones.domain.repositories.tabla_km_repository import TablaKmRepository
from src.modules.liquidaciones.domain.services.matching_sucursales_tabla_km import (
    CandidatoPropuesto,
    FilaSinMatch,
    proponer_matches_tabla_km,
)
from src.modules.liquidaciones.domain.services.vinculacion_siges import normalizar_nombre


@dataclass(frozen=True)
class MatchingSucursalesPorts:
    prestadores: PrestadorRepository
    tabla_km: TablaKmRepository
    siges: SigesCatalogoGateway
    descartes: MatchingDescarteRepository


async def _sin_match_n0(
    ports: MatchingSucursalesPorts, prestador_id: UUID
) -> tuple[list[TablaKm], list[SigesSucursalCliente]]:
    prestador = await validar_prestador_vinculado_siges(ports.prestadores, prestador_id)
    sucursales = await ports.siges.list_sucursales_de_prestador(prestador.siges_empresa_id)  # type: ignore[arg-type]
    claves_siges = {
        (normalizar_nombre(s.empresa_nombre), normalizar_nombre(s.sucursal_nombre))
        for s in sucursales
    }
    filas = await ports.tabla_km.list_by_prestador(prestador_id)
    # Una fila con siges_sucursal_id ya está vinculada (N1/N2/manual) aunque
    # su nombre no matchee textualmente — no es "sin match", no hay que
    # volver a proponerle candidatos (mismo criterio que el diagnóstico).
    sin_match = [
        f
        for f in filas
        if f.siges_sucursal_id is None
        and (normalizar_nombre(f.empresa_nombre), normalizar_nombre(f.sucursal_nombre))
        not in claves_siges
    ]
    return sin_match, sucursales


def _a_fila_sin_match(f: TablaKm) -> FilaSinMatch:
    # Domicilio/localidad locales alimentan el ancla por dirección (N2).
    return FilaSinMatch(
        f.id, f.empresa_nombre, f.sucursal_nombre, f.domicilio_cliente, f.localidad_cliente
    )


@dataclass(frozen=True)
class VinculoN1Aplicado:
    tabla_km_id: UUID
    empresa_nombre: str
    sucursal_nombre: str
    siges_sucursal_id: int


@dataclass(frozen=True)
class ResultadoAutoVinculoN1:
    vinculadas: int
    sin_cambios: int
    detalle: list[VinculoN1Aplicado] = field(default_factory=list)


class AutoVincularMatchesN1TablaKm:
    """Aplica en bloque los matches N1 (igualdad exacta bajo
    `normalizar_nombre_fuerte`) — aprobado para auto-vínculo (decisión 0.4.a),
    mismo nivel de confianza que el N0 existente. Idempotente: `_sin_match_n0`
    excluye toda fila con `siges_sucursal_id` ya asignado, así que re-correrlo
    sobre filas ya vinculadas no las vuelve a tocar (`sin_cambios` queda en 0
    salvo que se agregue otro camino de "sin cambios" en el futuro)."""

    def __init__(self, ports: MatchingSucursalesPorts) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID) -> ResultadoAutoVinculoN1:
        sin_match, sucursales = await _sin_match_n0(self._ports, prestador_id)
        filas_n1 = [_a_fila_sin_match(f) for f in sin_match]
        propuestas = proponer_matches_tabla_km(filas_n1, sucursales)
        por_id = {s.siges_sucursal_id: s for s in sucursales}
        por_fila = {f.id: f for f in sin_match}

        detalle: list[VinculoN1Aplicado] = []
        for fila_id, candidatos in propuestas.items():
            top = candidatos[0]
            if top.nivel != "N1":
                continue
            fila, siges = por_fila[fila_id], por_id[top.siges_sucursal_id]
            await self._ports.tabla_km.update_domicilio(
                fila.id,
                domicilio_cliente=siges.domicilio,
                localidad_cliente=siges.localidad,
                provincia_cliente=siges.provincia,
                siges_sucursal_id=siges.siges_sucursal_id,
                id_costo_servicios=siges.id_costo_servicios,
            )
            detalle.append(
                VinculoN1Aplicado(
                    fila.id, fila.empresa_nombre, fila.sucursal_nombre, siges.siges_sucursal_id
                )
            )
        return ResultadoAutoVinculoN1(len(detalle), 0, detalle)


@dataclass(frozen=True)
class CandidatoN2Detalle:
    siges_sucursal_id: int
    sucursal_nombre: str
    domicilio: str | None
    score: float
    motivo: str
    misma_direccion: bool


@dataclass(frozen=True)
class PropuestaN2:
    tabla_km_id: UUID
    empresa_nombre: str
    sucursal_nombre: str
    candidatos: list[CandidatoN2Detalle]


class ListarPropuestasN2TablaKm:
    """Read-only: candidatos difusos para las filas que N0 y N1 no pudieron
    resolver, excluyendo los ya descartados por un operador (decisión
    0.4.d). SIEMPRE requiere confirmación humana — este caso de uso nunca
    escribe nada."""

    def __init__(self, ports: MatchingSucursalesPorts) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID) -> list[PropuestaN2]:
        sin_match, sucursales = await _sin_match_n0(self._ports, prestador_id)
        filas = [_a_fila_sin_match(f) for f in sin_match]
        propuestas = proponer_matches_tabla_km(filas, sucursales)
        descartados = await self._ports.descartes.list_descartados_por_fila(
            [f.id for f in filas]
        )
        por_id = {s.siges_sucursal_id: s for s in sucursales}
        por_fila = {f.id: f for f in sin_match}

        resultado: list[PropuestaN2] = []
        for fila_id, candidatos in propuestas.items():
            n2 = _filtrar_n2(candidatos, descartados.get(fila_id, set()))
            if not n2:
                continue
            fila = por_fila[fila_id]
            resultado.append(
                PropuestaN2(
                    fila.id,
                    fila.empresa_nombre,
                    fila.sucursal_nombre,
                    [_a_detalle(c, por_id[c.siges_sucursal_id]) for c in n2],
                )
            )
        return resultado


def _filtrar_n2(
    candidatos: list[CandidatoPropuesto], descartados: set[int]
) -> list[CandidatoPropuesto]:
    return [c for c in candidatos if c.nivel == "N2" and c.siges_sucursal_id not in descartados]


def _a_detalle(candidato: CandidatoPropuesto, siges: SigesSucursalCliente) -> CandidatoN2Detalle:
    return CandidatoN2Detalle(
        siges.siges_sucursal_id,
        siges.sucursal_nombre,
        siges.domicilio,
        candidato.score,
        candidato.motivo,
        candidato.misma_direccion,
    )
