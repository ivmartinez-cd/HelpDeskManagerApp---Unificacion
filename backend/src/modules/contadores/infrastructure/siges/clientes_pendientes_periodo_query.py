"""SQL de clientes (grupos económicos) distintos con anexo de Impresión
activo pendiente de EXACTAMENTE el período inmediato anterior al mes en
curso. Mismo universo base que `estado_cierre_grupos_query.py`
(Facturado=0 AND ListoParaFacturar=0, ID_EstadoAnexo=1, discriminador='I')
pero con igualdad de período en vez de "menor que": acá interesa aislar el
arrastre del cierre que acaba de pasar, sin mezclar demorados más viejos de
otros meses.

Trae el detalle (no solo el conteo) para que la card de Inicio pueda listar
cuáles son — mismo campo `grupo` (G.descripcion) que usa el resto del
módulo (ver `anexos_pendientes_query.py`)."""

CLIENTES_PENDIENTES_PERIODO_SQL = """
WITH ultimo AS (
  SELECT FA.ID_Anexo, FA.PeriodoFacturacion, FA.Facturado, FA.ListoParaFacturar,
         ROW_NUMBER() OVER (PARTITION BY FA.ID_Anexo
                            ORDER BY FA.PeriodoFacturacion DESC,
                                     FA.Nro_Proceso DESC) AS rn
  FROM dbo.Factura_Anexo FA
)
SELECT DISTINCT G.id, G.descripcion AS grupo
FROM ultimo u
INNER JOIN dbo.Anexo A ON A.ID_Anexo = u.ID_Anexo
INNER JOIN dbo.GrupoEconomico G ON G.id = A.ID_GrupoE
WHERE u.rn = 1
  AND u.Facturado = 0
  AND u.ListoParaFacturar = 0
  AND A.ID_EstadoAnexo = 1
  AND A.discriminador = 'I'
  AND u.PeriodoFacturacion = ?
ORDER BY G.descripcion
"""
