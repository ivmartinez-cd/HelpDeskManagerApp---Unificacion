from datetime import datetime

from pydantic import BaseModel, ConfigDict


class _Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EmpresaSchema(_Schema):
    id: str
    nombre: str


class ConteoSchema(_Schema):
    nombre: str
    cantidad: int


class ConteoSubcategoriaSchema(_Schema):
    nombre: str
    cantidad: int
    categoria: str


class KpisSchema(BaseModel):
    total: int
    categoria_principal: str
    categoria_principal_cantidad: int
    categoria_principal_pct: int
    sucursal_principal: str
    sucursal_principal_cantidad: int


class FiltrosSchema(_Schema):
    sucursal: str
    categoria: str
    subcategoria: str


class OpcionFiltroSchema(_Schema):
    valor: str
    cantidad: int


class OpcionesFiltroSchema(_Schema):
    sucursales: list[OpcionFiltroSchema]
    categorias: list[OpcionFiltroSchema]
    subcategorias: list[OpcionFiltroSchema]


class ItemSinReparacionSchema(_Schema):
    subcategoria: str
    cantidad: int
    pct: int


class ItemMejoraSchema(_Schema):
    categoria: str
    subcategoria: str
    cantidad: int
    pct: int
    sucursal_principal: str
    sucursal_principal_cantidad: int
    sucursal_principal_pct: int
    concentrado: bool


class OportunidadesMejoraSchema(_Schema):
    total: int
    fuera_del_equipo_total: int
    fuera_del_equipo_pct: int
    sin_reparacion_total: int
    sin_reparacion_pct: int
    sin_reparacion_items: list[ItemSinReparacionSchema]
    items: list[ItemMejoraSchema]


class CategoriaSchema(BaseModel):
    nombre: str
    color: str
    subcategorias: list[str]


class ReporteResponse(BaseModel):
    """Todo lo del dashboard salvo la tabla de incidentes (paginada aparte).

    `kpis` y `evolucion` son de la selección filtrada; `categorias`,
    `subcategorias`, `sucursales` y `oportunidades` del período completo.
    `pendientes_ia` = casos distintos sin tipificación guardada (los que la IA
    todavía tiene que ver); `pendientes_revision` = incidentes que hoy se
    muestran "Pendiente de revision" (incluye los de confianza media/baja)."""

    empresa: EmpresaSchema
    periodo: str
    meses: int
    periodos: list[str]
    rango_etiqueta: str
    generado_en: datetime
    pendientes_ia: int
    pendientes_revision: int
    filtros: FiltrosSchema
    filtros_activos: bool
    opciones: OpcionesFiltroSchema
    kpis: KpisSchema
    evolucion: list[ConteoSchema]
    categorias: list[ConteoSchema]
    subcategorias: list[ConteoSubcategoriaSchema]
    sucursales: list[ConteoSchema]
    oportunidades: OportunidadesMejoraSchema
    colores: dict[str, str]
    taxonomia: list[CategoriaSchema]


class TrabajoSchema(_Schema):
    descripcion: str
    observ: str | None
    fecha: str | None
    estado: str | None
    tecnico: str | None


class IncidenteSchema(_Schema):
    id: str
    numero: str
    fecha: str
    sucursal: str | None
    maquina: str | None
    estado: str | None
    descripcion: str
    costo: float | None
    solicitante: str | None
    tecnico: str | None
    tipo_trabajo: str | None
    causa: str | None
    articulo: str | None
    fecha_cierre: str | None
    solucion: str | None
    trabajos: list[TrabajoSchema]
    categoria: str | None
    subcategoria: str | None
