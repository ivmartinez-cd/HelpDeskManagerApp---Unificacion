"""Tests de AsignarZonaSucursal — zona de la fila de Tabla KM desde la alerta ALT008."""

import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.asignar_zona_sucursal import (
    AsignarZonaSucursal,
    AsignarZonaSucursalPorts,
)
from src.modules.liquidaciones.domain.errors import ParSinTablaKmError, SpstNoEncontradoError
from tests.unit.domain.liquidaciones.factories import make_spst, make_tabla_km
from tests.unit.domain.liquidaciones.fakes_config import (
    FakeConfigSpstRepository,
    FakeConfigTablaKmRepository,
)


def _use_case(
    tabla_km: FakeConfigTablaKmRepository, spsts: FakeConfigSpstRepository
) -> AsignarZonaSucursal:
    return AsignarZonaSucursal(AsignarZonaSucursalPorts(tabla_km=tabla_km, spsts=spsts))


class TestAsignarZonaSucursal:
    async def test_asigna_spst_buscando_la_fila_por_clave_normalizada(self) -> None:
        prestador_id = uuid.uuid4()
        spst = make_spst(prestador_id=prestador_id)
        fila = make_tabla_km(
            prestador_id=prestador_id, empresa_nombre="Diarco", sucursal_nombre="Santa Rosa "
        )
        tabla_km = FakeConfigTablaKmRepository([fila])

        actualizada = await _use_case(tabla_km, FakeConfigSpstRepository([spst])).execute(
            prestador_id, empresa_nombre="DIARCO", sucursal_nombre="santa rosa", spst_id=spst.id
        )

        assert actualizada.id == fila.id
        assert tabla_km.rows[0].spst_id == spst.id

    async def test_generica_deja_la_fila_sin_spst(self) -> None:
        prestador_id = uuid.uuid4()
        spst = make_spst(prestador_id=prestador_id)
        fila = make_tabla_km(prestador_id=prestador_id, spst_id=spst.id)
        tabla_km = FakeConfigTablaKmRepository([fila])

        await _use_case(tabla_km, FakeConfigSpstRepository([spst])).execute(
            prestador_id,
            empresa_nombre=fila.empresa_nombre,
            sucursal_nombre=fila.sucursal_nombre,
            spst_id=None,
        )

        assert tabla_km.rows[0].spst_id is None

    async def test_spst_de_otro_prestador_rechazado(self) -> None:
        prestador_id = uuid.uuid4()
        ajeno = make_spst()
        fila = make_tabla_km(prestador_id=prestador_id)

        with pytest.raises(SpstNoEncontradoError):
            await _use_case(
                FakeConfigTablaKmRepository([fila]), FakeConfigSpstRepository([ajeno])
            ).execute(
                prestador_id,
                empresa_nombre=fila.empresa_nombre,
                sucursal_nombre=fila.sucursal_nombre,
                spst_id=ajeno.id,
            )

    async def test_par_sin_fila_en_tabla_km_lanza_not_found(self) -> None:
        prestador_id = uuid.uuid4()

        with pytest.raises(ParSinTablaKmError):
            await _use_case(FakeConfigTablaKmRepository([]), FakeConfigSpstRepository([])).execute(
                prestador_id, empresa_nombre="OCA", sucursal_nombre="Santa Rosa", spst_id=None
            )
