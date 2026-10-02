"""Export a SiGes de un proceso real (`GrillaEstimacion.ExportarCsv` +
`CsvExportService` v1.7): equipos efectivos del tablero (decisiones del
operador restauradas igual que en el tablero), menú Todos / Solo estimados,
observación manual y `#IdLog` de la auditoría."""

from datetime import UTC, date, datetime
from typing import Any

import pytest

from src.modules.contadores.application.dtos.decision_operador_dto import (
    ClaveDecisionDto,
    DecisionOperadorDto,
    LecturaElegidaDto,
)
from src.modules.contadores.application.dtos.receso_dto import RecesoDto
from src.modules.contadores.application.dtos.solicitud_tablero_siges_dto import (
    SolicitudTableroSigesDto,
)
from src.modules.contadores.application.use_cases.generar_export_csv import (
    GenerarExportCsvUseCase,
    OpcionesExportCsv,
)
from src.modules.contadores.domain.ports.candidatos_equipo_port import (
    LecturaCandidataSiges,
    MetadataEquipoSiges,
)
from src.modules.contadores.domain.ports.estim_log_port import (
    EntradaEstimLog,
    ResumenAuditoriaMaquina,
)
from src.modules.contadores.infrastructure.ejemplo.decisiones_operador_store import (
    DecisionesOperadorStore,
)
from src.shared.domain.errors import BusinessRuleViolationError
from tests.unit.application.contadores._fila_grilla_siges_builder import fila_siges

_FECHA = date(2026, 4, 30)
_SOLICITUD = SolicitudTableroSigesDto(5, 900, 44, _FECHA)
_CON_PARQUE: dict[str, Any] = dict(prom_parque_cliente_modelo=500.0, pcm_cant=6)
_ENCABEZADO = "SERIE;FECHA;TIPO;CLASE_1;CONTADOR_1;CLASE_2;CONTADOR_2;MOTIVO;OBSERVACION"


class FakeGateway:
    def __init__(self, filas: list[Any]) -> None:
        self.filas = filas
        self.frescas: list[bool] = []
        self.operadores: list[str | None] = []

    async def fetch_grilla(
        self,
        nro_proceso: int,
        fecha_objetivo: date,
        *,
        fresca: bool = False,
        operador: str | None = None,
    ) -> list[Any]:
        self.frescas.append(fresca)
        self.operadores.append(operador)
        return self.filas


class FakeRecesos:
    async def listar(self, id_grupo_economico: int) -> list[RecesoDto]:
        return []

    async def listar_para_proceso(self, id_anexo: int, ids_grupo: list[int]) -> list[RecesoDto]:
        return []

    async def actualizar(self, receso: RecesoDto) -> RecesoDto | None:
        raise NotImplementedError

    async def crear(self, receso_sin_id: RecesoDto) -> RecesoDto:
        raise NotImplementedError

    async def eliminar(self, id_receso: int) -> None:
        raise NotImplementedError


class FakeEstimLog:
    def __init__(self, resumen: dict[int, ResumenAuditoriaMaquina] | None = None) -> None:
        self.resumen = resumen or {}

    async def registrar(self, entrada: EntradaEstimLog) -> None:
        raise NotImplementedError

    async def resumen_por_maquina(self, nro_proceso: int) -> dict[int, ResumenAuditoriaMaquina]:
        return self.resumen


class FakeCandidatos:
    async def fetch_lecturas(
        self, id_maquina: int, id_clase_contador: int
    ) -> list[LecturaCandidataSiges]:
        return [
            LecturaCandidataSiges(12, date(2026, 3, 31), 1, 1_000.0, True),
            LecturaCandidataSiges(11, date(2026, 1, 30), 1, 400.0, True),
        ]

    async def fetch_lecturas_de_equipos(
        self, equipos: list[tuple[int, int]]
    ) -> dict[tuple[int, int], list[LecturaCandidataSiges]]:
        return {e: await self.fetch_lecturas(*e) for e in equipos}

    async def fetch_metadata_equipo(self, id_maquina: int) -> MetadataEquipoSiges | None:
        return None


def _grilla() -> list[Any]:
    """101: Mono ya real + Color por parque; 102: sin datos (pendiente);
    103: Mono por parque."""
    return [
        fila_siges(id_maquina=103, nro_serie="S103", **_CON_PARQUE),
        fila_siges(id_maquina=101, nro_serie="S101", pendiente_estimar=False),
        fila_siges(id_maquina=101, nro_serie="S101", id_clase_contador=20, **_CON_PARQUE),
        fila_siges(id_maquina=102, nro_serie="S102"),
    ]


async def _exportar(
    decisiones: DecisionesOperadorStore | None = None,
    opciones: OpcionesExportCsv | None = None,
    **kwargs: Any,
) -> list[str]:
    use_case = GenerarExportCsvUseCase(
        kwargs.get("gateway", FakeGateway(_grilla())),
        decisiones or DecisionesOperadorStore(),
        FakeRecesos(),
        kwargs.get("estim_log", FakeEstimLog()),
        kwargs.get("candidatos"),
    )
    contenido = await use_case.execute(kwargs.get("solicitud", _SOLICITUD), opciones)
    assert contenido.endswith("\r\n")
    return contenido.removesuffix("\r\n").split("\r\n")


async def test_todos_una_linea_por_maquina_ordenada_por_serie() -> None:
    lineas = await _exportar()

    assert lineas == [
        _ENCABEZADO,
        "S101;30/04/2026;;10;;20;1500;;C:Parque cli/mod | +500 imp | P80 6eq | sin historia propia",
        "S102;30/04/2026;;10;;;;;",
        "S103;30/04/2026;19;10;1500;;;19;Parque cli/mod | +500 imp | P80 6eq | sin historia propia",
    ]


async def test_solo_estimados_filtra_fila_por_fila() -> None:
    """El Mono real de 101 queda afuera: el Color pasa a ser el principal y,
    sin la otra clase, la observación va sin prefijo (como el legacy)."""
    lineas = await _exportar(opciones=OpcionesExportCsv(solo_estimados=True))

    assert lineas == [
        _ENCABEZADO,
        "S101;30/04/2026;19;20;1500;;;19;Parque cli/mod | +500 imp | P80 6eq | sin historia propia",
        "S103;30/04/2026;19;10;1500;;;19;Parque cli/mod | +500 imp | P80 6eq | sin historia propia",
    ]


async def test_decision_marcar_pendiente_del_proceso_deja_la_fila_vacia() -> None:
    decisiones = DecisionesOperadorStore()
    await decisiones.guardar(ClaveDecisionDto(5, 103, "10"), DecisionOperadorDto("MarcarPendiente"))

    todos = await _exportar(decisiones)
    solo = await _exportar(decisiones, OpcionesExportCsv(solo_estimados=True))

    assert todos[-1] == "S103;30/04/2026;;10;;;;;"
    assert [linea.split(";")[0] for linea in solo[1:]] == ["S101"]


async def test_descartar_hasta_ignora_lo_decidido_antes() -> None:
    decisiones = DecisionesOperadorStore()
    await decisiones.guardar(ClaveDecisionDto(5, 103, "10"), DecisionOperadorDto("MarcarPendiente"))
    opciones = OpcionesExportCsv(descartar_hasta=datetime.now(UTC))

    lineas = await _exportar(decisiones, opciones)

    assert lineas[-1].startswith("S103;30/04/2026;19;10;1500;")


async def test_decisiones_de_otro_proceso_no_cuentan() -> None:
    decisiones = DecisionesOperadorStore()
    await decisiones.guardar(ClaveDecisionDto(6, 103, "10"), DecisionOperadorDto("MarcarPendiente"))

    lineas = await _exportar(decisiones)

    assert lineas[-1].startswith("S103;30/04/2026;19;10;1500;")


async def test_pl_manual_se_relee_de_siges_por_id_contador() -> None:
    decisiones = DecisionesOperadorStore()
    guardada = DecisionOperadorDto(
        accion="PL_Manual",
        partida=LecturaElegidaDto(date(2026, 1, 30), 999.0, 1, id_contador=11),
        llegada=LecturaElegidaDto(date(2026, 3, 31), 1_000.0, 1, id_contador=12),
    )
    await decisiones.guardar(ClaveDecisionDto(5, 102, "10"), guardada)

    lineas = await _exportar(decisiones, candidatos=FakeCandidatos())

    serie, _, tipo, _, contador, *_, motivo, obs = lineas[2].split(";")
    assert (serie, tipo, motivo) == ("S102", "14", "14")
    assert obs.startswith("P/L manual | +")
    assert int(contador) > 1_000


async def test_pl_manual_sin_id_contador_se_descarta_al_releer() -> None:
    decisiones = DecisionesOperadorStore()
    guardada = DecisionOperadorDto(
        accion="PL_Manual",
        partida=LecturaElegidaDto(date(2026, 1, 30), 400.0, 1),
        llegada=LecturaElegidaDto(date(2026, 3, 31), 1_000.0, 1),
    )
    await decisiones.guardar(ClaveDecisionDto(5, 102, "10"), guardada)

    lineas = await _exportar(decisiones, candidatos=FakeCandidatos())

    assert lineas[2] == "S102;30/04/2026;;10;;;;;"


async def test_observacion_manual_saneada_e_id_log_de_la_auditoria() -> None:
    estim_log = FakeEstimLog({103: ResumenAuditoriaMaquina("4817", "⚠ ver Δ con cliente")})

    lineas = await _exportar(estim_log=estim_log)

    assert lineas[-1].endswith(
        ";19;(!) ver  con cliente | Parque cli/mod | +500 imp | P80 6eq"
        " | sin historia propia | #4817"
    )


async def test_reusa_la_grilla_cargada_y_sin_grilla_solo_encabezado() -> None:
    gateway = FakeGateway([])
    solicitud = SolicitudTableroSigesDto(5, 900, 44, _FECHA, "ana")

    lineas = await _exportar(gateway=gateway, solicitud=solicitud)

    assert lineas == [_ENCABEZADO]
    assert gateway.frescas == [False]
    assert gateway.operadores == ["ana"]  # la grilla que cargó ESE operador


async def test_maquina_sin_clase_10_ni_20_no_genera_el_archivo() -> None:
    """v1.7: `principal = cl10 ?? cl20!` tira una excepción y no se
    descarga nada; acá el export falla con el equipo que lo impide."""
    solo_clase_30 = fila_siges(id_maquina=104, nro_serie="S104", id_clase_contador=30)
    gateway = FakeGateway([*_grilla(), solo_clase_30])

    with pytest.raises(BusinessRuleViolationError, match="S104"):
        await _exportar(gateway=gateway)
