from collections import defaultdict
from datetime import datetime

from src.modules.sla.domain.entities.incidente_sla import IncidenteSla
from src.modules.sla.domain.entities.sla_snapshot import SlaSnapshot, TecnicoVencidos


def _pct(parte: int, total: int) -> float:
    return round(parte * 100 / total, 2) if total else 0.0


def _agrupar_por_tecnico(vencidos: list[IncidenteSla]) -> list[TecnicoVencidos]:
    # Se agrupa por id_tecnico (la identidad real en Siges), no por el nombre
    # -- dos técnicos nunca deberían compartir Den_Comercial, pero el id es la
    # clave confiable y es la que necesita el filtro por operador.
    ids_incidente_por_tecnico: dict[int, list[int]] = defaultdict(list)
    nombre_por_id: dict[int, str] = {}
    for incidente in vencidos:
        ids_incidente_por_tecnico[incidente.id_tecnico].append(incidente.id_incidente)
        nombre_por_id[incidente.id_tecnico] = incidente.tecnico
    grupos = [
        TecnicoVencidos(
            tecnico=nombre_por_id[id_tecnico],
            id_tecnico=id_tecnico,
            cantidad=len(ids),
            ids_incidente=ids,
        )
        for id_tecnico, ids in ids_incidente_por_tecnico.items()
    ]
    return sorted(grupos, key=lambda g: (-g.cantidad, g.tecnico))


def build_snapshot(
    periodo: int, incidentes: list[IncidenteSla], updated_at: datetime
) -> SlaSnapshot:
    """La misma cuenta Correcto/Vencido que reemplazaba la tabla dinámica de
    Excel manual — movida acá desde el use case para que RefreshSlaSnapshot
    (el único que consulta MERCURIO) sea la única fuente de un snapshot."""
    vencidos = [i for i in incidentes if i.es_vencido]
    total, cant_vencidos = len(incidentes), len(vencidos)
    return SlaSnapshot(
        periodo=periodo,
        total=total,
        correctos=total - cant_vencidos,
        vencidos=cant_vencidos,
        pct_correctos=_pct(total - cant_vencidos, total),
        pct_vencidos=_pct(cant_vencidos, total),
        vencidos_por_tecnico=_agrupar_por_tecnico(vencidos),
        incidentes_vencidos=vencidos,
        updated_at=updated_at,
    )
