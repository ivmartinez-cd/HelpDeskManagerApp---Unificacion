"""ModificacionesConAviso: guarda las modificaciones y publica un aviso por
liquidación y tanda, para `liquidaciones.view`."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from src.modules.liquidaciones.domain.entities.modificacion_prestador import (
    TIPO_MODIFICACION,
    ModificacionPrestador,
)
from src.modules.liquidaciones.infrastructure.repositories.modificaciones_con_aviso import (
    ModificacionesConAviso,
)
from src.modules.notificaciones.domain.entities.notificacion import NuevaNotificacion


class _Inner:
    def __init__(self) -> None:
        self.guardadas: list[ModificacionPrestador] = []

    async def bulk_create(self, modificaciones: Sequence[ModificacionPrestador]) -> None:
        self.guardadas.extend(modificaciones)


class _Liquidaciones:
    def __init__(self, numeros: dict[uuid.UUID, str]) -> None:
        self._numeros = numeros

    async def get_by_id(self, liquidacion_id: uuid.UUID) -> Any:
        numero = self._numeros.get(liquidacion_id)
        return SimpleNamespace(numero_liquidacion=numero) if numero else None


class _Publicador:
    def __init__(self) -> None:
        self.publicadas: list[NuevaNotificacion] = []

    async def publicar(self, notificaciones: list[NuevaNotificacion]) -> None:
        self.publicadas.extend(notificaciones)


def _mod(liq: uuid.UUID, incidente: str, campo: str = "km", valor: str = "10") -> Any:
    return ModificacionPrestador(
        id=uuid.uuid4(),
        liquidacion_id=liq,
        numero_incidente=incidente,
        tipo_cambio=TIPO_MODIFICACION,
        campo=campo,
        valor_anterior="1",
        valor_nuevo=valor,
        detectada_en=datetime.now(UTC),
        vista_en=None,
    )


def _decorador(numeros: dict[uuid.UUID, str]) -> tuple[ModificacionesConAviso, _Inner, _Publicador]:
    inner, pub = _Inner(), _Publicador()
    return ModificacionesConAviso(inner, _Liquidaciones(numeros), pub), inner, pub  # type: ignore[arg-type]


async def test_guarda_y_avisa_una_vez_por_liquidacion() -> None:
    a, b = uuid.uuid4(), uuid.uuid4()
    repo, inner, pub = _decorador({a: "3905-7"})
    filas = [_mod(a, "INC-1"), _mod(a, "INC-1", "costo"), _mod(a, "INC-2"), _mod(b, "INC-9")]

    await repo.bulk_create(filas)

    assert inner.guardadas == filas
    aviso_a, aviso_b = pub.publicadas
    assert aviso_a.titulo == "Liquidación 3905-7: el prestador modificó 3 valores"
    assert aviso_a.cuerpo.startswith("2 incidentes con cambios")
    assert aviso_a.audiencia == "permiso:liquidaciones.view"
    assert aviso_a.url == f"/liquidaciones/{a}"
    assert aviso_a.clave == f"liquidaciones.modificaciones:{a}:{filas[0].id}"
    assert aviso_b.titulo == "Liquidación sin número: el prestador modificó 1 valor"


async def test_el_reenvio_masivo_avisa_con_el_resumen() -> None:
    liq = uuid.uuid4()
    repo, _, pub = _decorador({liq: "10"})
    resumen = _mod(liq, "-", "resumen", "45 incidentes modificados en un reenvío masivo")

    await repo.bulk_create([resumen])

    (aviso,) = pub.publicadas
    assert aviso.titulo == "Liquidación 10: el prestador reenvió la liquidación"
    assert aviso.cuerpo.startswith("45 incidentes modificados en un reenvío masivo.")
