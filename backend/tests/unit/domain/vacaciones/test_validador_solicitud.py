"""Validador de solicitudes: orden de fallo exacto del legacy y bypass admin."""

import uuid
from datetime import date

import pytest

from src.modules.vacaciones.domain.entities.empleado import EstadoEmpleado
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud
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
from src.modules.vacaciones.domain.services.validador_solicitud import (
    ContextoAgenda,
    ContextoCreacion,
    ContextoEdicion,
    DatosSolicitud,
    validar_creacion,
    validar_edicion,
)
from tests.unit.domain.vacaciones.factories import (
    make_config,
    make_empleado,
    make_saldo,
    make_solicitud,
)

HOY = date(2026, 8, 13)


def _datos(**overrides: object) -> DatosSolicitud:
    defaults: dict[str, object] = {
        "empleado": make_empleado(),
        "start_date": date(2026, 9, 7),
        "end_date": date(2026, 9, 11),
        "dias": 7,
        "target_year": 2026,
    }
    defaults.update(overrides)
    return DatosSolicitud(**defaults)  # type: ignore[arg-type]


def _agenda(**overrides: object) -> ContextoAgenda:
    defaults: dict[str, object] = {
        "solicitudes_propias": (),
        "contrapartes": {},
        "solicitudes_contrapartes": (),
        "limite_cargo": None,
        "nombre_cargo": "Analista",
        "rangos_mismo_cargo": (),
    }
    defaults.update(overrides)
    return ContextoAgenda(**defaults)  # type: ignore[arg-type]


def _ctx(**overrides: object) -> ContextoCreacion:
    defaults: dict[str, object] = {
        "hoy": HOY,
        "es_admin": False,
        "config": make_config(),
        "saldo": make_saldo(),
    }
    defaults.update(overrides)
    return ContextoCreacion(**defaults)  # type: ignore[arg-type]


class TestValidarCreacion:
    def test_empleado_inactivo_falla_primero(self) -> None:
        datos = _datos(empleado=make_empleado(status=EstadoEmpleado.INACTIVE), dias=0)
        with pytest.raises(EmpleadoInactivoError):
            validar_creacion(datos, _agenda(), _ctx(saldo=make_saldo(available=0)))

    def test_rango_sin_dias(self) -> None:
        with pytest.raises(RangoSinDiasError):
            validar_creacion(_datos(dias=0), _agenda(), _ctx())

    def test_anio_pasado_bloqueado_sin_admin(self) -> None:
        with pytest.raises(AnioPasadoError):
            validar_creacion(_datos(target_year=2025), _agenda(), _ctx())

    def test_anio_pasado_permitido_para_admin(self) -> None:
        validar_creacion(_datos(target_year=2025), _agenda(), _ctx(es_admin=True))

    def test_fecha_de_inicio_pasada_bloqueada_sin_admin(self) -> None:
        with pytest.raises(FechaPasadaError):
            validar_creacion(
                _datos(start_date=date(2026, 3, 2), end_date=date(2026, 3, 4)),
                _agenda(),
                _ctx(),
            )

    def test_fecha_de_inicio_hoy_permitida_sin_admin(self) -> None:
        validar_creacion(_datos(start_date=HOY, end_date=date(2026, 8, 14)), _agenda(), _ctx())

    def test_fecha_de_inicio_pasada_permitida_para_admin(self) -> None:
        validar_creacion(
            _datos(start_date=date(2026, 3, 2), end_date=date(2026, 3, 4)),
            _agenda(),
            _ctx(es_admin=True),
        )

    def test_mas_de_un_anio_adelante_bloqueado_incluso_admin(self) -> None:
        with pytest.raises(AnioMuyLejanoError):
            validar_creacion(_datos(target_year=2028), _agenda(), _ctx(es_admin=True))

    def test_adelanto_deshabilitado(self) -> None:
        ctx = _ctx(config=make_config(allow_advance_request=False))
        with pytest.raises(AdelantoNoHabilitadoError):
            validar_creacion(_datos(target_year=2027), _agenda(), ctx)

    def test_adelanto_antes_de_la_apertura_informa_la_fecha(self) -> None:
        with pytest.raises(CicloAunNoAbiertoError) as exc:
            validar_creacion(_datos(target_year=2027), _agenda(), _ctx())
        assert "01/10/2026" in exc.value.message

    def test_solape_propio(self) -> None:
        propia = make_solicitud(start_date=date(2026, 9, 10), end_date=date(2026, 9, 15))
        with pytest.raises(SolapamientoPropioError):
            validar_creacion(_datos(), _agenda(solicitudes_propias=(propia,)), _ctx())

    def test_exclusion_mutua_reporta_el_nombre(self) -> None:
        contraparte_id = uuid.uuid4()
        agenda = _agenda(
            contrapartes={contraparte_id: "Martín García"},
            solicitudes_contrapartes=(make_solicitud(empleado_id=contraparte_id),),
        )
        with pytest.raises(ExclusionMutuaError) as exc:
            validar_creacion(_datos(), agenda, _ctx())
        assert "Martín García" in exc.value.message

    def test_limite_cargo_cuenta_por_dia_no_por_cantidad(self) -> None:
        # 2 rangos solapados con el pedido pero nunca el mismo día → no falla
        agenda = _agenda(
            limite_cargo=2,
            rangos_mismo_cargo=(
                (date(2026, 9, 7), date(2026, 9, 8)),
                (date(2026, 9, 10), date(2026, 9, 11)),
            ),
        )
        validar_creacion(_datos(), agenda, _ctx())

    def test_limite_cargo_excedido_en_algun_dia(self) -> None:
        agenda = _agenda(
            limite_cargo=2,
            nombre_cargo="Técnico N2",
            rangos_mismo_cargo=(
                (date(2026, 9, 7), date(2026, 9, 9)),
                (date(2026, 9, 9), date(2026, 9, 11)),
            ),
        )
        with pytest.raises(LimiteCargoError) as exc:
            validar_creacion(_datos(), agenda, _ctx())
        assert "Técnico N2" in exc.value.message

    def test_ciclo_cerrado_bloquea_sin_admin(self) -> None:
        with pytest.raises(CicloNoHabilitadoError):
            validar_creacion(_datos(), _agenda(), _ctx(saldo=make_saldo(cycle_open=False)))

    def test_ciclo_cerrado_permitido_para_admin(self) -> None:
        validar_creacion(
            _datos(), _agenda(), _ctx(es_admin=True, saldo=make_saldo(cycle_open=False))
        )

    def test_saldo_insuficiente(self) -> None:
        with pytest.raises(SaldoInsuficienteError) as exc:
            validar_creacion(_datos(dias=15), _agenda(), _ctx())
        assert "solicita 15" in exc.value.message
        assert "dispone de 14" in exc.value.message

    def test_limite_de_adelanto(self) -> None:
        ctx = _ctx(
            hoy=date(2026, 11, 1),
            config=make_config(max_advance_days=10),
            saldo=make_saldo(used=5, pending=3, available=6),
        )
        # Fechas futuras respecto de `hoy`: la regla de fecha pasada no debe
        # tapar la del límite de adelanto.
        datos = _datos(
            start_date=date(2027, 1, 4), end_date=date(2027, 1, 6), target_year=2027, dias=3
        )
        with pytest.raises(LimiteAdelantoError):
            validar_creacion(datos, _agenda(), ctx)

    def test_feliz_sin_errores(self) -> None:
        validar_creacion(_datos(), _agenda(), _ctx())


class TestValidarEdicion:
    def _ctx_ed(self, **overrides: object) -> ContextoEdicion:
        defaults: dict[str, object] = {
            "es_admin": False,
            "saldo": make_saldo(available=2),
            "estado_actual": EstadoSolicitud.PENDING,
            "dias_actuales": 5,
        }
        defaults.update(overrides)
        return ContextoEdicion(**defaults)  # type: ignore[arg-type]

    def test_no_pendiente_bloqueada_sin_admin(self) -> None:
        with pytest.raises(SoloPendientesEditablesError):
            validar_edicion(
                _datos(), _agenda(), self._ctx_ed(estado_actual=EstadoSolicitud.APPROVED)
            )

    def test_no_pendiente_permitida_para_admin(self) -> None:
        validar_edicion(
            _datos(dias=7),
            _agenda(),
            self._ctx_ed(es_admin=True, estado_actual=EstadoSolicitud.APPROVED),
        )

    def test_empleado_inactivo_bloquea_incluso_admin(self) -> None:
        datos = _datos(empleado=make_empleado(status=EstadoEmpleado.INACTIVE))
        with pytest.raises(EmpleadoInactivoError):
            validar_edicion(datos, _agenda(), self._ctx_ed(es_admin=True))

    def test_saldo_con_add_back_de_los_dias_actuales(self) -> None:
        # disponible 2 + 5 actuales = 7 → pedir 7 pasa, 8 falla
        validar_edicion(_datos(dias=7), _agenda(), self._ctx_ed())
        with pytest.raises(SaldoInsuficienteError) as exc:
            validar_edicion(_datos(dias=8), _agenda(), self._ctx_ed())
        assert "dispone de 7" in exc.value.message

    def test_no_valida_anio_ni_ciclo(self) -> None:
        # target en el pasado y ciclo cerrado: la edición no los mira (paridad)
        ctx = self._ctx_ed(saldo=make_saldo(available=10, cycle_open=False))
        validar_edicion(_datos(target_year=2024, dias=3), _agenda(), ctx)
