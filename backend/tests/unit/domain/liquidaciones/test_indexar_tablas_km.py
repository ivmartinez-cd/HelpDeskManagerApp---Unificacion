"""El índice de Tabla KM ignora las filas archivadas: si la sucursal tiene la fila
vieja archivada y la vigente con el mismo nombre, vale la vigente."""

from src.modules.liquidaciones.domain.services.motor_reglas._resolucion import (
    indexar_tablas_km,
    resolver_tabla_km,
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
