"""SQL real completo de la grilla de estimación contra Siges/MERCURIO —
copiado tal cual de `Queries/GetGrillaEstimacion.sql` del proyecto original
(el código gana si contradice los documentos, ver brief de migración): NO se
reescribió la lógica a mano, se ejecuta el mismo script ya validado en
producción. Único cambio estructural: se antepone `DECLARE
@NroProceso/@FechaObjetivo` porque pyodbc no soporta parámetros con nombre en
un batch de texto arbitrario como sí lo hace ADO.NET — se declaran acá y se
asignan desde los placeholders posicionales `?` (2 parámetros: nro_proceso,
fecha_objetivo).

Única desviación de negocio deliberada (no estructural): REGLAS_DE_NEGOCIO
§14 dejaba sin resolver el desempate cuando un T8/T13 y un T4 caen en la
misma fecha como candidatos de Partida/Llegada — el `TOP 1 ... ORDER BY
FechaTomaContador DESC` original no tenía segundo criterio, así que el
empate era no determinístico. Decisión del usuario 2026-09-05: T8/T13 gana
sobre T4 (ver comentarios "DESEMPATE" en #UltimoReal/#RealAnterior más
abajo). El resto de la query sigue siendo copia literal del .sql original.

Pipeline con tablas temporales (11 pasos) porque los índices recomendados en
MIGRACION_SISTEMAS.md §3 no existen en producción — ver ese documento antes
de tocar esta query. `WITH (NOLOCK)` en todas las lecturas a Siges: nota de
seguridad de MIGRACION_SISTEMAS.md §7, la app lee mientras el ERP sigue en
operación.

Columnas del SELECT final (orden posicional, 0-73) documentadas en el
.sql original — ver ese archivo o `pyodbc_grilla_estimacion_gateway.py`
para el mapeo a `EquipoProceso`/`ClaseProceso`."""

GRILLA_ESTIMACION_SQL = """
DECLARE @NroProceso int = ?;
DECLARE @FechaObjetivo date = ?;

-- MIGRABLE_TO_SP: dbo.sp_GetGrillaEstimacion
-- ============================================================================
-- Devuelve una fila por (ID_Maquina, ID_ClaseContador) para el proceso
-- indicado. Trae todo lo que la grilla del tablero necesita para mostrar +
-- todo lo que CalculadorContadores necesita para proponer el estimado.
--
-- Parámetros
--   @NroProceso     int     -- Factura_Anexo.Nro_Proceso
--   @FechaObjetivo  date    -- por defecto FA.PeriodoHasta; editable por operador
--
-- Columnas devueltas (orden = orden del SqlDataReader, ver SiGesRepository):
--    0  ID_Maquina               int
--    1  ID_ClaseContador         int           10 = Mono, 20 = Color
--    2  NroSerie                 nvarchar
--    3  ID_Empresa               int           SNAPSHOT (FC.ID_Empresa) — empresa al momento del cierre
--    4  EmpresaDesc              nvarchar      SNAPSHOT — Empresa.Den_Comercial del snapshot
--    5  ID_Sucursal              int           SNAPSHOT
--    6  SucursalDesc             nvarchar      SNAPSHOT
--    7  Id_Sector                int           SNAPSHOT — NULL si la máquina no tenía sector al cierre
--    8  SectorDesc               nvarchar      SNAPSHOT — NULL ídem
--    9  ID_GrupoEconomico        int
--   10  ID_ArtGen                int
--   11  ModeloDesc               nvarchar      ArtGen.Descripcion
--   12  IdTecnologia             int           1 = Mono, 2 = Color
--   13  Velocidad                int           NULL = no cargada → fallback x3 prom modelo
--   14  PendienteEstimar         bit           1 = falta lectura real (regla del Estado del Proyecto)
--   15  ContadorAnterior_Valor   decimal(18,2) Últ. facturado (read-only en grilla)
--   16  ContadorAnterior_Fecha   date          NULL si no se conoce
--   17  ContadorAnterior_TipoToma int          NULL ídem
--   18  UltimoReal_Valor         decimal(18,2) NULL si no hay real en los últimos N meses
--   19  UltimoReal_Fecha         date
--   20  UltimoReal_TipoToma      int
--   21  RealAnterior_Valor       decimal(18,2) NULL si no hay segundo real. Separación preferida ≥45d (@MinPreferred), fallback ≥15d (@MinAbsoluto)
--   22  RealAnterior_Fecha       date
--   23  RealAnterior_TipoToma    int
--   24  T4ST_Valor               decimal(18,2) NULL si no hay T4 (ST) reciente. Caso especial Llegada T4.
--   25  T4ST_Fecha               date
--   26  T4ST_ParaFacturar        bit           1 si Contadores.Para_Facturar > 0 del T4 (operador lo revisó). 0 = sin revisar
--   27  Prom6FC                  decimal(18,2) Promedio impresiones últimos 6 procesos cerrados (FC)
--   28  PromParque_Cliente_Tec   decimal(18,2) Fallback antigüedad: parque del cliente, misma tecnología, 6m.
--                                              REGIMEN ESCALONADO (Paquete 10.A): N≥5 → mediana truncada P80,
--                                              N=2..4 → mediana cruda, N≤1 → NULL (cae al siguiente nivel).
--   29  CntParque_Cliente_Tec    int           Cantidad de equipos en el parque (antes del truncado P80)
--   30  PromParque_Cliente_Modelo decimal(18,2) Cascada T19 nivel 1 — mismo régimen escalonado
--   31  PromParque_Grupo_Modelo   decimal(18,2) Cascada T19 nivel 2 — mismo régimen escalonado
--   32  PromParque_Global_Modelo  decimal(18,2) Cascada T19 nivel 3 — mismo régimen escalonado
--   33  PromGlobalModelo_Imp     decimal(18,2) Para el fallback "salto > 3× prom modelo" cuando Velocidad es NULL.
--                                              Usa la mediana truncada del nivel global (= col 32).
--   34  Q1_ParqueClienteTec      decimal(18,2) Para IQR (mono ≥ 5 equipos)
--   35  Q3_ParqueClienteTec      decimal(18,2) Para IQR
--   36  PeriodoHasta             date          Cierre del proceso
--   37  PeriodoDesde             date          Apertura del proceso
--   38  ID_EstadoMaquina         int           Maquina.ID_Estado_Maquina
--   39  EstadoMaquinaDesc        nvarchar      Estado_Maquina.Descripcion (NULL si sin estado)
--   40  H01                      decimal(18,2) ImpresionesReales del proceso cerrado N-1 (más reciente = UF)
--   41  H02                      decimal(18,2) N-2 (UF-1)
--   42  H03                      decimal(18,2) N-3
--   43  H04                      decimal(18,2) N-4
--   44  H05                      decimal(18,2) N-5
--   45  H06                      decimal(18,2) N-6
--   46  H07                      decimal(18,2) N-7
--   47  H08                      decimal(18,2) N-8
--   48  H09                      decimal(18,2) N-9
--   49  H10                      decimal(18,2) N-10
--   50  H11                      decimal(18,2) N-11 (más antiguo). 0 si el proceso no existe.
--   51  FC_ImpreContadorActual   decimal(18,2) Impresiones del contador actual en el proceso (NULL si PendienteEstimar)
--   52  FC_Fecha_ContActual      date          Fecha de toma del contador actual (NULL si PendienteEstimar)
--   53  FC_TipoToma_ContActual   int           Tipo de toma del contador actual  (NULL si PendienteEstimar)
--   54  FC_ImpresionesReales     decimal(18,2) Factura_Contador.ImpresionesReales del proceso actual (NULL si PendienteEstimar)
--   55  EmpresaActualDesc        nvarchar      NULL salvo cuando la máquina cambió de empresa desde el
--                                              cierre del proceso. En ese caso trae Empresa.Den_Comercial
--                                              de la empresa ACTUAL (Maquina.ID_Empresa). El front lo
--                                              renderiza como badge rojo "Ubic Actual: XXX" debajo del
--                                              estado en la celda Modelo. Cambio solo a nivel de empresa
--                                              (movimientos sucursal/sector dentro de la misma empresa
--                                              no disparan la alerta).
--   56  ID_ModoOper              int           Maquina.ID_ModoOper. Define qué clases de contador maneja la
--                                              máquina y la SEMÁNTICA de cada una:
--                                                  1 = Solo Mono             → Cl.10
--                                                  2 = Suma Mono y Color     → Cl.20 (TOTAL = mono + color)
--                                                  3 = Discrimina M y C      → Cl.10 (mono) + Cl.20 (solo color)
--                                                  4 = Suma M y C con Dig.   → Cl.20
--                                                  5 = Discrim. M y C + Dig. → Cl.10 + Cl.20 + Cl.30
--                                                  6 = Mono con Dig.         → Cl.10 + Cl.30
--                                                  7 = Solo Digitalización   → Cl.30
--                                              Crítico: el promedio T19 de Cl.20 NO es comparable entre
--                                              ModoOper=2 (total) y ModoOper=3 (solo color); las CTE de
--                                              parque particionan por este campo.
--   57  EsClaseSintetica         bit           1 = la fila NO existe en Factura_Contador para este proceso.
--                                              Fue sintetizada porque MaquinaModoOper_ClaseContador declara
--                                              esa clase como obligatoria para el ModoOper de la máquina.
--                                              Caso típico: máquina ModoOper=3 con solo Cl.20 cargada en FC →
--                                              la grilla muestra también Cl.10 sintética para que el operador
--                                              vea el estimado y sepa que tiene que cargar la lectura faltante
--                                              en el ERP antes de facturar. ContadorAnterior heredado del
--                                              último proceso cerrado donde sí existía esa (Maq, Clase).
--                                              Snapshot de ubicación heredado de la fila FC existente del
--                                              mismo equipo en este proceso.
--
-- ── Métricas de auditoría del estimador robusto (Paquete 10.A) ───────────────
-- Cada nivel de parque expone N, descartados, mediana cruda y media cruda para
-- mostrar la composición en el tooltip de la grilla y persistir en Estim_Log.
--   58  PCT_CntDescartados       int           ParqueClienteTec — equipos descartados por > P80
--   59  PCT_MedianaCruda         decimal(18,2) ParqueClienteTec — mediana sin truncar (referencia)
--   60  PCT_MediaCruda           decimal(18,2) ParqueClienteTec — media sin truncar (referencia)
--   61  PCM_CntDescartados       int           ParqueClienteModelo — equipos descartados por > P80
--   62  PCM_Cant                 int           ParqueClienteModelo — N total del parque
--   63  PCM_MedianaCruda         decimal(18,2) ParqueClienteModelo — mediana sin truncar
--   64  PCM_MediaCruda           decimal(18,2) ParqueClienteModelo — media sin truncar
--   65  PGM_CntDescartados       int           ParqueGrupoModelo (Grupo Económico) — equipos descartados
--   66  PGM_Cant                 int           ParqueGrupoModelo — N total
--   67  PGM_MedianaCruda         decimal(18,2) ParqueGrupoModelo — mediana sin truncar
--   68  PGM_MediaCruda           decimal(18,2) ParqueGrupoModelo — media sin truncar
--   69  PGL_CntDescartados       int           ParqueGlobalModelo — equipos descartados
--   70  PGL_Cant                 int           ParqueGlobalModelo — N total
--   71  PGL_MedianaCruda         decimal(18,2) ParqueGlobalModelo — mediana sin truncar
--   72  PGL_MediaCruda           decimal(18,2) ParqueGlobalModelo — media sin truncar
--
-- ============================================================================
-- ESTRATEGIA DE EJECUCIÓN — pipeline con tablas temporales
-- ============================================================================
-- Hasta v1 (mientras Sistemas no haya creado los índices recomendados en
-- MIGRACION_SISTEMAS §3), la query se ejecuta en pasos materializados a tempdb
-- para FORZAR un plan de ejecución óptimo sin depender de índices físicos en
-- las tablas grandes (Contadores 4.4M filas, Factura_Contador 3.1M filas).
--
-- Pasos:
--   #FCActual                 -- lo que está cargado en Factura_Contador para el proceso
--   #ClasesEsperadas          -- clases declaradas por MaquinaModoOper_ClaseContador
--   #ClasesSinteticas         -- clases esperadas pero NO cargadas en FC; ContadorAnterior
--                                heredado del último proceso cerrado, snapshot heredado
--                                de la fila FC existente del mismo equipo
--   #BaseProceso              -- UNION ALL de #FCActual + #ClasesSinteticas, con flag
--                                EsClaseSintetica para que la UI marque las sintéticas
--   #ContEquipos              -- TODOS los Contadores de esos equipos, una sola seek
--                                por máquina con índice in-memory (Maq, Clase, Fecha DESC)
--   #EquipoMeta               -- joins a Maquina/Articulo/ArtGen/Empresa/Sucursal/Sector
--   #UltimoReal /             -- derivados de #ContEquipos (todo en memoria, indexado)
--   #RealAnterior /
--   #T4ST
--   #FCRecientesEnriq         -- FC últimos 6 meses + Maquina/ArtGen/Anexo, una vez
--   #ParqueClienteTec /       -- agregados sobre #FCRecientesEnriq (filtro JOIN)
--   #ParqueClienteModelo /
--   #ParqueGrupoModelo /
--   #ParqueGlobalModelo
--   #Prom6FC                  -- últimos 6 procesos del propio equipo
--   #ContadorAnterior /       -- lookup por ID_Contador (PK clustered, fast)
--   #ContadorActual
--   #HistoricoFC11            -- top 11 procesos cerrados por (Maq, Clase) — pivot
--   SELECT FINAL              -- joins sobre temps, sin tocar tablas grandes
--
-- Cuando se creen los índices recomendados (MIGRACION_SISTEMAS §3) este
-- approach sigue funcionando, solo que los índices físicos también acelerarían
-- las consultas iniciales contra Contadores y Factura_Contador. La simplificación
-- a una sola query con CTEs es opcional en ese momento (no bloqueante).
--
-- Notas
--   * Tipos "reales": 1, 2, 3, 6, 7, 9, 10, 12, 15, 17, 20, 21, 22, 23
--     (sync con TipoToma.Reales). T20/21/22/23 = Whatsapp/SDS HP/VPN/Print Screen.
--     Tipo 4 (ST) sale en columnas separadas. Iniciales 8/13/16 no son reales.
--     T18 (WebCliente) NO entra: seleccionable a mano en el panel, no auto-sugerido.
--   * NOLOCK en todas las lecturas a tablas SiGes — coherente con el resto.
--   * Las temp tables se limpian explícitamente al final por higiene; aunque
--     SqlClient resetea la conexión al devolverla al pool (sp_reset_connection
--     drop temp tables), el DROP defensivo evita sorpresas.
--
-- Notas de migración a SP
--   CREATE PROCEDURE dbo.sp_GetGrillaEstimacion
--     @NroProceso int, @FechaObjetivo date
--   AS BEGIN
--     SET NOCOUNT ON;
--     <cuerpo>
--   END
-- ============================================================================

SET NOCOUNT ON;

-- Defensa ante reuso de conexión sin reset (caso raro): drop si quedó algún temp.
IF OBJECT_ID('tempdb..#FCActual')         IS NOT NULL DROP TABLE #FCActual;
IF OBJECT_ID('tempdb..#ClasesEsperadas')  IS NOT NULL DROP TABLE #ClasesEsperadas;
IF OBJECT_ID('tempdb..#ClasesSinteticas') IS NOT NULL DROP TABLE #ClasesSinteticas;
IF OBJECT_ID('tempdb..#BaseProceso')      IS NOT NULL DROP TABLE #BaseProceso;
IF OBJECT_ID('tempdb..#ContEquipos')      IS NOT NULL DROP TABLE #ContEquipos;
IF OBJECT_ID('tempdb..#EquipoMeta')       IS NOT NULL DROP TABLE #EquipoMeta;
IF OBJECT_ID('tempdb..#UltimoReal')       IS NOT NULL DROP TABLE #UltimoReal;
IF OBJECT_ID('tempdb..#RealAnterior')     IS NOT NULL DROP TABLE #RealAnterior;
IF OBJECT_ID('tempdb..#T4ST')             IS NOT NULL DROP TABLE #T4ST;
IF OBJECT_ID('tempdb..#FCRecientesEnriq') IS NOT NULL DROP TABLE #FCRecientesEnriq;
IF OBJECT_ID('tempdb..#ParqueClienteTec') IS NOT NULL DROP TABLE #ParqueClienteTec;
IF OBJECT_ID('tempdb..#ParqueClienteModelo') IS NOT NULL DROP TABLE #ParqueClienteModelo;
IF OBJECT_ID('tempdb..#ParqueGrupoModelo')   IS NOT NULL DROP TABLE #ParqueGrupoModelo;
IF OBJECT_ID('tempdb..#ParqueGlobalModelo')  IS NOT NULL DROP TABLE #ParqueGlobalModelo;
IF OBJECT_ID('tempdb..#Prom6FC')          IS NOT NULL DROP TABLE #Prom6FC;
IF OBJECT_ID('tempdb..#ContadorAnterior') IS NOT NULL DROP TABLE #ContadorAnterior;
IF OBJECT_ID('tempdb..#ContadorActual')   IS NOT NULL DROP TABLE #ContadorActual;
IF OBJECT_ID('tempdb..#HistoricoFC11')    IS NOT NULL DROP TABLE #HistoricoFC11;

-- ─────────────────────────────────────────────────────────────────────────────
-- Variables del proceso (una sola consulta a Factura_Anexo + Anexo)
-- ─────────────────────────────────────────────────────────────────────────────
DECLARE @PeriodoDesde     date;
DECLARE @PeriodoHasta     date;
DECLARE @ID_Anexo         int;
DECLARE @ID_GrupoE        int;

-- Ventana de separación para el segundo real (#RealAnterior, regla de tres P/L).
--   @MinPreferred: separación buscada primero (≥45d → MAPE mediano ~21,6% y, sobre
--     todo, P95 del error 132% vs 161% con 15d. Validado Paquete 10.B, jun-2026).
--   @MinAbsoluto:  fallback cuando no hay ningún real ≥45d antes del último.
--   Trade-off: introduce bias agregado ~ -5,6% (subestima), alineado con la
--   política "no facturar de más / evitar notas de crédito".
DECLARE @MinPreferred     int = 45;
DECLARE @MinAbsoluto      int = 15;

-- Antigüedad máxima de un T4 para poder usarse como Partida/Llegada o sugerencia.
--   Un T4 más viejo que esto (respecto de @PeriodoHasta) se considera información
--   obsoleta y NO se usa para estimar. Solo aplica a T4 (las guardas de empresa +
--   antigüedad protegen contra usar lecturas de cuando el equipo estaba en otra
--   empresa o de hace demasiado tiempo).
DECLARE @MaxMesesAntiguedad int = 24;

SELECT
    @PeriodoDesde = FA.PeriodoDesde,
    @PeriodoHasta = FA.PeriodoHasta,
    @ID_Anexo     = A.ID_Anexo,
    @ID_GrupoE    = A.ID_GrupoE
FROM       Factura_Anexo FA WITH (NOLOCK)
INNER JOIN Anexo         A  WITH (NOLOCK) ON A.ID_Anexo = FA.ID_Anexo
WHERE FA.Nro_Proceso = @NroProceso;

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 1 — #BaseProceso (con SÍNTESIS de clases faltantes)
--
--   Factura_Contador NO es la fuente de verdad para "qué clases tiene cada
--   máquina". La fuente de verdad es Maquina.ID_ModoOper +
--   MaquinaModoOper_ClaseContador. Si una máquina con ModoOper=3 (Cl.10 + Cl.20)
--   tiene solo Cl.20 cargada en FC, la grilla debe mostrar TAMBIÉN Cl.10
--   (sintética) para que el operador vea el estimado y sepa que tiene que
--   cargar la lectura faltante en el ERP antes de facturar.
--
--   Construcción:
--     1.A  #FCActual         — lo que ESTÁ cargado en FC para este proceso
--     1.B  #ClasesEsperadas  — lo que ModoOper dice que DEBERÍA haber
--     1.C  #ClasesSinteticas — diferencia (esperadas − actuales) con datos
--                              heredados: snapshot de la fila FC existente del
--                              mismo equipo, ContadorAnterior = ID_ContadorActual
--                              del último proceso cerrado donde sí existía
--                              esa (Maquina, Clase).
--     1.D  #BaseProceso      — UNION ALL de #FCActual + #ClasesSinteticas, con
--                              flag EsClaseSintetica para que la UI marque la fila.
-- ─────────────────────────────────────────────────────────────────────────────

-- 1.A — Lo que está cargado en FC
SELECT
    FC.Nro_Proceso,
    FC.ID_Maquina,
    FC.ID_ClaseContador,
    FC.ID_ContadorAnterior,
    FC.ID_ContadorActual,
    FC.ImpreContadorActual,
    FC.ImpresionesReales,
    FC.ID_Empresa            AS Snap_ID_Empresa,
    FC.ID_Sucursal           AS Snap_ID_Sucursal,
    FC.ID_Sector             AS Snap_ID_Sector
INTO #FCActual
FROM Factura_Contador FC WITH (NOLOCK)
WHERE FC.Nro_Proceso = @NroProceso;

CREATE NONCLUSTERED INDEX ix_fcact_maq_clase ON #FCActual (ID_Maquina, ID_ClaseContador);

-- 1.B — Clases esperadas según ModoOper de cada máquina del proceso
SELECT DISTINCT
    FCA.ID_Maquina,
    MMOC.IdClaseContador AS ID_ClaseContador
INTO #ClasesEsperadas
FROM       #FCActual FCA
INNER JOIN Maquina   M    WITH (NOLOCK) ON M.ID_Maquina       = FCA.ID_Maquina
INNER JOIN MaquinaModoOper_ClaseContador MMOC WITH (NOLOCK)
                                          ON MMOC.IdModoOper  = M.ID_ModoOper;

CREATE NONCLUSTERED INDEX ix_ce_maq_clase ON #ClasesEsperadas (ID_Maquina, ID_ClaseContador);

-- 1.C — Clases sintéticas: las esperadas que no están en FC.
--   Snapshot heredado de cualquier fila FC del mismo equipo en este proceso.
--   ContadorAnterior = ID_ContadorActual del último proceso cerrado donde
--   esa (Maq, Clase) sí existía (NULL si nunca tuvo).
SELECT
    CE.ID_Maquina,
    CE.ID_ClaseContador,
    SnapFC.Snap_ID_Empresa,
    SnapFC.Snap_ID_Sucursal,
    SnapFC.Snap_ID_Sector,
    PrevFC.ID_ContadorActual AS ID_ContadorAnterior
INTO #ClasesSinteticas
FROM       #ClasesEsperadas CE
LEFT  JOIN #FCActual         FCA ON FCA.ID_Maquina       = CE.ID_Maquina
                                AND FCA.ID_ClaseContador = CE.ID_ClaseContador
-- Snapshot heredado: TOP 1 de cualquier otra clase del mismo equipo en este proceso.
-- Las columnas en #FCActual ya están aliasadas como Snap_*, no como ID_*.
OUTER APPLY (
    SELECT TOP 1
        FC2.Snap_ID_Empresa,
        FC2.Snap_ID_Sucursal,
        FC2.Snap_ID_Sector
    FROM   #FCActual FC2
    WHERE  FC2.ID_Maquina = CE.ID_Maquina
) SnapFC
-- ContadorAnterior heredado: ID_ContadorActual del último proceso CERRADO
-- donde esa (Maq, Clase) sí estaba cargada en FC
OUTER APPLY (
    SELECT TOP 1 FC3.ID_ContadorActual
    FROM       Factura_Contador FC3 WITH (NOLOCK)
    INNER JOIN Factura_Anexo    FA3 WITH (NOLOCK) ON FA3.Nro_Proceso = FC3.Nro_Proceso
    WHERE  FC3.ID_Maquina       = CE.ID_Maquina
      AND  FC3.ID_ClaseContador = CE.ID_ClaseContador
      AND  FA3.ListoParaFacturar = 1
      AND  FA3.Nro_Proceso      < @NroProceso
    ORDER BY FA3.Nro_Proceso DESC
) PrevFC
WHERE FCA.ID_Maquina IS NULL;  -- solo las que NO están en FC actual

-- 1.D — #BaseProceso: UNION de FC reales + sintéticas
SELECT
    @NroProceso                        AS Nro_Proceso,
    ID_Maquina,
    ID_ClaseContador,
    ID_ContadorAnterior,
    ID_ContadorActual,
    ImpreContadorActual,
    ImpresionesReales,
    Snap_ID_Empresa,
    Snap_ID_Sucursal,
    Snap_ID_Sector,
    CAST(CASE WHEN ID_ContadorActual = ID_ContadorAnterior
              THEN 1 ELSE 0 END AS bit) AS PendienteEstimar,
    CAST(0 AS bit)                     AS EsClaseSintetica
INTO #BaseProceso
FROM #FCActual

UNION ALL

SELECT
    @NroProceso                        AS Nro_Proceso,
    CS.ID_Maquina,
    CS.ID_ClaseContador,
    CS.ID_ContadorAnterior,
    NULL                               AS ID_ContadorActual,
    NULL                               AS ImpreContadorActual,
    NULL                               AS ImpresionesReales,
    CS.Snap_ID_Empresa,
    CS.Snap_ID_Sucursal,
    CS.Snap_ID_Sector,
    CAST(1 AS bit)                     AS PendienteEstimar,
    CAST(1 AS bit)                     AS EsClaseSintetica
FROM #ClasesSinteticas CS;

CREATE NONCLUSTERED INDEX ix_bp_maq_clase
    ON #BaseProceso (ID_Maquina, ID_ClaseContador);

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 2 — #ContEquipos: TODAS las lecturas de Contadores de los equipos del
--   proceso, una sola seek por máquina (usa índice existente
--   Contadores.ID_Maquina+FechaTomaContador) acotado a 3 años de historia.
--   Le ponemos un índice in-memory (ID_Maquina, ID_ClaseContador, Fecha DESC)
--   para que UltimoReal/RealAnterior/T4ST sean seek + top1 instantáneos.
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    C.ID_Maquina,
    C.ID_ClaseContador,
    C.FechaTomaContador,
    C.ID_TipoToma,
    C.Estado,
    C.Contador,
    C.Para_Facturar,           -- nivel fila: 0 = sin revisar (técnico), >0 = operador validó
    C.ID_Empresa,              -- SNAPSHOT de empresa al momento de la lectura (clave para no cruzar empresas)
    C.ID_Sucursal              -- SNAPSHOT de sucursal: una mudanza física cambia la curva de impresión (guarda del par P/L)
INTO #ContEquipos
FROM Contadores C WITH (NOLOCK)
WHERE EXISTS (
        SELECT 1 FROM #BaseProceso BP WHERE BP.ID_Maquina = C.ID_Maquina
      )
  AND C.FechaTomaContador >= DATEADD(YEAR, -3, @PeriodoHasta);

CREATE NONCLUSTERED INDEX ix_ce_maq_clase_fecha
    ON #ContEquipos (ID_Maquina, ID_ClaseContador, FechaTomaContador DESC)
    INCLUDE (ID_TipoToma, Estado, Contador, Para_Facturar, ID_Empresa, ID_Sucursal);

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 3 — #EquipoMeta: una fila por máquina con sus joins de catálogo.
--   Ubicación viene del SNAPSHOT (BaseProceso). Empresa actual (M.ID_Empresa)
--   se resuelve aparte por el badge "Ubic Actual: XXX".
-- ─────────────────────────────────────────────────────────────────────────────
SELECT DISTINCT
    BP.ID_Maquina,
    M.Nro_Serie               AS NroSerie,
    BP.Snap_ID_Empresa        AS ID_Empresa,
    BP.Snap_ID_Sucursal       AS ID_Sucursal,
    BP.Snap_ID_Sector         AS Id_Sector,
    E.Den_Comercial           AS EmpresaDesc,
    Suc.Descripcion           AS SucursalDesc,
    Sec.descripcion           AS SectorDesc,
    CASE WHEN M.ID_Empresa <> BP.Snap_ID_Empresa
         THEN EAct.Den_Comercial
    END                       AS EmpresaActualDesc,
    AG.Id_ArtGen              AS ID_ArtGen,
    AG.Descripcion            AS ModeloDesc,
    AG.Id_Tecnologia          AS IdTecnologia,
    AG.Velocidad,
    @ID_GrupoE                AS ID_GrupoEconomico,
    M.ID_Estado_Maquina       AS ID_EstadoMaquina,
    EstMaq.Descripcion        AS EstadoMaquinaDesc,
    M.ID_ModoOper             AS ID_ModoOper
INTO #EquipoMeta
FROM       #BaseProceso BP
INNER JOIN Maquina       M      WITH (NOLOCK) ON M.ID_Maquina      = BP.ID_Maquina
INNER JOIN Articulo      Art    WITH (NOLOCK) ON Art.ID_Articulo   = M.ID_Articulo
INNER JOIN ArtGen        AG     WITH (NOLOCK) ON AG.Id_ArtGen      = Art.ID_ArtGen
INNER JOIN Empresa       E      WITH (NOLOCK) ON E.ID_Empresa      = BP.Snap_ID_Empresa
INNER JOIN Sucursal      Suc    WITH (NOLOCK) ON Suc.Id_Sucursal   = BP.Snap_ID_Sucursal
                                             AND Suc.ID_Empresa    = BP.Snap_ID_Empresa
LEFT  JOIN Sector        Sec    WITH (NOLOCK) ON Sec.Id_Empresa    = BP.Snap_ID_Empresa
                                             AND Sec.Id_Sucursal   = BP.Snap_ID_Sucursal
                                             AND Sec.Id_Sector     = BP.Snap_ID_Sector
                                             AND Sec.Estado       <> 1
LEFT  JOIN Empresa       EAct   WITH (NOLOCK) ON EAct.ID_Empresa   = M.ID_Empresa
LEFT  JOIN Estado_Maquina EstMaq WITH (NOLOCK) ON EstMaq.Id        = M.ID_Estado_Maquina;

CREATE NONCLUSTERED INDEX ix_em_maquina ON #EquipoMeta (ID_Maquina);

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 4 — #UltimoReal: último contador "real" por (Maq, Clase).
--   Tipos reales: 1,2,3,6,7,9,10,12,15,17,20,21,22,23. Estado <> 1 (no anulado).
--   GUARDA DE EMPRESA + SUCURSAL (todos los tipos): la lectura debe ser de la misma
--   empresa Y sucursal snapshot que el proceso. La guarda de empresa evita usar
--   lecturas de cuando el equipo estaba en otra empresa (casi siempre con reinicio
--   de contador). La guarda de SUCURSAL evita cruzar una mudanza física dentro de
--   la misma empresa: al mudarse de sucursal cambia la curva de impresión, así que
--   un contador de partida de la sucursal vieja no representa el ritmo actual. Un
--   cambio de ANEXO sin cambio de sucursal NO rompe el par (mismo puesto físico,
--   solo cambian condiciones comerciales → se asume continuidad). Si no hay par en
--   la sucursal actual → el equipo cae a la cascada T19 (guarda dura).
--   T4 (ST) puede ser Partida o Llegada del par —revisado o no— si cumple empresa,
--   sucursal y antigüedad ≤ @MaxMesesAntiguedad. Cuando un T4 entra al par, el motor
--   marca la fila con semáforo amarillo + confirmación (EstimarEntreReales). El flag
--   Para_Facturar (revisado vs no) ya NO condiciona la elegibilidad del par; solo
--   afecta la sugerencia standalone en #T4ST + EstimarConT4ST cuando no hay par.
--   T8 (Inicial) / T13 (Final) tambien son elegibles como ancla del par (misma
--   antigüedad que T4) — el contador de apertura de la sucursal nueva es el punto
--   de partida natural de la curva post-mudanza. La guarda de sucursal deja pasar
--   solo el T8/T13 de la sucursal actual (el T13 de cierre de la sucursal vieja
--   queda filtrado). T8/T13 NO disparan amarillo (es el ancla buscada, no un T4).
--   Lee de #ContEquipos (memoria, indexada).
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    BP.ID_Maquina,
    BP.ID_ClaseContador,
    BP.Snap_ID_Empresa     AS Snap_ID_Empresa,   -- empresa del proceso, para guardar el par P/L en la misma empresa
    BP.Snap_ID_Sucursal    AS Snap_ID_Sucursal,  -- sucursal del proceso, para no cruzar una mudanza física en el par P/L
    UR.Contador            AS Valor,
    UR.FechaTomaContador   AS Fecha,
    UR.ID_TipoToma         AS TipoToma,
    URNT.FechaTomaContador AS UltimoRealNoT4_Fecha   -- último real FACTURADO excluyendo T4 (referencia para validar un T4 corrector)
INTO #UltimoReal
FROM #BaseProceso BP
OUTER APPLY (
    SELECT TOP 1 C.Contador, C.FechaTomaContador, C.ID_TipoToma
    FROM   #ContEquipos C
    WHERE  C.ID_Maquina       = BP.ID_Maquina
      AND  C.ID_ClaseContador = BP.ID_ClaseContador
      AND  C.Estado          <> 1
      -- GUARDA DE EMPRESA (todo el par P/L, no solo T4): la lectura debe ser de la
      -- MISMA empresa snapshot que el proceso. Un equipo que estuvo en otra empresa
      -- casi siempre tuvo un reinicio de contador al cambiar; sus lecturas previas
      -- NO sirven para estimar el período actual. Si no hay par en la empresa
      -- actual → el equipo cae a la cascada T19. (Un reinicio dentro de la misma
      -- empresa —reemplazo de placa— queda permeable: ambas lecturas siguen acá.)
      AND  C.ID_Empresa = BP.Snap_ID_Empresa
      -- GUARDA DE SUCURSAL: no cruzar una mudanza física. Una sucursal distinta es
      -- otra curva de impresión; su contador no sirve de partida. (NULL-safe: si el
      -- snapshot de sucursal viniera NULL en alguna lectura vieja, el = la excluye.)
      AND  C.ID_Sucursal = BP.Snap_ID_Sucursal
      AND (C.ID_TipoToma IN (1,2,3,6,7,9,10,12,15,17,20,21,22,23)
           -- T4 / T8 (Inicial) / T13 (Final): pueden ser Partida o Llegada del par.
           -- T4 reciente y en curva → el motor (EstimarEntreReales) marca amarillo +
           -- confirmación. T8/T13 = ancla de apertura de la sucursal (no marca amarillo).
           -- Solo se exige antigüedad ≤ @MaxMesesAntiguedad (empresa+sucursal ya aplican).
           OR (C.ID_TipoToma IN (4,8,13)
               AND C.FechaTomaContador >= DATEADD(MONTH, -@MaxMesesAntiguedad, @PeriodoHasta)))
    -- DESEMPATE (REGLAS_DE_NEGOCIO §14, decisión 2026-09-05 — única desviación
    -- deliberada del .sql original, que dejaba esto sin resolver: TOP 1 sin
    -- segundo criterio de orden era no determinístico si dos candidatos caían
    -- en la misma fecha). Real > T8/T13 (ancla, sin revisión) > T4 (respaldo).
    ORDER BY C.FechaTomaContador DESC,
             CASE
                 WHEN C.ID_TipoToma IN (1,2,3,6,7,9,10,12,15,17,20,21,22,23) THEN 0
                 WHEN C.ID_TipoToma IN (8,13) THEN 1
                 ELSE 2
             END
) UR
-- Último real FACTURADO **excluyendo T4** (tipos reales sin el 4). Es la referencia
-- de la regla "un T4 solo sirve si su fecha es posterior al último real facturado".
-- Misma empresa snapshot. NULL si el equipo no tiene ningún real no-T4.
OUTER APPLY (
    SELECT TOP 1 C.FechaTomaContador
    FROM   #ContEquipos C
    WHERE  C.ID_Maquina       = BP.ID_Maquina
      AND  C.ID_ClaseContador = BP.ID_ClaseContador
      AND  C.Estado          <> 1
      AND  C.ID_Empresa       = BP.Snap_ID_Empresa
      AND  C.ID_TipoToma IN (1,2,3,6,7,9,10,12,15,17,20,21,22,23)   -- SOLO reales, sin T4
    ORDER BY C.FechaTomaContador DESC
) URNT;

CREATE NONCLUSTERED INDEX ix_ur ON #UltimoReal (ID_Maquina, ID_ClaseContador);

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 5 — #RealAnterior: real previo al UltimoReal (regla de tres P/L).
--   Patrón preferred + fallback (Paquete 10.B):
--     1) RA_Pref   → primer real con ≥ @MinPreferred días de separación (45d).
--                    Ventana más larga: amortigua el ruido mensual, baja el P95
--                    del error de 161% a 132%.
--     2) RA_Fall   → fallback con ≥ @MinAbsoluto días (15d) cuando no hay ninguno
--                    que cumpla la separación preferida (equipos con poca historia
--                    o cadencia corta).
--   COALESCE arrastra el registro COMPLETO del preferido; solo si es NULL usa el
--   fallback. NUNCA mezcla campos de ambos (Valor/Fecha/TipoToma del mismo real).
--   Si no existe ninguno → CalculadorContadores cae al fallback parque.
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    UR.ID_Maquina,
    UR.ID_ClaseContador,
    COALESCE(RA_Pref.Contador,          RA_Fall.Contador)          AS Valor,
    COALESCE(RA_Pref.FechaTomaContador, RA_Fall.FechaTomaContador) AS Fecha,
    COALESCE(RA_Pref.ID_TipoToma,       RA_Fall.ID_TipoToma)       AS TipoToma
INTO #RealAnterior
FROM #UltimoReal UR
OUTER APPLY (
    SELECT TOP 1 C.Contador, C.FechaTomaContador, C.ID_TipoToma
    FROM   #ContEquipos C
    WHERE  C.ID_Maquina       = UR.ID_Maquina
      AND  C.ID_ClaseContador = UR.ID_ClaseContador
      AND  C.Estado          <> 1
      -- GUARDA DE EMPRESA + SUCURSAL (todo el par P/L): el RealAnterior debe ser de la
      -- misma empresa Y sucursal que el UltimoReal/proceso. No se cruza un cambio de
      -- empresa ni una mudanza de sucursal (otra curva de impresión).
      AND  C.ID_Empresa  = UR.Snap_ID_Empresa
      AND  C.ID_Sucursal = UR.Snap_ID_Sucursal
      AND (C.ID_TipoToma IN (1,2,3,6,7,9,10,12,15,17,20,21,22,23)
           -- T4 / T8 / T13: pueden ser RealAnterior del par. T4 → amarillo +
           -- confirmación; T8/T13 = ancla de apertura de la sucursal (sin amarillo).
           -- Solo se exige antigüedad ≤ @MaxMesesAntiguedad (empresa+sucursal ya aplican).
           OR (C.ID_TipoToma IN (4,8,13)
               AND C.FechaTomaContador >= DATEADD(MONTH, -@MaxMesesAntiguedad, @PeriodoHasta)))
      AND  C.FechaTomaContador <= DATEADD(DAY, -@MinPreferred, UR.Fecha)
    -- DESEMPATE (REGLAS_DE_NEGOCIO §14, decisión 2026-09-05): ver comentario
    -- en #UltimoReal más arriba. Real > T8/T13 > T4.
    ORDER BY C.FechaTomaContador DESC,
             CASE
                 WHEN C.ID_TipoToma IN (1,2,3,6,7,9,10,12,15,17,20,21,22,23) THEN 0
                 WHEN C.ID_TipoToma IN (8,13) THEN 1
                 ELSE 2
             END
) RA_Pref
OUTER APPLY (
    SELECT TOP 1 C.Contador, C.FechaTomaContador, C.ID_TipoToma
    FROM   #ContEquipos C
    WHERE  C.ID_Maquina       = UR.ID_Maquina
      AND  C.ID_ClaseContador = UR.ID_ClaseContador
      AND  C.Estado          <> 1
      -- GUARDA DE EMPRESA + SUCURSAL (todo el par P/L): el RealAnterior debe ser de la
      -- misma empresa Y sucursal que el UltimoReal/proceso. No se cruza un cambio de
      -- empresa ni una mudanza de sucursal (otra curva de impresión).
      AND  C.ID_Empresa  = UR.Snap_ID_Empresa
      AND  C.ID_Sucursal = UR.Snap_ID_Sucursal
      AND (C.ID_TipoToma IN (1,2,3,6,7,9,10,12,15,17,20,21,22,23)
           -- T4 / T8 / T13: pueden ser RealAnterior del par. T4 → amarillo +
           -- confirmación; T8/T13 = ancla de apertura de la sucursal (sin amarillo).
           -- Solo se exige antigüedad ≤ @MaxMesesAntiguedad (empresa+sucursal ya aplican).
           OR (C.ID_TipoToma IN (4,8,13)
               AND C.FechaTomaContador >= DATEADD(MONTH, -@MaxMesesAntiguedad, @PeriodoHasta)))
      AND  C.FechaTomaContador <= DATEADD(DAY, -@MinAbsoluto, UR.Fecha)
    -- DESEMPATE (REGLAS_DE_NEGOCIO §14, decisión 2026-09-05): ver comentario
    -- en #UltimoReal más arriba. Real > T8/T13 > T4.
    ORDER BY C.FechaTomaContador DESC,
             CASE
                 WHEN C.ID_TipoToma IN (1,2,3,6,7,9,10,12,15,17,20,21,22,23) THEN 0
                 WHEN C.ID_TipoToma IN (8,13) THEN 1
                 ELSE 2
             END
) RA_Fall
WHERE UR.Fecha IS NOT NULL;

CREATE NONCLUSTERED INDEX ix_ra ON #RealAnterior (ID_Maquina, ID_ClaseContador);

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 6 — #T4ST: última lectura T4 (ST). Caso especial en el motor.
--   ParaFacturar viene del valor a NIVEL FILA (Contadores.Para_Facturar) de ese
--   T4: 0 = técnico lo cargó, sin revisar → el motor lo sugiere con borde
--   amarillo + confirmación; >0 = operador lo validó → dato confiable. (Antes se
--   usaba @T4ParaFacturar, el flag a nivel Tipo_Toma, constante para el proceso.)
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    BP.ID_Maquina,
    BP.ID_ClaseContador,
    T4.Contador            AS Valor,
    T4.FechaTomaContador   AS Fecha,
    CASE WHEN T4.Para_Facturar > 0 THEN CAST(1 AS bit)
         ELSE CAST(0 AS bit) END                AS ParaFacturar
INTO #T4ST
FROM #BaseProceso BP
OUTER APPLY (
    SELECT TOP 1 C.Contador, C.FechaTomaContador, C.Para_Facturar
    FROM   #ContEquipos C
    WHERE  C.ID_Maquina       = BP.ID_Maquina
      AND  C.ID_ClaseContador = BP.ID_ClaseContador
      AND  C.Estado          <> 1
      AND  C.ID_TipoToma     = 4
      -- No sugerir T4 de otra empresa (snapshot) ni más viejo que @MaxMesesAntiguedad
      AND  C.ID_Empresa       = BP.Snap_ID_Empresa
      AND  C.FechaTomaContador >= DATEADD(MONTH, -@MaxMesesAntiguedad, @PeriodoHasta)
    ORDER BY C.FechaTomaContador DESC
) T4;

CREATE NONCLUSTERED INDEX ix_t4 ON #T4ST (ID_Maquina, ID_ClaseContador);

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 7 — #FCRecientesEnriq: filas de Factura_Contador de procesos cerrados
--   en los últimos 6 meses, enriquecidas con datos de Maquina/ArtGen/Anexo.
--   Estrategia: filtrar primero Factura_Anexo por (ListoParaFacturar=1, fecha)
--   — tabla chica, scan rápido — luego JOIN a FC por Nro_Proceso (clustered seek).
--   Esto materializa una sola vez lo que las cuatro CTE de parque consumen.
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    FC.Nro_Proceso,
    FC.ID_Maquina,
    FC.ID_ClaseContador,
    FC.ImpresionesReales,
    M.ID_Empresa,
    AG.Id_Tecnologia,
    AG.Id_ArtGen,
    M.ID_ModoOper,
    A.ID_GrupoE
INTO #FCRecientesEnriq
FROM       Factura_Anexo    FA WITH (NOLOCK)
INNER JOIN Anexo            A  WITH (NOLOCK) ON A.ID_Anexo       = FA.ID_Anexo
INNER JOIN Factura_Contador FC WITH (NOLOCK) ON FC.Nro_Proceso   = FA.Nro_Proceso
INNER JOIN Maquina          M  WITH (NOLOCK) ON M.ID_Maquina     = FC.ID_Maquina
INNER JOIN Articulo         Ar WITH (NOLOCK) ON Ar.ID_Articulo   = M.ID_Articulo
INNER JOIN ArtGen           AG WITH (NOLOCK) ON AG.Id_ArtGen     = Ar.ID_ArtGen
WHERE FA.ListoParaFacturar = 1
  AND FA.PeriodoHasta     >= DATEADD(MONTH, -6, @PeriodoHasta)
  AND FA.PeriodoHasta     <  @PeriodoHasta
  AND FC.ImpresionesReales > 0;

-- Índices para soportar los 4 GROUP BY de las CTE de parque
CREATE NONCLUSTERED INDEX ix_fcre_cli_tec
    ON #FCRecientesEnriq (ID_Empresa, Id_Tecnologia, ID_ModoOper, ID_ClaseContador);
CREATE NONCLUSTERED INDEX ix_fcre_cli_modelo
    ON #FCRecientesEnriq (ID_Empresa, Id_ArtGen, ID_ModoOper, ID_ClaseContador);
CREATE NONCLUSTERED INDEX ix_fcre_ge_modelo
    ON #FCRecientesEnriq (ID_GrupoE, Id_ArtGen, ID_ModoOper, ID_ClaseContador);
CREATE NONCLUSTERED INDEX ix_fcre_modelo
    ON #FCRecientesEnriq (Id_ArtGen, ID_ModoOper, ID_ClaseContador);

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 8 — Cuatro temp de parque, particionadas por ModoOper.
--   El JOIN al subset de #EquipoMeta filtra automáticamente a las dimensiones
--   que están presentes en este proceso.
--
--   ESTIMADOR ROBUSTO (Paquete 10.A) — régimen escalonado por N:
--     N ≥ 5  → MEDIANA TRUNCADA P80 (descartar equipos con valor > P80 del grupo,
--              tomar mediana del resto). Los grandes en red no entran al estimador.
--     N = 2..4 → MEDIANA CRUDA (sin truncar; muestra chica, perdés señal valiosa
--                si descartás algo).
--     N ≤ 1  → NULL en `Prom` → CalculadorContadores cae al siguiente nivel.
--
--   Cada CTE expone además N, descartados, mediana cruda y media cruda para que
--   el tooltip de la grilla y `Estim_Log` puedan mostrar/persistir la composición.
--
--   Patrón en 6 CTEs encadenadas por nivel (compat 100, sin PERCENTILE_CONT):
--     *_Raw       → universo del parque (1 fila por equipo×mes en ventana 6m)
--     *_Ord       → ROW_NUMBER + COUNT() OVER por grupo
--     *_Stats    → P80 y mediana cruda discretos por grupo (AVG con CASE WHEN rn = ...)
--     *_TruncOrd → ROW_NUMBER + COUNT() OVER sobre el subconjunto ≤ P80
--     *_Trunc    → mediana discreta del subconjunto truncado
--     *_Agg      → COUNT(DISTINCT) total/usado y media cruda
--   El SELECT FINAL combina y aplica el régimen escalonado en `Prom`.
--
--   Mediana discreta (estándar): AVG(CASE WHEN rn IN ((n+1)/2, (n+2)/2) ...)
--     n impar  → rn=(n+1)/2 = (n+2)/2 — el del medio
--     n par    → rn=n/2 y n/2+1 — promedio de los dos del centro
--   P80 discreto: valor en posición CEILING(n * 0.80) — es PERCENTILE_DISC.
--
--   La ponderación es por filas (un equipo con 6 meses cargados pesa 6×). Es la
--   semántica que ya tenía la versión AVG anterior — no la cambiamos en este paquete.
-- ─────────────────────────────────────────────────────────────────────────────

-- 8.a) Parque del CLIENTE + misma tecnología + mismo ModoOper.
--      ID_Empresa = snapshot del target (= empresa que estamos facturando).
--      FCRE.ID_Empresa = M.ID_Empresa (actual) → parque construido con máquinas
--      que HOY están en el cliente.
--
--      Compatibility level 100 (sin PERCENTILE_CONT): mediana y P80 discretos
--      con ROW_NUMBER + COUNT. La mediana es la "estándar" (promedio de los dos
--      centros si N es par); el P80 es el valor en la posición CEILING(N*0.8).
;WITH PCT_Raw AS (
    SELECT
        FCRE.ID_Empresa, EM2.IdTecnologia, FCRE.ID_ModoOper, FCRE.ID_ClaseContador,
        FCRE.ID_Maquina, FCRE.ImpresionesReales
    FROM       #FCRecientesEnriq FCRE
    INNER JOIN (SELECT DISTINCT ID_Empresa, IdTecnologia, ID_ModoOper FROM #EquipoMeta) EM2
            ON EM2.ID_Empresa   = FCRE.ID_Empresa
           AND EM2.IdTecnologia = FCRE.Id_Tecnologia
           AND EM2.ID_ModoOper  = FCRE.ID_ModoOper
),
PCT_Ord AS (
    SELECT
        ID_Empresa, IdTecnologia, ID_ModoOper, ID_ClaseContador,
        ID_Maquina, ImpresionesReales,
        ROW_NUMBER() OVER (PARTITION BY ID_Empresa, IdTecnologia, ID_ModoOper, ID_ClaseContador
                           ORDER BY ImpresionesReales) AS rn,
        COUNT(*)     OVER (PARTITION BY ID_Empresa, IdTecnologia, ID_ModoOper, ID_ClaseContador) AS n
    FROM PCT_Raw
),
PCT_Stats AS (
    -- `n` es invariante dentro del grupo (sale de COUNT() OVER), por eso se
    -- incluye en el GROUP BY sin alterar el agrupamiento. Eso permite usarlo
    -- como literal dentro del CASE WHEN sin window functions anidadas en AVG.
    SELECT
        ID_Empresa, IdTecnologia, ID_ModoOper, ID_ClaseContador, n,
        CAST(AVG(CASE WHEN rn = CAST(CEILING(CAST(n AS decimal(10,2)) * 0.80) AS int)
                      THEN ImpresionesReales END) AS decimal(18,2)) AS P80,
        CAST(AVG(CASE WHEN rn IN ((n + 1) / 2, (n + 2) / 2)
                      THEN ImpresionesReales END) AS decimal(18,2)) AS MedianaCruda,
        CAST(AVG(CASE WHEN rn = CAST(CEILING(CAST(n AS decimal(10,2)) * 0.25) AS int)
                      THEN ImpresionesReales END) AS decimal(18,2)) AS Q1,
        CAST(AVG(CASE WHEN rn = CAST(CEILING(CAST(n AS decimal(10,2)) * 0.75) AS int)
                      THEN ImpresionesReales END) AS decimal(18,2)) AS Q3
    FROM PCT_Ord
    GROUP BY ID_Empresa, IdTecnologia, ID_ModoOper, ID_ClaseContador, n
),
PCT_TruncOrd AS (
    SELECT
        R.ID_Empresa, R.IdTecnologia, R.ID_ModoOper, R.ID_ClaseContador,
        R.ImpresionesReales,
        ROW_NUMBER() OVER (PARTITION BY R.ID_Empresa, R.IdTecnologia, R.ID_ModoOper, R.ID_ClaseContador
                           ORDER BY R.ImpresionesReales) AS rn,
        COUNT(*)     OVER (PARTITION BY R.ID_Empresa, R.IdTecnologia, R.ID_ModoOper, R.ID_ClaseContador) AS n
    FROM       PCT_Raw   R
    INNER JOIN PCT_Stats S
            ON S.ID_Empresa = R.ID_Empresa AND S.IdTecnologia = R.IdTecnologia
           AND S.ID_ModoOper = R.ID_ModoOper AND S.ID_ClaseContador = R.ID_ClaseContador
    WHERE R.ImpresionesReales <= S.P80
),
PCT_Trunc AS (
    SELECT
        ID_Empresa, IdTecnologia, ID_ModoOper, ID_ClaseContador, n,
        CAST(AVG(CASE WHEN rn IN ((n + 1) / 2, (n + 2) / 2)
                      THEN ImpresionesReales END) AS decimal(18,2)) AS MedianaTrunc
    FROM PCT_TruncOrd
    GROUP BY ID_Empresa, IdTecnologia, ID_ModoOper, ID_ClaseContador, n
),
PCT_Agg AS (
    SELECT
        R.ID_Empresa, R.IdTecnologia, R.ID_ModoOper, R.ID_ClaseContador,
        COUNT(DISTINCT R.ID_Maquina) AS Cant,
        COUNT(DISTINCT CASE WHEN R.ImpresionesReales <= S.P80 THEN R.ID_Maquina END) AS CantUsada,
        CAST(AVG(CAST(R.ImpresionesReales AS decimal(18,2))) AS decimal(18,2)) AS MediaCruda
    FROM       PCT_Raw   R
    INNER JOIN PCT_Stats S
            ON S.ID_Empresa = R.ID_Empresa AND S.IdTecnologia = R.IdTecnologia
           AND S.ID_ModoOper = R.ID_ModoOper AND S.ID_ClaseContador = R.ID_ClaseContador
    GROUP BY R.ID_Empresa, R.IdTecnologia, R.ID_ModoOper, R.ID_ClaseContador
)
SELECT
    A.ID_Empresa, A.IdTecnologia, A.ID_ModoOper, A.ID_ClaseContador,
    CAST(CASE
        WHEN A.Cant >= 5 THEN T.MedianaTrunc
        WHEN A.Cant >= 2 THEN S.MedianaCruda
        ELSE NULL
    END AS decimal(18,2))           AS Prom,
    A.Cant,
    A.Cant - A.CantUsada            AS CntDescartados,
    S.MedianaCruda,
    A.MediaCruda,
    S.Q1,
    S.Q3
INTO #ParqueClienteTec
FROM      PCT_Agg   A
LEFT JOIN PCT_Stats S ON S.ID_Empresa = A.ID_Empresa AND S.IdTecnologia = A.IdTecnologia
                    AND S.ID_ModoOper = A.ID_ModoOper AND S.ID_ClaseContador = A.ID_ClaseContador
LEFT JOIN PCT_Trunc T ON T.ID_Empresa = A.ID_Empresa AND T.IdTecnologia = A.IdTecnologia
                    AND T.ID_ModoOper = A.ID_ModoOper AND T.ID_ClaseContador = A.ID_ClaseContador;


-- 8.b) Parque del CLIENTE + mismo MODELO + mismo ModoOper.
;WITH PCM_Raw AS (
    SELECT
        EM2.ID_Empresa, EM2.ID_ArtGen, EM2.ID_ModoOper, FCRE.ID_ClaseContador,
        FCRE.ID_Maquina, FCRE.ImpresionesReales
    FROM       #FCRecientesEnriq FCRE
    INNER JOIN (SELECT DISTINCT ID_Empresa, ID_ArtGen, ID_ModoOper FROM #EquipoMeta) EM2
            ON EM2.ID_Empresa  = FCRE.ID_Empresa
           AND EM2.ID_ArtGen   = FCRE.Id_ArtGen
           AND EM2.ID_ModoOper = FCRE.ID_ModoOper
),
PCM_Ord AS (
    SELECT
        ID_Empresa, ID_ArtGen, ID_ModoOper, ID_ClaseContador,
        ID_Maquina, ImpresionesReales,
        ROW_NUMBER() OVER (PARTITION BY ID_Empresa, ID_ArtGen, ID_ModoOper, ID_ClaseContador
                           ORDER BY ImpresionesReales) AS rn,
        COUNT(*)     OVER (PARTITION BY ID_Empresa, ID_ArtGen, ID_ModoOper, ID_ClaseContador) AS n
    FROM PCM_Raw
),
PCM_Stats AS (
    SELECT
        ID_Empresa, ID_ArtGen, ID_ModoOper, ID_ClaseContador, n,
        CAST(AVG(CASE WHEN rn = CAST(CEILING(CAST(n AS decimal(10,2)) * 0.80) AS int)
                      THEN ImpresionesReales END) AS decimal(18,2)) AS P80,
        CAST(AVG(CASE WHEN rn IN ((n + 1) / 2, (n + 2) / 2)
                      THEN ImpresionesReales END) AS decimal(18,2)) AS MedianaCruda
    FROM PCM_Ord
    GROUP BY ID_Empresa, ID_ArtGen, ID_ModoOper, ID_ClaseContador, n
),
PCM_TruncOrd AS (
    SELECT
        R.ID_Empresa, R.ID_ArtGen, R.ID_ModoOper, R.ID_ClaseContador,
        R.ImpresionesReales,
        ROW_NUMBER() OVER (PARTITION BY R.ID_Empresa, R.ID_ArtGen, R.ID_ModoOper, R.ID_ClaseContador
                           ORDER BY R.ImpresionesReales) AS rn,
        COUNT(*)     OVER (PARTITION BY R.ID_Empresa, R.ID_ArtGen, R.ID_ModoOper, R.ID_ClaseContador) AS n
    FROM       PCM_Raw   R
    INNER JOIN PCM_Stats S
            ON S.ID_Empresa = R.ID_Empresa AND S.ID_ArtGen = R.ID_ArtGen
           AND S.ID_ModoOper = R.ID_ModoOper AND S.ID_ClaseContador = R.ID_ClaseContador
    WHERE R.ImpresionesReales <= S.P80
),
PCM_Trunc AS (
    SELECT
        ID_Empresa, ID_ArtGen, ID_ModoOper, ID_ClaseContador, n,
        CAST(AVG(CASE WHEN rn IN ((n + 1) / 2, (n + 2) / 2)
                      THEN ImpresionesReales END) AS decimal(18,2)) AS MedianaTrunc
    FROM PCM_TruncOrd
    GROUP BY ID_Empresa, ID_ArtGen, ID_ModoOper, ID_ClaseContador, n
),
PCM_Agg AS (
    SELECT
        R.ID_Empresa, R.ID_ArtGen, R.ID_ModoOper, R.ID_ClaseContador,
        COUNT(DISTINCT R.ID_Maquina) AS Cant,
        COUNT(DISTINCT CASE WHEN R.ImpresionesReales <= S.P80 THEN R.ID_Maquina END) AS CantUsada,
        CAST(AVG(CAST(R.ImpresionesReales AS decimal(18,2))) AS decimal(18,2)) AS MediaCruda
    FROM       PCM_Raw   R
    INNER JOIN PCM_Stats S
            ON S.ID_Empresa = R.ID_Empresa AND S.ID_ArtGen = R.ID_ArtGen
           AND S.ID_ModoOper = R.ID_ModoOper AND S.ID_ClaseContador = R.ID_ClaseContador
    GROUP BY R.ID_Empresa, R.ID_ArtGen, R.ID_ModoOper, R.ID_ClaseContador
)
SELECT
    A.ID_Empresa, A.ID_ArtGen, A.ID_ModoOper, A.ID_ClaseContador,
    CAST(CASE
        WHEN A.Cant >= 5 THEN T.MedianaTrunc
        WHEN A.Cant >= 2 THEN S.MedianaCruda
        ELSE NULL
    END AS decimal(18,2))           AS Prom,
    A.Cant,
    A.Cant - A.CantUsada            AS CntDescartados,
    S.MedianaCruda,
    A.MediaCruda
INTO #ParqueClienteModelo
FROM      PCM_Agg   A
LEFT JOIN PCM_Stats S ON S.ID_Empresa = A.ID_Empresa AND S.ID_ArtGen = A.ID_ArtGen
                    AND S.ID_ModoOper = A.ID_ModoOper AND S.ID_ClaseContador = A.ID_ClaseContador
LEFT JOIN PCM_Trunc T ON T.ID_Empresa = A.ID_Empresa AND T.ID_ArtGen = A.ID_ArtGen
                    AND T.ID_ModoOper = A.ID_ModoOper AND T.ID_ClaseContador = A.ID_ClaseContador;


-- 8.c) Parque del GRUPO ECONÓMICO + mismo modelo + mismo ModoOper.
;WITH PGM_Raw AS (
    SELECT
        FCRE.ID_GrupoE AS ID_GrupoEconomico, EM2.ID_ArtGen, EM2.ID_ModoOper,
        FCRE.ID_ClaseContador, FCRE.ID_Maquina, FCRE.ImpresionesReales
    FROM       #FCRecientesEnriq FCRE
    INNER JOIN (SELECT DISTINCT ID_GrupoEconomico, ID_ArtGen, ID_ModoOper FROM #EquipoMeta) EM2
            ON EM2.ID_GrupoEconomico = FCRE.ID_GrupoE
           AND EM2.ID_ArtGen         = FCRE.Id_ArtGen
           AND EM2.ID_ModoOper       = FCRE.ID_ModoOper
),
PGM_Ord AS (
    SELECT
        ID_GrupoEconomico, ID_ArtGen, ID_ModoOper, ID_ClaseContador,
        ID_Maquina, ImpresionesReales,
        ROW_NUMBER() OVER (PARTITION BY ID_GrupoEconomico, ID_ArtGen, ID_ModoOper, ID_ClaseContador
                           ORDER BY ImpresionesReales) AS rn,
        COUNT(*)     OVER (PARTITION BY ID_GrupoEconomico, ID_ArtGen, ID_ModoOper, ID_ClaseContador) AS n
    FROM PGM_Raw
),
PGM_Stats AS (
    SELECT
        ID_GrupoEconomico, ID_ArtGen, ID_ModoOper, ID_ClaseContador, n,
        CAST(AVG(CASE WHEN rn = CAST(CEILING(CAST(n AS decimal(10,2)) * 0.80) AS int)
                      THEN ImpresionesReales END) AS decimal(18,2)) AS P80,
        CAST(AVG(CASE WHEN rn IN ((n + 1) / 2, (n + 2) / 2)
                      THEN ImpresionesReales END) AS decimal(18,2)) AS MedianaCruda
    FROM PGM_Ord
    GROUP BY ID_GrupoEconomico, ID_ArtGen, ID_ModoOper, ID_ClaseContador, n
),
PGM_TruncOrd AS (
    SELECT
        R.ID_GrupoEconomico, R.ID_ArtGen, R.ID_ModoOper, R.ID_ClaseContador,
        R.ImpresionesReales,
        ROW_NUMBER() OVER (PARTITION BY R.ID_GrupoEconomico, R.ID_ArtGen, R.ID_ModoOper, R.ID_ClaseContador
                           ORDER BY R.ImpresionesReales) AS rn,
        COUNT(*)     OVER (PARTITION BY R.ID_GrupoEconomico, R.ID_ArtGen, R.ID_ModoOper, R.ID_ClaseContador) AS n
    FROM       PGM_Raw   R
    INNER JOIN PGM_Stats S
            ON S.ID_GrupoEconomico = R.ID_GrupoEconomico AND S.ID_ArtGen = R.ID_ArtGen
           AND S.ID_ModoOper = R.ID_ModoOper AND S.ID_ClaseContador = R.ID_ClaseContador
    WHERE R.ImpresionesReales <= S.P80
),
PGM_Trunc AS (
    SELECT
        ID_GrupoEconomico, ID_ArtGen, ID_ModoOper, ID_ClaseContador, n,
        CAST(AVG(CASE WHEN rn IN ((n + 1) / 2, (n + 2) / 2)
                      THEN ImpresionesReales END) AS decimal(18,2)) AS MedianaTrunc
    FROM PGM_TruncOrd
    GROUP BY ID_GrupoEconomico, ID_ArtGen, ID_ModoOper, ID_ClaseContador, n
),
PGM_Agg AS (
    SELECT
        R.ID_GrupoEconomico, R.ID_ArtGen, R.ID_ModoOper, R.ID_ClaseContador,
        COUNT(DISTINCT R.ID_Maquina) AS Cant,
        COUNT(DISTINCT CASE WHEN R.ImpresionesReales <= S.P80 THEN R.ID_Maquina END) AS CantUsada,
        CAST(AVG(CAST(R.ImpresionesReales AS decimal(18,2))) AS decimal(18,2)) AS MediaCruda
    FROM       PGM_Raw   R
    INNER JOIN PGM_Stats S
            ON S.ID_GrupoEconomico = R.ID_GrupoEconomico AND S.ID_ArtGen = R.ID_ArtGen
           AND S.ID_ModoOper = R.ID_ModoOper AND S.ID_ClaseContador = R.ID_ClaseContador
    GROUP BY R.ID_GrupoEconomico, R.ID_ArtGen, R.ID_ModoOper, R.ID_ClaseContador
)
SELECT
    A.ID_GrupoEconomico, A.ID_ArtGen, A.ID_ModoOper, A.ID_ClaseContador,
    CAST(CASE
        WHEN A.Cant >= 5 THEN T.MedianaTrunc
        WHEN A.Cant >= 2 THEN S.MedianaCruda
        ELSE NULL
    END AS decimal(18,2))           AS Prom,
    A.Cant,
    A.Cant - A.CantUsada            AS CntDescartados,
    S.MedianaCruda,
    A.MediaCruda
INTO #ParqueGrupoModelo
FROM      PGM_Agg   A
LEFT JOIN PGM_Stats S ON S.ID_GrupoEconomico = A.ID_GrupoEconomico AND S.ID_ArtGen = A.ID_ArtGen
                    AND S.ID_ModoOper = A.ID_ModoOper AND S.ID_ClaseContador = A.ID_ClaseContador
LEFT JOIN PGM_Trunc T ON T.ID_GrupoEconomico = A.ID_GrupoEconomico AND T.ID_ArtGen = A.ID_ArtGen
                    AND T.ID_ModoOper = A.ID_ModoOper AND T.ID_ClaseContador = A.ID_ClaseContador;


-- 8.d) Parque GLOBAL + mismo modelo + mismo ModoOper.
;WITH PGL_Raw AS (
    SELECT
        EM2.ID_ArtGen, EM2.ID_ModoOper, FCRE.ID_ClaseContador,
        FCRE.ID_Maquina, FCRE.ImpresionesReales
    FROM       #FCRecientesEnriq FCRE
    INNER JOIN (SELECT DISTINCT ID_ArtGen, ID_ModoOper FROM #EquipoMeta) EM2
            ON EM2.ID_ArtGen   = FCRE.Id_ArtGen
           AND EM2.ID_ModoOper = FCRE.ID_ModoOper
),
PGL_Ord AS (
    SELECT
        ID_ArtGen, ID_ModoOper, ID_ClaseContador,
        ID_Maquina, ImpresionesReales,
        ROW_NUMBER() OVER (PARTITION BY ID_ArtGen, ID_ModoOper, ID_ClaseContador
                           ORDER BY ImpresionesReales) AS rn,
        COUNT(*)     OVER (PARTITION BY ID_ArtGen, ID_ModoOper, ID_ClaseContador) AS n
    FROM PGL_Raw
),
PGL_Stats AS (
    SELECT
        ID_ArtGen, ID_ModoOper, ID_ClaseContador, n,
        CAST(AVG(CASE WHEN rn = CAST(CEILING(CAST(n AS decimal(10,2)) * 0.80) AS int)
                      THEN ImpresionesReales END) AS decimal(18,2)) AS P80,
        CAST(AVG(CASE WHEN rn IN ((n + 1) / 2, (n + 2) / 2)
                      THEN ImpresionesReales END) AS decimal(18,2)) AS MedianaCruda
    FROM PGL_Ord
    GROUP BY ID_ArtGen, ID_ModoOper, ID_ClaseContador, n
),
PGL_TruncOrd AS (
    SELECT
        R.ID_ArtGen, R.ID_ModoOper, R.ID_ClaseContador,
        R.ImpresionesReales,
        ROW_NUMBER() OVER (PARTITION BY R.ID_ArtGen, R.ID_ModoOper, R.ID_ClaseContador
                           ORDER BY R.ImpresionesReales) AS rn,
        COUNT(*)     OVER (PARTITION BY R.ID_ArtGen, R.ID_ModoOper, R.ID_ClaseContador) AS n
    FROM       PGL_Raw   R
    INNER JOIN PGL_Stats S
            ON S.ID_ArtGen = R.ID_ArtGen AND S.ID_ModoOper = R.ID_ModoOper
           AND S.ID_ClaseContador = R.ID_ClaseContador
    WHERE R.ImpresionesReales <= S.P80
),
PGL_Trunc AS (
    SELECT
        ID_ArtGen, ID_ModoOper, ID_ClaseContador, n,
        CAST(AVG(CASE WHEN rn IN ((n + 1) / 2, (n + 2) / 2)
                      THEN ImpresionesReales END) AS decimal(18,2)) AS MedianaTrunc
    FROM PGL_TruncOrd
    GROUP BY ID_ArtGen, ID_ModoOper, ID_ClaseContador, n
),
PGL_Agg AS (
    SELECT
        R.ID_ArtGen, R.ID_ModoOper, R.ID_ClaseContador,
        COUNT(DISTINCT R.ID_Maquina) AS Cant,
        COUNT(DISTINCT CASE WHEN R.ImpresionesReales <= S.P80 THEN R.ID_Maquina END) AS CantUsada,
        CAST(AVG(CAST(R.ImpresionesReales AS decimal(18,2))) AS decimal(18,2)) AS MediaCruda
    FROM       PGL_Raw   R
    INNER JOIN PGL_Stats S
            ON S.ID_ArtGen = R.ID_ArtGen AND S.ID_ModoOper = R.ID_ModoOper
           AND S.ID_ClaseContador = R.ID_ClaseContador
    GROUP BY R.ID_ArtGen, R.ID_ModoOper, R.ID_ClaseContador
)
SELECT
    A.ID_ArtGen, A.ID_ModoOper, A.ID_ClaseContador,
    CAST(CASE
        WHEN A.Cant >= 5 THEN T.MedianaTrunc
        WHEN A.Cant >= 2 THEN S.MedianaCruda
        ELSE NULL
    END AS decimal(18,2))           AS Prom,
    A.Cant,
    A.Cant - A.CantUsada            AS CntDescartados,
    S.MedianaCruda,
    A.MediaCruda
INTO #ParqueGlobalModelo
FROM      PGL_Agg   A
LEFT JOIN PGL_Stats S ON S.ID_ArtGen = A.ID_ArtGen AND S.ID_ModoOper = A.ID_ModoOper
                    AND S.ID_ClaseContador = A.ID_ClaseContador
LEFT JOIN PGL_Trunc T ON T.ID_ArtGen = A.ID_ArtGen AND T.ID_ModoOper = A.ID_ModoOper
                    AND T.ID_ClaseContador = A.ID_ClaseContador;

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 9 — #Prom6FC: promedio facturado de los últimos 6 procesos cerrados del
--   propio equipo. Ventana = 7 meses, excluyendo el proceso actual.
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    FC2.ID_Maquina,
    FC2.ID_ClaseContador,
    AVG(CAST(NULLIF(FC2.ImpresionesReales, 0) AS decimal(18,2))) AS Prom
INTO #Prom6FC
FROM       Factura_Anexo    FA2 WITH (NOLOCK)
INNER JOIN Factura_Contador FC2 WITH (NOLOCK) ON FC2.Nro_Proceso = FA2.Nro_Proceso
INNER JOIN #BaseProceso     BP                ON BP.ID_Maquina       = FC2.ID_Maquina
                                              AND BP.ID_ClaseContador = FC2.ID_ClaseContador
WHERE FA2.ListoParaFacturar = 1
  AND FA2.Nro_Proceso      <> @NroProceso
  AND FA2.PeriodoHasta     >= DATEADD(MONTH, -7, @PeriodoHasta)
GROUP BY FC2.ID_Maquina, FC2.ID_ClaseContador;

CREATE NONCLUSTERED INDEX ix_p6 ON #Prom6FC (ID_Maquina, ID_ClaseContador);

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 10 — #ContadorAnterior y #ContadorActual: lookups por ID_Contador.
--   Usa la PK clustered de Contadores (rápido por sí solo).
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    BP.ID_Maquina,
    BP.ID_ClaseContador,
    C.Contador            AS Valor,
    C.FechaTomaContador   AS Fecha,
    C.ID_TipoToma         AS TipoToma
INTO #ContadorAnterior
FROM       #BaseProceso BP
LEFT  JOIN Contadores  C WITH (NOLOCK) ON C.ID_Contador = BP.ID_ContadorAnterior;

CREATE NONCLUSTERED INDEX ix_ca ON #ContadorAnterior (ID_Maquina, ID_ClaseContador);

SELECT
    BP.ID_Maquina,
    BP.ID_ClaseContador,
    C.FechaTomaContador   AS Fecha,
    C.ID_TipoToma         AS TipoToma
INTO #ContadorActual
FROM       #BaseProceso BP
LEFT  JOIN Contadores  C WITH (NOLOCK) ON C.ID_Contador = BP.ID_ContadorActual;

CREATE NONCLUSTERED INDEX ix_cact ON #ContadorActual (ID_Maquina, ID_ClaseContador);

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 11 — #HistoricoFC11: top 11 procesos cerrados del propio equipo,
--   pivotados a columnas H01..H11. Sin ventana temporal — queremos los
--   últimos 11 procesos cerrados independientemente de la fecha.
--
--   Nota: este paso puede tocar Factura_Contador para máquinas con muchos
--   procesos. El filtro EXISTS contra #BaseProceso permite seek por
--   ID_Maquina si existe un índice; sin él, scan + filter. Aceptable porque
--   el resultado se acota a 11 filas por máquina vía ROW_NUMBER.
-- ─────────────────────────────────────────────────────────────────────────────
;WITH HistoricoRaw AS (
    SELECT
        FC2.ID_Maquina,
        FC2.ID_ClaseContador,
        ISNULL(FC2.ImpresionesReales, 0) AS Imp,
        ROW_NUMBER() OVER (
            PARTITION BY FC2.ID_Maquina, FC2.ID_ClaseContador
            ORDER BY FC2.Nro_Proceso DESC
        ) AS RN
    FROM       Factura_Contador FC2 WITH (NOLOCK)
    INNER JOIN Factura_Anexo    FA2 WITH (NOLOCK) ON FA2.Nro_Proceso = FC2.Nro_Proceso
    WHERE FA2.ListoParaFacturar = 1
      AND FA2.Nro_Proceso      <> @NroProceso
      AND EXISTS (
            SELECT 1 FROM #BaseProceso BP
            WHERE BP.ID_Maquina       = FC2.ID_Maquina
              AND BP.ID_ClaseContador = FC2.ID_ClaseContador
          )
)
SELECT
    ID_Maquina,
    ID_ClaseContador,
    MAX(CASE WHEN RN =  1 THEN Imp END) AS H01,
    MAX(CASE WHEN RN =  2 THEN Imp END) AS H02,
    MAX(CASE WHEN RN =  3 THEN Imp END) AS H03,
    MAX(CASE WHEN RN =  4 THEN Imp END) AS H04,
    MAX(CASE WHEN RN =  5 THEN Imp END) AS H05,
    MAX(CASE WHEN RN =  6 THEN Imp END) AS H06,
    MAX(CASE WHEN RN =  7 THEN Imp END) AS H07,
    MAX(CASE WHEN RN =  8 THEN Imp END) AS H08,
    MAX(CASE WHEN RN =  9 THEN Imp END) AS H09,
    MAX(CASE WHEN RN = 10 THEN Imp END) AS H10,
    MAX(CASE WHEN RN = 11 THEN Imp END) AS H11
INTO #HistoricoFC11
FROM HistoricoRaw
WHERE RN <= 11
GROUP BY ID_Maquina, ID_ClaseContador;

CREATE NONCLUSTERED INDEX ix_h11 ON #HistoricoFC11 (ID_Maquina, ID_ClaseContador);

-- ─────────────────────────────────────────────────────────────────────────────
-- SELECT FINAL — JOINs sobre temps.
--   Columnas 0-57: mismo orden y semántica que la versión anterior
--                  (SiGesRepository las lee por índice).
--   Columnas 58-72: agregados Paquete 10.A para auditoría del estimador robusto
--                  (N parque, descartados, mediana cruda, media cruda por nivel).
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    BP.ID_Maquina                                                   AS [0_ID_Maquina],
    BP.ID_ClaseContador                                             AS [1_ID_ClaseContador],
    EM.NroSerie                                                     AS [2_NroSerie],
    EM.ID_Empresa                                                   AS [3_ID_Empresa],
    EM.EmpresaDesc                                                  AS [4_EmpresaDesc],
    EM.ID_Sucursal                                                  AS [5_ID_Sucursal],
    EM.SucursalDesc                                                 AS [6_SucursalDesc],
    EM.Id_Sector                                                    AS [7_Id_Sector],
    EM.SectorDesc                                                   AS [8_SectorDesc],
    EM.ID_GrupoEconomico                                            AS [9_ID_GrupoEconomico],
    EM.ID_ArtGen                                                    AS [10_ID_ArtGen],
    EM.ModeloDesc                                                   AS [11_ModeloDesc],
    EM.IdTecnologia                                                 AS [12_IdTecnologia],
    EM.Velocidad                                                    AS [13_Velocidad],
    BP.PendienteEstimar                                             AS [14_PendienteEstimar],
    CA.Valor                                                        AS [15_ContadorAnterior_Valor],
    CA.Fecha                                                        AS [16_ContadorAnterior_Fecha],
    CA.TipoToma                                                     AS [17_ContadorAnterior_TipoToma],
    UR.Valor                                                        AS [18_UltimoReal_Valor],
    UR.Fecha                                                        AS [19_UltimoReal_Fecha],
    UR.TipoToma                                                     AS [20_UltimoReal_TipoToma],
    RA.Valor                                                        AS [21_RealAnterior_Valor],
    RA.Fecha                                                        AS [22_RealAnterior_Fecha],
    RA.TipoToma                                                     AS [23_RealAnterior_TipoToma],
    T4.Valor                                                        AS [24_T4ST_Valor],
    T4.Fecha                                                        AS [25_T4ST_Fecha],
    CAST(ISNULL(T4.ParaFacturar, 0) AS bit)                         AS [26_T4ST_ParaFacturar],
    P6.Prom                                                         AS [27_Prom6FC],
    PCT.Prom                                                        AS [28_PromParque_Cliente_Tec],
    ISNULL(PCT.Cant, 0)                                             AS [29_CntParque_Cliente_Tec],
    PCM.Prom                                                        AS [30_PromParque_Cliente_Modelo],
    PGM.Prom                                                        AS [31_PromParque_Grupo_Modelo],
    PGL.Prom                                                        AS [32_PromParque_Global_Modelo],
    PGL.Prom                                                        AS [33_PromGlobalModelo_Imp],
    PCT.Q1                                                          AS [34_Q1_ParqueClienteTec],
    PCT.Q3                                                          AS [35_Q3_ParqueClienteTec],
    @PeriodoHasta                                                   AS [36_PeriodoHasta],
    @PeriodoDesde                                                   AS [37_PeriodoDesde],
    EM.ID_EstadoMaquina                                             AS [38_ID_EstadoMaquina],
    EM.EstadoMaquinaDesc                                            AS [39_EstadoMaquinaDesc],
    -- Histórico BarChart: H01 = UF (más reciente), H11 = más antiguo. 0 si no existe.
    ISNULL(HP.H01, 0)                                               AS [40_H01],
    ISNULL(HP.H02, 0)                                               AS [41_H02],
    ISNULL(HP.H03, 0)                                               AS [42_H03],
    ISNULL(HP.H04, 0)                                               AS [43_H04],
    ISNULL(HP.H05, 0)                                               AS [44_H05],
    ISNULL(HP.H06, 0)                                               AS [45_H06],
    ISNULL(HP.H07, 0)                                               AS [46_H07],
    ISNULL(HP.H08, 0)                                               AS [47_H08],
    ISNULL(HP.H09, 0)                                               AS [48_H09],
    ISNULL(HP.H10, 0)                                               AS [49_H10],
    ISNULL(HP.H11, 0)                                               AS [50_H11],
    -- Contador actual del proceso (NULL cuando PendienteEstimar = 1)
    CASE WHEN BP.PendienteEstimar = 0 THEN BP.ImpreContadorActual ELSE NULL END AS [51_FC_ImpreContadorActual],
    CASE WHEN BP.PendienteEstimar = 0 THEN CTACT.Fecha            ELSE NULL END AS [52_FC_Fecha_ContActual],
    CASE WHEN BP.PendienteEstimar = 0 THEN CTACT.TipoToma         ELSE NULL END AS [53_FC_TipoToma_ContActual],
    CASE WHEN BP.PendienteEstimar = 0 THEN BP.ImpresionesReales   ELSE NULL END AS [54_FC_ImpresionesReales],
    EM.EmpresaActualDesc                                            AS [55_EmpresaActualDesc],
    EM.ID_ModoOper                                                  AS [56_ID_ModoOper],
    BP.EsClaseSintetica                                             AS [57_EsClaseSintetica],
    -- ── Métricas de auditoría del estimador robusto (Paquete 10.A) ───────────
    ISNULL(PCT.CntDescartados, 0)                                   AS [58_PCT_CntDescartados],
    PCT.MedianaCruda                                                AS [59_PCT_MedianaCruda],
    PCT.MediaCruda                                                  AS [60_PCT_MediaCruda],
    ISNULL(PCM.CntDescartados, 0)                                   AS [61_PCM_CntDescartados],
    ISNULL(PCM.Cant, 0)                                             AS [62_PCM_Cant],
    PCM.MedianaCruda                                                AS [63_PCM_MedianaCruda],
    PCM.MediaCruda                                                  AS [64_PCM_MediaCruda],
    ISNULL(PGM.CntDescartados, 0)                                   AS [65_PGM_CntDescartados],
    ISNULL(PGM.Cant, 0)                                             AS [66_PGM_Cant],
    PGM.MedianaCruda                                                AS [67_PGM_MedianaCruda],
    PGM.MediaCruda                                                  AS [68_PGM_MediaCruda],
    ISNULL(PGL.CntDescartados, 0)                                   AS [69_PGL_CntDescartados],
    ISNULL(PGL.Cant, 0)                                             AS [70_PGL_Cant],
    PGL.MedianaCruda                                                AS [71_PGL_MedianaCruda],
    PGL.MediaCruda                                                  AS [72_PGL_MediaCruda],
    UR.UltimoRealNoT4_Fecha                                         AS [73_UltimoRealNoT4_Fecha]
FROM       #BaseProceso       BP
INNER JOIN #EquipoMeta        EM  ON EM.ID_Maquina = BP.ID_Maquina
LEFT  JOIN #ContadorAnterior  CA  ON CA.ID_Maquina       = BP.ID_Maquina
                                 AND CA.ID_ClaseContador = BP.ID_ClaseContador
LEFT  JOIN #UltimoReal        UR  ON UR.ID_Maquina       = BP.ID_Maquina
                                 AND UR.ID_ClaseContador = BP.ID_ClaseContador
LEFT  JOIN #RealAnterior      RA  ON RA.ID_Maquina       = BP.ID_Maquina
                                 AND RA.ID_ClaseContador = BP.ID_ClaseContador
LEFT  JOIN #T4ST              T4  ON T4.ID_Maquina       = BP.ID_Maquina
                                 AND T4.ID_ClaseContador = BP.ID_ClaseContador
LEFT  JOIN #Prom6FC           P6  ON P6.ID_Maquina       = BP.ID_Maquina
                                 AND P6.ID_ClaseContador = BP.ID_ClaseContador
LEFT  JOIN #ParqueClienteTec  PCT ON PCT.ID_Empresa       = EM.ID_Empresa
                                 AND PCT.IdTecnologia     = EM.IdTecnologia
                                 AND PCT.ID_ModoOper      = EM.ID_ModoOper
                                 AND PCT.ID_ClaseContador = BP.ID_ClaseContador
LEFT  JOIN #ParqueClienteModelo PCM ON PCM.ID_Empresa     = EM.ID_Empresa
                                 AND PCM.ID_ArtGen        = EM.ID_ArtGen
                                 AND PCM.ID_ModoOper      = EM.ID_ModoOper
                                 AND PCM.ID_ClaseContador = BP.ID_ClaseContador
LEFT  JOIN #ParqueGrupoModelo PGM ON PGM.ID_GrupoEconomico = EM.ID_GrupoEconomico
                                 AND PGM.ID_ArtGen          = EM.ID_ArtGen
                                 AND PGM.ID_ModoOper        = EM.ID_ModoOper
                                 AND PGM.ID_ClaseContador   = BP.ID_ClaseContador
LEFT  JOIN #ParqueGlobalModelo PGL ON PGL.ID_ArtGen         = EM.ID_ArtGen
                                 AND PGL.ID_ModoOper        = EM.ID_ModoOper
                                 AND PGL.ID_ClaseContador   = BP.ID_ClaseContador
LEFT  JOIN #HistoricoFC11     HP   ON HP.ID_Maquina         = BP.ID_Maquina
                                  AND HP.ID_ClaseContador   = BP.ID_ClaseContador
LEFT  JOIN #ContadorActual    CTACT ON CTACT.ID_Maquina       = BP.ID_Maquina
                                  AND CTACT.ID_ClaseContador = BP.ID_ClaseContador
ORDER BY EM.EmpresaDesc, EM.SucursalDesc, EM.NroSerie, BP.ID_ClaseContador;

-- ─────────────────────────────────────────────────────────────────────────────
-- Cleanup: drop temps explícitos por higiene.
--   SqlClient resetea la conexión al pool (sp_reset_connection) y eso
--   ya las dropea, pero el DROP defensivo evita sorpresas si en el futuro
--   se cambia el driver o el modo de ejecución.
-- ─────────────────────────────────────────────────────────────────────────────
DROP TABLE #FCActual;
DROP TABLE #ClasesEsperadas;
DROP TABLE #ClasesSinteticas;
DROP TABLE #BaseProceso;
DROP TABLE #ContEquipos;
DROP TABLE #EquipoMeta;
DROP TABLE #UltimoReal;
DROP TABLE #RealAnterior;
DROP TABLE #T4ST;
DROP TABLE #FCRecientesEnriq;
DROP TABLE #ParqueClienteTec;
DROP TABLE #ParqueClienteModelo;
DROP TABLE #ParqueGrupoModelo;
DROP TABLE #ParqueGlobalModelo;
DROP TABLE #Prom6FC;
DROP TABLE #ContadorAnterior;
DROP TABLE #ContadorActual;
DROP TABLE #HistoricoFC11;
"""
