"""Consultas read-only contra Siges/MERCURIO para el panel de candidatos
manuales del Estimador (MODELO_DE_DATOS.md §3.6) — `CANDIDATOS_EQUIPO_SQL`
portada tal cual de `Queries/GetCandidatos.sql` (el código gana si contradice
los documentos, ver brief de migración). `WITH (NOLOCK)` es intencional,
mismo criterio que el resto de `contadores` (`MIGRACION_SISTEMAS.md` §7).

Una desviación consciente respecto al .sql original: se usa
`C.Para_Facturar` (a nivel de fila) en vez de `TT.Para_Facturar` (a nivel de
Tipo_Toma, constante) — el join a `Tipo_Toma` del .sql original queda afuera.
El criterio de "T4 sin revisar" que ya usa la grilla real
(`grilla_estimacion_query.py`, paso #T4ST) es `Contadores.Para_Facturar > 0`,
no el flag fijo de `Tipo_Toma` — se necesita ese mismo criterio acá para
marcar la validez de cada lectura de forma consistente en toda la app.

`METADATA_EQUIPO_SQL` no viene de un .sql documentado (el panel original
recibía esta identidad ya resuelta desde la grilla) — son los mismos joins de
identidad que usa la grilla real (`#EquipoMeta`), pero por `ID_Maquina` suelto
y con la ubicación ACTUAL de la máquina en vez del snapshot de un proceso
puntual (no hay proceso en contexto cuando se abre el panel de candidatos
directamente)."""

CANDIDATOS_EQUIPO_SQL = """
SELECT TOP 24
    C.FechaTomaContador,
    C.ID_TipoToma,
    C.Contador,
    C.Para_Facturar
FROM  Contadores  C  WITH (NOLOCK)
WHERE  C.ID_Maquina       = ?
  AND  C.ID_ClaseContador = ?
  AND  C.Estado          <> 1
ORDER BY C.FechaTomaContador DESC, C.ID_Contador DESC
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
