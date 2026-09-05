"""Validación de solicitudes, pura y en el ORDEN EXACTO del legacy
(vacation.controller.ts). El caller precarga los datos (solicitudes activas,
exclusiones, rangos del cargo, saldo) y esta función solo decide.

Crear: activo → días>0 → año → fecha de inicio no pasada (bypass admin; regla
propia, no del legacy) → solape propio → exclusión mutua → límite por cargo →
ciclo abierto (bypass admin) → saldo → límite de adelanto.
Editar (paridad legacy, NO re-valida año ni ciclo): editable solo PENDING
(bypass admin) → activo → días>0 → solape → exclusión → límite → saldo con
add-back de los días actuales.
"""

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, timedelta

from src.modules.vacaciones.domain.entities.empleado import Empleado
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud, Solicitud
from src.modules.vacaciones.domain.errors import (
    AdelantoNoHabilitadoError,
    AnioMuyLejanoError,
    AnioPasadoError,
    CicloAunNoAbiertoError,
    CicloNoHabilitadoError,
    EmpleadoInactivoError,
    ExclusionMutuaError,
    FechaPasadaError,
    LimiteAdelantoError,
    LimiteCargoError,
    RangoSinDiasError,
    SaldoInsuficienteError,
    SolapamientoPropioError,
    SoloPendientesEditablesError,
)
from src.modules.vacaciones.domain.services.ciclo_policy import fecha_apertura_proximo_ciclo
from src.modules.vacaciones.domain.value_objects.config_vacaciones import ConfigVacaciones
from src.modules.vacaciones.domain.value_objects.saldo import Saldo


@dataclass(frozen=True, slots=True)
class DatosSolicitud:
    empleado: Empleado
    start_date: date
    end_date: date
    dias: int
    target_year: int


@dataclass(frozen=True, slots=True)
class ContextoAgenda:
    """Datos precargados. `rangos_mismo_cargo` y `solicitudes_contrapartes`
    deben venir ya filtrados a activas (PENDING|APPROVED) que solapan el rango
    pedido, excluyendo la solicitud en edición — igual que las queries legacy."""

    solicitudes_propias: tuple[Solicitud, ...]
    contrapartes: Mapping[uuid.UUID, str]
    solicitudes_contrapartes: tuple[Solicitud, ...]
    limite_cargo: int | None
    nombre_cargo: str
    rangos_mismo_cargo: tuple[tuple[date, date], ...]


@dataclass(frozen=True, slots=True)
class ContextoCreacion:
    hoy: date
    es_admin: bool
    config: ConfigVacaciones
    saldo: Saldo


@dataclass(frozen=True, slots=True)
class ContextoEdicion:
    es_admin: bool
    saldo: Saldo
    estado_actual: EstadoSolicitud
    dias_actuales: int


def validar_creacion(datos: DatosSolicitud, agenda: ContextoAgenda, ctx: ContextoCreacion) -> None:
    if not datos.empleado.esta_activo:
        raise EmpleadoInactivoError()
    _validar_dias(datos)
    _validar_anio(datos.target_year, ctx)
    _validar_fecha_pasada(datos, ctx)
    _validar_agenda(datos, agenda)
    _validar_ciclo_y_saldo(datos, ctx)
    _validar_limite_adelanto(datos, ctx)


def validar_edicion(datos: DatosSolicitud, agenda: ContextoAgenda, ctx: ContextoEdicion) -> None:
    if not ctx.es_admin and ctx.estado_actual is not EstadoSolicitud.PENDING:
        raise SoloPendientesEditablesError("editar")
    if not datos.empleado.esta_activo:
        raise EmpleadoInactivoError("No se pueden modificar solicitudes de empleados inactivos")
    _validar_dias(datos)
    _validar_agenda(datos, agenda)
    disponible_con_actual = ctx.saldo.available + ctx.dias_actuales
    if datos.dias > disponible_con_actual:
        raise SaldoInsuficienteError(datos.dias, disponible_con_actual)


def validar_anio_objetivo(
    target_year: int, *, hoy: date, es_admin: bool, config: ConfigVacaciones
) -> None:
    """Pre-chequeo público del año (mismas reglas que dentro de
    `validar_creacion`): el use case lo corre ANTES de asegurar ciclos para no
    crear filas de años inválidos — paridad con el orden del legacy."""
    ctx = ContextoCreacion(
        hoy=hoy,
        es_admin=es_admin,
        config=config,
        saldo=Saldo(annual=0, carry_over=0, used=0, pending=0, available=0, cycle_open=True),
    )
    _validar_anio(target_year, ctx)


def _validar_dias(datos: DatosSolicitud) -> None:
    if datos.dias <= 0:
        raise RangoSinDiasError()


def _validar_anio(target_year: int, ctx: ContextoCreacion) -> None:
    if target_year < ctx.hoy.year and not ctx.es_admin:
        raise AnioPasadoError()
    if target_year > ctx.hoy.year + 1:
        raise AnioMuyLejanoError()
    if target_year == ctx.hoy.year + 1:
        if not ctx.config.allow_advance_request:
            raise AdelantoNoHabilitadoError()
        apertura = fecha_apertura_proximo_ciclo(ctx.hoy, ctx.config)
        if ctx.hoy < apertura:
            raise CicloAunNoAbiertoError(target_year, apertura.strftime("%d/%m/%Y"))


def _validar_fecha_pasada(datos: DatosSolicitud, ctx: ContextoCreacion) -> None:
    if datos.start_date < ctx.hoy and not ctx.es_admin:
        raise FechaPasadaError()


def _validar_agenda(datos: DatosSolicitud, agenda: ContextoAgenda) -> None:
    _validar_solape_propio(datos, agenda.solicitudes_propias)
    _validar_exclusiones(agenda)
    _validar_limite_cargo(datos, agenda)


def _validar_solape_propio(datos: DatosSolicitud, propias: tuple[Solicitud, ...]) -> None:
    for solicitud in propias:
        if solicitud.solapa_con(datos.start_date, datos.end_date):
            raise SolapamientoPropioError()


def _validar_exclusiones(agenda: ContextoAgenda) -> None:
    for solicitud in agenda.solicitudes_contrapartes:
        nombre = agenda.contrapartes.get(solicitud.empleado_id, "otro empleado")
        raise ExclusionMutuaError(nombre)


def _validar_limite_cargo(datos: DatosSolicitud, agenda: ContextoAgenda) -> None:
    limite = agenda.limite_cargo
    if limite is None or len(agenda.rangos_mismo_cargo) < limite:
        return
    dia = datos.start_date
    while dia <= datos.end_date:
        cubren = sum(1 for (s, e) in agenda.rangos_mismo_cargo if s <= dia <= e)
        if cubren >= limite:
            raise LimiteCargoError(agenda.nombre_cargo, limite)
        dia += timedelta(days=1)


def _validar_ciclo_y_saldo(datos: DatosSolicitud, ctx: ContextoCreacion) -> None:
    if not ctx.saldo.cycle_open and not ctx.es_admin:
        raise CicloNoHabilitadoError(datos.target_year)
    if datos.dias > ctx.saldo.available:
        raise SaldoInsuficienteError(datos.dias, ctx.saldo.available)


def _validar_limite_adelanto(datos: DatosSolicitud, ctx: ContextoCreacion) -> None:
    if datos.target_year != ctx.hoy.year + 1 or ctx.config.max_advance_days <= 0:
        return
    total = ctx.saldo.used + ctx.saldo.pending + datos.dias
    if total > ctx.config.max_advance_days:
        raise LimiteAdelantoError(ctx.config.max_advance_days, datos.target_year)
