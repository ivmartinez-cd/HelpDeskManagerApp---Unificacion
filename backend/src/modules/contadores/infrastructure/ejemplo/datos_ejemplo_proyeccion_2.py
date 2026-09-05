"""Segunda mitad de los equipos de ejemplo — separado de
`datos_ejemplo_proyeccion.py` por el límite de 300 líneas por archivo
(ARCHITECTURE_GUIDE.md §4)."""

from datetime import date

from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef
from src.modules.contadores.domain.value_objects.estimacion.promedio_parque import PromedioParque
from src.modules.contadores.infrastructure.ejemplo.datos_ejemplo_proyeccion import (
    ClaseEjemplo,
    EquipoEjemplo,
    equipo_ejemplo,
    historico_ejemplo,
)


def _equipo_sin_historia() -> EquipoEjemplo:
    clase = ClaseEjemplo(
        "10",
        "MONO",
        45.0,
        LecturaRef(50_000, date(2026, 3, 31), 1),
        ultimo_real=LecturaRef(50_000, date(2025, 2, 28), 1),
        parque_cliente_tecnologia=PromedioParque(8_000, n_equipos=6),
        historico_12=historico_ejemplo(0, 8000),
    )
    return equipo_ejemplo((6, "CD0004MONO", "Brother HL-L5100"), "NORMAL", (clase,))


def _equipo_salto_imposible() -> EquipoEjemplo:
    clase = ClaseEjemplo(
        "10",
        "MONO",
        45.0,
        LecturaRef(100_000, date(2026, 3, 31), 1),
        parque_cliente_modelo=PromedioParque(900_000, n_equipos=3),
        historico_12=historico_ejemplo(0, 900_000),
    )
    return equipo_ejemplo((7, "CD0005MONO", "Kyocera ECOSYS P3155"), "NORMAL", (clase,))


def _equipo_pendiente() -> EquipoEjemplo:
    clase = ClaseEjemplo(
        "10",
        "MONO",
        45.0,
        LecturaRef(5_000, date(2026, 3, 31), 1),
        historico_12=historico_ejemplo(0, 0),
    )
    return equipo_ejemplo((8, "CD0010MONO", "Epson EcoTank M2170"), "NORMAL", (clase,))


def _equipo_en_transito() -> EquipoEjemplo:
    clase = ClaseEjemplo(
        "10",
        "MONO",
        45.0,
        LecturaRef(25_000, date(2026, 3, 31), 1),
        historico_12=historico_ejemplo(0, 0),
    )
    return equipo_ejemplo((9, "CD0009MONO", "Canon imageCLASS LBP226"), "EN_TRANSITO", (clase,))


def _clase_mono_del_equipo_color() -> ClaseEjemplo:
    return ClaseEjemplo(
        "10",
        "MONO",
        45.0,
        LecturaRef(60_000, date(2026, 3, 31), 1),
        ultimo_real=LecturaRef(70_172, date(2026, 3, 31), 1),
        real_anterior=LecturaRef(65_172, date(2026, 3, 1), 1),
        prom_6_facturados=5_000,
        historico_12=historico_ejemplo(5000, 10172),
    )


def _clase_color_del_equipo_color() -> ClaseEjemplo:
    return ClaseEjemplo(
        "20",
        "COLOR",
        25.0,
        LecturaRef(12_000, date(2026, 3, 31), 1),
        parque_cliente_tecnologia=PromedioParque(1_800, n_equipos=4),
        historico_12=historico_ejemplo(0, 1800),
    )


def _equipo_mono_y_color() -> EquipoEjemplo:
    clases = (_clase_mono_del_equipo_color(), _clase_color_del_equipo_color())
    identidad = (10, "CD0011COLOR", "Konica Minolta bizhub C3320i")
    return equipo_ejemplo(identidad, "NORMAL", clases)


def equipos_ejemplo_2() -> list[EquipoEjemplo]:
    return [
        _equipo_sin_historia(),
        _equipo_salto_imposible(),
        _equipo_pendiente(),
        _equipo_en_transito(),
        _equipo_mono_y_color(),
    ]
