"""Rubro de un contrato de Siges a partir de `Contrato.ID_EmpresaAdmin` (la
empresa propia de Canal Directo que lo administra). `Contrato` no tiene
columna de rubro; la correlación se verificó contra el parque activo de
todos los contratos el 2026-08-21 (SIGES_READONLY_CATALOGO_DATOS.md §3):
121 CD3 (CDSISA) = impresión, 681 CD4 (Directar) = cartelería digital,
1 CD1 (CDSA) = hardware IT, 2 CD2 (PS) = sin parque relevante."""

RUBRO_IMPRESION = "IMPRESION"
RUBRO_CARTELERIA = "CARTELERIA"
RUBRO_IT = "IT"
RUBRO_OTRO = "OTRO"
RUBRO_DESCONOCIDO = "DESCONOCIDO"

_POR_EMPRESA_ADMIN: dict[int, str] = {
    121: RUBRO_IMPRESION,
    681: RUBRO_CARTELERIA,
    1: RUBRO_IT,
    2: RUBRO_OTRO,
}


def rubro_por_empresa_admin(id_empresa_admin: int | None) -> str:
    if id_empresa_admin is None:
        return RUBRO_DESCONOCIDO
    return _POR_EMPRESA_ADMIN.get(id_empresa_admin, RUBRO_OTRO)
