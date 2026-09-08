import uuid
from datetime import UTC, date, datetime

from src.modules.tareas_varias.domain.entities.solicitud_tv import EstadoSolicitudTv, SolicitudTv
from src.modules.tareas_varias.domain.repositories.tecnico_identity_gateway import (
    TecnicoVinculado,
)
from src.modules.tareas_varias.domain.value_objects.conteo_tv import ConteoTv
from src.modules.tareas_varias.domain.value_objects.periodo import Periodo


def build_solicitud_tv(
    id_tecnico: int = 1314,
    tecnico: str = "CD - Agustin HACZEK",
    fecha: date | None = None,
    razon_social: str = "Exolgan",
    sucursal: str = "Dock Sur",
    tarea_realizada: str = "Se buscan toner en Drago y se llevan a Exolgan.",
    estado: EstadoSolicitudTv = EstadoSolicitudTv.PENDIENTE,
) -> SolicitudTv:
    return SolicitudTv(
        id=uuid.uuid4(),
        id_tecnico=id_tecnico,
        tecnico=tecnico,
        fecha=fecha or date(2026, 5, 18),
        razon_social=razon_social,
        sucursal=sucursal,
        tarea_realizada=tarea_realizada,
        estado=estado,
        creado_en=datetime.now(UTC),
    )


class FakeSolicitudTvRepository:
    def __init__(self, solicitudes: list[SolicitudTv] | None = None) -> None:
        self._por_id: dict[uuid.UUID, SolicitudTv] = {s.id: s for s in (solicitudes or [])}
        self.add_calls: list[SolicitudTv] = []
        self.save_calls: list[SolicitudTv] = []

    async def add(self, solicitud: SolicitudTv) -> None:
        self.add_calls.append(solicitud)
        self._por_id[solicitud.id] = solicitud

    async def get_by_id(self, solicitud_id: uuid.UUID) -> SolicitudTv | None:
        return self._por_id.get(solicitud_id)

    async def save(self, solicitud: SolicitudTv) -> None:
        self.save_calls.append(solicitud)
        self._por_id[solicitud.id] = solicitud

    async def list_by_periodo(
        self,
        periodo: Periodo,
        *,
        estado: EstadoSolicitudTv | None = None,
        id_tecnico: int | None = None,
    ) -> list[SolicitudTv]:
        resultado = [s for s in self._por_id.values() if s.periodo == periodo.value]
        if estado is not None:
            resultado = [s for s in resultado if s.estado == estado]
        if id_tecnico is not None:
            resultado = [s for s in resultado if s.id_tecnico == id_tecnico]
        return resultado

    async def count_aprobadas_por_tecnico(self, periodo: Periodo) -> dict[int, int]:
        conteo: dict[int, int] = {}
        for s in self._por_id.values():
            if s.periodo == periodo.value and s.estado == EstadoSolicitudTv.APROBADA:
                conteo[s.id_tecnico] = conteo.get(s.id_tecnico, 0) + 1
        return conteo

    async def contar_por_tecnico_y_periodo(self, anio: int) -> dict[tuple[int, int], ConteoTv]:
        conteo: dict[tuple[int, int], ConteoTv] = {}
        for s in self._por_id.values():
            if s.periodo // 100 != anio:
                continue
            clave = (s.id_tecnico, s.periodo)
            actual = conteo.get(clave, ConteoTv(0, 0))
            conteo[clave] = ConteoTv(
                solicitadas=actual.solicitadas + 1,
                aprobadas=actual.aprobadas + (1 if s.estado == EstadoSolicitudTv.APROBADA else 0),
            )
        return conteo


class FakeTecnicoIdentityGateway:
    def __init__(self, vinculos: dict[uuid.UUID, TecnicoVinculado] | None = None) -> None:
        self._vinculos = vinculos or {}

    async def get_por_usuario(self, user_id: uuid.UUID) -> TecnicoVinculado | None:
        return self._vinculos.get(user_id)
