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
- Universo (ajustado 2026-08-14 tras reporte del usuario, rondas 5-11):
  `M.Estado = 0 AND M.ID_Estado_Maquina = 1` ('Activa en Cliente' — más
  estricto que el `NOT IN (2, 8)` del parque por PST: acá se despachan
  técnicos, y una máquina en Baja Solicitada/No Localizado/Backup/Desguace no
  recibe preventivos), `E.Estado = 0` y `E.ID_Tipo_Empresa IN (101, 102)`
  (clientes reales; 201 son las empresas propias de CD —CD1/CD4—, 401/402
  técnicos y prestadores — no existe tabla Tipo_Empresa, semántica inferida
  por distribución de Den_Comercial en ronda 6).
- Cliente VIVO por actividad: alguna toma de contador O algún incidente de la
  empresa en los últimos N meses (`preventivos_meses_actividad`, default 3).
  Es la única señal que distingue la baja de facto (Garbarino: anexo
  "Activo", Empresa activa, máquinas 'Activa en Cliente'... y sin actividad
  desde 2022/2024) de los vivos: ni Empresa.Estado (rondas 5/7), ni el estado
  del anexo (el de Garbarino figura Activo), ni su FechaFinalizacion (54% del
  universo vivo tiene anexo vencido en tácita reconducción — ronda 9), ni
  FechaRestriccionServicio (la tienen todas) discriminan. Nivel EMPRESA a
  propósito: una máquina puntual puede pasar meses sin actividad estando
  viva, y los corporativos que facturan por otro canal (SC JOHNSON, TERNIUM)
  no tienen tomas pero sí incidentes. Datos bimodales (facturación mensual o
  nada): con N=3 caen 39 empresas / 792 máquinas, todas con años de
  inactividad.

Medido 2026-08-14 (rondas 3 y 11): 0.7-2.0 s por zona con el filtro de
actividad — alcanza consulta en vivo, sin snapshot local.

`Sucursal.Latitud`/`Longitud` (agregadas 2026-08-22 para el mapa de clientes)
son texto libre, no siempre numérico: el parseo y la validación de rango
quedan para `row_mapping`/`domain/services/coordenadas.py`, acá se traen tal
cual. Cobertura medida sobre el universo real: 96.4% de las sucursales caen
dentro del bbox de Argentina.
"""

# Los dos parámetros de PARQUE_ZONA_SQL: (meses_actividad, meses_actividad,
# zona) — pyodbc no soporta parámetros con nombre.
_ACTIVIDAD_EMPRESA_JOIN = """
LEFT JOIN (
    SELECT M2.ID_Empresa, MAX(CT.FechaTomaContador) AS ultima_toma
    FROM dbo.Contadores CT
    INNER JOIN dbo.Maquina M2 ON M2.ID_Maquina = CT.ID_Maquina
    WHERE CT.Estado = 0
    GROUP BY M2.ID_Empresa
) TOMA ON TOMA.ID_Empresa = E.ID_Empresa
LEFT JOIN (
    SELECT I2.ID_Empresa, MAX(I2.Fecha_Ingreso) AS ultimo_incidente
    FROM dbo.Incidente I2
    GROUP BY I2.ID_Empresa
) INC ON INC.ID_Empresa = E.ID_Empresa
"""

_EMPRESA_VIVA_WHERE = """
  AND (TOMA.ultima_toma >= DATEADD(month, -?, GETDATE())
       OR INC.ultimo_incidente >= DATEADD(month, -?, GETDATE()))
"""

# Solo impresoras (regla del usuario, 2026-08-14): el parque de Siges mezcla
# los otros negocios de CD — pantallas LFD, notebooks, 'Reproductor Carteleria
# Digital', docks, headsets, celulares, etc. Preventivos aplica únicamente a
# PRT (impresora) y MFP (multifunción); quedan afuera también PRL/PLT/SCN/
# PrintBox por decisión explícita ("SOLO PRT O MFP").
_SOLO_IMPRESORAS_WHERE = """
  AND (AG.Descripcion LIKE 'PRT %' OR AG.Descripcion LIKE 'MFP %')
"""

PARQUE_ZONA_SQL = f"""
SELECT
    M.ID_Maquina AS id_maquina,
    S.Id_Sucursal AS id_sucursal,
    M.Nro_Serie AS serie,
    AG.Descripcion AS modelo,
    E.Den_Comercial AS cliente,
    S.descripcion AS sucursal,
    S.Cuadricula AS zona,
    TP.Dias AS frecuencia_dias,
    UP.fecha_ultimo_preventivo,
    S.Latitud AS latitud,
    S.Longitud AS longitud
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
{_ACTIVIDAD_EMPRESA_JOIN}
WHERE S.Estado = 0
  AND M.Estado = 0
  AND M.ID_Estado_Maquina = 1
  AND E.Estado = 0
  AND E.ID_Tipo_Empresa IN (101, 102)
{_EMPRESA_VIVA_WHERE}
{_SOLO_IMPRESORAS_WHERE}
  AND S.Cuadricula = ?
"""

# El catálogo trae TODAS las cuadrículas con parque activo; la exclusión de
# INTERIOR/agrupaciones de PST es regla de dominio (services/zonas.py), no SQL
# — así la lista configurable vive en un solo lugar. Parámetros:
# (meses_actividad, meses_actividad) — mismo criterio de cliente vivo que el
# parque, para que el conteo del chip coincida con la tabla.
ZONAS_SQL = f"""
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
INNER JOIN dbo.Articulo A ON A.Id_Articulo = M.ID_Articulo
INNER JOIN dbo.ArtGen AG ON AG.Id_ArtGen = A.Id_ArtGen
{_ACTIVIDAD_EMPRESA_JOIN}
WHERE S.Estado = 0
  AND LTRIM(RTRIM(S.Cuadricula)) <> ''
{_EMPRESA_VIVA_WHERE}
{_SOLO_IMPRESORAS_WHERE}
GROUP BY S.Cuadricula
"""
