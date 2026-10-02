"""Consultas read-only contra Siges/ORION para el panel de candidatos
manuales del Estimador (MODELO_DE_DATOS.md §3.6) — `CANDIDATOS_EQUIPO_SQL`
portada tal cual de `Queries/GetCandidatos.sql` del legacy: INNER JOIN a
`Tipo_Toma` (descripción y `Para_Facturar` del TIPO de toma, no de la fila de
`Contadores`) y snapshot de empresa/sucursal/anexo de cada lectura para
marcar los cambios de ubicación entre lecturas vecinas (se calculan en
`PyodbcCandidatosEquipoGateway`, como `SiGesRepository.GetCandidatosAsync`).
Los alias de columna solo existen para leer por nombre desde pyodbc; el
orden y el contenido son los del .sql original. `WITH (NOLOCK)` es
intencional, mismo criterio que el resto de `contadores`
(`MIGRACION_SISTEMAS.md` §7).

`METADATA_EQUIPO_SQL` no viene de un .sql documentado (el panel original
recibía esta identidad ya resuelta desde la grilla) — son los mismos joins de
identidad que usa la grilla real (`#EquipoMeta`), pero por `ID_Maquina` suelto
y con la ubicación ACTUAL de la máquina en vez del snapshot de un proceso
puntual (no hay proceso en contexto cuando se abre el panel de candidatos
directamente)."""

CANDIDATOS_EQUIPO_SQL = """
SELECT TOP 24
    C.ID_Contador,
    C.ID_Maquina,
    C.ID_ClaseContador,
    C.FechaTomaContador,
    C.Contador,
    C.ID_TipoToma,
    TT.Descripcion     AS DescTipoToma,
    TT.Para_Facturar   AS Para_Facturar,
    C.ID_Empresa,
    C.ID_Sucursal,
    C.ID_Anexo
FROM  Contadores  C  WITH (NOLOCK)
INNER JOIN Tipo_Toma TT WITH (NOLOCK)
    ON  TT.id          = C.ID_TipoToma
WHERE C.ID_Maquina       = ?
  AND C.ID_ClaseContador = ?
  AND C.Estado          <> 1
ORDER BY C.FechaTomaContador DESC,
         C.ID_Contador        DESC
"""

# `CANDIDATOS_EQUIPO_SQL` para varios equipos a la vez (relectura de las P/L
# manuales del tablero): mismas columnas y mismo TOP 24 por equipo/clase.
# `{maquinas}` son placeholders `?`; la clase se filtra en el gateway.
CANDIDATOS_EQUIPOS_LOTE_SQL = """
SELECT ID_Contador, ID_Maquina, ID_ClaseContador, FechaTomaContador, Contador,
       ID_TipoToma, DescTipoToma, Para_Facturar, ID_Empresa, ID_Sucursal, ID_Anexo
FROM (
    SELECT
        C.ID_Contador,
        C.ID_Maquina,
        C.ID_ClaseContador,
        C.FechaTomaContador,
        C.Contador,
        C.ID_TipoToma,
        TT.Descripcion     AS DescTipoToma,
        TT.Para_Facturar   AS Para_Facturar,
        C.ID_Empresa,
        C.ID_Sucursal,
        C.ID_Anexo,
        ROW_NUMBER() OVER (
            PARTITION BY C.ID_Maquina, C.ID_ClaseContador
            ORDER BY C.FechaTomaContador DESC, C.ID_Contador DESC
        ) AS Orden
    FROM  Contadores  C  WITH (NOLOCK)
    INNER JOIN Tipo_Toma TT WITH (NOLOCK)
        ON  TT.id          = C.ID_TipoToma
    WHERE C.ID_Maquina IN ({maquinas})
      AND C.Estado      <> 1
) L
WHERE L.Orden <= 24
ORDER BY ID_Maquina, ID_ClaseContador, Orden
"""

METADATA_EQUIPO_SQL = """
SELECT
    M.Nro_Serie,
    E.Den_Comercial   AS EmpresaDesc,
    Suc.Descripcion   AS SucursalDesc,
    Sec.descripcion   AS SectorDesc,
    AG.Descripcion    AS ModeloDesc,
    AG.Id_Tecnologia  AS IdTecnologia,
    AG.Velocidad      AS Velocidad
FROM       Maquina   M   WITH (NOLOCK)
INNER JOIN Articulo  Art WITH (NOLOCK) ON Art.ID_Articulo  = M.ID_Articulo
INNER JOIN ArtGen    AG  WITH (NOLOCK) ON AG.Id_ArtGen     = Art.ID_ArtGen
INNER JOIN Empresa   E   WITH (NOLOCK) ON E.ID_Empresa     = M.ID_Empresa
INNER JOIN Sucursal  Suc WITH (NOLOCK) ON Suc.Id_Sucursal  = M.ID_Sucursal
                                       AND Suc.ID_Empresa   = M.ID_Empresa
LEFT  JOIN Sector    Sec WITH (NOLOCK) ON Sec.Id_Empresa   = M.ID_Empresa
                                       AND Sec.Id_Sucursal  = M.ID_Sucursal
                                       AND Sec.Id_Sector    = M.ID_Sector
                                       AND Sec.Estado      <> 1
WHERE M.ID_Maquina = ?
"""
