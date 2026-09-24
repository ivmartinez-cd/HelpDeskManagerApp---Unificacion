"""`#IdLog` del CSV: el número entero más alto de la máquina en la auditoría
(`CsvExportService` v1.7: `Max(e.Id)` de `Estim_Log`), no un prefijo del
UUID; la observación manual es la última no vacía."""

import uuid

from src.modules.contadores.infrastructure.models.estim_log_model import EstimLogModel
from src.modules.contadores.infrastructure.repositories.sqlalchemy_estim_log_repository import (
    _acumular,
)


def _row(nro: int, observacion: str | None) -> EstimLogModel:
    return EstimLogModel(id=uuid.uuid4(), nro=nro, id_maquina=7, observacion=observacion)


def test_id_log_es_el_numero_mas_alto_y_la_observacion_la_ultima_no_vacia() -> None:
    resumen = None
    for row in (_row(12, "revisar"), _row(40, "  "), _row(35, None)):
        resumen = _acumular(row, resumen)

    assert resumen is not None
    assert (resumen.id_log_corto, resumen.observacion_manual) == ("40", "revisar")
