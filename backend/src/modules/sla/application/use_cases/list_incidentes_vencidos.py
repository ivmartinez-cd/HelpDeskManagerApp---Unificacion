from src.modules.sla.application.dtos.sla_dtos import IncidenteVencidoDTO
from src.modules.sla.application.use_cases.refresh_sla_snapshot import RefreshSlaSnapshot
from src.modules.sla.domain.entities.incidente_sla import IncidenteSla
from src.modules.sla.domain.repositories.prestador_lookup import PrestadorLookup
from src.modules.sla.domain.repositories.sla_snapshot_repository import SlaSnapshotRepository

AGENTE_LOCAL = "Local"
AGENTE_SIN_OPERADOR = "Sin operador asignado"


def _to_dto(incidente: IncidenteSla, agente: str) -> IncidenteVencidoDTO:
    return IncidenteVencidoDTO(
        id_incidente=incidente.id_incidente,
        tecnico=incidente.tecnico,
        id_tecnico=incidente.id_tecnico,
        region=incidente.region,
        cliente=incidente.cliente,
        sucursal=incidente.sucursal,
        modelo=incidente.modelo,
        nro_serie=incidente.nro_serie,
        fecha_ingreso=incidente.fecha_ingreso,
        fecha_operativo=incidente.fecha_operativo,
        tiempo=incidente.tiempo,
        rango=incidente.rango,
        sla_horas=incidente.sla_horas,
        horas_vencido=incidente.horas_vencido,
        agente=agente,
    )


class ListIncidentesVencidos:
    """Detalle de los incidentes vencidos del período — lee el mismo snapshot
    cacheado que GetSlaCompliance (ver RefreshSlaSnapshot)."""

    def __init__(
        self,
        repo: SlaSnapshotRepository,
        refresher: RefreshSlaSnapshot,
        pst_lookup: PrestadorLookup,
    ) -> None:
        self._repo = repo
        self._refresher = refresher
        self._pst_lookup = pst_lookup

    async def execute(
        self, periodo: int, *, siges_ids_filtro: list[int] | None = None
    ) -> list[IncidenteVencidoDTO]:
        """`siges_ids_filtro=None` trae todos los vencidos del período;
        con una lista (aunque esté vacía) filtra a esos `id_tecnico`
        exclusivamente -- lo resuelve la capa de presentación a partir del
        operador logueado, este caso de uso no sabe nada de operadores."""
        snapshot = await self._repo.get(periodo) or await self._refresher.execute(periodo)
        incidentes = _filtrar_por_tecnico(snapshot.incidentes_vencidos, siges_ids_filtro)
        pst_to_operador = await self._pst_lookup.get_pst_to_operador_mapping()
        return [_to_dto(i, _agente(i, pst_to_operador)) for i in incidentes]


def _filtrar_por_tecnico(
    incidentes: list[IncidenteSla], siges_ids_filtro: list[int] | None
) -> list[IncidenteSla]:
    if siges_ids_filtro is None:
        return incidentes
    filtro = set(siges_ids_filtro)
    return [i for i in incidentes if i.id_tecnico in filtro]


def _agente(incidente: IncidenteSla, pst_to_operador: dict[int, str]) -> str:
    if incidente.region == "LOCAL":
        return AGENTE_LOCAL
    return pst_to_operador.get(incidente.id_tecnico, AGENTE_SIN_OPERADOR)
