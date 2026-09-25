"""Mapeo de una fila de `getTopIncidents` al `Incidente` (sin enriquecer)."""

from src.modules.reporte_incidentes.domain.entities.incidente import Empresa, Incidente
from src.modules.reporte_incidentes.domain.services.bitacora import numero_con_digito
from src.modules.reporte_incidentes.infrastructure.wsayc.parsing import (
    Fila,
    elegir,
    fecha_iso,
    filas,
)

_CIERRE = (
    "FechaCierre", "fecha_cierre", "FechaResolucion", "fecha_resolucion", "fecha_fin", "FechaFin",
)


def _costo(fila: Fila) -> float | None:
    try:
        valor = float(elegir(fila, ("Costo", "importe")) or 0)
    except ValueError:
        return None
    return valor or None


def _descripcion(fila: Fila) -> str:
    # El listado no trae descripción larga: el Motivo y, si falta, artículo/tipo
    # como contexto para la tipificación.
    return (
        elegir(fila, ("Motivo", "descripcion", "Descripcion", "detalle"))
        or elegir(fila, ("Articulo", "ArtGen", "Tipo"))
        or ""
    )


def incidente(fila: Fila, empresa: Empresa) -> Incidente:
    return Incidente(
        id=elegir(fila, ("id", "IdIncidente", "incident_id")) or "",
        numero=numero_con_digito(elegir(fila, ("NroIncidente", "numero", "Numero", "nro")) or ""),
        fecha=fecha_iso(elegir(fila, ("Fecha", "fecha_alta"))),
        empresa_id=empresa.id,
        empresa_nombre=empresa.nombre,
        descripcion=_descripcion(fila),
        sucursal=elegir(fila, ("Sucursal",)),
        maquina=elegir(fila, ("NroSerie", "maquina", "Maquina", "serie")),
        # Estado "web" (Resuelto/…), el orientado al cliente.
        estado=elegir(fila, ("EstadoWeb", "Estado")),
        costo=_costo(fila),
        solicitante=elegir(fila, ("Solicitante",)),
        tipo_trabajo=elegir(fila, ("Tipo",)),
        articulo=elegir(fila, ("Articulo", "ArtGen")),
        fecha_cierre=fecha_iso(elegir(fila, _CIERRE)) or None,
    )


def incidentes(raw: object, empresa: Empresa) -> list[Incidente]:
    return [incidente(f, empresa) for f in filas(raw, "getTopIncidents", "Incident")]
