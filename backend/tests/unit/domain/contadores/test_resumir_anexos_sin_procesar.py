from datetime import UTC, datetime

from src.modules.contadores.application.dtos.anexo_sin_procesar import AnexoSinProcesar
from src.modules.contadores.application.use_cases.resumir_anexos_sin_procesar import (
    resumir_anexos_sin_procesar,
)

_CONSULTADO_EN = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)


def _anexo(grupo: str, id_anexo: int) -> AnexoSinProcesar:
    return AnexoSinProcesar(
        id_anexo=id_anexo,
        anexo=f"COD{id_anexo}/A",
        grupo=grupo,
        cliente=grupo,
        operador_id="op1",
        fecha_evento="2026-08-05",
        dias_vencido=26,
        periodo_esperado="202607",
        ultimo_periodo_procesado="202606",
    )


def test_resumen_cuenta_clientes_distintos_y_anexos_totales() -> None:
    anexos = [_anexo("Sika", 1), _anexo("Sika", 2), _anexo("Sika", 3), _anexo("Opdea", 4)]
    resumen = resumir_anexos_sin_procesar(anexos, consultado_en=_CONSULTADO_EN)
    assert resumen.clientes == 2
    assert resumen.anexos == 4
    assert resumen.consultado_en == _CONSULTADO_EN


def test_resumen_vacio() -> None:
    resumen = resumir_anexos_sin_procesar([], consultado_en=_CONSULTADO_EN)
    assert resumen.clientes == 0
    assert resumen.anexos == 0
