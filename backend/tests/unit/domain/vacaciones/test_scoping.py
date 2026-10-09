"""Alcance de datos por actor: propio / sector / global (paridad legacy)."""

import uuid

import pytest

from src.modules.vacaciones.domain.errors import OperacionNoPermitidaError
from src.modules.vacaciones.domain.services.scoping import (
    DatosSolicitudAjena,
    alcance_para_calendario,
    alcance_para_listado,
    verificar_admin_global,
    verificar_administra,
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

    def test_admin_decide_lo_ajeno_pero_no_lo_propio(self) -> None:
        verificar_puede_decidir(make_actor(es_admin=True, empleado_id=EMPLEADO), self._ajena())
        actor = make_actor(es_admin=True, empleado_id=OTRO_EMPLEADO)
        with pytest.raises(OperacionNoPermitidaError, match="propia"):
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
        datos = DatosSolicitudAjena(empleado_id=EMPLEADO, department_id=SECTOR)
        verificar_puede_modificar_solicitud(make_actor(empleado_id=EMPLEADO), datos)
        verificar_puede_modificar_solicitud(make_actor(es_admin=True), datos)

    def test_el_jefe_no_modifica_solicitudes_ajenas(self) -> None:
        actor = make_actor(sector_gestionado_id=SECTOR)
        datos = DatosSolicitudAjena(empleado_id=EMPLEADO, department_id=SECTOR)
        with pytest.raises(OperacionNoPermitidaError):
            verificar_puede_modificar_solicitud(actor, datos)

    def test_admin_de_sector_modifica_solo_las_de_su_sector(self) -> None:
        actor = make_actor(es_admin=True, sector_gestionado_id=SECTOR)
        verificar_puede_modificar_solicitud(
            actor, DatosSolicitudAjena(empleado_id=EMPLEADO, department_id=SECTOR)
        )
        with pytest.raises(OperacionNoPermitidaError):
            verificar_puede_modificar_solicitud(
                actor, DatosSolicitudAjena(empleado_id=EMPLEADO, department_id=uuid.uuid4())
            )


class TestAdminDeSector:
    """Admin (`manage`) con sector asignado: administra su sector y no ve
    gente de otros (caso jefe de Taller y Stock, 2026-10-09)."""

    def test_el_sector_manda_sobre_manage(self) -> None:
        actor = make_actor(es_admin=True, sector_gestionado_id=SECTOR)
        assert actor.es_admin_global is False
        assert actor.es_jefe_de_sector is True
        assert alcance_para_listado(actor).department_id == SECTOR
        assert alcance_para_calendario(actor).department_id == SECTOR

    def test_administra_solo_su_sector(self) -> None:
        actor = make_actor(es_admin=True, sector_gestionado_id=SECTOR)
        assert actor.administra(SECTOR) is True
        assert actor.administra(OTRO_SECTOR) is False
        assert make_actor(es_admin=True).administra(OTRO_SECTOR) is True
        assert make_actor(sector_gestionado_id=SECTOR).administra(SECTOR) is False

    def test_no_ve_ni_decide_solicitudes_de_otro_sector(self) -> None:
        actor = make_actor(es_admin=True, sector_gestionado_id=SECTOR)
        ajena = DatosSolicitudAjena(empleado_id=OTRO_EMPLEADO, department_id=OTRO_SECTOR)
        with pytest.raises(OperacionNoPermitidaError):
            verificar_puede_ver_solicitud(actor, ajena)
        with pytest.raises(OperacionNoPermitidaError):
            verificar_puede_decidir(actor, ajena)
        propia_del_sector = DatosSolicitudAjena(empleado_id=EMPLEADO, department_id=SECTOR)
        verificar_puede_ver_solicitud(actor, propia_del_sector)
        verificar_puede_decidir(actor, propia_del_sector)

    def test_acciones_globales_solo_admin_general(self) -> None:
        verificar_admin_global(make_actor(es_admin=True))
        with pytest.raises(OperacionNoPermitidaError):
            verificar_admin_global(make_actor(es_admin=True, sector_gestionado_id=SECTOR))
        with pytest.raises(OperacionNoPermitidaError):
            verificar_administra(
                make_actor(es_admin=True, sector_gestionado_id=SECTOR), OTRO_SECTOR
            )
