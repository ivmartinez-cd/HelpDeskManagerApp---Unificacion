"""FijarKmReferencia: km cobrados → km de referencia de la fila de Tabla KM."""

import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.fijar_km_referencia import (
    FijarKmReferencia,
    FijarKmReferenciaPorts,
)
from src.modules.liquidaciones.domain.errors import KmReferenciaInvalidoError, ParSinTablaKmError
from tests.unit.domain.liquidaciones.factories import make_tabla_km
from tests.unit.domain.liquidaciones.fakes_config import FakeConfigTablaKmRepository


class TestFijarKmReferencia:
    async def test_fija_los_km_en_la_fila_del_par(self) -> None:
        prestador_id = uuid.uuid4()
        fila = make_tabla_km(
            prestador_id=prestador_id,
            empresa_nombre="Diarco",
            sucursal_nombre="Santa Rosa",
            kms_a_facturar=0.0,
        )
        repo = FakeConfigTablaKmRepository([fila])

        actualizada = await FijarKmReferencia(FijarKmReferenciaPorts(repo)).execute(
            prestador_id, empresa_nombre="DIARCO", sucursal_nombre="santa rosa", kms=26.0
        )

        assert actualizada.id == fila.id
        assert repo.rows[0].kms_a_facturar == 26.0

    async def test_km_cero_rechazado(self) -> None:
        with pytest.raises(KmReferenciaInvalidoError):
            await FijarKmReferencia(
                FijarKmReferenciaPorts(FakeConfigTablaKmRepository([]))
            ).execute(uuid.uuid4(), empresa_nombre="X", sucursal_nombre="Y", kms=0)

    async def test_par_sin_fila_lanza_not_found(self) -> None:
        with pytest.raises(ParSinTablaKmError):
            await FijarKmReferencia(
                FijarKmReferenciaPorts(FakeConfigTablaKmRepository([]))
            ).execute(uuid.uuid4(), empresa_nombre="X", sucursal_nombre="Y", kms=10)
