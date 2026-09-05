"""Tests del import CSV de Tabla KM (`_liq_csv_upsert_tabla_km.import_tabla_km`)
— upsert por (prestador, empresa, sucursal): reimportar el mismo CSV no debe
duplicar filas, y un SPST ya vinculado a mano sobrevive al reimport (el CSV no
trae columna de SPST)."""

import io
import uuid

from fastapi import UploadFile

from src.modules.liquidaciones.application.use_cases.config_tabla_km import (
    ConfigTablaKmPorts,
    CreateTablaKm,
    UpdateTablaKm,
)
from src.modules.liquidaciones.presentation._liq_csv_upsert_tabla_km import import_tabla_km
from tests.unit.domain.liquidaciones.fakes import FakePrestadorRepository
from tests.unit.domain.liquidaciones.fakes_config import FakeConfigTablaKmRepository

_HEADER = (
    "PST_CLAVE,EMPRESA,SUCURSAL,DOMICILIO,LOCALIDAD,PROVINCIA,"
    "KMS_RECORRIDO,KMS_A_FACTURAR,UMBRAL_VIATICO,APLICA_VIATICO,URL_MAPS,OBSERVACIONES\n"
)
_VACIO = {"creados": 0, "actualizados": 0, "sinCambios": 0, "descartadas": 0}


def _archivo(contenido: str) -> UploadFile:
    return UploadFile(file=io.BytesIO(contenido.encode("utf-8")), filename="tabla_km.csv")


async def _importar(csv_text: str, prestadores: FakePrestadorRepository, tabla_km):
    ports = ConfigTablaKmPorts(tabla_km=tabla_km)
    resultado, tocados = await import_tabla_km(
        _archivo(csv_text), CreateTablaKm(ports), UpdateTablaKm(ports), prestadores, tabla_km
    )
    return resultado, tocados


async def _pentacom(prestadores: FakePrestadorRepository):
    return await prestadores.create(
        nombre="PENTACOM", nombre_corto="PENTACOM", cuit=None, region=None
    )


async def test_import_csv_crea_fila_y_marca_prestador_tocado() -> None:
    prestadores = FakePrestadorRepository()
    prestador = await _pentacom(prestadores)
    tabla_km = FakeConfigTablaKmRepository()
    csv_text = _HEADER + "PENTACOM,Adecoagro,Las Horquetas,,,,100,100,30,SI,,\n"

    resultado, tocados = await _importar(csv_text, prestadores, tabla_km)

    assert resultado == {**_VACIO, "creados": 1}
    assert tocados == {prestador.id}
    assert len(tabla_km.rows) == 1


async def test_reimportar_el_mismo_csv_no_duplica() -> None:
    prestadores = FakePrestadorRepository()
    await _pentacom(prestadores)
    tabla_km = FakeConfigTablaKmRepository()
    csv_text = _HEADER + "PENTACOM,Adecoagro,Las Horquetas,,,,100,100,30,SI,,\n"

    primero, _ = await _importar(csv_text, prestadores, tabla_km)
    segundo, tocados_2 = await _importar(csv_text, prestadores, tabla_km)

    assert primero == {**_VACIO, "creados": 1}
    assert segundo == {**_VACIO, "sinCambios": 1}
    assert tocados_2 == set()  # nada nuevo, no hay que re-vincular SPST
    assert len(tabla_km.rows) == 1


async def test_reimportar_con_km_distinto_actualiza_en_vez_de_duplicar() -> None:
    prestadores = FakePrestadorRepository()
    await _pentacom(prestadores)
    tabla_km = FakeConfigTablaKmRepository()
    original = _HEADER + "PENTACOM,Adecoagro,Las Horquetas,,,,100,100,30,SI,,\n"
    await _importar(original, prestadores, tabla_km)

    corregido = _HEADER + "PENTACOM,Adecoagro,Las Horquetas,,,,120,120,30,SI,,\n"
    resultado, _ = await _importar(corregido, prestadores, tabla_km)

    assert resultado == {**_VACIO, "actualizados": 1}
    assert len(tabla_km.rows) == 1
    assert tabla_km.rows[0].kms_recorrido == 120


async def test_reimportar_preserva_spst_ya_vinculado() -> None:
    """El CSV no trae SPST — reimportar no debe desvincular lo que ya se
    vinculó a mano (ej. con "Vincular SPST")."""
    prestadores = FakePrestadorRepository()
    await _pentacom(prestadores)
    tabla_km = FakeConfigTablaKmRepository()
    csv_text = _HEADER + "PENTACOM,Adecoagro,Las Horquetas,,,,100,100,30,SI,,\n"
    await _importar(csv_text, prestadores, tabla_km)
    spst_id = uuid.uuid4()
    await tabla_km.update_vinculo_spst(tabla_km.rows[0].id, spst_id=spst_id)

    corregido = _HEADER + "PENTACOM,Adecoagro,Las Horquetas,,,,120,120,30,SI,,\n"
    resultado, _ = await _importar(corregido, prestadores, tabla_km)

    assert resultado == {**_VACIO, "actualizados": 1}
    assert tabla_km.rows[0].spst_id == spst_id


async def test_import_csv_prestador_desconocido_descarta_fila() -> None:
    prestadores = FakePrestadorRepository()
    tabla_km = FakeConfigTablaKmRepository()
    csv_text = _HEADER + "NOEXISTE,Adecoagro,Las Horquetas,,,,100,100,30,SI,,\n"

    resultado, tocados = await _importar(csv_text, prestadores, tabla_km)

    assert resultado == {**_VACIO, "descartadas": 1}
    assert tocados == set()
    assert tabla_km.rows == []
