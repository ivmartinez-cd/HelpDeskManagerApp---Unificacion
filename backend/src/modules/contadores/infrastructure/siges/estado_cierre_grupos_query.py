"""SQL del estado real de cierre por grupo económico contra SiGesReadOnly.

Mismo universo base que `anexos_pendientes_query.py` (`Factura_Anexo`, última
fila por anexo = período abierto, solo `discriminador='I'` activos) pero SIN
sus dos filtros a propósito: acá interesa el grupo aunque su período abierto
ya sea el mes en curso o esté `A LIBERAR` (`ListoParaFacturar=1`) — son casos
donde el cliente YA avanzó y no debería seguir contando como "sin cerrar" en
otro lado (ver `filtrar_pendientes_por_periodo_real.py`). `sin_cerrar` es
`1` si ALGUNO de los anexos activos del grupo sigue con un período anterior
al actual y sin facturar."""

ESTADO_CIERRE_GRUPOS_SQL = """
WITH ultimo AS (
  SELECT FA.ID_Anexo, FA.PeriodoFacturacion, FA.Facturado,
         ROW_NUMBER() OVER (PARTITION BY FA.ID_Anexo
                            ORDER BY FA.PeriodoFacturacion DESC,
                                     FA.Nro_Proceso DESC) AS rn
  FROM dbo.Factura_Anexo FA
)
SELECT G.descripcion AS grupo,
       MAX(CASE WHEN u.Facturado = 0 AND u.PeriodoFacturacion < ?
                THEN 1 ELSE 0 END) AS sin_cerrar
FROM ultimo u
INNER JOIN dbo.Anexo A ON A.ID_Anexo = u.ID_Anexo
INNER JOIN dbo.GrupoEconomico G ON G.id = A.ID_GrupoE
WHERE u.rn = 1
  AND A.ID_EstadoAnexo = 1
  AND A.discriminador = 'I'
GROUP BY G.descripcion
"""
