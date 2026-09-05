from datetime import date

from pydantic import BaseModel, ConfigDict

from src.modules.contadores.application.dtos.boxplot_parque_dto import BoxplotParqueDto
from src.modules.contadores.application.dtos.candidatos_equipo_dto import CandidatosEquipoDto
from src.modules.contadores.application.dtos.receso_dto import RecesoDto
from src.modules.contadores.application.use_cases.get_tablero_proyeccion import (
    TableroProyeccionResult,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)


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
    ultimo_facturado_valor: float
    ultimo_facturado_fecha: date
    ultimo_facturado_tipo: int
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
    nota_operador: str | None
    es_clase_sintetica: bool


class ResumenProyeccionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reales: int
    estimados: int
    pendientes: int
    sospechosos: int
    total: int


class TableroProyeccionSchema(BaseModel):
    filas: list[FilaProyeccionSchema]
    resumen: ResumenProyeccionSchema

    @classmethod
    def from_result(cls, result: TableroProyeccionResult) -> "TableroProyeccionSchema":
        return cls(
            filas=[FilaProyeccionSchema.model_validate(f) for f in result.filas],
            resumen=ResumenProyeccionSchema.model_validate(result.resumen),
        )


class CandidatoLecturaSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fecha: date
    tipo_toma: int
    valor: float
    valido: bool
    motivo_invalidez: str | None


class BoxplotParqueSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    minimo: float
    q1: float
    mediana: float
    q3: float
    maximo: float
    valor_equipo: float

    @classmethod
    def from_dto_or_none(cls, dto: BoxplotParqueDto | None) -> "BoxplotParqueSchema | None":
        return cls.model_validate(dto) if dto is not None else None


class CandidatosEquipoSchema(BaseModel):
    id_maquina: int
    nro_serie: str
    empresa: str
    sucursal: str
    sector: str
    modelo: str
    tecnologia: str
    velocidad_ppm: float | None
    lecturas: list[CandidatoLecturaSchema]
    boxplot: BoxplotParqueSchema | None

    @classmethod
    def from_dto(cls, dto: CandidatosEquipoDto) -> "CandidatosEquipoSchema":
        return cls(
            id_maquina=dto.id_maquina,
            nro_serie=dto.nro_serie,
            empresa=dto.empresa,
            sucursal=dto.sucursal,
            sector=dto.sector,
            modelo=dto.modelo,
            tecnologia=dto.tecnologia,
            velocidad_ppm=dto.velocidad_ppm,
            lecturas=[CandidatoLecturaSchema.model_validate(lectura) for lectura in dto.lecturas],
            boxplot=BoxplotParqueSchema.from_dto_or_none(dto.boxplot),
        )


class RecalcularCandidatoResponseSchema(BaseModel):
    estim_propuesto: float | None
    impresiones: float | None
    tipo_toma: int | None
    fuente: str
    metodo_detalle: str
    semaforo: str
    requiere_confirmacion: bool

    @classmethod
    def from_resultado(cls, r: EstimacionResultado) -> "RecalcularCandidatoResponseSchema":
        return cls(
            estim_propuesto=r.estim_propuesto,
            impresiones=r.impresiones,
            tipo_toma=r.tipo_toma,
            fuente=r.fuente,
            metodo_detalle=r.metodo_detalle,
            semaforo=r.semaforo,
            requiere_confirmacion=r.requiere_confirmacion,
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
