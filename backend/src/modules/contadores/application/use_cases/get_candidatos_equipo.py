from src.modules.contadores.application.dtos.boxplot_parque_dto import BoxplotParqueDto
from src.modules.contadores.application.dtos.candidato_lectura_dto import CandidatoLecturaDto
from src.modules.contadores.application.dtos.candidatos_equipo_dto import CandidatosEquipoDto
from src.modules.contadores.application.dtos.contexto_proceso_dto import ContextoProcesoDto
from src.modules.contadores.application.use_cases._construir_estimacion_input import (
    construir_estimacion_input,
)
from src.modules.contadores.domain.services.estimacion.cascada_parque import (
    resolver_cascada_parque,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import (
    EstimacionInput,
)
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef
from src.modules.contadores.infrastructure.ejemplo.datos_ejemplo_proyeccion import (
    ClaseEjemplo,
    EquipoEjemplo,
    equipos_ejemplo,
)

_TIPO_TOMA_ST = 4


class GetCandidatosEquipoUseCase:
    def execute(
        self, id_maquina: int, clase: str, ctx: ContextoProcesoDto
    ) -> CandidatosEquipoDto | None:
        equipo, clase_ej = buscar_equipo_y_clase(id_maquina, clase)
        if equipo is None or clase_ej is None:
            return None
        entrada = construir_estimacion_input(equipo, clase_ej, ctx)
        return CandidatosEquipoDto(
            id_maquina=equipo.id_maquina,
            nro_serie=equipo.nro_serie,
            empresa=equipo.empresa,
            sucursal=equipo.sucursal,
            sector=equipo.sector,
            modelo=equipo.modelo,
            tecnologia=clase_ej.tecnologia,
            velocidad_ppm=clase_ej.velocidad_ppm,
            lecturas=_lecturas_de(clase_ej),
            boxplot=_boxplot_de(entrada),
        )


def buscar_equipo_y_clase(
    id_maquina: int, clase: str
) -> tuple[EquipoEjemplo | None, ClaseEjemplo | None]:
    equipo = next((e for e in equipos_ejemplo() if e.id_maquina == id_maquina), None)
    if equipo is None:
        return None, None
    clase_ej = next((c for c in equipo.clases if c.clase == clase), None)
    return equipo, clase_ej


def _lecturas_de(clase: ClaseEjemplo) -> list[CandidatoLecturaDto]:
    candidatas = [
        clase.ultimo_contador_facturado,
        clase.ultimo_real,
        clase.real_anterior,
        clase.t4_mas_reciente,
    ]
    presentes = [c for c in candidatas if c is not None]
    vistas: set[tuple[float, object, int]] = set()
    lecturas = []
    for lectura in sorted(presentes, key=lambda x: x.fecha, reverse=True):
        clave = (lectura.valor, lectura.fecha, lectura.tipo_toma)
        if clave in vistas:
            continue
        vistas.add(clave)
        lecturas.append(_a_dto(lectura, clase))
    return lecturas


def _a_dto(lectura: LecturaRef, clase: ClaseEjemplo) -> CandidatoLecturaDto:
    es_t4_sin_revisar = lectura.tipo_toma == _TIPO_TOMA_ST and not clase.t4_revisado
    return CandidatoLecturaDto(
        fecha=lectura.fecha,
        tipo_toma=lectura.tipo_toma,
        valor=lectura.valor,
        valido=not es_t4_sin_revisar,
        motivo_invalidez="PF=0 (Servicio Técnico sin revisar)" if es_t4_sin_revisar else None,
    )


def _boxplot_de(entrada: EstimacionInput) -> BoxplotParqueDto | None:
    """Distribución sintética alrededor del valor de parque usado — el
    fixture de ejemplo no modela una muestra cruda de equipos, así que el
    spread es ilustrativo, no una estadística real (aceptable para el
    alcance de datos de ejemplo; con SiGes real se calcularía de la muestra)."""
    nivel = resolver_cascada_parque(entrada)
    if nivel is None:
        return None
    valor = nivel.promedio.valor
    return BoxplotParqueDto(
        minimo=valor * 0.4,
        q1=valor * 0.7,
        mediana=valor,
        q3=valor * 1.3,
        maximo=valor * 1.8,
        valor_equipo=valor,
    )
