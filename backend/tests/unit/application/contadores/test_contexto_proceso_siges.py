"""Contexto de proceso real y política de carga de la grilla:
- recesos con el grupo económico de la fila de Siges (`A.ID_GrupoE`) y el
  anexo del proceso, como `Index.CargarTablero` + `Receso.AplicaA` del legacy
  — no con el grupo que vino en el request;
- el tablero pide la grilla fresca; recalcular/forzar/candidatos reusan la
  última cargada;
- el tablero real restaura las decisiones de SU proceso y relee de Siges la
  P/L manual guardada."""

from datetime import date
from typing import Any

from src.modules.contadores.application.dtos.decision_operador_dto import (
    ClaveDecisionDto,
    DecisionOperadorDto,
    LecturaElegidaDto,
)
from src.modules.contadores.application.dtos.receso_dto import RecesoDto
from src.modules.contadores.application.dtos.solicitud_recalculo_siges_dto import (
    SolicitudRecalculoSigesDto,
)
from src.modules.contadores.application.dtos.solicitud_tablero_siges_dto import (
    SolicitudTableroSigesDto,
)
from src.modules.contadores.application.use_cases._construir_entrada_siges import (
    ConstructorEntradaSiges,
    contexto_proceso_siges,
)
from src.modules.contadores.application.use_cases.get_tablero_proyeccion_siges import (
    GetTableroProyeccionSigesUseCase,
)
from src.modules.contadores.domain.ports.candidatos_equipo_port import (
    LecturaCandidataSiges,
    MetadataEquipoSiges,
)
from src.modules.contadores.domain.value_objects.estimacion.receso_cliente import RecesoCliente
from src.modules.contadores.infrastructure.ejemplo.decisiones_operador_store import (
    DecisionesOperadorStore,
)
from tests.unit.application.contadores._fila_grilla_siges_builder import (
    PERIODO_DESDE,
    PERIODO_HASTA,
    fila_siges,
)

_FECHA = date(2026, 4, 30)
_GRUPO_FILA = 900
_GRUPO_REQUEST = 123
_ANEXO_PROCESO = 44


class FakeGateway:
    def __init__(self, filas: list[Any]) -> None:
        self.filas = filas
        self.llamadas: list[tuple[int, date, bool, str | None]] = []

    async def fetch_grilla(
        self,
        nro_proceso: int,
        fecha_objetivo: date,
        *,
        fresca: bool = False,
        operador: str | None = None,
    ) -> list[Any]:
        self.llamadas.append((nro_proceso, fecha_objetivo, fresca, operador))
        return self.filas


class FakeRecesos:
    def __init__(self) -> None:
        self.grupos_listados: list[int] = []
        self.anexos_listados: list[int] = []

    async def listar(self, id_grupo_economico: int) -> list[RecesoDto]:
        raise AssertionError("el contexto del proceso usa listar_para_proceso")

    async def listar_para_proceso(self, id_anexo: int, ids_grupo: list[int]) -> list[RecesoDto]:
        self.anexos_listados.append(id_anexo)
        self.grupos_listados.extend(ids_grupo)
        return [RecesoDto(1, g, None, date(2026, 4, 10), date(2026, 4, 12), "") for g in ids_grupo]

    async def crear(self, receso_sin_id: RecesoDto) -> RecesoDto:
        return receso_sin_id

    async def actualizar(self, receso: RecesoDto) -> RecesoDto | None:
        return receso

    async def eliminar(self, id_receso: int) -> None:
        return None


async def test_contexto_usa_grupo_de_la_fila_y_anexo_del_proceso() -> None:
    recesos = FakeRecesos()

    ctx = await contexto_proceso_siges(
        fila_siges(id_grupo_economico=_GRUPO_FILA), _FECHA, _ANEXO_PROCESO, recesos
    )

    assert recesos.grupos_listados == [_GRUPO_FILA]
    assert recesos.anexos_listados == [_ANEXO_PROCESO]
    assert (ctx.id_grupo_economico, ctx.id_anexo) == (_GRUPO_FILA, _ANEXO_PROCESO)
    assert (ctx.fecha_objetivo, ctx.periodo_desde, ctx.periodo_hasta) == (
        _FECHA, PERIODO_DESDE, PERIODO_HASTA
    )
    assert ctx.recesos == [RecesoCliente(date(2026, 4, 10), date(2026, 4, 12), _GRUPO_FILA, None)]


async def test_recalcular_reusa_la_grilla_y_arma_la_entrada_con_el_grupo_de_la_fila() -> None:
    gateway = FakeGateway([fila_siges(id_grupo_economico=_GRUPO_FILA)])
    recesos = FakeRecesos()
    solicitud = SolicitudRecalculoSigesDto(5, _GRUPO_REQUEST, _ANEXO_PROCESO, _FECHA, "ana")

    resultado = await ConstructorEntradaSiges(gateway, recesos).construir(101, "10", solicitud)

    assert resultado is not None
    entrada, _ = resultado
    assert gateway.llamadas == [(5, _FECHA, False, "ana")]  # la grilla de ESE operador
    assert recesos.grupos_listados == [_GRUPO_FILA]
    assert (entrada.id_grupo_economico, entrada.id_anexo) == (_GRUPO_FILA, _ANEXO_PROCESO)


async def test_recalcular_equipo_que_no_esta_en_la_grilla_devuelve_none() -> None:
    gateway = FakeGateway([fila_siges()])
    solicitud = SolicitudRecalculoSigesDto(5, _GRUPO_REQUEST, _ANEXO_PROCESO, _FECHA)

    resultado = await ConstructorEntradaSiges(gateway, FakeRecesos()).construir(
        999, "10", solicitud
    )

    assert resultado is None


async def test_tablero_pide_la_grilla_fresca() -> None:
    gateway = FakeGateway([])
    use_case = GetTableroProyeccionSigesUseCase(
        gateway, DecisionesOperadorStore(), FakeRecesos()
    )

    resultado = await use_case.execute(
        SolicitudTableroSigesDto(5, _GRUPO_REQUEST, _ANEXO_PROCESO, _FECHA, "ana")
    )

    assert gateway.llamadas == [(5, _FECHA, True, "ana")]
    assert resultado.filas == []


async def test_tablero_restaura_solo_las_decisiones_de_su_proceso() -> None:
    decisiones = DecisionesOperadorStore()
    await decisiones.guardar(ClaveDecisionDto(6, 101, "10"), DecisionOperadorDto("MarcarPendiente"))
    use_case = GetTableroProyeccionSigesUseCase(
        FakeGateway([fila_siges()]), decisiones, FakeRecesos()
    )

    resultado = await use_case.execute(
        SolicitudTableroSigesDto(5, _GRUPO_REQUEST, _ANEXO_PROCESO, _FECHA)
    )

    # La decisión del proceso 6 no se arrastra al 5 (`Estim_Log.NroProceso`).
    assert [f.editado_por_operador for f in resultado.filas] == [False]
    assert resultado.restauracion.restauradas == 0

    await decisiones.guardar(ClaveDecisionDto(5, 101, "10"), DecisionOperadorDto("MarcarPendiente"))
    propio = await use_case.execute(
        SolicitudTableroSigesDto(5, _GRUPO_REQUEST, _ANEXO_PROCESO, _FECHA)
    )
    assert [f.fuente for f in propio.filas] == ["Pendiente"]
    assert propio.restauracion.restauradas == 1


async def test_tablero_relee_la_pl_manual_por_id_contador() -> None:
    decisiones = DecisionesOperadorStore()
    guardada = DecisionOperadorDto(
        accion="PL_Manual",
        partida=LecturaElegidaDto(date(2026, 2, 1), 500.0, 1, id_contador=11),
        llegada=LecturaElegidaDto(date(2026, 3, 31), 1_000.0, 1, id_contador=12),
    )
    await decisiones.guardar(ClaveDecisionDto(5, 101, "10"), guardada)
    candidatos = FakeCandidatos()
    use_case = GetTableroProyeccionSigesUseCase(
        FakeGateway([fila_siges()]), decisiones, FakeRecesos(), candidatos
    )

    await use_case.execute(SolicitudTableroSigesDto(5, _GRUPO_REQUEST, _ANEXO_PROCESO, _FECHA))

    assert candidatos.llamadas == [(101, 10)]


class FakeCandidatos:
    def __init__(self) -> None:
        self.llamadas: list[tuple[int, int]] = []

    async def fetch_lecturas(
        self, id_maquina: int, id_clase_contador: int
    ) -> list[LecturaCandidataSiges]:
        self.llamadas.append((id_maquina, id_clase_contador))
        return [
            LecturaCandidataSiges(12, date(2026, 3, 31), 1, 1_000.0, True),
            LecturaCandidataSiges(11, date(2026, 2, 1), 1, 500.0, True),
        ]

    async def fetch_metadata_equipo(self, id_maquina: int) -> MetadataEquipoSiges | None:
        return None
