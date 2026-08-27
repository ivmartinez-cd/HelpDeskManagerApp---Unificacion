from src.modules.sla.application.dtos.derivados_dtos import IncidenteDerivadoDTO
from src.modules.sla.domain.entities.incidente_derivado import IncidenteDerivado
from src.modules.sla.domain.repositories.derivados_query_gateway import DerivadosQueryGateway
from src.modules.sla.domain.repositories.prestador_lookup import PrestadorLookup
from src.modules.sla.domain.value_objects.periodo import Periodo


def _to_dto(inc: IncidenteDerivado, operador: str | None) -> IncidenteDerivadoDTO:
    return IncidenteDerivadoDTO(
        id_incidente=inc.id_incidente,
        fecha_ingreso=inc.fecha_ingreso,
        tipo=inc.tipo,
        estado=inc.estado,
        cliente=inc.cliente,
        sucursal=inc.sucursal,
        nro_serie=inc.nro_serie,
        modelo=inc.modelo,
        tecnico=inc.tecnico,
        id_tecnico=inc.id_tecnico,
        operador=operador,
        dias_desde_ingreso=inc.dias_desde_ingreso,
        demorado=inc.demorado,
    )


def _filtrar_del_interior(
    incidentes: list[IncidenteDerivado],
    pst_ids: set[int],
    siges_ids_filtro: list[int] | None,
) -> list[IncidenteDerivado]:
    del_interior = [i for i in incidentes if i.id_tecnico in pst_ids]
    if siges_ids_filtro is None:
        return del_interior
    filtro = set(siges_ids_filtro)
    return [i for i in del_interior if i.id_tecnico in filtro]


class ListIncidentesDerivados:
    """Incidentes de PST del interior en estado Derivado (200) — el operador
    todavía no los consultó con el técnico. Consulta en vivo a Siges para el
    período mensual elegido, sin snapshot."""

    def __init__(self, gateway: DerivadosQueryGateway, pst_lookup: PrestadorLookup) -> None:
        self._gateway = gateway
        self._pst_lookup = pst_lookup

    async def execute(
        self, periodo: int, *, siges_ids_filtro: list[int] | None = None
    ) -> list[IncidenteDerivadoDTO]:
        vo = Periodo(periodo)
        pst_ids = set(await self._pst_lookup.get_all_pst_siges_ids())
        pst_to_operador = await self._pst_lookup.get_pst_to_operador_mapping()
        todos = await self._gateway.find_incidentes_derivados(vo.primer_dia, vo.ultimo_dia)
        incidentes = _filtrar_del_interior(todos, pst_ids, siges_ids_filtro)
        ordenados = sorted(incidentes, key=lambda i: i.dias_desde_ingreso, reverse=True)
        return [_to_dto(i, pst_to_operador.get(i.id_tecnico)) for i in ordenados]
