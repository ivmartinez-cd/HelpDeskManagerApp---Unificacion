from src.modules.contadores.application.dtos.candidato_lectura_dto import CandidatoLecturaDto
from src.modules.contadores.application.dtos.candidatos_equipo_dto import CandidatosEquipoDto
from src.modules.contadores.application.dtos.contexto_proceso_dto import ContextoProcesoDto
from src.modules.contadores.application.use_cases._boxplot_de_entrada import boxplot_de_entrada
from src.modules.contadores.application.use_cases._construir_estimacion_input import (
    construir_estimacion_input,
)
from src.modules.contadores.domain.ports.candidatos_equipo_port import LecturaCandidataSiges
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef
from src.modules.contadores.infrastructure.ejemplo.datos_ejemplo_proyeccion import (
    ClaseEjemplo,
    EquipoEjemplo,
    equipos_ejemplo,
)

_TIPO_TOMA_ST = 4
_ETIQUETA_OK = "✓ ok"


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
            boxplot=boxplot_de_entrada(entrada),
        )


def entrada_ejemplo(
    id_maquina: int, clase: str, ctx: ContextoProcesoDto
) -> EstimacionInput | None:
    """La fila de un equipo de ejemplo tal como la calcula el tablero —
    `None` si el equipo/clase no existe."""
    equipo, clase_ej = buscar_equipo_y_clase(id_maquina, clase)
    if equipo is None or clase_ej is None:
        return None
    return construir_estimacion_input(equipo, clase_ej, ctx)


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
    """Mismas reglas que el panel real (`EsUsableComoCandidate` y
    `ValidacionLabel` del legacy, en `LecturaCandidataSiges`): un T4 sin
    revisar es "⚠ T4-PF0" pero igual se puede elegir como P/L. Las lecturas
    de ejemplo no existen en Siges: sin `id_contador`."""
    candidata = _candidata_de(lectura, clase)
    etiqueta = candidata.etiqueta_validacion
    valido = etiqueta == _ETIQUETA_OK
    return CandidatoLecturaDto(
        fecha=lectura.fecha,
        tipo_toma=lectura.tipo_toma,
        valor=lectura.valor,
        valido=valido,
        motivo_invalidez=None if valido else etiqueta,
        para_facturar=candidata.para_facturar,
        usable=candidata.usable,
        etiqueta_validacion=etiqueta,
    )


def _candidata_de(lectura: LecturaRef, clase: ClaseEjemplo) -> LecturaCandidataSiges:
    return LecturaCandidataSiges(
        id_contador=0,
        fecha=lectura.fecha,
        tipo_toma=lectura.tipo_toma,
        valor=lectura.valor,
        para_facturar=lectura.tipo_toma != _TIPO_TOMA_ST or clase.t4_revisado,
    )
