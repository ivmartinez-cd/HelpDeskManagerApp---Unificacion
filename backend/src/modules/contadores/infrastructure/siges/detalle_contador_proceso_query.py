"""SQL del reporte completo "Detalle de contadores por nro de proceso" —
mismo origen de datos que `falta_contador_proceso_query.py` (`dbo.Factura_Contador`
+ `dbo.Maquina`, investigación documentada ahí y en
`SIGES_READONLY_CATALOGO_DATOS.md` §"Factura_Contador"), pero sin el filtro
`ID_ContadorActual = ID_ContadorAnterior`: acá se trae el proceso completo y
el flag `falta_contador` viaja como columna calculada, para que la pantalla
de reporte pueda alternar entre "todo el proceso" y "solo falta contador"
sin una segunda consulta.

Columnas y joins verificados 1:1 el 2026-09-07 contra una captura real del
reporte compartida por el usuario (serie `CNB1R4C0MV`, ISSN → Nro_Proceso
99089 real, resuelto por la serie y contrastado campo por campo con
`explore_siges_detalle_contadores_proceso.py`/consultas ad-hoc):
- `Empresa`/`Sucursal`/`Sector` salen del SNAPSHOT de `Factura_Contador`
  (`FC.ID_Empresa`/`FC.ID_Sucursal`/`FC.ID_Sector`), no de la ubicación
  ACTUAL de la máquina — mismo criterio que `grilla_estimacion_query.py`
  (una mudanza física no debe cruzar el detalle de un proceso ya cerrado).
  `Sector` es NULL-able (máquina sin sector al cierre).
- `Modelo` sale de `Maquina.ID_Articulo → Articulo.ID_ArtGen → ArtGen.Descripcion`,
  mismo join que `candidatos_query.py` (METADATA_EQUIPO_SQL) — sin snapshot,
  la máquina rara vez cambia de artículo entre el cierre y hoy.
- `Fecha Toma Ant./Act.` salen directo de `Factura_Contador.FechaTomaContadorAnterior/Actual`
  (no hace falta joinear `Contadores`: la fecha ya viaja en la propia fila).
- `Estado Máquina`/`Direccion_IP`/`Mascara_IP` son de `dbo.Maquina` (actual,
  no snapshot — la tabla no guarda un historial de estos campos).
- **`Contador Actual` NO es un mapeo directo de `ImpreContadorActual`**:
  verificado que en una fila "Falta Contador" (`ID_ContadorActual =
  ID_ContadorAnterior`, mismo registro físico de `Contadores` para ambos)
  `ImpreContadorActual` guarda el mismo valor que el anterior (1 y 1, en el
  caso verificado), pero el reporte muestra `Contador Act. = 0` — el reporte
  no repite el valor viejo, señala "sin lectura nueva" con 0. Se calcula en
  el gateway, no en el SQL (más legible para testear con un runner fake).
- **`Tipo` combina "FALTA CONTADOR" + la clase** (verificado contra la
  captura: "FALTA CONTADOR Mono"). El caso "AUTOMATICO" (real con delta 0,
  `ID_ContadorActual <> ID_ContadorAnterior AND ImpresionesReales = 0`) sale
  de la investigación documentada en `falta_contador_proceso_query.py`, no
  de una captura propia — no confirmado con una captura del reporte. El
  resto de los casos (lectura real con delta != 0) no tiene `Tipo` conocido:
  se deja en `NULL`, nunca inventado.

`ID_ClaseContador IN (10, 20)` (Mono/Color) es el mismo recorte que ya usa
`FALTA_CONTADOR_POR_PROCESO_SQL` — no hay evidencia de que el reporte legacy
incluya otras clases, y no se investigó esa hipótesis.

`nro_proceso`/`nombre_anexo`/`periodo_facturacion` se suman via el mismo join
`Factura_Anexo`→`Anexo` que ya usa `PROCESOS_POR_GRUPO_ECONOMICO_SQL`
(`proceso_estimacion_query.py`) para no perder de qué proceso/anexo es cada
fila cuando `DETALLE_CONTADORES_POR_GRUPO_SQL` junta varios procesos en una
sola respuesta.

`DETALLE_CONTADORES_POR_GRUPO_SQL` acota a `Anexo` activos (`ID_EstadoAnexo = 1`,
mismo filtro que `PROCESOS_POR_GRUPO_ECONOMICO_SQL` usa para el combo de
Proceso) y, dentro de esos, a su `Nro_Proceso` más reciente (subquery por
`PeriodoHasta DESC`) — probado sin acotar contra un cliente real (Autopistas
del Sol, grupo 543): sin el recorte de proceso más reciente trae 7604 filas
de 148 procesos desde 2019 (todo el historial), no el parque actual.
"Elegí un cliente y traé todos los anexos" (pedido del usuario) es el
snapshot vigente de cada anexo activo, uno por anexo, no el historial."""

_SELECT_FILAS = """
    E.Den_Comercial         AS empresa,
    Suc.Descripcion         AS sucursal,
    Sec.descripcion         AS sector,
    AG.Descripcion          AS modelo,
    M.Nro_Serie             AS serie,
    FC.ID_ClaseContador     AS clase,
    FC.FechaTomaContadorAnterior AS fecha_toma_anterior,
    FC.ImpreContadorAnterior     AS contador_anterior,
    FC.FechaTomaContadorActual   AS fecha_toma_actual,
    FC.ImpreContadorActual       AS contador_actual_bruto,
    FC.ImpresionesReales    AS impresiones_reales,
    EstMaq.Descripcion      AS estado_maquina,
    M.Direccion_IP          AS direccion_ip,
    M.Mascara_IP            AS mascara_ip,
    FC.Nro_Proceso          AS nro_proceso,
    A.NombreAnexo           AS nombre_anexo,
    CONVERT(varchar(7), FA.PeriodoDesde, 120) AS periodo_facturacion,
    CASE WHEN FC.ID_ContadorActual = FC.ID_ContadorAnterior THEN 1 ELSE 0 END
        AS falta_contador,
    CASE WHEN FC.ID_ContadorActual <> FC.ID_ContadorAnterior
              AND FC.ImpresionesReales = 0
         THEN 1 ELSE 0 END AS es_automatico
"""

_FROM_FILAS = """
FROM       dbo.Factura_Contador FC     WITH (NOLOCK)
INNER JOIN dbo.Maquina          M      WITH (NOLOCK) ON M.ID_Maquina     = FC.ID_Maquina
INNER JOIN dbo.Empresa          E      WITH (NOLOCK) ON E.ID_Empresa     = FC.ID_Empresa
INNER JOIN dbo.Sucursal         Suc    WITH (NOLOCK) ON Suc.Id_Sucursal  = FC.ID_Sucursal
LEFT  JOIN dbo.Sector           Sec    WITH (NOLOCK) ON Sec.Id_Empresa   = FC.ID_Empresa
                                                     AND Sec.Id_Sucursal = FC.ID_Sucursal
                                                     AND Sec.Id_Sector   = FC.ID_Sector
INNER JOIN dbo.Articulo         Art    WITH (NOLOCK) ON Art.ID_Articulo  = M.ID_Articulo
INNER JOIN dbo.ArtGen           AG     WITH (NOLOCK) ON AG.Id_ArtGen     = Art.ID_ArtGen
LEFT  JOIN dbo.Estado_Maquina   EstMaq WITH (NOLOCK) ON EstMaq.Id        = M.ID_Estado_Maquina
INNER JOIN dbo.Factura_Anexo    FA     WITH (NOLOCK) ON FA.Nro_Proceso   = FC.Nro_Proceso
INNER JOIN dbo.Anexo            A      WITH (NOLOCK) ON A.ID_Anexo       = FA.ID_Anexo
"""

DETALLE_CONTADORES_POR_PROCESO_SQL = f"""
SELECT{_SELECT_FILAS}
{_FROM_FILAS}
WHERE FC.Nro_Proceso = ?
  AND FC.ID_ClaseContador IN (10, 20)
ORDER BY M.Nro_Serie, FC.ID_ClaseContador
"""

DETALLE_CONTADORES_POR_GRUPO_SQL = f"""
SELECT{_SELECT_FILAS}
{_FROM_FILAS}
WHERE A.ID_GrupoE = ?
  AND A.ID_EstadoAnexo = 1
  AND FC.ID_ClaseContador IN (10, 20)
  AND FA.Nro_Proceso = (
        SELECT TOP 1 FA2.Nro_Proceso
        FROM dbo.Factura_Anexo FA2 WITH (NOLOCK)
        WHERE FA2.ID_Anexo = FA.ID_Anexo
        ORDER BY FA2.PeriodoHasta DESC, FA2.Nro_Proceso DESC
      )
ORDER BY A.NombreAnexo, M.Nro_Serie, FC.ID_ClaseContador
"""
