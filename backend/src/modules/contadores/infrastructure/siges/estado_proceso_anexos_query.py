"""SQL del estado real de proceso de facturación por anexo contra
SiGesReadOnly, para el KPI "Anexos sin procesar" (operadores que se olvidan
de generar el proceso de un anexo).

Mismo universo base que `estado_cierre_grupos_query.py`
(`ID_EstadoAnexo=1 AND discriminador='I'` — solo Impresión, los demás tipos
van por una vista rota en la réplica), pero **no** reusa su CTE
`ROW_NUMBER()`: ese busca el último proceso de CUALQUIER período; acá
interesa el último período que llegó a tener proceso realmente, así que un
anexo sin ninguna fila en `Factura_Anexo` sale con `ultimo_periodo_procesado
NULL` en vez de quedar afuera del resultado — el caso de uso necesita ver
también los anexos sin ningún historial para poder descartarlos a propósito
(sin historial no hay prueba de olvido, ver `listar_anexos_sin_procesar.py`).

Sin parámetros: todo el juicio de "¿le tocaba estar procesado?" vive en el
dominio (comparando contra `hoy`), no en la query — así la caché del gateway
sirve a cualquier `today` que llegue del cliente.

`maquinas_activas` cuenta `Maquina.ID_Anexo` con `Estado=0` (vigente, mismo
criterio que `EQUIPOS_SIN_REAL_SQL`): caso real 2026-09-03, el anexo de OCA
tenía 12 máquinas ligadas pero las 12 "De Baja" — 0 activas. Sin parque
vigente no hay nada que facturar, así que el dominio descarta esos anexos
en vez de acusar al operador de un olvido que no existe."""

ESTADO_PROCESO_ANEXOS_SQL = """
SELECT A.ID_Anexo AS id_anexo,
       A.NombreAnexo AS anexo,
       G.descripcion AS grupo,
       (SELECT MAX(FA.PeriodoFacturacion)
        FROM dbo.Factura_Anexo FA
        WHERE FA.ID_Anexo = A.ID_Anexo AND FA.Nro_Proceso IS NOT NULL)
           AS ultimo_periodo_procesado,
       (SELECT COUNT(*)
        FROM dbo.Maquina M
        WHERE M.ID_Anexo = A.ID_Anexo AND M.Estado = 0)
           AS maquinas_activas
FROM dbo.Anexo A
INNER JOIN dbo.GrupoEconomico G ON G.id = A.ID_GrupoE
WHERE A.ID_EstadoAnexo = 1
  AND A.discriminador = 'I'
"""
