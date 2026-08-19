"""SQL del estado real de cierre por grupo económico contra SiGesReadOnly.

Mismo universo base y misma definición de "pendiente" que
`anexos_pendientes_query.py` (`Facturado=0 AND ListoParaFacturar=0` — regla
de la TL, 2026-08-14: A LIBERAR ya salió de la cola del contador) pero SIN su
filtro de "mes en curso afuera": acá interesa el grupo aunque su período
abierto ya sea el mes en curso, porque eso es justamente lo que indica que
el cliente YA avanzó y no debería seguir contando como "sin cerrar" en otro
lado (ver `filtrar_pendientes_por_periodo_real.py`). `sin_cerrar` es `1` si
ALGUNO de los anexos activos del grupo sigue pendiente (mismo criterio que
el reporte) de un período anterior al actual."""

ESTADO_CIERRE_GRUPOS_SQL = """
WITH ultimo AS (
  SELECT FA.ID_Anexo, FA.PeriodoFacturacion, FA.Facturado, FA.ListoParaFacturar,
         ROW_NUMBER() OVER (PARTITION BY FA.ID_Anexo
                            ORDER BY FA.PeriodoFacturacion DESC,
                                     FA.Nro_Proceso DESC) AS rn
  FROM dbo.Factura_Anexo FA
)
SELECT G.descripcion AS grupo,
       MAX(CASE WHEN u.Facturado = 0 AND u.ListoParaFacturar = 0
                     AND u.PeriodoFacturacion < ?
                THEN 1 ELSE 0 END) AS sin_cerrar
FROM ultimo u
INNER JOIN dbo.Anexo A ON A.ID_Anexo = u.ID_Anexo
INNER JOIN dbo.GrupoEconomico G ON G.id = A.ID_GrupoE
WHERE u.rn = 1
  AND A.ID_EstadoAnexo = 1
  AND A.discriminador = 'I'
GROUP BY G.descripcion
"""
