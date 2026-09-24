"""Tests de integración de SqlAlchemyCorridasDespachoRepository (`insumos_despacho_corrida`).

Todo el test corre en una transacción: `iniciada_en` (DEFAULT now()) es igual en todas las
corridas y el desempate es por id; `terminada_en` usa clock_timestamp() y avanza.
"""

from dataclasses import replace
from datetime import timedelta

import pytest
from sqlalchemy import func, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.despachados.corrida import (
    Corrida,
    OrigenCorrida,
    ResumenCorrida,
)
from src.modules.insumos.domain.repositories.acciones_despacho_repository import (
    CorridasDespachoRepository,
)
from src.modules.insumos.infrastructure.models.despacho_corrida_model import (
    DespachoCorridaModel,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_corridas_despacho_repository import (  # noqa: E501
    SqlAlchemyCorridasDespachoRepository,
)


def _repo(session: AsyncSession) -> CorridasDespachoRepository:
    return SqlAlchemyCorridasDespachoRepository(session)


async def test_sin_corridas_no_hay_ultima(db_session: AsyncSession) -> None:
    repo = _repo(db_session)

    assert await repo.ultima() is None
    assert await repo.ultima_terminada() is None


async def test_iniciar_devuelve_la_corrida_en_curso(db_session: AsyncSession) -> None:
    repo = _repo(db_session)

    corrida = await repo.iniciar(OrigenCorrida.MANUAL, "Ana Operadora")

    assert corrida == Corrida(
        id=corrida.id,
        origen=OrigenCorrida.MANUAL,
        iniciada_en=corrida.iniciada_en,
        usuario_nombre="Ana Operadora",
    )
    assert corrida.iniciada_en.tzinfo is not None
    assert await repo.ultima() == corrida
    assert await repo.ultima_terminada() is None


async def test_terminar_guarda_el_resumen_y_la_hora_real(db_session: AsyncSession) -> None:
    repo = _repo(db_session)
    corrida = await repo.iniciar(OrigenCorrida.PROGRAMADA, None)
    assert await repo.ultima() == corrida  # queda cargada en la sesión antes del UPDATE
    resumen = ResumenCorrida(envios_nuevos=3, consultas_ok=40, consultas_error=2)

    await repo.terminar(corrida.id, resumen)

    terminada = await repo.ultima()
    assert terminada is not None and terminada.terminada_en is not None
    assert terminada.terminada_en > terminada.iniciada_en
    assert terminada == replace(corrida, terminada_en=terminada.terminada_en, resumen=resumen)
    assert await repo.ultima_terminada() == terminada


async def test_terminar_con_el_error_que_corto_la_corrida(db_session: AsyncSession) -> None:
    repo = _repo(db_session)
    corrida = await repo.iniciar(OrigenCorrida.PROGRAMADA, None)

    await repo.terminar(corrida.id, ResumenCorrida(error="Siges no respondió"))

    terminada = await repo.ultima_terminada()
    assert terminada is not None
    assert terminada.resumen == ResumenCorrida(error="Siges no respondió")


async def test_cerrar_interrumpidas_cierra_solo_las_que_siguen_en_curso(
    db_session: AsyncSession,
) -> None:
    repo = _repo(db_session)
    terminada = await repo.iniciar(OrigenCorrida.PROGRAMADA, None)
    await repo.terminar(terminada.id, ResumenCorrida(consultas_ok=5))
    await repo.iniciar(OrigenCorrida.MANUAL, "Ana Operadora")
    await repo.iniciar(OrigenCorrida.PROGRAMADA, None)

    assert await repo.cerrar_interrumpidas("Proceso reiniciado") == 2
    assert await repo.cerrar_interrumpidas("Proceso reiniciado") == 0

    ultima = await repo.ultima()
    assert ultima is not None and ultima.terminada_en is not None
    assert ultima.resumen == ResumenCorrida(error="Proceso reiniciado")
    assert await repo.ultima_terminada() == ultima


async def test_ultima_y_ultima_terminada_ordenan_por_su_propia_fecha(
    db_session: AsyncSession,
) -> None:
    repo = _repo(db_session)
    primera = await repo.iniciar(OrigenCorrida.PROGRAMADA, None)
    segunda = await repo.iniciar(OrigenCorrida.MANUAL, "Ana Operadora")
    await repo.terminar(segunda.id, ResumenCorrida())
    await repo.terminar(primera.id, ResumenCorrida())
    en_curso = await repo.iniciar(OrigenCorrida.PROGRAMADA, None)
    # Iniciada ayer aunque se inserta última (id mayor): no es la última.
    await db_session.execute(
        insert(DespachoCorridaModel).values(
            origen="programada", iniciada_en=func.now() - timedelta(days=1)
        )
    )

    ultima = await repo.ultima()
    ultima_terminada = await repo.ultima_terminada()

    assert ultima is not None and ultima.id == en_curso.id
    assert ultima_terminada is not None and ultima_terminada.id == primera.id


async def test_check_constraint_rechaza_un_origen_invalido(db_session: AsyncSession) -> None:
    with pytest.raises(IntegrityError, match="ck_insumos_despacho_corrida_origen"):
        await db_session.execute(insert(DespachoCorridaModel).values(origen="webhook"))
