"""Schemas de "Reclamar en OCA" (camelCase, ver `despachados_schemas.py`). Datos de dominio:
el mapeo a los campos del formulario de OCA lo hace el frontend."""

from src.modules.insumos.domain.value_objects.despachados.reclamo_oca import (
    ContactoReclamoOca,
    ReclamoOca,
)
from src.modules.insumos.presentation.schemas.despachados_schemas import CamelOut


class ContactoReclamoOut(CamelOut):
    nombre: str
    apellido: str
    empresa: str
    email: str
    cuit: str
    telefono: str

    @classmethod
    def from_contacto(cls, contacto: ContactoReclamoOca | None) -> "ContactoReclamoOut | None":
        if contacto is None:
            return None
        return cls(**{c: getattr(contacto, c) for c in cls.model_fields})


class ReclamoOcaOut(CamelOut):
    guia: str
    operativa: str
    contacto: ContactoReclamoOut | None
    comentario: str

    @classmethod
    def from_reclamo(cls, reclamo: ReclamoOca) -> "ReclamoOcaOut":
        return cls(
            guia=reclamo.guia,
            operativa=reclamo.operativa,
            contacto=ContactoReclamoOut.from_contacto(reclamo.contacto),
            comentario=reclamo.comentario,
        )
