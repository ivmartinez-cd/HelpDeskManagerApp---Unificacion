"""Tests del import CSV de tarifarios (`_liq_csv_upsert_tarifarios.import_tarifarios`)
— upsert por (prestador, tipo_servicio, spst_id, vigencia_desde): reimportar el
mismo CSV no debe duplicar filas. La columna `SPST` resuelve por nombre dentro
del prestador (vacía = tarifa genérica)."""

import io
from datetime import date

from fastapi import UploadFile

from src.modules.liquidaciones.application.use_cases.config_tarifarios import (
    ConfigTarifariosPorts,
    CreateTarifario,
    UpdateTarifario,
)
from src.modules.liquidaciones.presentation._liq_csv_upsert_tarifarios import import_tarifarios
from tests.unit.domain.liquidaciones.fakes import FakePrestadorRepository, FakeSpstRepository
from tests.unit.domain.liquidaciones.fakes_config import FakeConfigTarifarioRepository

_HEADER = "PST_CLAVE,TIPO_SERVICIO,SPST,COSTO_SERVICIO,COSTO_KM,VIGENCIA_DESDE,VIGENCIA_HASTA\n"
_VACIO = {"creados": 0, "actualizados": 0, "sinCambios": 0, "descartadas": 0}


def _archivo(contenido: str) -> UploadFile:
    return UploadFile(file=io.BytesIO(contenido.encode("utf-8")), filename="tarifarios.csv")


async def _importar(
    csv_text: str,
    prestadores: FakePrestadorRepository,
    tarifarios: FakeConfigTarifarioRepository,
    spsts: FakeSpstRepository | None = None,
) -> dict:
    ports = ConfigTarifariosPorts(tarifarios=tarifarios)
    return await import_tarifarios(
        _archivo(csv_text),
        CreateTarifario(ports),
        UpdateTarifario(ports),
        prestadores,
        tarifarios,
        spsts or FakeSpstRepository(),
    )


async def test_import_csv_recadena_vigencias_del_grupo() -> None:
    prestadores = FakePrestadorRepository()
    await prestadores.create(nombre="PENTACOM", nombre_corto="PENTACOM", cuit=None, region=None)
    tarifarios = FakeConfigTarifarioRepository()
    csv_text = (
        _HEADER
        + "PENTACOM,correctivo,,1500,100,2026-01-01,\n"
        + "PENTACOM,correctivo,,1800,120,2026-06-01,\n"
    )

    resultado = await _importar(csv_text, prestadores, tarifarios)

    assert resultado == {**_VACIO, "creados": 2}
    por_desde = {t.vigencia_desde: t for t in tarifarios.rows}
    assert por_desde[date(2026, 1, 1)].vigencia_hasta == date(2026, 5, 31)
    assert por_desde[date(2026, 6, 1)].vigencia_hasta is None


async def test_import_csv_prestador_desconocido_descarta_fila() -> None:
    prestadores = FakePrestadorRepository()
    tarifarios = FakeConfigTarifarioRepository()
    csv_text = _HEADER + "NOEXISTE,correctivo,,1500,100,2026-01-01,\n"

    resultado = await _importar(csv_text, prestadores, tarifarios)

    assert resultado == {**_VACIO, "descartadas": 1}
    assert tarifarios.rows == []


async def test_reimportar_el_mismo_csv_no_duplica() -> None:
    """El caso que reportó el bug: exportar, no tocar nada, volver a cargar."""
    prestadores = FakePrestadorRepository()
    await prestadores.create(nombre="PENTACOM", nombre_corto="PENTACOM", cuit=None, region=None)
    tarifarios = FakeConfigTarifarioRepository()
    csv_text = _HEADER + "PENTACOM,correctivo,,1500,100,2026-01-01,\n"

    primero = await _importar(csv_text, prestadores, tarifarios)
    segundo = await _importar(csv_text, prestadores, tarifarios)

    assert primero == {**_VACIO, "creados": 1}
    assert segundo == {**_VACIO, "sinCambios": 1}
    assert len(tarifarios.rows) == 1


async def test_reimportar_con_costo_distinto_actualiza_en_vez_de_duplicar() -> None:
    """El flujo esperado: exportar, corregir un precio a mano, reimportar."""
    prestadores = FakePrestadorRepository()
    await prestadores.create(nombre="PENTACOM", nombre_corto="PENTACOM", cuit=None, region=None)
    tarifarios = FakeConfigTarifarioRepository()
    inicial = _HEADER + "PENTACOM,correctivo,,1500,100,2026-01-01,\n"
    await _importar(inicial, prestadores, tarifarios)

    resultado = await _importar(
        _HEADER + "PENTACOM,correctivo,,1650,100,2026-01-01,\n", prestadores, tarifarios
    )

    assert resultado == {**_VACIO, "actualizados": 1}
    assert len(tarifarios.rows) == 1
    assert tarifarios.rows[0].costo_servicio == 1650


async def test_columna_spst_resuelve_por_nombre_dentro_del_prestador() -> None:
    prestadores = FakePrestadorRepository()
    prestador = await prestadores.create(
        nombre="PENTACOM", nombre_corto="PENTACOM", cuit=None, region=None
    )
    spsts = FakeSpstRepository()
    spst = await spsts.create(
        prestador_id=prestador.id,
        nombre="Ushuaia",
        domicilio=None,
        localidad=None,
        provincia=None,
        zona_cobertura=None,
    )
    tarifarios = FakeConfigTarifarioRepository()
    csv_text = _HEADER + "PENTACOM,correctivo,Ushuaia,1500,100,2026-01-01,\n"

    resultado = await _importar(csv_text, prestadores, tarifarios, spsts)

    assert resultado == {**_VACIO, "creados": 1}
    assert tarifarios.rows[0].spst_id == spst.id


async def test_columna_spst_desconocido_descarta_fila() -> None:
    prestadores = FakePrestadorRepository()
    await prestadores.create(nombre="PENTACOM", nombre_corto="PENTACOM", cuit=None, region=None)
    tarifarios = FakeConfigTarifarioRepository()
    csv_text = _HEADER + "PENTACOM,correctivo,No Existe,1500,100,2026-01-01,\n"

    resultado = await _importar(csv_text, prestadores, tarifarios)

    assert resultado == {**_VACIO, "descartadas": 1}
    assert tarifarios.rows == []
