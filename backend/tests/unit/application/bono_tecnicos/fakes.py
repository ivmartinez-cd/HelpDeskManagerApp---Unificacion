import uuid
from datetime import UTC, date, datetime

from src.modules.bono_tecnicos.domain.entities.bono_tecnico_input import BonoTecnicoInput
from src.modules.bono_tecnicos.domain.entities.conteo_tecnico import ConteoTecnico
from src.modules.bono_tecnicos.domain.entities.incidente_bono import IncidenteBono
from src.modules.bono_tecnicos.domain.entities.solicitud_tv import EstadoSolicitudTv, SolicitudTv
from src.modules.bono_tecnicos.domain.repositories.tecnico_identity_gateway import (
    TecnicoVinculado,
)
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo


def build_incidente(
    id_incidente: int,
    categoria: str = "Correctivo",
    cliente: str = "Aerolineas Argentinas",
    sucursal: str = "EZE - Hangares",
    nro_serie: str = "ZDBXBJCH1000C2D",
) -> IncidenteBono:
    return IncidenteBono(
        id_incidente=id_incidente,
        categoria=categoria,
        cliente=cliente,
        sucursal=sucursal,
        nro_serie=nro_serie,
    )


def build_conteo(
    tecnico: str,
    id_tecnico: int = 1,
    periodo: int = 202605,
    correctivo: int = 0,
    preventivo: int = 0,
    inst_des: int = 0,
    pre_correctivo: int = 0,
    entrega_insumos: int = 0,
) -> ConteoTecnico:
    return ConteoTecnico(
        tecnico=tecnico,
        id_tecnico=id_tecnico,
        periodo=periodo,
        correctivo=correctivo,
        preventivo=preventivo,
        inst_des=inst_des,
        pre_correctivo=pre_correctivo,
        entrega_insumos=entrega_insumos,
    )


class FakeConteoTecnicoGateway:
    def __init__(
        self,
        conteos: list[ConteoTecnico] | None = None,
        incidentes: list[IncidenteBono] | None = None,
    ) -> None:
        self._conteos = conteos or []
        self._incidentes = incidentes or []
        self.periodos_consultados: list[Periodo] = []
        self.incidentes_consultados: list[tuple[Periodo, int]] = []

    async def find_conteos(self, periodo: Periodo) -> list[ConteoTecnico]:
        self.periodos_consultados.append(periodo)
        return self._conteos

    async def find_incidentes(self, periodo: Periodo, id_tecnico: int) -> list[IncidenteBono]:
        self.incidentes_consultados.append((periodo, id_tecnico))
        return self._incidentes


class FakeBonoTecnicoInputRepository:
    def __init__(self, inputs: list[BonoTecnicoInput] | None = None) -> None:
        self._por_clave = {(i.id_tecnico, i.periodo): i for i in (inputs or [])}
        self.periodos_consultados: list[Periodo] = []

    async def find_by_periodo(self, periodo: Periodo) -> list[BonoTecnicoInput]:
        self.periodos_consultados.append(periodo)
        return [i for i in self._por_clave.values() if i.periodo == periodo.value]

    async def upsert(self, input_: BonoTecnicoInput) -> None:
        self._por_clave[(input_.id_tecnico, input_.periodo)] = input_


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


class FakeTecnicoIdentityGateway:
    def __init__(self, vinculos: dict[uuid.UUID, TecnicoVinculado] | None = None) -> None:
        self._vinculos = vinculos or {}

    async def get_por_usuario(self, user_id: uuid.UUID) -> TecnicoVinculado | None:
        return self._vinculos.get(user_id)


class FakeDiasSugeridosGateway:
    def __init__(self, dias_sugeridos: dict[int, int] | None = None) -> None:
        self._dias_sugeridos = dias_sugeridos or {}
        self.consultas: list[tuple[Periodo, list[int]]] = []

    async def get_dias_sugeridos_por_tecnico(
        self, periodo: Periodo, ids_tecnico: list[int]
    ) -> dict[int, int]:
        self.consultas.append((periodo, ids_tecnico))
        return {i: v for i, v in self._dias_sugeridos.items() if i in ids_tecnico}
