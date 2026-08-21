from __future__ import annotations

from pydantic import BaseModel

from src.modules.analisis_log_hp.domain.entities.cds_incident import CdsIncident, CdsReplacement


class CdsReplacementSchema(BaseModel):
    articulo: str
    cantidad: int

    @classmethod
    def from_entity(cls, r: CdsReplacement) -> CdsReplacementSchema:
        return cls(articulo=r.articulo, cantidad=r.cantidad)


class CdsIncidentSchema(BaseModel):
    id: str
    numero_incidente: str
    fecha: str
    fecha_cierre: str | None
    tipo: str
    estado: str
    motivo: str
    contador: str | None
    repuestos: list[CdsReplacementSchema]
    tareas_realizadas: list[str]

    @classmethod
    def from_entity(cls, i: CdsIncident) -> CdsIncidentSchema:
        return cls(
            id=i.id,
            numero_incidente=i.numero_incidente,
            fecha=i.fecha,
            fecha_cierre=i.fecha_cierre,
            tipo=i.tipo,
            estado=i.estado,
            motivo=i.motivo,
            contador=i.contador,
            repuestos=[CdsReplacementSchema.from_entity(r) for r in i.repuestos],
            tareas_realizadas=i.tareas_realizadas,
        )
