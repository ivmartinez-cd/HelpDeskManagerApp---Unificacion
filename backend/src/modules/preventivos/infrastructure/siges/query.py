"""Consultas a SiGesReadOnly del módulo preventivos (solo SELECT,
parametrizadas — ARCHITECTURE_GUIDE §8). Fuentes confirmadas con dato real el
2026-08-14 (ver SIGES_READONLY_CATALOGO_DATOS.md §3 "Preventivos por zona"):

- Zona = `Sucursal.Cuadricula` (texto libre; el catálogo es el DISTINCT de
  sucursales activas, no un enum).
- Frecuencia = `Sucursal.TipoPreventivo` → `TipoPreventivo.Dias` (0 = sin
  preventivo pactado; se expone tal cual y el dominio lo trata como
  "sin_frecuencia").
- Último preventivo = MAX de `Incidente` tipo 102 (Preventivo) en estado
  terminal no anulado (500 Finalizado / 600 Cerrado / 700 Resuelto /
  710 Resuelto c/pendientes). `Fecha_Cierre` usa el sentinel 1900-01-01
  incluso en incidentes cerrados, por eso la fecha efectiva cae a
  `Fecha_Ingreso` cuando el cierre es sentinel.
- Universo (ajustado 2026-08-14 tras reporte del usuario, ronda 5/6):
  `M.Estado = 0 AND M.ID_Estado_Maquina = 1` ('Activa en Cliente' — más
  estricto que el `NOT IN (2, 8)` del parque por PST: acá se despachan
  técnicos, y una máquina en Baja Solicitada/No Localizado/Backup/Desguace no
  recibe preventivos), `E.Estado = 0` y `E.ID_Tipo_Empresa IN (101, 102)`
  (clientes reales; 201 son las empresas propias de CD —CD1/CD4—, 401/402
  técnicos y prestadores — no existe tabla Tipo_Empresa, semántica inferida
  por distribución de Den_Comercial en ronda 6).

Medido 2026-08-14 (scripts/explore_siges_preventivos_ronda3.py): 0.18-0.42 s
por zona (1400-1900 filas) — alcanza consulta en vivo, sin snapshot local.
"""

PARQUE_ZONA_SQL = """
SELECT
    M.ID_Maquina AS id_maquina,
    M.Nro_Serie AS serie,
    AG.Descripcion AS modelo,
    E.Den_Comercial AS cliente,
    S.descripcion AS sucursal,
    S.Cuadricula AS zona,
    TP.Dias AS frecuencia_dias,
    UP.fecha_ultimo_preventivo
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa
INNER JOIN dbo.Articulo A ON A.Id_Articulo = M.ID_Articulo
INNER JOIN dbo.ArtGen AG ON AG.Id_ArtGen = A.Id_ArtGen
LEFT JOIN dbo.TipoPreventivo TP ON TP.Tipo = S.TipoPreventivo
LEFT JOIN (
    SELECT I.ID_Maquina,
           MAX(CASE WHEN I.Fecha_Cierre > '1900-01-01' THEN I.Fecha_Cierre
                    ELSE I.Fecha_Ingreso END) AS fecha_ultimo_preventivo
    FROM dbo.Incidente I
    WHERE I.ID_Tipo_Incidente = 102
      AND I.ID_Estado_Incidente IN (500, 600, 700, 710)
    GROUP BY I.ID_Maquina
) UP ON UP.ID_Maquina = M.ID_Maquina
WHERE S.Estado = 0
  AND M.Estado = 0
  AND M.ID_Estado_Maquina = 1
  AND E.Estado = 0
  AND E.ID_Tipo_Empresa IN (101, 102)
  AND S.Cuadricula = ?
"""

# El catálogo trae TODAS las cuadrículas con parque activo; la exclusión de
# INTERIOR/agrupaciones de PST es regla de dominio (services/zonas.py), no SQL
# — así la lista configurable vive en un solo lugar.
ZONAS_SQL = """
SELECT
    S.Cuadricula AS zona,
    COUNT(M.ID_Maquina) AS maquinas_activas
FROM dbo.Sucursal S
INNER JOIN dbo.Maquina M
    ON M.ID_Sucursal = S.Id_Sucursal
   AND M.Estado = 0
   AND M.ID_Estado_Maquina = 1
INNER JOIN dbo.Empresa E
    ON E.ID_Empresa = M.ID_Empresa
   AND E.Estado = 0
   AND E.ID_Tipo_Empresa IN (101, 102)
WHERE S.Estado = 0
  AND LTRIM(RTRIM(S.Cuadricula)) <> ''
GROUP BY S.Cuadricula
"""
