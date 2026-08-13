"""Conteo mensual del reporte de descuentos (paridad discountedReport legacy)."""

import uuid
from datetime import UTC, date, datetime

from src.modules.vacaciones.domain.entities.ausencia import Ausencia, TipoAusencia
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud
from src.modules.vacaciones.domain.services.descuentos import (
    dias_corridos_en_mes,
    dias_descontados_en_mes,
)

_EMPLEADO = uuid.uuid4()


def _ausencia(
    start: date, end: date, tipo: TipoAusencia, *, half_day: bool = False
) -> Ausencia:
    return Ausencia(
        id=uuid.uuid4(),
        empleado_id=_EMPLEADO,
        start_date=start,
        end_date=end,
        days_count=(end - start).days + 1,
        half_day=half_day,
        tipo=tipo,
        reason=None,
        status=EstadoSolicitud.APPROVED,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


class TestDiasDescontadosEnMes:
    def test_solo_cuenta_dias_habiles(self) -> None:
        # Vie 7 a lun 10 de agosto 2026: vie + lun hábiles, finde no cuenta.
        ausencias = [
            _ausencia(date(2026, 8, 7), date(2026, 8, 10), TipoAusencia.DESCUENTO_DIA)
        ]
        total = dias_descontados_en_mes(
            ausencias, year=2026, month=8, feriados=frozenset()
        )
        assert total == 2.0

    def test_medio_dia_computa_media_jornada(self) -> None:
        ausencias = [
            _ausencia(
                date(2026, 8, 3), date(2026, 8, 3), TipoAusencia.DESCUENTO_DIA, half_day=True
            )
        ]
        total = dias_descontados_en_mes(
            ausencias, year=2026, month=8, feriados=frozenset()
        )
        assert total == 0.5

    def test_feriado_no_cuenta(self) -> None:
        ausencias = [
            _ausencia(date(2026, 8, 17), date(2026, 8, 17), TipoAusencia.DESCUENTO_DIA)
        ]
        total = dias_descontados_en_mes(
            ausencias, year=2026, month=8, feriados=frozenset({date(2026, 8, 17)})
        )
        assert total == 0.0

    def test_otros_tipos_no_descuentan(self) -> None:
        ausencias = [
            _ausencia(date(2026, 8, 3), date(2026, 8, 5), TipoAusencia.BAJA_ENFERMEDAD)
        ]
        total = dias_descontados_en_mes(
            ausencias, year=2026, month=8, feriados=frozenset()
        )
        assert total == 0.0


class TestDiasCorridosEnMes:
    def test_cuenta_dias_corridos_incluso_finde(self) -> None:
        # Guardia sáb 20 y dom 21 de junio 2026.
        ausencias = [_ausencia(date(2026, 6, 20), date(2026, 6, 21), TipoAusencia.GUARDIA)]
        assert dias_corridos_en_mes(ausencias, TipoAusencia.GUARDIA, year=2026, month=6) == 2

    def test_recorta_al_mes_pedido(self) -> None:
        ausencias = [
            _ausencia(date(2026, 7, 30), date(2026, 8, 2), TipoAusencia.BAJA_ENFERMEDAD)
        ]
        assert (
            dias_corridos_en_mes(ausencias, TipoAusencia.BAJA_ENFERMEDAD, year=2026, month=8)
            == 2
        )
