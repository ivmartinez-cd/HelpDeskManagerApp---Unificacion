from src.modules.bono_tecnicos.application.dtos.incidente_bono_dto import (
    GetIncidentesTecnicoRequest,
    IncidenteBonoDTO,
)
from src.modules.bono_tecnicos.domain.repositories.incidente_tecnico_gateway import (
    IncidenteTecnicoGateway,
)
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo


class GetIncidentesTecnico:
    """Detalle de incidentes de un técnico y período — la pantalla que abre
    al entrar al detalle de una fila de `GetPuntajesPeriodo`, equivalente a
    las tablas por categoría de "Tecnicos.xlsx" para ese técnico."""

    def __init__(self, gateway: IncidenteTecnicoGateway) -> None:
        self._gateway = gateway

    async def execute(self, request: GetIncidentesTecnicoRequest) -> list[IncidenteBonoDTO]:
        periodo = Periodo(request.periodo)
        incidentes = await self._gateway.find_incidentes(periodo, request.id_tecnico)
        return [
            IncidenteBonoDTO(
                id_incidente=i.id_incidente,
                categoria=i.categoria,
                cliente=i.cliente,
                sucursal=i.sucursal,
                nro_serie=i.nro_serie,
            )
            for i in incidentes
        ]
