"""Casos de uso del vínculo y sync de configuración contra Siges (ADR-014).

Política del ADR, no negociable acá:
- El sync **solo actualiza campos espejo de filas ya vinculadas** (hoy: `cuit`
  de prestadores). Nunca crea, desactiva ni borra; las empresas de Siges sin
  vínculo local se reportan como disponibles.
- El nombre local es curado a mano: si difiere del `Den_Comercial` de Siges se
  reporta como diferencia informativa, sin escribir.
- Dry-run first-class: `dry_run=True` calcula el mismo resultado sin persistir.
"""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.dtos.siges_config import (
    PropuestasVinculoResultado,
    PropuestaVinculo,
    SigesEmpresaDisponible,
    SyncCambio,
    SyncDiferenciaNombre,
    SyncSigesResultado,
)
from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.entities.spst import Spst
from src.modules.liquidaciones.domain.errors import (
    PrestadorNoEncontradoError,
    SpstNoEncontradoError,
)
from src.modules.liquidaciones.domain.repositories.prestador_repository import (
    PrestadorRepository,
)
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCatalogoGateway,
    SigesEmpresaInfo,
)
from src.modules.liquidaciones.domain.repositories.spst_repository import SpstRepository
from src.modules.liquidaciones.domain.services.vinculacion_siges import (
    normalizar_nombre,
    proponer_vinculos,
)


@dataclass(frozen=True)
class SigesConfigPorts:
    prestadores: PrestadorRepository
    spsts: SpstRepository
    siges: SigesCatalogoGateway


def _solo_digitos(cuit: str | None) -> str:
    return "".join(ch for ch in (cuit or "") if ch.isdigit())


class ProponerVinculosSiges:
    """Matching de alta confianza local↔Siges para filas aún sin vincular; la
    confirmación de cada propuesta es manual (endpoint de vínculo)."""

    def __init__(self, ports: SigesConfigPorts) -> None:
        self._ports = ports

    async def execute(self) -> PropuestasVinculoResultado:
        empresas = await self._ports.siges.list_empresas_activas()
        prestadores = await self._ports.prestadores.list_all()
        spsts = await self._ports.spsts.list_all()

        vinculados = {p.siges_empresa_id for p in prestadores if p.siges_empresa_id} | {
            s.siges_empresa_id for s in spsts if s.siges_empresa_id
        }
        candidatos = [e for e in empresas if e.siges_empresa_id not in vinculados]

        propuestas = self._proponer(prestadores, spsts, candidatos)
        propuestos = {p.siges_empresa_id for p in propuestas}
        disponibles = [
            SigesEmpresaDisponible(
                siges_empresa_id=e.siges_empresa_id,
                den_comercial=e.den_comercial,
                razon_social=e.razon_social,
                cuit=e.cuit,
                tipo=e.tipo,
            )
            for e in candidatos
            if e.siges_empresa_id not in propuestos
        ]
        return PropuestasVinculoResultado(propuestas=propuestas, disponibles=disponibles)

    def _proponer(
        self,
        prestadores: list[Prestador],
        spsts: list[Spst],
        candidatos: list[SigesEmpresaInfo],
    ) -> list[PropuestaVinculo]:
        den_por_id = {e.siges_empresa_id: e.den_comercial for e in candidatos}
        pst = [e for e in candidatos if e.tipo == "PST"]
        spst = [e for e in candidatos if e.tipo == "SPST"]
        matches_p = proponer_vinculos(
            [(p.id, p.nombre) for p in prestadores if p.siges_empresa_id is None], pst
        )
        matches_s = proponer_vinculos(
            [(s.id, s.nombre) for s in spsts if s.siges_empresa_id is None], spst
        )
        nombres_p = {p.id: p.nombre for p in prestadores}
        nombres_s = {s.id: s.nombre for s in spsts}
        return [
            PropuestaVinculo("prestador", pid, nombres_p[pid], sid, den_por_id[sid])
            for pid, sid in matches_p.items()
        ] + [
            PropuestaVinculo("spst", sid_local, nombres_s[sid_local], sid, den_por_id[sid])
            for sid_local, sid in matches_s.items()
        ]


class VincularPrestadorSiges:
    def __init__(self, ports: SigesConfigPorts) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID, *, siges_empresa_id: int | None) -> Prestador:
        actualizado = await self._ports.prestadores.vincular_siges(
            prestador_id, siges_empresa_id=siges_empresa_id
        )
        if actualizado is None:
            raise PrestadorNoEncontradoError(prestador_id)
        return actualizado


class VincularSpstSiges:
    def __init__(self, ports: SigesConfigPorts) -> None:
        self._ports = ports

    async def execute(self, spst_id: UUID, *, siges_empresa_id: int | None) -> Spst:
        actualizado = await self._ports.spsts.vincular_siges(
            spst_id, siges_empresa_id=siges_empresa_id
        )
        if actualizado is None:
            raise SpstNoEncontradoError(spst_id)
        return actualizado


class SyncConfigDesdeSiges:
    """Sincroniza los campos espejo de los prestadores vinculados (los SPST no
    tienen campos espejo — su vínculo alimenta los datasets siguientes del
    ADR-014, no este sync)."""

    def __init__(self, ports: SigesConfigPorts) -> None:
        self._ports = ports

    async def execute(self, *, dry_run: bool) -> SyncSigesResultado:
        por_id = {
            e.siges_empresa_id: e for e in await self._ports.siges.list_empresas_activas()
        }
        cambios: list[SyncCambio] = []
        nombres_distintos: list[SyncDiferenciaNombre] = []
        sin_cambios = 0
        sin_vinculo: list[str] = []
        vinculo_roto: list[str] = []

        for prestador in await self._ports.prestadores.list_all():
            if prestador.siges_empresa_id is None:
                sin_vinculo.append(prestador.nombre_corto)
                continue
            info = por_id.get(prestador.siges_empresa_id)
            if info is None:
                vinculo_roto.append(prestador.nombre_corto)
                continue
            if not await self._sync_prestador(prestador, info, cambios, dry_run=dry_run):
                sin_cambios += 1
            self._comparar_nombre(prestador, info, nombres_distintos)

        return SyncSigesResultado(
            dry_run=dry_run,
            cambios=cambios,
            nombres_distintos=nombres_distintos,
            sin_cambios=sin_cambios,
            sin_vinculo=sin_vinculo,
            vinculo_roto=vinculo_roto,
        )

    async def _sync_prestador(
        self,
        prestador: Prestador,
        info: SigesEmpresaInfo,
        cambios: list[SyncCambio],
        *,
        dry_run: bool,
    ) -> bool:
        """Devuelve True si registró un cambio. `cuit` es campo espejo: se pisa
        con el valor de Siges salvo que Siges no lo tenga (nunca se borra)."""
        if info.cuit is None or _solo_digitos(info.cuit) == _solo_digitos(prestador.cuit):
            return False
        cambios.append(
            SyncCambio(
                local_id=prestador.id,
                local_nombre=prestador.nombre_corto,
                campo="cuit",
                valor_anterior=prestador.cuit,
                valor_nuevo=info.cuit,
            )
        )
        if not dry_run:
            await self._ports.prestadores.update(
                prestador.id,
                nombre=prestador.nombre,
                nombre_corto=prestador.nombre_corto,
                cuit=info.cuit,
                region=prestador.region,
            )
        return True

    def _comparar_nombre(
        self,
        prestador: Prestador,
        info: SigesEmpresaInfo,
        nombres_distintos: list[SyncDiferenciaNombre],
    ) -> None:
        if normalizar_nombre(prestador.nombre) == normalizar_nombre(info.den_comercial):
            return
        nombres_distintos.append(
            SyncDiferenciaNombre(
                local_id=prestador.id,
                local_nombre=prestador.nombre,
                siges_den_comercial=info.den_comercial,
            )
        )
