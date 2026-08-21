"""Reglas de acceso y conteo de las bajas (paridad absence.controller legacy)."""

import uuid
from datetime import UTC, date, datetime

import pytest

from src.modules.vacaciones.domain.entities.ausencia import Ausencia, TipoAusencia
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud
from src.modules.vacaciones.domain.errors import (
    OperacionNoPermitidaError,
    SoloAusenciasPendientesError,
)
from src.modules.vacaciones.domain.services.reglas_ausencia import (
    dias_de_baja,
    resolver_empleados_destino,
    verificar_puede_cambiar_estado,
    verificar_puede_modificar_ausencia,
)
from tests.unit.domain.vacaciones.factories import make_actor


def make_ausencia(**overrides: object) -> Ausencia:
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "empleado_id": uuid.uuid4(),
        "start_date": date(2026, 8, 3),
        "end_date": date(2026, 8, 4),
        "days_count": 2,
        "half_day": False,
        "tipo": TipoAusencia.BAJA_ENFERMEDAD,
        "reason": None,
        "status": EstadoSolicitud.APPROVED,
        "created_at": datetime(2026, 8, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    return Ausencia(**defaults)  # type: ignore[arg-type]


class TestDiasDeBaja:
    def test_dias_corridos_inclusive(self) -> None:
        # lunes a miércoles = 3 días corridos
        assert dias_de_baja(date(2026, 8, 3), date(2026, 8, 5)) == 3

    def test_fin_viernes_extiende_finde(self) -> None:
        # mismo calendarDaysBetween del legacy: viernes suma sáb+dom
        assert dias_de_baja(date(2026, 8, 7), date(2026, 8, 7)) == 3

    def test_fin_sabado_extiende_domingo(self) -> None:
        assert dias_de_baja(date(2026, 8, 8), date(2026, 8, 8)) == 2

    def test_rango_invertido_da_cero(self) -> None:
        assert dias_de_baja(date(2026, 8, 5), date(2026, 8, 3)) == 0


class TestResolverEmpleadosDestino:
    def test_admin_usa_lista_dada(self) -> None:
        ids = [uuid.uuid4(), uuid.uuid4()]
        actor = make_actor(es_admin=True)
        assert resolver_empleados_destino(actor, ids) == ids

    def test_jefe_usa_lista_dada_sin_chequeo_de_sector(self) -> None:
        ids = [uuid.uuid4()]
        actor = make_actor(sector_gestionado_id=uuid.uuid4())
        assert resolver_empleados_destino(actor, ids) == ids

    def test_empleado_ignora_lista_y_usa_el_propio(self) -> None:
        propio = uuid.uuid4()
        actor = make_actor(empleado_id=propio)
        assert resolver_empleados_destino(actor, [uuid.uuid4()]) == [propio]

    def test_admin_sin_lista_cae_al_propio(self) -> None:
        propio = uuid.uuid4()
        actor = make_actor(es_admin=True, empleado_id=propio)
        assert resolver_empleados_destino(actor, []) == [propio]

    def test_sin_destino_lanza(self) -> None:
        with pytest.raises(Exception, match="No se ha indicado"):
            resolver_empleados_destino(make_actor(), [])


class TestVerificarPuedeModificar:
    def test_admin_modifica_cualquiera(self) -> None:
        actor = make_actor(es_admin=True)
        verificar_puede_modificar_ausencia(actor, make_ausencia(), accion="editar")

    def test_dueno_solo_pendientes(self) -> None:
        empleado_id = uuid.uuid4()
        actor = make_actor(empleado_id=empleado_id)
        pendiente = make_ausencia(
            empleado_id=empleado_id, status=EstadoSolicitud.PENDING
        )
        verificar_puede_modificar_ausencia(actor, pendiente, accion="editar")
        aprobada = make_ausencia(empleado_id=empleado_id)
        with pytest.raises(SoloAusenciasPendientesError):
            verificar_puede_modificar_ausencia(actor, aprobada, accion="editar")

    def test_jefe_no_modifica_ajenas(self) -> None:
        # Paridad legacy: el jefe crea bajas pero NO edita/borra las ajenas.
        actor = make_actor(sector_gestionado_id=uuid.uuid4())
        with pytest.raises(OperacionNoPermitidaError):
            verificar_puede_modificar_ausencia(actor, make_ausencia(), accion="editar")


class TestVerificarPuedeCambiarEstado:
    def test_solo_admin(self) -> None:
        verificar_puede_cambiar_estado(make_actor(es_admin=True))
        with pytest.raises(OperacionNoPermitidaError):
            verificar_puede_cambiar_estado(make_actor(empleado_id=uuid.uuid4()))


# --- Solicitudes de home office / cambio de horario (2026-08-21) ---------------

from datetime import time as _time  # noqa: E402

from src.modules.vacaciones.domain.entities.ausencia import (  # noqa: E402
    TipoAusencia as _Tipo,
)
from src.modules.vacaciones.domain.services.reglas_ausencia import (  # noqa: E402
    estado_inicial,
    validar_horario,
)
from src.shared.domain.errors import ValidationError as _ValidationError  # noqa: E402


def test_estado_inicial_admin_y_jefe_aprobada_empleado_pendiente() -> None:
    assert estado_inicial(make_actor(es_admin=True)) is EstadoSolicitud.APPROVED
    assert estado_inicial(make_actor(sector_gestionado_id=uuid.uuid4())) is EstadoSolicitud.APPROVED
    assert estado_inicial(make_actor(empleado_id=uuid.uuid4())) is EstadoSolicitud.PENDING


def test_cambio_de_horario_exige_rango_valido() -> None:
    validar_horario(_Tipo.CAMBIO_HORARIO, _time(8, 0), _time(17, 0))
    with pytest.raises(_ValidationError):
        validar_horario(_Tipo.CAMBIO_HORARIO, None, None)
    with pytest.raises(_ValidationError):
        validar_horario(_Tipo.CAMBIO_HORARIO, _time(17, 0), _time(8, 0))


def test_otros_tipos_no_llevan_horario() -> None:
    validar_horario(_Tipo.HOME_OFFICE, None, None)
    with pytest.raises(_ValidationError):
        validar_horario(_Tipo.HOME_OFFICE, _time(8, 0), _time(17, 0))
