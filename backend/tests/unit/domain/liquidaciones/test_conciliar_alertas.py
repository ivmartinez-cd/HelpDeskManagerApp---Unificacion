"""conciliar_alertas: el triage de la TL sobrevive al re-análisis; lo pendiente
se regenera limpio; lo que el motor ya no genera desaparece."""

import uuid
from datetime import datetime

from src.modules.liquidaciones.domain.entities.alerta import Alerta
from src.modules.liquidaciones.domain.services.conciliar_alertas import conciliar_alertas
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import AlertaGenerada

_AHORA = datetime(2026, 1, 1)


def _generada(incidente_id: uuid.UUID, tipo: str = "ALT001") -> AlertaGenerada:
    return AlertaGenerada(
        incidente_id=incidente_id,
        tipo_alerta=tipo,
        descripcion="desc",
        riesgo=0.8,
        datos_contexto={},
    )


def _existente(
    incidente_id: uuid.UUID,
    tipo: str = "ALT001",
    *,
    estado: str = "pendiente",
    justificacion: str | None = None,
    incidente_relacionado_id: uuid.UUID | None = None,
) -> Alerta:
    return Alerta(
        id=uuid.uuid4(),
        incidente_id=incidente_id,
        liquidacion_id=uuid.uuid4(),
        tipo_alerta=tipo,
        descripcion="desc",
        datos_contexto={},
        riesgo=0.8,
        estado=estado,
        fecha_generacion=_AHORA,
        justificacion=justificacion,
        incidente_relacionado_id=incidente_relacionado_id,
    )


def test_preserva_descartada_con_justificacion() -> None:
    inc = uuid.uuid4()
    existente = _existente(inc, estado="descartada", justificacion="acordado con PST")
    [conciliada] = conciliar_alertas([existente], [_generada(inc)])
    assert conciliada.estado == "descartada"
    assert conciliada.justificacion == "acordado con PST"


def test_preserva_resuelta_y_en_revision() -> None:
    inc1, inc2 = uuid.uuid4(), uuid.uuid4()
    existentes = [
        _existente(inc1, estado="resuelta", justificacion="ok"),
        _existente(inc2, estado="en_revision"),
    ]
    conciliadas = conciliar_alertas(existentes, [_generada(inc1), _generada(inc2)])
    assert [c.estado for c in conciliadas] == ["resuelta", "en_revision"]


def test_pendiente_se_regenera_limpia() -> None:
    inc = uuid.uuid4()
    existente = _existente(inc, estado="pendiente", justificacion="no deberia estar")
    [conciliada] = conciliar_alertas([existente], [_generada(inc)])
    assert conciliada.estado == "pendiente"
    assert conciliada.justificacion is None


def test_alerta_nueva_entra_pendiente() -> None:
    [conciliada] = conciliar_alertas([], [_generada(uuid.uuid4())])
    assert conciliada.estado == "pendiente"


def test_distinto_tipo_no_matchea() -> None:
    inc = uuid.uuid4()
    existente = _existente(inc, tipo="ALT002", estado="descartada", justificacion="x")
    [conciliada] = conciliar_alertas([existente], [_generada(inc, tipo="ALT001")])
    assert conciliada.estado == "pendiente"


def test_lo_que_el_motor_ya_no_genera_desaparece() -> None:
    existente = _existente(uuid.uuid4(), estado="descartada", justificacion="x")
    assert conciliar_alertas([existente], []) == []


def test_preserva_incidente_relacionado() -> None:
    inc, relacionado = uuid.uuid4(), uuid.uuid4()
    existente = _existente(
        inc, estado="descartada", justificacion="x", incidente_relacionado_id=relacionado
    )
    [conciliada] = conciliar_alertas([existente], [_generada(inc)])
    assert conciliada.incidente_relacionado_id == relacionado


def test_pendiente_se_regenera_sin_incidente_relacionado() -> None:
    inc, relacionado = uuid.uuid4(), uuid.uuid4()
    existente = _existente(
        inc, estado="pendiente", incidente_relacionado_id=relacionado
    )
    [conciliada] = conciliar_alertas([existente], [_generada(inc)])
    assert conciliada.incidente_relacionado_id is None
