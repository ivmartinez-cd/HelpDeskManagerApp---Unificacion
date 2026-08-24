from src.modules.bono_tecnicos.domain.entities.bono_tecnico_input import BonoTecnicoInput
from src.modules.bono_tecnicos.domain.entities.conteo_tecnico import ConteoTecnico
from src.modules.bono_tecnicos.domain.entities.incidente_bono import IncidenteBono
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


class FakeDiasSugeridosGateway:
    def __init__(self, dias_sugeridos: dict[int, int] | None = None) -> None:
        self._dias_sugeridos = dias_sugeridos or {}
        self.consultas: list[tuple[Periodo, list[int]]] = []

    async def get_dias_sugeridos_por_tecnico(
        self, periodo: Periodo, ids_tecnico: list[int]
    ) -> dict[int, int]:
        self.consultas.append((periodo, ids_tecnico))
        return {i: v for i, v in self._dias_sugeridos.items() if i in ids_tecnico}
