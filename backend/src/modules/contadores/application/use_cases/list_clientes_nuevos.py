"""Listado de fichas anotado con lo que Siges sabe de cada empresa cruzada.
Sin gateway (Siges no configurado) o si Siges falla, las fichas salen sin
anotación: el seguimiento manual de la TL no depende de MERCURIO."""

import logging
from dataclasses import dataclass
from datetime import date, timedelta

from src.modules.contadores.application.dtos.cliente_nuevo_dtos import (
    CandidatosClientesNuevosResult,
    ClienteNuevoResult,
)
from src.modules.contadores.application.use_cases._cliente_nuevo_mapper import (
    to_cliente_nuevo_result,
)
from src.modules.contadores.domain.entities.cliente_nuevo import ResumenSigesClienteNuevo
from src.modules.contadores.domain.repositories.cliente_nuevo_repository import (
    ClienteNuevoRepository,
)
from src.modules.contadores.domain.repositories.clientes_nuevos_siges_port import (
    ClientesNuevosSigesPort,
)
from src.modules.contadores.domain.services.rubro_empresa_admin import RUBRO_CARTELERIA
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)

DEFAULT_VENTANA_CANDIDATOS_DIAS = 120


@dataclass(frozen=True, slots=True)
class ListClientesNuevosDependencies:
    repo: ClienteNuevoRepository
    siges: ClientesNuevosSigesPort | None


class ListClientesNuevosUseCase:
    def __init__(self, deps: ListClientesNuevosDependencies) -> None:
        self._deps = deps

    async def execute(self, *, force_refresh: bool = False) -> list[ClienteNuevoResult]:
        fichas = await self._deps.repo.list_all()
        ids = frozenset(f.siges_empresa_id for f in fichas if f.siges_empresa_id is not None)
        resumen = await self._resumen(ids, force_refresh)
        return [
            to_cliente_nuevo_result(
                f, resumen.get(f.siges_empresa_id) if f.siges_empresa_id is not None else None
            )
            for f in fichas
        ]

    async def _resumen(
        self, ids: frozenset[int], force_refresh: bool
    ) -> dict[int, ResumenSigesClienteNuevo]:
        if self._deps.siges is None or not ids:
            return {}
        try:
            return await self._deps.siges.resumen_por_empresa(ids, force_refresh=force_refresh)
        except ExternalServiceError as exc:
            # Fallback consciente: el listado sale sin anotación de Siges en
            # vez de romper la pantalla de la TL (ARCHITECTURE_GUIDE §6).
            logger.warning(
                "Siges no respondió; las fichas de clientes nuevos van sin instalaciones",
                extra={"empresas": len(ids)},
                exc_info=exc,
            )
            return {}


class ListCandidatosClientesNuevosUseCase:
    """Empresas de Siges con primer contrato reciente que todavía no tienen
    ficha — para que la TL las cargue con un clic en vez de tipear el mail.
    Los contratos de cartelería (CD4/Directar) no son de Contadores: se
    excluyen (pedido del usuario 2026-08-21)."""

    def __init__(self, deps: ListClientesNuevosDependencies) -> None:
        self._deps = deps

    async def execute(
        self, *, hoy: date, dias: int = DEFAULT_VENTANA_CANDIDATOS_DIAS, force_refresh: bool = False
    ) -> CandidatosClientesNuevosResult:
        desde = hoy - timedelta(days=dias)
        if self._deps.siges is None:
            return CandidatosClientesNuevosResult(candidatos=[], firmado_desde=desde)
        candidatos = await self._deps.siges.candidatos_desde(desde, force_refresh=force_refresh)
        con_ficha = await self._deps.repo.list_siges_empresa_ids()
        return CandidatosClientesNuevosResult(
            candidatos=[
                c
                for c in candidatos
                if c.empresa_id not in con_ficha and c.rubro != RUBRO_CARTELERIA
            ],
            firmado_desde=desde,
        )
