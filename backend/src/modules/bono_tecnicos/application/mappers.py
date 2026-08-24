from src.modules.bono_tecnicos.application.dtos.solicitud_tv_dto import SolicitudTvDTO
from src.modules.bono_tecnicos.domain.entities.solicitud_tv import SolicitudTv


def solicitud_tv_a_dto(solicitud: SolicitudTv) -> SolicitudTvDTO:
    return SolicitudTvDTO(
        id=solicitud.id,
        id_tecnico=solicitud.id_tecnico,
        tecnico=solicitud.tecnico,
        periodo=solicitud.periodo,
        fecha=solicitud.fecha,
        razon_social=solicitud.razon_social,
        sucursal=solicitud.sucursal,
        tarea_realizada=solicitud.tarea_realizada,
        estado=solicitud.estado.value,
        creado_en=solicitud.creado_en,
        resuelta_en=solicitud.resuelta_en,
        resuelta_por_email=solicitud.resuelta_por_email,
        motivo_rechazo=solicitud.motivo_rechazo,
    )
