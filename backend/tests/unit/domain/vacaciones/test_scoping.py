"""Alcance de datos por actor: propio / sector / global (paridad legacy)."""

import uuid

import pytest

from src.modules.vacaciones.domain.errors import OperacionNoPermitidaError
from src.modules.vacaciones.domain.services.scoping import (
    DatosSolicitudAjena,
    alcance_para_calendario,
    alcance_para_listado,
    verificar_puede_decidir,
    verificar_puede_modificar_solicitud,
    verificar_puede_ver_solicitud,
)
from tests.unit.domain.vacaciones.factories import make_actor

SECTOR = uuid.uuid4()
OTRO_SECTOR = uuid.uuid4()
EMPLEADO = uuid.uuid4()
OTRO_EMPLEADO = uuid.uuid4()


class TestAlcanceParaListado:
    def test_admin_ve_todo(self) -> None:
        filtro = alcance_para_listado(make_actor(es_admin=True))
        assert filtro.department_id is None
        assert filtro.empleado_id is None
        assert filtro.sin_acceso is False

    def test_jefe_ve_su_sector(self) -> None:
        filtro = alcance_para_listado(make_actor(sector_gestionado_id=SECTOR))
        assert filtro.department_id == SECTOR

    def test_empleado_ve_lo_propio(self) -> None:
        filtro = alcance_para_listado(make_actor(empleado_id=EMPLEADO))
        assert filtro.empleado_id == EMPLEADO

    def test_usuario_sin_vinculo_no_ve_nada(self) -> None:
        assert alcance_para_listado(make_actor()).sin_acceso is True


class TestAlcanceParaCalendario:
    def test_empleado_ve_el_calendario_completo(self) -> None:
        filtro = alcance_para_calendario(make_actor(empleado_id=EMPLEADO))
        assert filtro.department_id is None
        assert filtro.sin_acceso is False

    def test_jefe_lo_ve_acotado_a_su_sector(self) -> None:
        filtro = alcance_para_calendario(make_actor(sector_gestionado_id=SECTOR))
        assert filtro.department_id == SECTOR


class TestVerificarPuedeDecidir:
    def _ajena(self) -> DatosSolicitudAjena:
        return DatosSolicitudAjena(empleado_id=OTRO_EMPLEADO, department_id=SECTOR)

    def test_admin_decide_todo_incluso_lo_propio(self) -> None:
        actor = make_actor(es_admin=True, empleado_id=OTRO_EMPLEADO)
        verificar_puede_decidir(actor, self._ajena())

    def test_jefe_no_decide_fuera_de_su_sector(self) -> None:
        actor = make_actor(sector_gestionado_id=OTRO_SECTOR)
        with pytest.raises(OperacionNoPermitidaError) as exc:
            verificar_puede_decidir(actor, self._ajena())
        assert "tu sector" in exc.value.message

    def test_jefe_no_decide_su_propia_solicitud(self) -> None:
        actor = make_actor(sector_gestionado_id=SECTOR, empleado_id=OTRO_EMPLEADO)
        with pytest.raises(OperacionNoPermitidaError) as exc:
            verificar_puede_decidir(actor, self._ajena())
        assert "propia" in exc.value.message

    def test_jefe_decide_en_su_sector(self) -> None:
        actor = make_actor(sector_gestionado_id=SECTOR, empleado_id=EMPLEADO)
        verificar_puede_decidir(actor, self._ajena())

    def test_aprobador_global_decide_ajenas_pero_no_la_propia(self) -> None:
        global_ = make_actor(empleado_id=EMPLEADO)
        verificar_puede_decidir(global_, self._ajena())
        propia = DatosSolicitudAjena(empleado_id=EMPLEADO, department_id=SECTOR)
        with pytest.raises(OperacionNoPermitidaError):
            verificar_puede_decidir(global_, propia)


class TestVerificarPuedeVer:
    def test_duenio_jefe_y_admin_pueden_ver(self) -> None:
        datos = DatosSolicitudAjena(empleado_id=EMPLEADO, department_id=SECTOR)
        verificar_puede_ver_solicitud(make_actor(empleado_id=EMPLEADO), datos)
        verificar_puede_ver_solicitud(make_actor(sector_gestionado_id=SECTOR), datos)
        verificar_puede_ver_solicitud(make_actor(es_admin=True), datos)

    def test_tercero_no_puede_ver(self) -> None:
        datos = DatosSolicitudAjena(empleado_id=EMPLEADO, department_id=SECTOR)
        with pytest.raises(OperacionNoPermitidaError):
            verificar_puede_ver_solicitud(make_actor(empleado_id=OTRO_EMPLEADO), datos)


class TestVerificarPuedeModificar:
    def test_duenio_y_admin_pueden(self) -> None:
        verificar_puede_modificar_solicitud(make_actor(empleado_id=EMPLEADO), EMPLEADO)
        verificar_puede_modificar_solicitud(make_actor(es_admin=True), EMPLEADO)

    def test_el_jefe_no_modifica_solicitudes_ajenas(self) -> None:
        actor = make_actor(sector_gestionado_id=SECTOR)
        with pytest.raises(OperacionNoPermitidaError):
            verificar_puede_modificar_solicitud(actor, EMPLEADO)
