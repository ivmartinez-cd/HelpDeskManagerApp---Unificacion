"""Test de integración de SincronizarDespachos con los repositorios Postgres de Despachados.

Los fakes de los tests unit imitan dos reglas de la base de las que depende el orden del
flujo: la FK de remito a envío (el alta de envíos va antes que los remitos) y que
`cerrar_interrumpidas` cierra TODA corrida sin terminar (va antes de iniciar la nueva). Acá
las hace cumplir la base de verdad. Siges, OCA, los feriados y el candado siguen en memoria.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.application.use_cases.despachados.sincronizar_despachos import (
    MOTIVO_INTERRUMPIDA,
    SincronizarDespachos,
    SincronizarDespachosPorts,
)
from src.modules.insumos.domain.entities.despachados.corrida import (
    Corrida,
    OrigenCorrida,
    ResumenCorrida,
)
from src.modules.insumos.infrastructure.models.despacho_corrida_model import (
    DespachoCorridaModel,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_corridas_despacho_repository import (  # noqa: E501
    SqlAlchemyCorridasDespachoRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_envios_despacho_repository import (  # noqa: E501
    SqlAlchemyEnviosDespachoRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_historial_estados_repository import (  # noqa: E501
    SqlAlchemyHistorialEstadosRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_remitos_despacho_repository import (  # noqa: E501
    SqlAlchemyRemitosDespachoRepository,
)
from tests.unit.application.insumos._offline_fakes import FakeExclusiveLock
from tests.unit.application.insumos.despachados.fakes_despachados import (
    AHORA,
    CONFIG,
    GUIA_A,
    FakeCalendarioFeriados,
    FakeDespachosSiges,
    FakeOcaSeguimiento,
    despacho,
    estado_oca,
)


async def _sin_pausa(segundos: float) -> None:
    return None


class MundoConBase:
    """Repositorios de HDM contra la base de test; Siges y OCA en memoria."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.siges = FakeDespachosSiges()
        self.oca = FakeOcaSeguimiento([])
        self.envios = SqlAlchemyEnviosDespachoRepository(session)
        self.remitos = SqlAlchemyRemitosDespachoRepository(session)
        self.historial = SqlAlchemyHistorialEstadosRepository(session)
        self.corridas = SqlAlchemyCorridasDespachoRepository(session)

    async def correr(self) -> ResumenCorrida:
        ports = SincronizarDespachosPorts(
            siges=self.siges,
            oca=self.oca,
            envios=self.envios,
            remitos=self.remitos,
            historial=self.historial,
            corridas=self.corridas,
            feriados=FakeCalendarioFeriados(),
            candado=FakeExclusiveLock(),
            confirmar=self.session.commit,
            reloj=lambda: AHORA,
            pausar=_sin_pausa,
        )
        return await SincronizarDespachos(ports, CONFIG).execute(OrigenCorrida.PROGRAMADA)

    async def corridas_guardadas(self) -> list[tuple[int, str | None, bool]]:
        """(id, error, terminada) de cada corrida, releída de la base."""
        stmt = (
            select(DespachoCorridaModel)
            .order_by(DespachoCorridaModel.id)
            .execution_options(populate_existing=True)
        )
        filas = (await self.session.execute(stmt)).scalars().all()
        return [(f.id, f.error, f.terminada_en is not None) for f in filas]


async def test_da_de_alta_la_guia_nueva_con_sus_remitos_y_la_consulta_en_oca(
    db_session: AsyncSession,
) -> None:
    mundo = MundoConBase(db_session)
    mundo.siges.despachos = [despacho(GUIA_A, 1), despacho(GUIA_A, 2)]
    mundo.oca.respuestas = {GUIA_A: estado_oca(GUIA_A)}

    resumen = await mundo.correr()

    assert resumen == ResumenCorrida(envios_nuevos=1, consultas_ok=1)
    assert [r.id_remito for r in await mundo.remitos.listar_por_guia(GUIA_A)] == [1, 2]
    guardado = await mundo.envios.obtener(GUIA_A)
    assert guardado is not None
    assert (guardado.estado_oca, guardado.consultado_en) == (estado_oca(GUIA_A), AHORA)
    assert len(await mundo.historial.listar_por_guia(GUIA_A)) == 1


async def test_cierra_la_corrida_colgada_pero_no_la_que_esta_corriendo(
    db_session: AsyncSession,
) -> None:
    mundo = MundoConBase(db_session)
    colgada = await mundo.corridas.iniciar(OrigenCorrida.PROGRAMADA, None)
    mundo.siges.despachos = [despacho(GUIA_A, 1)]
    vistas: list[Corrida | None] = []

    async def mirar_la_ultima_corrida(guia: str) -> None:
        vistas.append(await mundo.corridas.ultima())

    mundo.oca.al_responder = mirar_la_ultima_corrida

    resumen = await mundo.correr()

    [en_curso] = vistas
    assert en_curso is not None
    assert (en_curso.id != colgada.id, en_curso.terminada_en) == (True, None)
    assert resumen.error is None
    assert await mundo.corridas_guardadas() == [
        (colgada.id, MOTIVO_INTERRUMPIDA, True),
        (en_curso.id, None, True),
    ]
