"""Decisión vigente del operador sobre una fila del tablero de UN proceso — el
equivalente de "la última entrada de `Estim_Log` por (NroProceso, IdMaquina,
IdClaseContador)" que el legacy relee al cargar la grilla
(`SqliteAuditRepository.GetUltimasDecisionesProcesoAsync` +
`GrillaEstimacion.RestaurarOverridesAsync`).

No guarda un valor calculado: guarda la acción y sus insumos (el método
forzado, o la Partida/Llegada elegidas con su `ID_Contador`) para volver a
correr el motor con los datos del día, como el legacy — un valor congelado se
arrastraría igual aunque cambien las lecturas o el proceso."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef

# Mismos nombres que `AccionAudit` del legacy.
AccionDecision = Literal[
    "PL_Manual",
    "ForzarCascada",
    "ForzarEntreReales",
    "MarcarPendiente",
    "AceptarSugerencia",
]


@dataclass(frozen=True, slots=True)
class LecturaElegidaDto:
    """Una Partida o Llegada elegida a mano (`CandidatoContador` del legacy).
    `id_contador` es `None` solo en el modo ejemplo (sus lecturas no existen
    en Siges); `para_facturar` es el de `Tipo_Toma`."""

    fecha: date
    valor: float
    tipo_toma: int
    id_contador: int | None = None
    para_facturar: bool = True

    def a_lectura_ref(self) -> LecturaRef:
        return LecturaRef(self.valor, self.fecha, self.tipo_toma, self.para_facturar)


@dataclass(frozen=True, slots=True)
class ParPartidaLlegadaDto:
    """P/L manual de un equipo/clase, tal como la elige el operador en el
    panel de candidatos (vista previa o "Aceptar P/L manual")."""

    id_maquina: int
    clase: str
    partida: LecturaElegidaDto
    llegada: LecturaElegidaDto


@dataclass(frozen=True, slots=True)
class DecisionOperadorDto:
    """`partida`/`llegada` solo para `PL_Manual`. La observación que escriba
    el operador no es parte de la decisión: el legacy la graba solo en la
    auditoría (`Estim_Log.Observacion`) y no la muestra en la grilla.
    `actualizado_en` lo pone el repositorio al guardar."""

    accion: AccionDecision
    partida: LecturaElegidaDto | None = None
    llegada: LecturaElegidaDto | None = None
    actualizado_en: datetime | None = None


@dataclass(frozen=True, slots=True)
class ClaveDecisionDto:
    nro_proceso: int
    id_maquina: int
    clase: str


@dataclass(frozen=True, slots=True)
class SolicitudRestauracionDto:
    """Qué decisiones restaurar al armar el tablero de un proceso.
    `descartar_hasta` es el botón "Descartar y empezar limpio" del banner de
    restauración: el legacy solo limpia lo restaurado en pantalla (la
    auditoría queda y la próxima carga vuelve a restaurar), así que acá se
    ignoran las decisiones guardadas hasta ese momento y siguen valiendo las
    que el operador tome después."""

    nro_proceso: int
    descartar_hasta: datetime | None = None
