"""Consultas read-only contra Siges/MERCURIO para los combos de selección
del Estimador de Contadores (MODELO_DE_DATOS.md §3.1-§3.3) — portadas tal
cual del SQL real del proyecto original (`Queries/GetGruposEconomicos.sql`,
`GetProcesos.sql`, `GetAnexos.sql`; el código gana si contradice los
documentos, ver brief de migración). `WITH (NOLOCK)` es intencional: nota de
seguridad de `MIGRACION_SISTEMAS.md` §7, no un olvido — la app lee mientras
el ERP sigue en operación, y el riesgo de leer una fila de una transacción
abierta es tolerable para esto."""

GRUPOS_ECONOMICOS_ACTIVOS_SQL = """
SELECT DISTINCT
    GE.id,
    GE.descripcion
FROM       GrupoEconomico  GE  WITH (NOLOCK)
INNER JOIN Anexo           A   WITH (NOLOCK) ON  A.ID_GrupoE   = GE.id
INNER JOIN Factura_Anexo   FA  WITH (NOLOCK) ON  FA.ID_Anexo   = A.ID_Anexo
WHERE  FA.ListoParaFacturar = 0
  AND  A.ID_EstadoAnexo = 1
  AND  FA.PeriodoHasta >= CAST(DATEADD(YEAR, -2, GETDATE()) AS date)
ORDER BY GE.descripcion
"""

PROCESOS_POR_GRUPO_ECONOMICO_SQL = """
SELECT
    FA.Nro_Proceso,
    CONVERT(varchar(7), FA.PeriodoDesde, 120)   AS PeriodoFacturacion,
    A.NombreAnexo,
    FA.PeriodoHasta,
    A.ID_Anexo
FROM       Factura_Anexo  FA  WITH (NOLOCK)
INNER JOIN Anexo          A   WITH (NOLOCK) ON  A.ID_Anexo  = FA.ID_Anexo
WHERE  FA.ListoParaFacturar = 0
  AND  A.ID_EstadoAnexo     = 1
  AND  A.ID_GrupoE          = ?
  AND  FA.PeriodoHasta      >= CAST(DATEADD(YEAR, -2, GETDATE()) AS date)
ORDER BY
    FA.PeriodoHasta DESC,
    A.NombreAnexo
"""

ANEXOS_POR_GRUPO_ECONOMICO_SQL = """
SELECT
    A.ID_Anexo,
    A.NombreAnexo
FROM   Anexo A WITH (NOLOCK)
WHERE  A.ID_GrupoE      = ?
  AND  A.ID_EstadoAnexo = 1
ORDER BY A.NombreAnexo
"""
