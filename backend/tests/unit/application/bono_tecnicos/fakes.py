import uuid

from src.modules.bono_tecnicos.domain.entities.bono_tecnico_input import BonoTecnicoInput
from src.modules.bono_tecnicos.domain.entities.conteo_tecnico import ConteoTecnico
from src.modules.bono_tecnicos.domain.entities.incidente_bono import IncidenteBono
from src.modules.bono_tecnicos.domain.repositories.tecnico_identity_gateway import (
    TecnicoVinculado,
)
from src.modules.bono_tecnicos.domain.value_objects.conteo_tv import ConteoTv, ResumenTvTecnico
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
        conteos_anio: list[ConteoTecnico] | None = None,
    ) -> None:
        self._conteos = conteos or []
        self._incidentes = incidentes or []
        self._conteos_anio = conteos_anio if conteos_anio is not None else (conteos or [])
        self.periodos_consultados: list[Periodo] = []
        self.incidentes_consultados: list[tuple[Periodo, int]] = []
        self.anios_consultados: list[int] = []

    async def find_conteos(self, periodo: Periodo) -> list[ConteoTecnico]:
        self.periodos_consultados.append(periodo)
        return self._conteos

    async def find_conteos_anio(self, anio: int) -> list[ConteoTecnico]:
        self.anios_consultados.append(anio)
        return self._conteos_anio

    async def find_incidentes(self, periodo: Periodo, id_tecnico: int) -> list[IncidenteBono]:
        self.incidentes_consultados.append((periodo, id_tecnico))
        return self._incidentes


class FakeBonoTecnicoInputRepository:
    def __init__(self, inputs: list[BonoTecnicoInput] | None = None) -> None:
        self._por_clave = {(i.id_tecnico, i.periodo): i for i in (inputs or [])}
        self.periodos_consultados: list[Periodo] = []
        self.anios_consultados: list[int] = []

    async def find_by_periodo(self, periodo: Periodo) -> list[BonoTecnicoInput]:
        self.periodos_consultados.append(periodo)
        return [i for i in self._por_clave.values() if i.periodo == periodo.value]

    async def find_by_anio(self, anio: int) -> list[BonoTecnicoInput]:
        self.anios_consultados.append(anio)
        return [i for i in self._por_clave.values() if i.periodo // 100 == anio]

    async def upsert(self, input_: BonoTecnicoInput) -> None:
        self._por_clave[(input_.id_tecnico, input_.periodo)] = input_


def build_solicitud_tv(
    id_tecnico: int = 1314,
    periodo: int = 202605,
    estado: str = "PENDIENTE",
) -> tuple[int, int, str]:
    """Una fila mínima de TV (id_tecnico, periodo, estado) para
    `FakeTareasVariasGateway` — el detalle de una `SolicitudTv` (fecha,
    razón social...) vive del otro lado del puerto, en el módulo
    `tareas_varias` (ver `tests/unit/application/tareas_varias/fakes.py`),
    bono_tecnicos solo necesita el conteo."""
    return (id_tecnico, periodo, estado)


class FakeTareasVariasGateway:
    """Doble de `TareasVariasGateway` (`bono_tecnicos.domain.repositories.
    tareas_varias_gateway`) para no depender del módulo `tareas_varias` en
    los tests de bono_tecnicos, mismo criterio que el puerto real."""

    def __init__(self, solicitudes: list[tuple[int, int, str]] | None = None) -> None:
        self._solicitudes = solicitudes or []

    async def count_aprobadas_por_tecnico(self, periodo: Periodo) -> dict[int, int]:
        conteo: dict[int, int] = {}
        for id_tecnico, p, estado in self._solicitudes:
            if p == periodo.value and estado == "APROBADA":
                conteo[id_tecnico] = conteo.get(id_tecnico, 0) + 1
        return conteo

    async def contar_por_tecnico_y_periodo(self, anio: int) -> dict[tuple[int, int], ConteoTv]:
        conteo: dict[tuple[int, int], ConteoTv] = {}
        for id_tecnico, p, estado in self._solicitudes:
            if p // 100 != anio:
                continue
            clave = (id_tecnico, p)
            actual = conteo.get(clave, ConteoTv(0, 0))
            conteo[clave] = ConteoTv(
                solicitadas=actual.solicitadas + 1,
                aprobadas=actual.aprobadas + (1 if estado == "APROBADA" else 0),
            )
        return conteo

    async def resumen_tecnico(self, periodo: Periodo, id_tecnico: int) -> ResumenTvTecnico:
        propias = [
            estado
            for it, p, estado in self._solicitudes
            if it == id_tecnico and p == periodo.value
        ]
        return ResumenTvTecnico(
            aprobadas=propias.count("APROBADA"),
            pendientes=propias.count("PENDIENTE"),
            rechazadas=propias.count("RECHAZADA"),
        )


class FakeTecnicoIdentityGateway:
    def __init__(self, vinculos: dict[uuid.UUID, TecnicoVinculado] | None = None) -> None:
        self._vinculos = vinculos or {}

    async def get_por_usuario(self, user_id: uuid.UUID) -> TecnicoVinculado | None:
        return self._vinculos.get(user_id)


class FakeDiasSugeridosGateway:
    def __init__(self, dias_sugeridos: dict[int, float] | None = None) -> None:
        self._dias_sugeridos = dias_sugeridos or {}
        self.consultas: list[tuple[Periodo, list[int]]] = []

    async def get_dias_sugeridos_por_tecnico(
        self, periodo: Periodo, ids_tecnico: list[int]
    ) -> dict[int, float]:
        self.consultas.append((periodo, ids_tecnico))
        return {i: v for i, v in self._dias_sugeridos.items() if i in ids_tecnico}
