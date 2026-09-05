"""Tests del caso de uso de vínculo Tabla KM ↔ SPST (dry-run + aplicar)."""

from src.modules.liquidaciones.application.use_cases.vincular_tabla_km_spst import (
    VincularTablaKmSpst,
    VincularTablaKmSpstPorts,
)
from tests.unit.domain.liquidaciones.factories import make_spst, make_tabla_km
from tests.unit.domain.liquidaciones.fakes_config import (
    FakeConfigSpstRepository,
    FakeConfigTablaKmRepository,
)


def _use_case(
    tabla_km: FakeConfigTablaKmRepository, spsts: FakeConfigSpstRepository
) -> VincularTablaKmSpst:
    return VincularTablaKmSpst(VincularTablaKmSpstPorts(tabla_km=tabla_km, spsts=spsts))


class TestVincularTablaKmSpst:
    async def test_dry_run_no_escribe(self) -> None:
        prestador_id = make_spst().prestador_id
        spst = make_spst(prestador_id=prestador_id, zona_cobertura="Valle Fértil")
        fila = make_tabla_km(
            prestador_id=prestador_id, localidad_cliente="SAN AGUSTIN DEL VALLE FERTIL"
        )
        tabla_km = FakeConfigTablaKmRepository([fila])
        spsts = FakeConfigSpstRepository([spst])

        resultado = await _use_case(tabla_km, spsts).execute(prestador_id, dry_run=True)

        assert resultado.con_propuesta == 1
        assert resultado.vinculadas == 0
        assert tabla_km.rows[0].spst_id is None

    async def test_aplicar_vincula_solo_las_que_matchean(self) -> None:
        prestador_id = make_spst().prestador_id
        spst = make_spst(prestador_id=prestador_id, zona_cobertura="Valle Fértil")
        con_match = make_tabla_km(prestador_id=prestador_id, localidad_cliente="Valle Fertil")
        sin_match = make_tabla_km(prestador_id=prestador_id, localidad_cliente="San Rafael")
        tabla_km = FakeConfigTablaKmRepository([con_match, sin_match])
        spsts = FakeConfigSpstRepository([spst])

        resultado = await _use_case(tabla_km, spsts).execute(prestador_id, dry_run=False)

        assert resultado.vinculadas == 1
        assert resultado.sin_propuesta == 1
        por_id = {t.id: t for t in tabla_km.rows}
        assert por_id[con_match.id].spst_id == spst.id
        assert por_id[sin_match.id].spst_id is None

    async def test_fila_ya_vinculada_no_se_cuenta(self) -> None:
        prestador_id = make_spst().prestador_id
        spst = make_spst(prestador_id=prestador_id, zona_cobertura="Valle Fértil")
        ya_vinculada = make_tabla_km(
            prestador_id=prestador_id, localidad_cliente="Valle Fertil", spst_id=spst.id
        )
        tabla_km = FakeConfigTablaKmRepository([ya_vinculada])
        spsts = FakeConfigSpstRepository([spst])

        resultado = await _use_case(tabla_km, spsts).execute(prestador_id, dry_run=False)

        assert resultado.total_sin_vincular == 0
        assert resultado.vinculadas == 0

    async def test_propuesta_por_provincia_no_se_aplica_sin_incluir_provincia(self) -> None:
        prestador_id = make_spst().prestador_id
        spst = make_spst(
            prestador_id=prestador_id, zona_cobertura="Gral. Roca", provincia="Río Negro"
        )
        fila = make_tabla_km(
            prestador_id=prestador_id, localidad_cliente="Cipolletti", provincia_cliente="Río Negro"
        )
        tabla_km = FakeConfigTablaKmRepository([fila])
        spsts = FakeConfigSpstRepository([spst])

        resultado = await _use_case(tabla_km, spsts).execute(prestador_id, dry_run=False)

        assert resultado.por_provincia == 1
        assert resultado.con_propuesta == 0
        assert resultado.vinculadas == 0
        assert tabla_km.rows[0].spst_id is None

    async def test_incluir_provincia_aplica_la_propuesta(self) -> None:
        prestador_id = make_spst().prestador_id
        spst = make_spst(
            prestador_id=prestador_id, zona_cobertura="Gral. Roca", provincia="Río Negro"
        )
        fila = make_tabla_km(
            prestador_id=prestador_id, localidad_cliente="Cipolletti", provincia_cliente="Río Negro"
        )
        tabla_km = FakeConfigTablaKmRepository([fila])
        spsts = FakeConfigSpstRepository([spst])

        resultado = await _use_case(tabla_km, spsts).execute(
            prestador_id, dry_run=False, incluir_provincia=True
        )

        assert resultado.con_propuesta == 1
        assert resultado.vinculadas == 1
        assert tabla_km.rows[0].spst_id == spst.id
