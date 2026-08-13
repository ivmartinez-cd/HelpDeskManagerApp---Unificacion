"""SQL read-only contra `dbo.Empresa` de Siges para el catálogo de PST/SPST
(ADR-014). Misma cuenta `db_datareader` (`SLA_MERCURIO_USER`) que ya usan los
módulos sla/prestadores. `Estado = 0` es **activo** (semántica invertida,
verificada con dato real — ver ADR-014). Sin parámetros de usuario: los LIKE
son literales fijos, no se interpola nada (ARCHITECTURE_GUIDE §8)."""

EMPRESAS_PST_ACTIVAS_SQL = """
SELECT ID_Empresa, Den_Comercial, razon_social, cuit
FROM dbo.Empresa
WHERE Estado = 0
  AND (Den_Comercial LIKE 'PST %' OR Den_Comercial LIKE 'SPST%')
ORDER BY Den_Comercial
"""

COSTOS_HABILITADOS_SQL = """
SELECT ID_Empresa, descripcion, fecha_vigencia, CostoKm,
       correctivo, preventivo, instalacion, PreCorrectivo, guardia, sistemas
FROM dbo.CostoServicio
WHERE habilitado = 1 AND ID_Empresa IN ({placeholders})
ORDER BY ID_Empresa, descripcion, fecha_vigencia
"""


def build_costos_habilitados_sql(cantidad: int) -> str:
    placeholders = ", ".join("?" for _ in range(cantidad))
    return COSTOS_HABILITADOS_SQL.format(placeholders=placeholders)


# Sucursales de cliente activas asignadas a un PST (`Estado = 0` es activo —
# semántica invertida, ver ADR-014). `Ciudad` aporta localidad/provincia cuando
# la sucursal la tiene cargada (LEFT JOIN: muchas no).
SUCURSALES_DE_PRESTADOR_SQL = """
SELECT S.Id_Sucursal, E.Den_Comercial, S.descripcion, S.Domicilio,
       C.DesCiudad, C.DesProvincia
FROM dbo.Sucursal S
JOIN dbo.Empresa E ON E.ID_Empresa = S.Id_Empresa
LEFT JOIN dbo.Ciudad C ON C.Id_Ciudad = S.Id_Ciudad
WHERE S.ID_Prestador = ? AND S.Estado = 0
ORDER BY E.Den_Comercial, S.descripcion
"""
