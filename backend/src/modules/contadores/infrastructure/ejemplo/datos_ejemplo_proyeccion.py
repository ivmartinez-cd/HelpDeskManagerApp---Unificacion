"""Datos de ejemplo de la herramienta Proyección — TEMPORAL mientras no se
resuelve el acceso real a SiGes (credencial `SiGesReadOnly` pendiente de
rotación, ver MIGRACION_SISTEMAS.md del repo del Estimador). Un proceso
ficticio (grupo económico, anexo, ~10 equipos) que cubre los casos visuales
de REGLAS_DE_NEGOCIO.md §7 (semáforo, coloreo, salto imposible). El día que
se conecte a SiGes, solo hay que reemplazar `equipos_ejemplo()` por una
consulta real — el resto del pipeline (armado de EstimacionInput + `estimar()`)
no cambia."""

from datetime import date

from src.modules.contadores.application.dtos.equipo_proceso_dto import (
    ClaseProceso as ClaseEjemplo,
)
from src.modules.contadores.application.dtos.equipo_proceso_dto import (
    EquipoProceso as EquipoEjemplo,
)
from src.modules.contadores.domain.value_objects.estimacion.estado_maquina import EstadoMaquina
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef

FECHA_OBJETIVO_EJEMPLO = date(2026, 4, 30)
PERIODO_DESDE_EJEMPLO = date(2026, 4, 1)
PERIODO_HASTA_EJEMPLO = date(2026, 5, 1)
ID_GRUPO_ECONOMICO_EJEMPLO = 1
ID_ANEXO_EJEMPLO = 1
NOMBRE_GRUPO_ECONOMICO_EJEMPLO = "Cliente Demo S.A."
NOMBRE_PROCESO_EJEMPLO = "2026-04 · Anexo Principal · Proc. 1001"
NRO_PROCESO_EJEMPLO = 1001


def historico_ejemplo(normal: float, actual: float) -> tuple[float, ...]:
    """11 meses estables (histórico real) + el mes actual (estimado)."""
    return (normal,) * 11 + (actual,)


def equipo_ejemplo(
    identidad: tuple[int, str, str], estado: EstadoMaquina, clases: tuple[ClaseEjemplo, ...]
) -> EquipoEjemplo:
    id_maquina, nro_serie, modelo = identidad
    return EquipoEjemplo(
        id_maquina,
        nro_serie,
        NOMBRE_GRUPO_ECONOMICO_EJEMPLO,
        "Casa Central",
        "Administración",
        modelo,
        estado,
        clases,
    )


def _equipo_real_cargado() -> EquipoEjemplo:
    clase = ClaseEjemplo(
        "10",
        "MONO",
        45.0,
        LecturaRef(118_500, date(2026, 3, 31), 1),
        ya_real=True,
        valor_real_cargado=122_300,
        prom_6_facturados=3_600,
        historico_12=historico_ejemplo(3600, 3800),
    )
    return equipo_ejemplo((1, "CD0001MONO", "HP LaserJet M404"), "NORMAL", (clase,))


def _equipo_t4_sin_revisar() -> EquipoEjemplo:
    clase = ClaseEjemplo(
        "10",
        "MONO",
        45.0,
        LecturaRef(95_000, date(2026, 3, 31), 1),
        t4_mas_reciente=LecturaRef(105_000, date(2026, 4, 25), 4),
        t4_revisado=False,
        prom_6_facturados=12_000,
        historico_12=historico_ejemplo(12000, 12000),
    )
    return equipo_ejemplo((2, "CD0002MONO", "Xerox WorkCentre 3335"), "NORMAL", (clase,))


def _equipo_backup() -> EquipoEjemplo:
    clase = ClaseEjemplo(
        "10",
        "MONO",
        45.0,
        LecturaRef(40_000, date(2026, 3, 31), 1),
        historico_12=historico_ejemplo(0, 0),
    )
    return equipo_ejemplo((3, "CD0008MONO", "HP LaserJet P2055"), "BACKUP", (clase,))


def _equipo_coloreo_bajo() -> EquipoEjemplo:
    clase = ClaseEjemplo(
        "10",
        "MONO",
        45.0,
        LecturaRef(50_000, date(2026, 3, 31), 1),
        ultimo_real=LecturaRef(51_034, date(2026, 3, 31), 1),
        real_anterior=LecturaRef(43_034, date(2026, 2, 1), 1),
        prom_6_facturados=8_000,
        historico_12=historico_ejemplo(8000, 1034),
    )
    return equipo_ejemplo((4, "CD0007MONO", "Brother HL-L5100"), "NORMAL", (clase,))


def _equipo_coloreo_alto() -> EquipoEjemplo:
    clase = ClaseEjemplo(
        "10",
        "MONO",
        45.0,
        LecturaRef(100_000, date(2026, 3, 31), 1),
        ultimo_real=LecturaRef(115_517, date(2026, 3, 31), 1),
        real_anterior=LecturaRef(84_517, date(2026, 2, 1), 1),
        prom_6_facturados=8_000,
        historico_12=historico_ejemplo(8000, 15517),
    )
    return equipo_ejemplo((5, "CD0006MONO", "HP LaserJet M404"), "NORMAL", (clase,))


def equipos_ejemplo() -> list[EquipoEjemplo]:
    from src.modules.contadores.infrastructure.ejemplo.datos_ejemplo_proyeccion_2 import (
        equipos_ejemplo_2,
    )

    return [
        _equipo_real_cargado(),
        _equipo_t4_sin_revisar(),
        _equipo_backup(),
        _equipo_coloreo_bajo(),
        _equipo_coloreo_alto(),
        *equipos_ejemplo_2(),
    ]
