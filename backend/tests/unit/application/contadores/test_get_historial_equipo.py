from datetime import date

from src.modules.contadores.application.use_cases.get_historial_equipo import (
    GetHistorialEquipoUseCase,
)
from src.modules.contadores.domain.ports.historial_equipo_port import LecturaHistorialSiges


class FakePort:
    def __init__(self, lecturas: list[LecturaHistorialSiges]) -> None:
        self._lecturas = lecturas
        self.llamada: tuple[int, int, date] | None = None

    async def fetch_historial(
        self, id_maquina: int, id_clase_contador: int, desde: date
    ) -> list[LecturaHistorialSiges]:
        self.llamada = (id_maquina, id_clase_contador, desde)
        return self._lecturas


def _lectura(fecha: date, valor: float) -> LecturaHistorialSiges:
    return LecturaHistorialSiges(
        fecha=fecha,
        valor=valor,
        id_tipo_toma=1,
        tipo_toma_desc="Real",
        para_facturar=True,
        fc_nro_proceso=None,
        fc_periodo_hasta=None,
        fc_impresiones=None,
        fc_periodo_facturacion=None,
        id_factura=0,
        snap_id_empresa=1,
        snap_id_sucursal=1,
        snap_id_anexo=1,
    )


async def test_pide_desde_24_meses_atras() -> None:
    port = FakePort([_lectura(date(2026, 1, 1), 1000)])

    await GetHistorialEquipoUseCase(port).execute(5, 10, hoy=date(2026, 9, 8))

    assert port.llamada is not None
    _, _, desde = port.llamada
    assert desde == date(2024, 9, 1)


async def test_enriquece_las_lecturas_del_puerto() -> None:
    port = FakePort([_lectura(date(2026, 2, 1), 1500), _lectura(date(2026, 1, 1), 1000)])

    resultado = await GetHistorialEquipoUseCase(port).execute(5, 10, hoy=date(2026, 9, 8))

    assert len(resultado) == 2
    mas_reciente = next(r for r in resultado if r.fecha == date(2026, 2, 1))
    assert mas_reciente.delta == 500
