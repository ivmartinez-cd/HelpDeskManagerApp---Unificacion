from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from src.modules.contadores.application.dtos.receso_dto import RecesoDto
from src.modules.contadores.application.dtos.resumen_proyeccion_dto import (
    RestauracionDecisionesDto,
)
from src.modules.contadores.application.use_cases.get_tablero_proyeccion import (
    TableroProyeccionResult,
)
from src.modules.contadores.domain.services.historial_equipo import LecturaHistorial
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    DetalleParque,
)


class DetalleParqueSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    n_equipos: int
    n_descartados: int
    es_mediana_truncada: bool
    mediana_cruda: float | None
    media_cruda: float | None

    @classmethod
    def from_dto_or_none(cls, dto: DetalleParque | None) -> "DetalleParqueSchema | None":
        return cls.model_validate(dto) if dto is not None else None


class NivelParqueHistoricoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    n: int
    p80: float | None
    cruda: float | None


class ParqueHistoricoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cliente_modelo: NivelParqueHistoricoSchema
    grupo_modelo: NivelParqueHistoricoSchema
    cliente_tec: NivelParqueHistoricoSchema
    global_modelo: NivelParqueHistoricoSchema


class FilaProyeccionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_maquina: int
    nro_serie: str
    empresa: str
    sucursal: str
    sector: str
    modelo: str
    tecnologia: str
    estado_maquina: str
    clase: str
    meses_sin_real: int | None
    historico_12: tuple[float, ...]
    prom_6_facturados: float | None
    ultimo_facturado_valor: float | None
    ultimo_facturado_fecha: date | None
    ultimo_facturado_tipo: int | None
    es_real: bool
    estim_propuesto: float | None
    tipo_toma: int | None
    impresiones: float | None
    fuente: str
    metodo_detalle: str
    coloreo: str | None
    borde_salto_imposible: bool
    semaforo: str
    requiere_confirmacion: bool
    es_clase_sintetica: bool
    detalle_parque: DetalleParqueSchema | None
    dias_par_pl: int | None
    tasa_diaria: float | None
    dias_proyectados: int | None
    detalle_calculo: str
    fecha_toma_actual: date | None
    editado_por_operador: bool
    guia_operador: str | None
    metodo: str
    etiqueta_nivel: str
    t4_sin_revisar: bool
    meses_sin_real_en_alerta: bool
    estado_maquina_desc: str
    empresa_actual_desc: str | None
    id_art_gen: int | None
    id_modo_oper: int
    ultimo_real_fecha: date | None
    ultimo_real_tipo: int | None
    real_anterior_fecha: date | None
    real_anterior_tipo: int | None
    parque_historico: ParqueHistoricoSchema | None


class ResumenProyeccionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reales: int
    estimados: int
    pendientes: int
    sospechosos: int
    total: int


class RestauracionDecisionesSchema(BaseModel):
    """Banner "Restauramos N decisiones de una sesión anterior (M
    descartadas)". `vigentes_hasta` es lo que se manda como `descartar_hasta`
    al apretar "Descartar y empezar limpio"."""

    model_config = ConfigDict(from_attributes=True)

    restauradas: int
    descartadas: int
    vigentes_hasta: datetime | None

    @classmethod
    def from_dto(cls, dto: RestauracionDecisionesDto) -> "RestauracionDecisionesSchema":
        return cls.model_validate(dto)


class TableroProyeccionSchema(BaseModel):
    filas: list[FilaProyeccionSchema]
    resumen: ResumenProyeccionSchema
    restauracion: RestauracionDecisionesSchema

    @classmethod
    def from_result(cls, result: TableroProyeccionResult) -> "TableroProyeccionSchema":
        return cls(
            filas=[FilaProyeccionSchema.model_validate(f) for f in result.filas],
            resumen=ResumenProyeccionSchema.model_validate(result.resumen),
            restauracion=RestauracionDecisionesSchema.from_dto(result.restauracion),
        )


class RecesoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_grupo_economico: int
    id_anexo: int | None
    fecha_desde: date
    fecha_hasta: date
    descripcion: str

    @classmethod
    def from_dto(cls, dto: RecesoDto) -> "RecesoSchema":
        return cls.model_validate(dto)


class GrupoEconomicoOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    descripcion: str


class ProcesoOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nro_proceso: int
    periodo_facturacion: str
    nombre_anexo: str
    periodo_hasta: date
    id_anexo: int


class AnexoOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_anexo: int
    nombre_anexo: str


class HistorialLecturaSchema(BaseModel):
    """Una fila de la línea de tiempo de un equipo (paridad con
    `HistorialLectura` / `DrillDownModal` legacy, MODELO_DE_DATOS.md §3.6)."""

    model_config = ConfigDict(from_attributes=True)

    fecha: date
    valor: float
    id_tipo_toma: int
    tipo_toma_desc: str
    para_facturar: bool
    fc_nro_proceso: int | None
    fc_periodo_hasta: date | None
    fc_impresiones: float | None
    fc_periodo_facturacion: str | None
    es_fc: bool
    delta: float | None
    es_ingreso: bool
    es_egreso: bool
    es_cambio_empresa: bool
    es_cambio_anexo: bool
    cambio_empresa_vs_anterior: bool
    cambio_sucursal_vs_anterior: bool
    cambio_anexo_vs_anterior: bool


class HistorialEquipoSchema(BaseModel):
    lecturas: list[HistorialLecturaSchema]

    @classmethod
    def from_lecturas(cls, lecturas: list[LecturaHistorial]) -> "HistorialEquipoSchema":
        schemas = [HistorialLecturaSchema.model_validate(lectura) for lectura in lecturas]
        return cls(lecturas=schemas)
