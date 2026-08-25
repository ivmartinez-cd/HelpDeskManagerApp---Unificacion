"""Constantes y fakes compartidos por los tests de routers de sla (las fixtures
viven en conftest.py de este paquete)."""

from __future__ import annotations

import uuid

from tests.integration.router_testing import current_identity
from tests.unit.application.sla.fakes_pendientes import FakePrestadorLookup

SLA = "/api/sla"
PEND = "/api/sla/pendientes-a-cerrar"
MESA = "/api/sla/mesa-de-ayuda"
MODULE = "sla"
PERIODO = 202608
PAGE_KEYS = {"items", "total", "page", "size"}
PST_PROPIO = 11
PST_AJENO = 22


class Lookup(FakePrestadorLookup):
    """El operador logueado tiene un PST propio; cualquier otro operador, ninguno."""

    def __init__(self) -> None:
        super().__init__(
            pst_ids=[PST_PROPIO, PST_AJENO],
            pst_to_operador={PST_PROPIO: "Operador", PST_AJENO: "Otra"},
        )

    async def get_siges_ids_por_operador(self, operador_id: uuid.UUID) -> list[int]:
        return [PST_PROPIO] if operador_id == current_identity().user.id else []
