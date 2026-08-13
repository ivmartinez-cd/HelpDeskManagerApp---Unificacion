"""Tests del import CSV de tarifarios (`_liq_csv.import_tarifarios`) — cada fila
se crea vía `CreateTarifario`, así que el grupo (prestador, tipo_servicio, zona)
queda recadenado igual que en el alta manual desde la UI."""

import io
from datetime import date

from fastapi import UploadFile

from src.modules.liquidaciones.application.use_cases.config_tarifarios import (
    ConfigTarifariosPorts,
    CreateTarifario,
)
from src.modules.liquidaciones.presentation._liq_csv import import_tarifarios
from tests.unit.domain.liquidaciones.fakes import FakePrestadorRepository
from tests.unit.domain.liquidaciones.fakes_config import FakeConfigTarifarioRepository

_HEADER = "PST_CLAVE,TIPO_SERVICIO,ZONA,COSTO_SERVICIO,COSTO_KM,VIGENCIA_DESDE,VIGENCIA_HASTA\n"


def _archivo(contenido: str) -> UploadFile:
    return UploadFile(file=io.BytesIO(contenido.encode("utf-8")), filename="tarifarios.csv")


async def test_import_csv_recadena_vigencias_del_grupo() -> None:
    prestadores = FakePrestadorRepository()
    await prestadores.create(nombre="PENTACOM", nombre_corto="PENTACOM", cuit=None, region=None)
    tarifarios = FakeConfigTarifarioRepository()
    crear = CreateTarifario(ConfigTarifariosPorts(tarifarios=tarifarios))
    csv_text = (
        _HEADER
        + "PENTACOM,correctivo,,1500,100,2026-01-01,\n"
        + "PENTACOM,correctivo,,1800,120,2026-06-01,\n"
    )

    resultado = await import_tarifarios(_archivo(csv_text), crear, prestadores)

    assert resultado == {"creados": 2}
    por_desde = {t.vigencia_desde: t for t in tarifarios.rows}
    assert por_desde[date(2026, 1, 1)].vigencia_hasta == date(2026, 5, 31)
    assert por_desde[date(2026, 6, 1)].vigencia_hasta is None


async def test_import_csv_prestador_desconocido_omite_fila() -> None:
    prestadores = FakePrestadorRepository()
    tarifarios = FakeConfigTarifarioRepository()
    crear = CreateTarifario(ConfigTarifariosPorts(tarifarios=tarifarios))
    csv_text = _HEADER + "NOEXISTE,correctivo,,1500,100,2026-01-01,\n"

    resultado = await import_tarifarios(_archivo(csv_text), crear, prestadores)

    assert resultado == {"creados": 0}
    assert tarifarios.rows == []
