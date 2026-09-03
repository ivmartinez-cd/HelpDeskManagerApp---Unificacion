"""RunEstimationZeroDesdeProcesoUseCase con un puerto y un writer fake:
verifica que reusa `build_estimation_zero_rows` (mismo filtro/agrupado que
el camino CSV) y que el cliente del writer sale del proceso, no de un
input del formulario."""

import pytest

from src.modules.contadores.application.dtos.run_estimation_zero_from_proceso_request import (
    RunEstimationZeroFromProcesoRequest,
)
from src.modules.contadores.application.use_cases.run_estimation_zero_desde_proceso import (
    RunEstimationZeroDesdeProcesoUseCase,
)
from src.modules.contadores.domain.errors import NoFaltaContadorRowsError
from src.modules.contadores.domain.ports.falta_contador_proceso_port import (
    ProcesoFaltaContador,
)
from src.modules.contadores.domain.value_objects.estimation_zero_row import EstimationZeroRow
from src.modules.contadores.domain.value_objects.falta_contador_source_row import (
    FaltaContadorSourceRow,
)


class FakePort:
    def __init__(self, proceso: ProcesoFaltaContador) -> None:
        self._proceso = proceso

    async def fetch(self, nro_proceso: int) -> ProcesoFaltaContador:
        return self._proceso


class FakeWriter:
    def __init__(self) -> None:
        self.llamada: tuple[list[EstimationZeroRow], str, str] | None = None

    def write(self, rows: list[EstimationZeroRow], *, output_dir: str, cliente: str) -> str:
        self.llamada = (rows, output_dir, cliente)
        return f"{output_dir}/{cliente}_Limpieza_Cero.csv"


async def test_execute_arma_filas_y_escribe_con_el_cliente_del_proceso() -> None:
    proceso = ProcesoFaltaContador(
        cliente="Cepas Argentina",
        filas=[
            FaltaContadorSourceRow(
                tipo="FALTA CONTADOR", serie="SER1", contador=100, nombre_clase="Mono"
            ),
        ],
    )
    writer = FakeWriter()
    use_case = RunEstimationZeroDesdeProcesoUseCase(FakePort(proceso), writer)

    path = await use_case.execute(
        RunEstimationZeroFromProcesoRequest(
            nro_proceso=99070, fecha_nueva="07/08/2026", output_dir="/tmp/out"
        )
    )

    assert path == "/tmp/out/Cepas Argentina_Limpieza_Cero.csv"
    assert writer.llamada is not None
    rows, output_dir, cliente = writer.llamada
    assert output_dir == "/tmp/out"
    assert cliente == "Cepas Argentina"
    assert [r.serie for r in rows] == ["SER1"]


async def test_execute_sin_filas_falta_contador_propaga_el_error_del_builder() -> None:
    proceso = ProcesoFaltaContador(cliente="Cliente SA", filas=[])
    use_case = RunEstimationZeroDesdeProcesoUseCase(FakePort(proceso), FakeWriter())

    with pytest.raises(NoFaltaContadorRowsError):
        await use_case.execute(
            RunEstimationZeroFromProcesoRequest(
                nro_proceso=1, fecha_nueva="07/08/2026", output_dir="/tmp/out"
            )
        )
