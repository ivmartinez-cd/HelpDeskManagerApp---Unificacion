"""RequestAlertsConAviso: al escalar alertas publica un aviso por alerta para
`insumos.view`; sin escaladas nuevas no publica nada."""

from collections.abc import Sequence
from datetime import UTC, datetime

from src.modules.insumos.domain.entities.request_alert import RequestAlert
from src.modules.insumos.infrastructure.repositories.request_alerts_con_aviso import (
    RequestAlertsConAviso,
)
from src.modules.notificaciones.domain.entities.notificacion import NuevaNotificacion

_ESCALADA = datetime(2026, 9, 30, 12, 0, tzinfo=UTC)


def _alerta(hp_id: int, customer_id: int | None = 77) -> RequestAlert:
    return RequestAlert(
        hp_request_id=hp_id,
        customer_id=customer_id,
        customer_name="Clínica Norte",
        device_serial="",
        sku="CF258A",
        description="Tóner negro",
        requested_at=_ESCALADA,
        first_seen_at=_ESCALADA,
        escalated_at=_ESCALADA,
    )


class _Inner:
    def __init__(self, escaladas: int, activas: list[RequestAlert]) -> None:
        self.escaladas, self.activas = escaladas, activas

    async def escalate_due(self, cutoff: datetime) -> int:
        return self.escaladas

    async def list_escalated(self) -> list[RequestAlert]:
        return self.activas

    async def acknowledge(self, hp_request_ids: Sequence[int]) -> int:
        return len(hp_request_ids)


class _Publicador:
    def __init__(self) -> None:
        self.publicadas: list[NuevaNotificacion] = []

    async def publicar(self, notificaciones: list[NuevaNotificacion]) -> None:
        self.publicadas.extend(notificaciones)


async def test_al_escalar_avisa_una_por_alerta_activa() -> None:
    pub = _Publicador()
    repo = RequestAlertsConAviso(_Inner(1, [_alerta(1), _alerta(2, None)]), pub)  # type: ignore[arg-type]

    assert await repo.escalate_due(_ESCALADA) == 1

    primera, segunda = pub.publicadas
    assert primera.clave == f"insumos.alerta:1:{_ESCALADA.isoformat()}"
    assert primera.audiencia == "permiso:insumos.view"
    assert primera.titulo == "Solicitud de insumo sin cargar: Clínica Norte"
    assert primera.cuerpo.startswith("Tóner negro.")
    assert primera.url == "/insumos?customerId=77"
    assert segunda.url == "/insumos"


async def test_sin_escaladas_nuevas_no_publica() -> None:
    pub = _Publicador()
    repo = RequestAlertsConAviso(_Inner(0, [_alerta(1)]), pub)  # type: ignore[arg-type]

    assert await repo.escalate_due(_ESCALADA) == 0
    assert pub.publicadas == []
