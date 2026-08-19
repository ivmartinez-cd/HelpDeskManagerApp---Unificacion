"""Confirmación/rechazo manual de un candidato N2 de matching de sucursales
(Fase 1). El operador SIEMPRE decide para N2 — acá no hay auto-vínculo."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    validar_prestador_vinculado_siges,
)
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.errors import TablaKmNoEncontradaError
from src.modules.liquidaciones.domain.repositories.matching_descarte_repository import (
    MatchingDescarteRepository,
)
from src.modules.liquidaciones.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCatalogoGateway,
)
from src.modules.liquidaciones.domain.repositories.tabla_km_repository import TablaKmRepository
from src.shared.domain.errors import NotFoundError


class SigesSucursalNoEncontradaError(NotFoundError):
    def __init__(self, siges_sucursal_id: int) -> None:
        super().__init__(f"Sucursal Siges {siges_sucursal_id} no encontrada")


@dataclass(frozen=True)
class ConfirmarRechazarPorts:
    prestadores: PrestadorRepository
    tabla_km: TablaKmRepository
    siges: SigesCatalogoGateway
    descartes: MatchingDescarteRepository


class ConfirmarVinculoTablaKm:
    """Confirma un candidato (propuesto por N2, o elegido a mano por el
    operador entre los top-N) — trae domicilio/localidad/provincia + vínculo,
    igual que `RefrescarDatosSiges._actualizar_fila`."""

    def __init__(self, ports: ConfirmarRechazarPorts) -> None:
        self._ports = ports

    async def execute(self, tabla_km_id: UUID, siges_sucursal_id: int) -> TablaKm:
        fila = await self._buscar_fila(tabla_km_id)
        prestador = await validar_prestador_vinculado_siges(
            self._ports.prestadores, fila.prestador_id
        )
        sucursales = await self._ports.siges.list_sucursales_de_prestador(
            prestador.siges_empresa_id  # type: ignore[arg-type]
        )
        candidato = next(
            (s for s in sucursales if s.siges_sucursal_id == siges_sucursal_id), None
        )
        if candidato is None:
            raise SigesSucursalNoEncontradaError(siges_sucursal_id)
        actualizada = await self._ports.tabla_km.update_domicilio(
            tabla_km_id,
            domicilio_cliente=candidato.domicilio,
            localidad_cliente=candidato.localidad,
            provincia_cliente=candidato.provincia,
            siges_sucursal_id=candidato.siges_sucursal_id,
            id_costo_servicios=candidato.id_costo_servicios,
        )
        if actualizada is None:
            raise TablaKmNoEncontradaError(tabla_km_id)
        return actualizada

    async def _buscar_fila(self, tabla_km_id: UUID) -> TablaKm:
        fila = await self._ports.tabla_km.get_by_id(tabla_km_id)
        if fila is None:
            raise TablaKmNoEncontradaError(tabla_km_id)
        return fila


class RechazarPropuestaTablaKm:
    """Persiste el descarte — el mismo candidato no vuelve a proponerse para
    esta fila en corridas futuras (decisión 0.4.d)."""

    def __init__(self, descartes: MatchingDescarteRepository) -> None:
        self._descartes = descartes

    async def execute(
        self, tabla_km_id: UUID, siges_sucursal_id: int, usuario_email: str
    ) -> None:
        await self._descartes.create(tabla_km_id, siges_sucursal_id, usuario_email)
