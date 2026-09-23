"""Consultas a SiGesReadOnly del módulo preventivos (solo SELECT,
parametrizadas — ARCHITECTURE_GUIDE §8). Fuentes confirmadas con dato real el
2026-08-14 (ver SIGES_READONLY_CATALOGO_DATOS.md §3 "Preventivos por zona"):

- Zona = `Sucursal.Cuadricula` (texto libre; el catálogo es el DISTINCT de
  sucursales activas, no un enum).
- Frecuencia = `Sucursal.TipoPreventivo` → `TipoPreventivo.Dias`. **Sin
  frecuencia queda afuera del universo (regla del usuario, 2026-09-02)**: una
  sucursal con `Dias = 0` o sin fila en `TipoPreventivo` no tiene preventivo
  pactado, así que sus máquinas no aparecen ni en la tabla, ni en el conteo
  del chip de zona, ni en el mapa (las tres consultas comparten
  `_CON_FRECUENCIA_WHERE`). El estado `sin_frecuencia` del dominio sigue
  existiendo como red de seguridad, pero con este filtro no debería llegar
  ninguna fila que lo produzca.
- Último preventivo = MAX de `Incidente` tipo 102 (Preventivo) en estado
  terminal no anulado (500 Finalizado / 600 Cerrado / 700 Resuelto /
  710 Resuelto c/pendientes). `Fecha_Cierre` usa el sentinel 1900-01-01
  incluso en incidentes cerrados, por eso la fecha efectiva cae a
  `Fecha_Ingreso` cuando el cierre es sentinel.
- **Scoping por sucursal (bug real corregido 2026-08-26)**: tanto el
  preventivo como la instalación exigen que `Incidente.ID_Sucursal` (la
  sucursal donde ocurrió el incidente, histórica) coincida con la
  `Maquina.ID_Sucursal` ACTUAL. Un `ID_Maquina` persiste en Siges aunque el
  equipo se reasigne entre clientes distintos con el tiempo; sin este
  scoping, el historial de preventivos del cliente ANTERIOR se le atribuye
  al actual. Caso confirmado: Fiter - Congreso/Z8PMB3BC600409X mostraba
  "vencido hace 779 días" por un Preventivo de 2024 hecho en OPDEA — otro
  cliente — antes de que el equipo llegara a Fiter en agosto 2024; auditado
  contra el universo real: 2160/16205 máquinas activas (13%) tenían este
  mismo problema.
- Fecha de instalación = MAX de `Incidente` tipo 103 (Instalación-
  Desinstalación) en estado terminal no anulado, pero por `Fecha_Ingreso`
  (no `Fecha_Cierre` como el preventivo — ver el comentario de `INC` más
  abajo).
  Ancla de `fecha_tentativa` cuando el equipo nunca tuvo un preventivo real
  en su sucursal actual (caso confirmado 2026-08-26, Cepas Argentinas/
  MXBC179G54: sus dos incidentes tipo 102 están en estado 900 Anulado — por
  eso no cuentan como "último preventivo" — pero sí hay una Instalación con
  Fecha_Ingreso 2026-04-20; el listado legacy usa esa fecha + la frecuencia
  como "preventivo sugerido" en vez de dejarlo en blanco). Si tampoco hay
  una Instalación real en la sucursal actual (ej. reasignación sin ese
  incidente registrado, caso Fiter), `fecha_tentativa` queda en None — no se
  aproxima con otro tipo de incidente (correctivo, taller) para no inventar
  una fecha sin fundamento real.
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

Medido 2026-09-23 contra el backend real, sobre las 8 zonas que se consultan:
0.1-0.7 s (la más grande, OESTE, 942 equipos, 0.6 s). Alcanza de sobra para
consulta en vivo, sin snapshot local. Antes de las optimizaciones de esa
fecha eran 9-34 s y las zonas más grandes se pasaban del timeout de ORION.

`Sucursal.Latitud`/`Longitud` (agregadas 2026-08-22 para el mapa de clientes)
son texto libre, no siempre numérico: el parseo y la validación de rango
quedan para `row_mapping`/`domain/services/coordenadas.py`, acá se traen tal
cual. Cobertura medida sobre el universo real: 96.4% de las sucursales caen
dentro del bbox de Argentina.
"""

# Parámetros de PARQUE_ZONA_SQL, en orden de aparición: (zona,
# meses_actividad, meses_actividad, zona) — pyodbc no soporta parámetros con
# nombre, y la zona aparece dos veces: una acota el barrido de `Incidente` (ver
# el JOIN a `SZ` más abajo) y la otra filtra el universo de máquinas.
# La toma `ID_TipoToma = 13` ('Contador Final') no cuenta como actividad: es
# la lectura de cierre al retirar el equipo, o sea señal de baja, no de
# cliente vivo (caso reportado 2026-09-22, Telecom Argentina: sin tomas reales
# desde 2020 ni incidentes desde 2025-02, 95 máquinas todavía 'Activa en
# Cliente', y seguía apareciendo solo por 9 tomas 'Contador Final' de 2026).
# Estimado (14) / Promedio Instalación (19) sí cuentan: indican que el anexo
# se sigue facturando.
# Chequeo por EXISTS, no por LEFT JOIN a un MAX agrupado (cambiado 2026-09-23
# por timeouts reales): preguntar "¿hay alguna toma/incidente posterior al
# corte?" deja que SQL Server corte en la primera fila que lo cumple y use el
# índice por empresa, mientras que agrupar `Contadores`/`Incidente` enteras
# para quedarse con el MAX por empresa obliga a barrer ambas tablas completas
# antes de filtrar nada. Es la misma condición: MAX(fecha) >= corte equivale a
# EXISTS(fecha >= corte). Medido contra el backend real el 2026-09-23 —
# catálogo de zonas 5.4 s → 0.4 s (mismas 14 zonas, mismos conteos), y el
# parque de CABA-N 35 s → 18 s (los 18 s restantes eran el barrido de
# `Incidente`, ver el JOIN a `SZ` más abajo).
_EMPRESA_VIVA_WHERE = """
  AND (EXISTS (
        SELECT 1
        FROM dbo.Contadores CT
        INNER JOIN dbo.Maquina M2 ON M2.ID_Maquina = CT.ID_Maquina
        WHERE M2.ID_Empresa = E.ID_Empresa
          AND CT.Estado = 0
          AND CT.ID_TipoToma <> 13
          AND CT.FechaTomaContador >= DATEADD(month, -?, GETDATE())
       )
       OR EXISTS (
        SELECT 1
        FROM dbo.Incidente I2
        WHERE I2.ID_Empresa = E.ID_Empresa
          AND I2.Fecha_Ingreso >= DATEADD(month, -?, GETDATE())
       ))
"""

# Solo impresoras (regla del usuario, 2026-08-14): el parque de Siges mezcla
# los otros negocios de CD — pantallas LFD, notebooks, 'Reproductor Carteleria
# Digital', docks, headsets, celulares, etc. Preventivos aplica únicamente a
# PRT (impresora) y MFP (multifunción); quedan afuera también PRL/PLT/SCN/
# PrintBox por decisión explícita ("SOLO PRT O MFP").
_SOLO_IMPRESORAS_WHERE = """
  AND (AG.Descripcion LIKE 'PRT %' OR AG.Descripcion LIKE 'MFP %')
"""

# Solo sucursales con frecuencia pactada (regla del usuario, 2026-09-02): sin
# `TipoPreventivo.Dias` > 0 no hay vencimiento que calcular ni visita que
# despachar, y el usuario no quiere ver esos clientes en la pantalla. Requiere
# el LEFT JOIN a TipoPreventivo como `TP` en cada consulta que lo use.
_TIPO_PREVENTIVO_JOIN = """
LEFT JOIN dbo.TipoPreventivo TP ON TP.Tipo = S.TipoPreventivo
"""
_CON_FRECUENCIA_WHERE = """
  AND ISNULL(TP.Dias, 0) > 0
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
    INC.fecha_ultimo_preventivo,
    INC.fecha_instalacion,
    S.Domicilio AS domicilio,
    S.Latitud AS latitud,
    S.Longitud AS longitud
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa
INNER JOIN dbo.Articulo A ON A.Id_Articulo = M.ID_Articulo
INNER JOIN dbo.ArtGen AG ON AG.Id_ArtGen = A.Id_ArtGen
{_TIPO_PREVENTIVO_JOIN}
LEFT JOIN (
    -- Una sola pasada por `Incidente` para las dos fechas (unificado
    -- 2026-09-23 por timeouts reales: dos subconsultas agrupadas eran dos
    -- barridos de la misma tabla; medido, 18 s → 14 s en CABA-N).
    --
    -- Agrupa también por ID_Sucursal (el de `Incidente`, histórico —no el
    -- actual de `Maquina`— así el JOIN de abajo exige que coincida con la
    -- sucursal de HOY): un equipo reasignado entre clientes arrastra su
    -- ID_Maquina en Siges, y sin este filtro el preventivo hecho en el
    -- cliente anterior se le atribuye al actual (caso confirmado 2026-08-26,
    -- Fiter - Congreso/Z8PMB3BC600409X: su único Preventivo real es de 2024,
    -- hecho en OPDEA — otro cliente — antes de que el equipo llegara a Fiter
    -- en agosto 2024; afecta 2160/16205 máquinas activas, ~13% del parque).
    --
    -- Preventivo (tipo 102) por fecha de cierre: es un servicio donde importa
    -- cuándo se completó. Instalación (tipo 103) por Fecha_Ingreso: es un
    -- evento puntual donde importa cuándo el equipo entró en servicio — el
    -- cierre es un trámite administrativo posterior, a veces al día
    -- siguiente, que corría `fecha_tentativa` un día de más contra el valor
    -- real (caso confirmado 2026-08-26: incidente 830662, Fecha_Ingreso 20/04
    -- vs Fecha_Cierre 21/04 — el listado legacy usa 20/04).
    --
    -- El INNER JOIN a `Sucursal` acota el barrido a las sucursales de la zona
    -- consultada (agregado 2026-09-23): sin él esta subconsulta agrupaba
    -- `Incidente` entera —todas las zonas del país— para después tirar el
    -- 95% en el JOIN de abajo. No cambia el resultado: el JOIN ya exige
    -- `INC.ID_Sucursal = M.ID_Sucursal`, y `M.ID_Sucursal` siempre es una
    -- sucursal de la zona (lo impone el filtro por `S.Cuadricula` del
    -- WHERE). Medido
    -- contra el backend real: CABA-N 16.4 s → 0.5 s, OESTE 13.9 s → 0.9 s,
    -- con filas idénticas.
    SELECT I.ID_Maquina, I.ID_Sucursal,
           MAX(CASE WHEN I.ID_Tipo_Incidente = 102
                    THEN (CASE WHEN I.Fecha_Cierre > '1900-01-01'
                               THEN I.Fecha_Cierre ELSE I.Fecha_Ingreso END)
               END) AS fecha_ultimo_preventivo,
           MAX(CASE WHEN I.ID_Tipo_Incidente = 103
                    THEN I.Fecha_Ingreso END) AS fecha_instalacion
    FROM dbo.Incidente I
    INNER JOIN dbo.Sucursal SZ
        ON SZ.Id_Sucursal = I.ID_Sucursal
       AND SZ.Cuadricula = ?
    WHERE I.ID_Tipo_Incidente IN (102, 103)
      AND I.ID_Estado_Incidente IN (500, 600, 700, 710)
    GROUP BY I.ID_Maquina, I.ID_Sucursal
) INC ON INC.ID_Maquina = M.ID_Maquina AND INC.ID_Sucursal = M.ID_Sucursal
WHERE S.Estado = 0
  AND M.Estado = 0
  AND M.ID_Estado_Maquina = 1
  AND E.Estado = 0
  AND E.ID_Tipo_Empresa IN (101, 102)
{_EMPRESA_VIVA_WHERE}
{_SOLO_IMPRESORAS_WHERE}
{_CON_FRECUENCIA_WHERE}
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
{_TIPO_PREVENTIVO_JOIN}
WHERE S.Estado = 0
  AND LTRIM(RTRIM(S.Cuadricula)) <> ''
{_EMPRESA_VIVA_WHERE}
{_SOLO_IMPRESORAS_WHERE}
{_CON_FRECUENCIA_WHERE}
GROUP BY S.Cuadricula
"""

# Universo completo (todas las zonas, sin parámetro de zona): la
# geocodificación es mantenimiento periódico, no una pantalla por zona.
# Trae Domicilio/Ciudad/Provincia para armar la dirección a geocodificar
# (domain/services/geocoding.py) de las sucursales cuya Latitud/Longitud no
# pasa domain/services/coordenadas.py — filtrado en Python, no acá: parsear
# "-58,75" vs "-58.75" en T-SQL es más frágil que en el mapeo de filas.
# Parámetros: (meses_actividad, meses_actividad) — mismo criterio de cliente
# vivo que el resto de las consultas del módulo.
SUCURSALES_GEOCODING_SQL = f"""
SELECT DISTINCT
    S.Id_Sucursal AS id_sucursal,
    E.Den_Comercial AS cliente,
    S.descripcion AS sucursal,
    S.Domicilio AS domicilio,
    C.DesCiudad AS ciudad,
    C.DesProvincia AS provincia,
    S.Latitud AS latitud,
    S.Longitud AS longitud
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa
INNER JOIN dbo.Articulo A ON A.Id_Articulo = M.ID_Articulo
INNER JOIN dbo.ArtGen AG ON AG.Id_ArtGen = A.Id_ArtGen
LEFT JOIN dbo.Ciudad C ON C.Id_Ciudad = S.Id_Ciudad
{_TIPO_PREVENTIVO_JOIN}
WHERE S.Estado = 0
  AND M.Estado = 0
  AND M.ID_Estado_Maquina = 1
  AND E.Estado = 0
  AND E.ID_Tipo_Empresa IN (101, 102)
{_EMPRESA_VIVA_WHERE}
{_SOLO_IMPRESORAS_WHERE}
{_CON_FRECUENCIA_WHERE}
"""
