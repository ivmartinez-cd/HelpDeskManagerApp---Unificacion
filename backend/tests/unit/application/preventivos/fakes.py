import uuid
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta

from src.modules.preventivos.domain.entities.equipo_preventivo import (
    EquipoPreventivo,
    ParqueZonaSnapshot,
)
from src.modules.preventivos.domain.entities.habilitacion_preventivo import (
    HabilitacionPreventivo,
)
from src.modules.preventivos.domain.entities.zona_parque import ZonaParque


def build_equipo(
    id_maquina: int,
    *,
    zona: str = "SUR",
    cliente: str = "Cliente",
    serie: str | None = None,
    frecuencia_dias: int | None = 180,
    fecha_ultimo_preventivo: date | None = None,
) -> EquipoPreventivo:
    return EquipoPreventivo(
        id_maquina=id_maquina,
        serie=serie if serie is not None else f"SERIE{id_maquina}",
        modelo="MFP Mono Samsung",
        cliente=cliente,
        sucursal="Casa Central",
        zona=zona,
        frecuencia_dias=frecuencia_dias,
        fecha_ultimo_preventivo=fecha_ultimo_preventivo,
    )


def build_habilitacion(
    siges_maquina_id: int, *, habilitado_hace_dias: int = 0
) -> HabilitacionPreventivo:
    return HabilitacionPreventivo(
        id=uuid.uuid4(),
        siges_maquina_id=siges_maquina_id,
        habilitado_por_user_id=uuid.uuid4(),
        habilitado_por_nombre="Ana Prueba",
        habilitado_en=datetime.now(UTC) - timedelta(days=habilitado_hace_dias),
        nota=None,
        activa=True,
        deshabilitado_en=None,
        deshabilitado_por=None,
    )


class FakePreventivosQueryGateway:
    def __init__(
        self, equipos: list[EquipoPreventivo] | None = None, zonas: list[ZonaParque] | None = None
    ) -> None:
        self._equipos = equipos or []
        self._zonas = zonas or []
        self.zonas_consultadas: list[str] = []

    async def list_equipos_por_zona(
        self, zona: str, *, force_refresh: bool = False
    ) -> ParqueZonaSnapshot:
        self.zonas_consultadas.append(zona)
        return ParqueZonaSnapshot(
            equipos=tuple(e for e in self._equipos if e.zona == zona),
            consultado_en=datetime.now(UTC),
        )

    async def list_zonas(self) -> list[ZonaParque]:
        return list(self._zonas)


class FakeHabilitacionRepository:
    def __init__(self, habilitaciones: list[HabilitacionPreventivo] | None = None) -> None:
        self.habilitaciones = list(habilitaciones or [])

    def _activa(self, siges_maquina_id: int) -> HabilitacionPreventivo | None:
        for h in self.habilitaciones:
            if h.siges_maquina_id == siges_maquina_id and h.activa:
                return h
        return None

    async def get_activa(self, siges_maquina_id: int) -> HabilitacionPreventivo | None:
        return self._activa(siges_maquina_id)

    async def list_activas_por_maquinas(
        self, siges_maquina_ids: Sequence[int]
    ) -> list[HabilitacionPreventivo]:
        ids = set(siges_maquina_ids)
        return [h for h in self.habilitaciones if h.activa and h.siges_maquina_id in ids]

    async def create(self, habilitacion: HabilitacionPreventivo) -> None:
        self.habilitaciones.append(habilitacion)

    async def desactivar(
        self, siges_maquina_id: int, *, deshabilitado_por: str, deshabilitado_en: datetime
    ) -> bool:
        habilitacion = self._activa(siges_maquina_id)
        if habilitacion is None:
            return False
        habilitacion.activa = False
        habilitacion.deshabilitado_por = deshabilitado_por
        habilitacion.deshabilitado_en = deshabilitado_en
        return True
