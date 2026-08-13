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
