"""Catálogo de técnicos de planta en Siges — insumo del vínculo
Empleado↔técnico. Mismo filtro que usa `bono_tecnicos` para identificar
técnicos de Canal Directo (`Den_Comercial LIKE 'CD - %'`) y la semántica de
`Estado` verificada en ADR-014 (`0`=activo)."""

TECNICOS_ACTIVOS_SQL = """
SELECT ID_Empresa, Den_Comercial
FROM dbo.Empresa
WHERE Estado = 0
  AND Den_Comercial LIKE 'CD - %'
ORDER BY Den_Comercial
"""
