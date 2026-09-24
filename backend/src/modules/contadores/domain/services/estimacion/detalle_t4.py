"""Textos `DetalleCalculo` / `EtiquetaNivel` de `EstimarConT4ST` del legacy,
carácter por carácter."""

from dataclasses import dataclass

from src.modules.contadores.domain.services.estimacion.formato_es_ar import (
    con_signo,
    entero,
    fecha_corta,
    hasta_dos_decimales,
)
from src.modules.contadores.domain.services.estimacion.redondeo import a_decimal
from src.modules.contadores.domain.services.estimacion.regla_de_tres import ReglaDeTres
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef


@dataclass(frozen=True, slots=True)
class Partida:
    """Partida elegida para proyectar el T4 (`partida` del legacy)."""

    lectura: LecturaRef
    descripcion: str  # "últ. real" / "últ. facturado"


_REVISADO = "T4 revisado (Para_Facturar>0)"
_SIN_REVISAR = "⚠ T4 SIN revisar (Para_Facturar=0) — confirmar"
_SIN_PAR = "T4 ST tal cual como Llegada — sin par válido para proyectar (P/L < 15d o P > L) · "
_BACKUP_REVISADO = "T4 ST revisado (Para_Facturar>0) como Llegada — dato confiable."
_BACKUP_SIN_REVISAR = (
    "T4 ST SIN revisar (Para_Facturar=0) como Llegada — confirmar antes de facturar."
)


def _nota_revision(revisado: bool) -> str:
    return _REVISADO if revisado else _SIN_REVISAR


def detalle_t4_proyectado(partida: Partida, t4: LecturaRef, r3: ReglaDeTres, revisado: bool) -> str:
    p = partida.lectura
    return (
        f"T4 ST proyectado · P:{fecha_corta(p.fecha)}={entero(a_decimal(p.valor))} "
        f"({partida.descripcion}) · L(T4):{fecha_corta(t4.fecha)}={entero(a_decimal(t4.valor))} · "
        f"Δ{r3.dias_par}d activos · {hasta_dos_decimales(r3.tasa_diaria)}/día · "
        f"{con_signo(r3.dias_proyectados)}d a fecha objetivo · {_nota_revision(revisado)}"
    )


def etiqueta_t4_proyectado(partida: Partida, revisado: bool) -> str:
    return f"T4 ST proyectado · Partida: {partida.descripcion} · {_nota_revision(revisado)}"


def detalle_t4_tal_cual(revisado: bool, sin_par: bool) -> str:
    """`sin_par`: se quiso proyectar pero no hubo Partida válida; si no, es
    un Backup (no se proyecta)."""
    if sin_par:
        return _SIN_PAR + _nota_revision(revisado)
    return _BACKUP_REVISADO if revisado else _BACKUP_SIN_REVISAR
