"""Índice de Tabla KM: si la sucursal tiene la fila vieja archivada y la vigente con
el mismo nombre, vale la vigente; si solo tiene la archivada, vale la archivada."""

from src.modules.liquidaciones.domain.services.motor_reglas._resolucion import (
    indexar_tablas_km,
    resolver_tabla_km,
    tablas_archivadas_en_uso,
)
from tests.unit.domain.liquidaciones.factories import make_incidente, make_tabla_km


def test_la_fila_archivada_no_pisa_a_la_vigente_en_ningun_orden() -> None:
    vigente = make_tabla_km(sucursal_nombre="358 - Arrecifes", kms_a_facturar=110.0)
    archivada = make_tabla_km(
        sucursal_nombre="358 - Arrecifes", kms_a_facturar=108.0, archivada=True
    )
    incidente = make_incidente(
        empresa_nombre=vigente.empresa_nombre, sucursal_nombre="358 - Arrecifes"
    )
    for filas in ([vigente, archivada], [archivada, vigente]):
        assert resolver_tabla_km(incidente, indexar_tablas_km(filas)) is vigente


def test_si_solo_hay_fila_archivada_se_usa_y_se_reporta_para_desarchivar() -> None:
    archivada = make_tabla_km(sucursal_nombre="EDIFICIO MEOPP", archivada=True)
    incidente = make_incidente(
        empresa_nombre=archivada.empresa_nombre, sucursal_nombre="EDIFICIO MEOPP"
    )
    assert resolver_tabla_km(incidente, indexar_tablas_km([archivada])) is archivada
    assert tablas_archivadas_en_uso([incidente, incidente], [archivada]) == [archivada]


def test_la_archivada_con_vigente_del_mismo_nombre_no_se_desarchiva() -> None:
    vigente = make_tabla_km(sucursal_nombre="358 - Arrecifes")
    archivada = make_tabla_km(sucursal_nombre="358 - Arrecifes", archivada=True)
    incidente = make_incidente(
        empresa_nombre=vigente.empresa_nombre, sucursal_nombre="358 - Arrecifes"
    )
    assert tablas_archivadas_en_uso([incidente], [archivada, vigente]) == []
