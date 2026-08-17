"""ReglaAlertaOut: tieneEvaluador refleja el catálogo real (ALT006/007 sin evaluador)."""

from src.modules.liquidaciones.presentation.schemas.reglas_alerta_schemas import ReglaAlertaOut
from tests.unit.domain.liquidaciones.factories import reglas_activas_default


def test_tiene_evaluador_por_codigo() -> None:
    reglas = reglas_activas_default()
    for codigo in ("ALT001", "ALT005"):
        if codigo in reglas:
            assert ReglaAlertaOut.from_entity(reglas[codigo]).tiene_evaluador is True


def test_alt006_y_alt007_sin_evaluador() -> None:
    import dataclasses

    base = next(iter(reglas_activas_default().values()))
    for codigo in ("ALT006", "ALT007"):
        regla = dataclasses.replace(base, codigo=codigo)
        assert ReglaAlertaOut.from_entity(regla).tiene_evaluador is False
