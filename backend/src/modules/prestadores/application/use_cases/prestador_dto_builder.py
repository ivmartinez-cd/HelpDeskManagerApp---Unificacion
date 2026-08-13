import uuid

from src.modules.prestadores.application.dtos.prestador_dtos import ContactoDTO, PrestadorDTO
from src.modules.prestadores.domain.entities.contacto_prestador import ContactoPrestador
from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.domain.repositories.user_provider import UserInfo


def build_prestador_dto(
    prestador: Prestador,
    contactos: list[ContactoPrestador],
    users: dict[uuid.UUID, UserInfo],
) -> PrestadorDTO:
    """Ensambla el DTO de un PST con su operador y contactos resueltos —
    compartido por los use cases que devuelven un `PrestadorDTO` completo
    (list/get/create/update/assign) para no repetir el mapeo en cada uno."""
    operador = users.get(prestador.operador_id) if prestador.operador_id else None
    return PrestadorDTO(
        id=prestador.id,
        siges_empresa_id=prestador.siges_empresa_id,
        den_comercial=prestador.den_comercial,
        razon_social=prestador.razon_social,
        cuit=prestador.cuit,
        equipos=prestador.equipos,
        operador_id=prestador.operador_id,
        operador_nombre=operador.full_name if operador else None,
        operador_color=operador.color if operador else None,
        is_active=prestador.is_active,
        contactos=[
            ContactoDTO(
                id=c.id,
                prestador_id=c.prestador_id,
                nombre=c.nombre,
                telefono=c.telefono,
                email=c.email,
                is_principal=c.is_principal,
                sort_order=c.sort_order,
            )
            for c in sorted(contactos, key=lambda c: c.sort_order)
        ],
    )
