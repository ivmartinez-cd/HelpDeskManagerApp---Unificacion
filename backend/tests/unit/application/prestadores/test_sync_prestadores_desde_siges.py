import uuid

from src.modules.prestadores.application.use_cases.sync_prestadores_desde_siges import (
    SyncPrestadoresDesdeSiges,
    SyncPrestadoresDesdeSigesDependencies,
)
from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.domain.repositories.siges_prestador_gateway import (
    SigesPrestadorInfo,
)
from tests.unit.domain.prestadores.fakes import FakePrestadorRepository, FakeSigesPrestadorGateway


async def test_actualiza_solo_los_que_cambiaron_y_no_crea_nada_nuevo() -> None:
    prestadores = FakePrestadorRepository()
    siges = FakeSigesPrestadorGateway()

    sin_cambios = Prestador(
        id=uuid.uuid4(), siges_empresa_id=1, den_comercial="PST A",
        razon_social="Razon A", cuit="20111111111", equipos=120,
        operador_id=None, is_active=True,
    )
    con_cambios = Prestador(
        id=uuid.uuid4(), siges_empresa_id=2, den_comercial="PST B",
        razon_social=None, cuit=None, equipos=None, operador_id=None, is_active=True,
    )
    prestadores.rows[sin_cambios.id] = sin_cambios
    prestadores.rows[con_cambios.id] = con_cambios

    siges.por_id[1] = SigesPrestadorInfo(
        siges_empresa_id=1, den_comercial="PST A", razon_social="Razon A", cuit="20111111111"
    )
    siges.por_id[2] = SigesPrestadorInfo(
        siges_empresa_id=2, den_comercial="PST B", razon_social="Razon B real", cuit="20222222222"
    )
    siges.equipos_por_id[1] = 120  # parque igual al persistido: no cuenta como cambio
    siges.equipos_por_id[2] = 841
    # 999 no está en la cartera local -- el gateway ni se entera de este id
    # (find_by_siges_ids solo se llama con los ids ya conocidos).

    use_case = SyncPrestadoresDesdeSiges(
        SyncPrestadoresDesdeSigesDependencies(prestadores=prestadores, siges=siges)
    )
    result = await use_case.execute()

    assert siges.calls == [[1, 2]]
    assert result.sin_cambios == 1
    assert result.actualizados == ["PST B"]
    assert prestadores.rows[con_cambios.id].razon_social == "Razon B real"
    assert prestadores.rows[con_cambios.id].cuit == "20222222222"
    assert prestadores.rows[con_cambios.id].equipos == 841
    assert len(prestadores.rows) == 2  # no se creó ningún PST nuevo


async def test_solo_el_parque_cambiado_tambien_cuenta_como_actualizacion() -> None:
    prestadores = FakePrestadorRepository()
    siges = FakeSigesPrestadorGateway()

    pst = Prestador(
        id=uuid.uuid4(), siges_empresa_id=740, den_comercial="PST Villa Mercedes",
        razon_social="INFOMAC S. A. S", cuit=None, equipos=800, operador_id=None, is_active=True,
    )
    prestadores.rows[pst.id] = pst
    siges.por_id[740] = SigesPrestadorInfo(
        siges_empresa_id=740, den_comercial="PST Villa Mercedes",
        razon_social="INFOMAC S. A. S", cuit=None,
    )
    siges.equipos_por_id[740] = 841

    result = await SyncPrestadoresDesdeSiges(
        SyncPrestadoresDesdeSigesDependencies(prestadores=prestadores, siges=siges)
    ).execute()

    assert result.actualizados == ["PST Villa Mercedes"]
    assert prestadores.rows[pst.id].equipos == 841


async def test_pst_sin_filas_en_el_conteo_queda_con_parque_cero() -> None:
    """Un PST sin máquinas activas no aparece en el GROUP BY — eso es un
    parque de 0 real, no un dato faltante."""
    prestadores = FakePrestadorRepository()
    siges = FakeSigesPrestadorGateway()

    pst = Prestador(
        id=uuid.uuid4(), siges_empresa_id=3, den_comercial="PST C",
        razon_social=None, cuit=None, equipos=15, operador_id=None, is_active=True,
    )
    prestadores.rows[pst.id] = pst
    siges.por_id[3] = SigesPrestadorInfo(
        siges_empresa_id=3, den_comercial="PST C", razon_social=None, cuit=None
    )

    result = await SyncPrestadoresDesdeSiges(
        SyncPrestadoresDesdeSigesDependencies(prestadores=prestadores, siges=siges)
    ).execute()

    assert result.actualizados == ["PST C"]
    assert prestadores.rows[pst.id].equipos == 0


async def test_pst_ausente_en_siges_no_se_toca() -> None:
    prestadores = FakePrestadorRepository()
    siges = FakeSigesPrestadorGateway()

    huerfano = Prestador(
        id=uuid.uuid4(), siges_empresa_id=5, den_comercial="PST viejo",
        razon_social=None, cuit=None, equipos=None, operador_id=None, is_active=True,
    )
    prestadores.rows[huerfano.id] = huerfano
    # siges.por_id vacío: la consulta no devuelve nada para el id 5.

    use_case = SyncPrestadoresDesdeSiges(
        SyncPrestadoresDesdeSigesDependencies(prestadores=prestadores, siges=siges)
    )
    result = await use_case.execute()

    assert result.actualizados == []
    assert result.sin_cambios == 0
    assert prestadores.rows[huerfano.id].den_comercial == "PST viejo"
    assert prestadores.rows[huerfano.id].is_active is True
