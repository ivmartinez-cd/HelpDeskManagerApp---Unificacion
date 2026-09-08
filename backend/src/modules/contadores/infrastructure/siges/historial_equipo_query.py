"""Consulta read-only contra Siges/MERCURIO para la línea de tiempo de un
equipo (MODELO_DE_DATOS.md §3.6) — `HISTORIAL_EQUIPO_SQL` portada tal cual
de `Queries/GetHistorialEquipo.sql` (el código gana si contradice los
documentos, ver brief de migración). `WITH (NOLOCK)` intencional, mismo
criterio que el resto de `contadores`.

La marca de "usado en facturación" es `Contadores.ID_Factura > 0` — no
alcanza con que la lectura sea `ID_ContadorActual` de un proceso todavía
abierto (por eso la CTE `PeriodosFC` excluye el placeholder de un proceso
activo no listo para facturar, donde `ID_ContadorActual = ID_ContadorAnterior`,
misma guarda que `grilla_estimacion_query.py`)."""

HISTORIAL_EQUIPO_SQL = """
;WITH
UltimoProceso AS (
    SELECT MAX(FC0.Nro_Proceso) AS Nro_Proceso
    FROM   Factura_Contador FC0 WITH (NOLOCK)
    WHERE  FC0.ID_Maquina       = ?
      AND  FC0.ID_ClaseContador = ?
),
PeriodosFC AS (
    SELECT
        FC.ID_ContadorActual,
        FC.ImpresionesReales,
        FC.Nro_Proceso,
        FA.PeriodoHasta,
        FA.PeriodoFacturacion
    FROM  Factura_Contador FC WITH (NOLOCK)
    JOIN  Factura_Anexo    FA WITH (NOLOCK)
           ON FA.Nro_Proceso      = FC.Nro_Proceso
    JOIN  UltimoProceso    UP
           ON 1 = 1
    WHERE FC.ID_Maquina       = ?
      AND FC.ID_ClaseContador = ?
      AND FA.PeriodoHasta     >= ?
      AND (
            FC.ID_SubProceso > 0
         OR FC.Nro_Proceso = UP.Nro_Proceso
      )
      AND (
            FC.ID_ContadorAnterior IS NULL
         OR FC.ID_ContadorActual <> FC.ID_ContadorAnterior
      )
)
SELECT
    CAST(C.FechaTomaContador AS date)   AS Fecha,
    C.Contador                          AS Valor,
    C.ID_TipoToma,
    TT.Descripcion                      AS TipoTomDesc,
    CAST(TT.Para_Facturar AS bit)       AS Para_Facturar,
    FC.Nro_Proceso                      AS FC_NroProceso,
    FC.PeriodoHasta                     AS FC_PeriodoHasta,
    FC.ImpresionesReales                AS FC_Impresiones,
    FC.PeriodoFacturacion               AS FC_PeriodoFact,
    ISNULL(C.ID_Factura, 0)             AS ID_Factura,
    C.ID_Empresa                        AS Snap_ID_Empresa,
    C.ID_Sucursal                       AS Snap_ID_Sucursal,
    C.ID_Anexo                          AS Snap_ID_Anexo
FROM       Contadores  C  WITH (NOLOCK)
INNER JOIN Tipo_Toma  TT  WITH (NOLOCK)
           ON TT.id              = C.ID_TipoToma
LEFT JOIN  PeriodosFC FC
           ON FC.ID_ContadorActual = C.ID_Contador
WHERE C.ID_Maquina       = ?
  AND C.ID_ClaseContador = ?
  AND C.Estado          <> 1
  AND C.FechaTomaContador >= ?
ORDER BY
    C.FechaTomaContador DESC,
    C.ID_Contador        DESC
"""
