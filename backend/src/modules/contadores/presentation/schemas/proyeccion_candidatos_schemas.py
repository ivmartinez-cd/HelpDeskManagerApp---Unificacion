"""Respuestas del panel de candidatos de la Proyección (`PanelCandidatos` del
Estimador de Contadores v1.7): lecturas elegibles como Partida/Llegada,
gráfico del parque, botones de método disponibles y la vista previa de un
cálculo (P/L manual o método forzado)."""

from datetime import date

from pydantic import BaseModel, ConfigDict

from src.modules.contadores.application.dtos.boxplot_parque_dto import BoxplotParqueDto
from src.modules.contadores.application.dtos.candidatos_equipo_dto import CandidatosEquipoDto
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.presentation.schemas.proyeccion_schemas import DetalleParqueSchema


class CandidatoLecturaSchema(BaseModel):
    """`usable` habilita elegirla como P o L (`EsUsableComoCandidate`);
    `id_contador` y `para_facturar` se devuelven tal cual en `/recalcular` y
    `/aceptar`. `etiqueta_validacion` es la columna "Valid." y los `cambio_*`
    las marcas de cambio de empresa/sucursal/anexo."""

    model_config = ConfigDict(from_attributes=True)

    fecha: date
    tipo_toma: int
    valor: float
    valido: bool
    motivo_invalidez: str | None
    id_contador: int | None
    desc_tipo_toma: str
    para_facturar: bool
    usable: bool
    etiqueta_validacion: str
    cambio_empresa_vs_anterior: bool
    cambio_sucursal_vs_anterior: bool
    cambio_anexo_vs_anterior: bool


class BoxplotParqueSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    n_equipos: int
    q1: float | None
    mediana: float
    q3: float | None
    valor_equipo: float | None

    @classmethod
    def from_dto_or_none(cls, dto: BoxplotParqueDto | None) -> "BoxplotParqueSchema | None":
        return cls.model_validate(dto) if dto is not None else None


class CandidatosEquipoSchema(BaseModel):
    """`puede_usar_cascada` / `puede_usar_entre_reales`: si el legacy ofrece
    los botones "Usar T19 (cascada)" / "Usar entre reales" para la fila tal
    como se ve hoy (`PuedeUsarCascada` / `PuedeUsarEntreReales`)."""

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
    puede_usar_cascada: bool = False
    puede_usar_entre_reales: bool = False

    @classmethod
    def from_dto(
        cls, dto: CandidatosEquipoDto, metodos: tuple[bool, bool] = (False, False)
    ) -> "CandidatosEquipoSchema":
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
            puede_usar_cascada=metodos[0],
            puede_usar_entre_reales=metodos[1],
        )


class RecalcularCandidatoResponseSchema(BaseModel):
    """Resultado de una vista previa o de un método forzado, con lo que el
    drawer muestra como en la grilla: `detalle_calculo` (tooltip),
    `guia_operador` (`NotaOperador`, no va al CSV), `metodo`/`etiqueta_nivel`
    (tooltip "Detalle de estimación"), `marcas` y el borde `t4_sin_revisar`."""

    model_config = ConfigDict(from_attributes=True)

    estim_propuesto: float | None
    impresiones: float | None
    tipo_toma: int | None
    fuente: str
    metodo_detalle: str
    semaforo: str
    requiere_confirmacion: bool
    dias_par_pl: int | None
    tasa_diaria: float | None
    dias_proyectados: int | None
    detalle_calculo: str
    etiqueta_nivel: str
    metodo: str
    marcas: list[str]
    guia_operador: str | None
    t4_sin_revisar: bool
    detalle_parque: DetalleParqueSchema | None

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
            dias_par_pl=r.dias_par_pl,
            tasa_diaria=r.tasa_diaria,
            dias_proyectados=r.dias_proyectados,
            detalle_calculo=r.detalle_calculo,
            etiqueta_nivel=r.etiqueta_nivel,
            metodo=r.metodo,
            marcas=sorted(r.marcas),
            guia_operador=r.nota_operador,
            t4_sin_revisar=r.t4_sin_revisar,
            detalle_parque=DetalleParqueSchema.from_dto_or_none(r.detalle_parque),
        )
