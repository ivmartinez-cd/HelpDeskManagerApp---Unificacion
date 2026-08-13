# Validación adversarial del pipeline de Liquidaciones — 2026-08-13

> **Actualización (mismo día, sesión de correcciones)**: todos los hallazgos fueron
> corregidos y re-verificados — ver la sección final "Estado de hallazgos tras las
> correcciones". El veredicto NO-APTO de las dos dimensiones del sync WS quedó
> levantado; el pendiente #1 de MIGRACION_ESTADO (correr el sync completo) ya no
> está bloqueado por H-1/H-2.

Auditoría de las dos fuentes automatizadas del módulo (config desde SigesReadOnly, ADR-014;
preliquidaciones desde wsAyC SOAP, ADR-015) contra el código real, la DB real (`helpdesk-db`)
y los servicios externos reales (solo lectura). Ejecutada con `DISABLE_BACKGROUND_JOBS=true`
verificado dentro del contenedor (`printenv` → `true`; sin `background_jobs: N job(s) iniciados`
en el log de arranque).

Capturas de la simulación Chromium en `capturas-validacion-2026-08-13/`.

## Veredicto por dimensión

| Dimensión | Veredicto |
|---|---|
| Arquitectura y calidad | **APTO-CON-RESERVAS** (gates verdes; §4 funciones >20 líneas extendido) |
| Vínculo de prestadores (Siges + CD) | **APTO** (34/34 verificados contra ambas fuentes) |
| Ruta Siges (config + tarifarios) | **APTO** (dry-run idempotente, conflictos reportados sin escribir) |
| Aditividad del sync WS (no pisa lo existente) | **APTO** (diff exacto = 0 filas tras 2 corridas) |
| **Dedup / numeración del sync WS** | **NO-APTO** (dígito verificador mal calculado → duplica lo importado por CSV) |
| Robustez del sync WS ante fallo SOAP | **NO-APTO** (crea liquidaciones vacías permanentes ante 502 transitorio) |
| Motor de reglas | **APTO-CON-RESERVAS** (ALT001/ALT002 verificadas a mano; el ceil de hoy endurece un caso no documentado) |
| Simulación E2E | **APTO** (UI ↔ DB ↔ cálculo manual coinciden) |

**Conclusión operativa: NO correr el sync completo (pendiente #1 de MIGRACION_ESTADO) hasta
corregir H-1 y H-2.** Si se corre hoy, crea ~31 duplicados de las 35 liquidaciones ya
importadas por CSV, importa ~2.000+ liquidaciones históricas con `numero_liquidacion`
incorrecto (links a webagentes rotos) y deja vacía toda liquidación cuyo
`getLiquidationDetails` falle en el momento del sync.

---

## Hallazgos, por severidad

| Sev | Dimensión | Hallazgo | Evidencia | Impacto | Reproducción |
|---|---|---|---|---|---|
| **CRÍTICO** | Dedup sync WS | H-1: `zeep_cd_liquidaciones_gateway.py:94` calcula el dígito verificador como `liq_id % 10`. El algoritmo real (legacy `core/numeracion_ayc.py`, caracterización §"Dígito verificador módulo-10") es **pesos 3-1-3-1 sobre los dígitos, `(10 - suma%10) % 10`**. Verificado: la fórmula 3-1-3-1 reproduce **35/35** números locales reales; `id % 10` solo 4/35 (3859-9, 3876-6, 3923-3, 3928-8 — coincidencias, entre ellas los DOS casos usados para "validar" el ADR-015) | Corrida controlada (solo SM TUCUMAN vinculado): 1ª corrida `creadas=23, yaExistentes=0` cuando debía ser `creadas=20, yaExistentes=3` — creó los duplicados `3852-2`, `3878-8`, `3911-1` de las locales `3852-6`, `3878-4`, `3911-8` (mismo período; `3911-1` con los mismos 18 incidentes y el mismo importe $998.305,20 que `3911-8`). Sonda SOAP read-only: AyC id 3739 (07/02/2026, 107 inc) ES la local `3739-6` del smoke test documentado; el gateway generaría `3739-9` | El sync completo duplicaría ~31 de las 35 liqs existentes; todo lo importado por WS queda con número inexistente en webagentes (los hipervínculos de P3/P8 apuntan a páginas que no existen); rompe la convivencia CSV↔WS que ADR-014 daba por garantizada | `POST /api/liquidaciones/sincronizar` con cualquier prestador que tenga una liq CSV cuyo sufijo ≠ `id%10` |
| **ALTO** | Robustez sync WS | H-2: si `getLiquidationDetails` falla, el gateway devuelve `[]` (`zeep_cd_liquidaciones_gateway.py:71-75`) y `SincronizarLiquidaciones._procesar` (`sincronizar_liquidaciones.py:77-92`) **crea la liquidación igual, con 0 incidentes y $0**. Por diseño aditivo, la corrida siguiente la cuenta `ya_existente` y nunca la repara | Ocurrió en vivo en la corrida controlada: wsAyC devolvió **502 de Cloudflare** (HTML → `zeep.exceptions.XMLSyntaxError`, log `SOAP getLiquidationDetails(id=3852) falló`) en 2 de 23 llamadas → `3852-2` y `3878-8` quedaron con `total_incidentes=0, total_importe=0` mientras el propio `getTopLiquidations` declaraba `CantIncidentes=33` y `38`. La 2ª corrida las contó `ya_existentes` sin repararlas | Liquidaciones vacías permanentes ante cualquier fallo transitorio del WS; el dato para detectarlo (`CdLiquidacion.cant_incidentes`) ya está en el VO y no se usa | Cortar la red a mitad de un sync, o esperar un 502 de CF (2/23 llamadas en esta corrida) |
| **MEDIO** | Sync WS / API | H-3: `sinPrestador` siempre devuelve 0: `sincronizar_liquidaciones.py:74` lo hardcodea (`sin_prestador=0`) aunque el docstring del propio archivo dice "los demás se contabilizan en `sin_prestador`" y el schema lo expone. La TL no tiene forma de ver qué prestadores quedaron fuera del sync | Código: `execute()` nunca cuenta los no vinculados; toast del frontend solo muestra el campo si `> 0` — o sea, nunca | El resultado del sync sobre-reporta cobertura; ADR-015 lo lista como campo del contrato | Desvincular un prestador y correr el sync: `sinPrestador` sigue en 0 |
| **MEDIO** | Motor de reglas | H-4: el cambio de hoy en ALT002 (`1b562e4`, `math.ceil`) no solo elimina el falso positivo documentado (cobrar `ceil(esperado)`): **convierte en alerta el caso "PST factura el piso/decimal exacto"**, antes tolerado. Con tabla 71.3 y cobrado 71: antes dif 0.3 ≤ 0.5 → ok; ahora esperado 72, dif 1 → alerta | Reanálisis real de SUPERNOVA `3849-2`: 8 alertas → 10 (aparecen ALT002 en `832521-5` [71 vs 71.3→72] y `834702-2` [45 vs 45.4→46]). En DB hay 176 filas de `tabla_kms` con fracción < 0.5 y 234 incidentes con `cant_km_esperado` decimal — superficie real del cambio de semántica | Próximo reanálisis masivo va a sumar alertas ALT002 sobre liquidaciones ya cerradas; puede ser deseado (facturar de menos también es hallazgo) pero no está documentado como decisión en P1 | `POST /api/liquidaciones/{id}/reanalyze` sobre `3849-2` (restaurada tras el test; ver "Escrituras realizadas") |
| **MEDIO** | Sync WS / operación | H-5: el sync completo es **un único request HTTP síncrono sin timeout ni progreso**: 34 × `getTopLiquidations` + una llamada `getLiquidationDetails` + motor de reglas por cada liq nueva. El histórico real medido (solo 15 prestadores sondeados: 1.228 liqs; JUJUY 115, SAN JUAN 189) proyecta ~2.000+ llamadas SOAP y minutos de request | Sondas read-only `getTopLiquidations(Top=200)` por prestador (tabla abajo) | Primer sync real: request de decenas de minutos, sin feedback, con el 502 intermitente de CF (H-2) degradando resultados a mitad de corrida | Correr el sync con todos los vinculados |
| **BAJO** | Sync WS | H-6: `list_con_cd_id()` (`sqlalchemy_prestador_repository.py:90-97`) no filtra `activo` — un prestador inactivo con `cd_prestador_id` entraría al sync. Hoy no hay contraejemplo en datos (el único inactivo, ZZTESTUI, no tiene vínculo), es un hueco solo de código | DB: `SELECT ... WHERE NOT activo` → solo ZZTESTUI, `cd_prestador_id IS NULL` | Baja administrativa de un PST no lo saca del sync | Vincular un cd_id a un prestador inactivo y sincronizar |
| **BAJO** | Arquitectura §4 | H-7: 40 funciones del módulo superan las 20 líneas (máx: `_liq_csv.import_tabla_km` 51, `import_tarifarios` 44, `sync_tarifarios.planificar_sync_tarifarios` 34) y `_liq_csv.py` queda en 302 líneas (>300). Medido con AST (span físico, incluye docstrings) | Listado completo en la sesión; ningún archivo restante >300, ninguna clase >200 | Deuda §4 declarada como regla dura en CLAUDE.md; sin ADR que la excuse | Script AST sobre `src/modules/liquidaciones` |
| **BAJO** | Catálogo de reglas | H-8: `ALT007` figura `activa=true` en `reglas_alerta` pero no tiene evaluador (a propósito, fiel al legacy — documentado en `regla_alerta.py:28`). Una regla "activa" que nunca genera nada es confusa para quien administre el catálogo | DB: 9 reglas, ALT006 inactiva sin evaluador, ALT007 **activa** sin evaluador | Confusión operativa; ninguna funcional | `SELECT codigo, activa FROM reglas_alerta` |

Sospechas (sin contraejemplo reproducible, se registran como tales):
- `_parse_liquidaciones` descarta ítems sin `id` o con `Fecha` no parseable en silencio (`continue`) — con el formato real observado no ocurre, pero un cambio de formato de AyC haría "desaparecer" liquidaciones sin log (§6 en el límite: el except general sí loguea, estos `continue` no).
- `extraer_periodo("", incidentes)` sobre los incidentes del WS puede diferir del período que la TL asignaría por nombre de archivo en el import CSV; en la corrida controlada los períodos coincidieron con `fecha_liquidacion - 1 mes` (23/23 razonables), sin contraejemplo.

---

## FASE 0 — Afirmación de la doc vs código real

| Afirmación (doc) | Estado | Evidencia |
|---|---|---|
| ADR-015 §1 "Aditivo puro: si `numero_liquidacion` existe, no se toca" | **VERIFICADO** (como no-update/no-delete) | Diff `EXCEPT` bidireccional en 5 tablas (liquidaciones/incidentes/alertas/observaciones/observacion_incidentes) de SM TUCUMAN tras 2 syncs: **0 filas** en todas. Use case solo llama `create`/`bulk_create`/`reanalizar` (`sincronizar_liquidaciones.py:57-92`) |
| ADR-015 §1 (implícito) "el dedup por `numero_liquidacion` reconoce lo ya importado" | **NO CUMPLE** | H-1: `creadas=23, yaExistentes=0` con 3 locales preexistentes → 3 duplicados. La "verificación" del ADR (JUJUY `3928-8`) funcionó de casualidad: 3928%10=8 coincide con el dv real |
| ADR-015 §2 "por empresa, `getTopLiquidations(IdEmpresa=str(cd_id))`, sin matching por nombre" | **VERIFICADO** | Log zeep: `<IdEmpresa>1285</IdEmpresa>`; gateway `zeep_cd_liquidaciones_gateway.py:53-57`; ningún uso del campo `Prestador` de la respuesta |
| ADR-015 §3 "`cd_prestador_id` nullable UNIQUE, migración `d6e3c1b4a829`, `PATCH /vincular-cd`" | **VERIFICADO** | Migración crea `uq_prestadores_cd_prestador_id`; endpoint en `config_routers/prestadores.py:82`; `IntegrityError` → `CdVinculoDuplicadoError` |
| ADR-015 §4 "`getLiquidationDetails` solo para las nuevas" | **VERIFICADO** | `_procesar` solo se invoca en la rama `not in existentes`; 2ª corrida: 0 llamadas a details (log) |
| ADR-015 §5 "sin dry-run porque es aditivo puro" | **PARCIAL** | La premisa "no hay nada que proteger" es falsa en la práctica: sin dry-run no hay forma de ver que va a crear duplicados (H-1) ni volumen (~2.000+). Coherente solo si H-1/H-2 se corrigen |
| ADR-015 §6 "estado inicial `abierta`, el estado del SOAP no se mapea" | **VERIFICADO** | Las 23 creadas nacieron `abierta` aunque el SOAP decía `Cerrada`/`Aprobada` (server_default `liquidacion_model.py:33`) |
| ADR-015 §7 "disparo manual, sin job de fondo" | **VERIFICADO** | Solo `POST /sincronizar` (permiso CREATE, `liquidaciones_router.py:116-122`) + botón dashboard; ningún registro en background_jobs |
| ADR-015 §8 "`ReanalizarLiquidacion` automático al crear" | **VERIFICADO** | 21/23 creadas con `total_alertas > 0` inmediato; `_procesar` llama `reanalizar.execute(liq.id)` |
| ADR-015 "SOAP caído → `[]` para ese prestador + log, no rompe lo importado" | **PARCIAL** | Loguea con contexto (`warning` + `exc_info`) y no rompe lo importado, pero en `get_incidentes` el mismo patrón **crea la liquidación vacía** (H-2) — "no romper" no es "no dejar basura" |
| ADR-015 "la sync no descarta ZZTESTUI ni no vinculados — `list_con_cd_id()` los excluye" | **VERIFICADO** (con matiz H-6) | ZZTESTUI: `cd_prestador_id IS NULL`, inactivo; el WHERE excluye NULL. No filtra `activo` |
| ADR-014 "sync config: solo actualiza espejo (cuit) de vinculados, nunca crea/desactiva; nombre distinto se reporta sin escribir; dry-run first-class" | **VERIFICADO** | 2 dry-runs idénticos: `cambios=[], sinCambios=34, nombresDistintos=2 (SM TUCUMAN, TUCUMAN/NAPA), sinVinculo=[ZZTESTUI]`; corrida real (`dryRun=false`): mismo resultado, 0 escrituras |
| ADR-014 "tarifarios: crea solo vigencias faltantes vía `CreateTarifario`; conflicto se reporta y JAMÁS se pisa" | **VERIFICADO** | Dry-run: `creados=0, sinCambios=5139`, conflictos = exactamente los 3 conocidos (SAN JUAN doble-instalación 92252/46126, VENADO 66794/66749, INFOMAC 23073/24559), intactos en DB |
| ADR-014 "vínculo `siges_empresa_id` UNIQUE, sin matching por nombre en runtime" | **VERIFICADO** | 34/35 vinculados (ZZTESTUI no); sync usa solo el id; UNIQUE en migración `c4d8a91f26e3` |
| MIGRACION_ESTADO "33 prestadores vinculados a cd" | **DESACTUALIZADO** (menor) | Hoy son **34** (todos menos ZZTESTUI) |
| Caracterización "numeración = id AyC + dígito módulo-10 (pesos 3-1-3-1)" | **VERIFICADO** (y es la spec que el gateway violó) | Fórmula reproduce 35/35 números reales; ids de AyC confirmados por sonda (3739↔`3739-6`, 3922↔`3922-4`, 3928↔`3928-8`) |

### Mapa real del pipeline

```
RUTA A — Config (SigesReadOnly, pyodbc, ADR-014)             RUTA B — Preliquidaciones (wsAyC SOAP, zeep, ADR-015)
┌─ MERCURIO/Siges (solo lectura, SQL parametrizado) ─┐        ┌─ wsg.cdsisa.com.ar/wsAyC_server.php ────────────────┐
│ dbo.Empresa (Estado=0, 'PST '/'SPST')              │        │ getTopLiquidations(IdEmpresa=cd_id, Top=200)        │
│ dbo.CostoServicio (wide, por vigencia)             │        │ getLiquidationDetails(nro=id)   [solo nuevas]       │
│ dbo.Sucursal (Estado=0)                            │        └────────────┬────────────────────────────────────────┘
└──────────────┬─────────────────────────────────────┘                     │ JSON-en-string → CdLiquidacion/CdIncidenteRow
   PyodbcSigesCatalogoGateway (ExternalServiceError)                       │ numero = f"{id}-{id%10}"  ← H-1 (debía ser 3-1-3-1)
               │                                              ZeepCdLiquidacionesGateway (except → [] + log ← H-2)
   ProponerVinculos / SyncConfig / SyncTarifarios /                        │
   BuscarSucursales  (dry-run first-class)                    SincronizarLiquidaciones:
               │                                                list_con_cd_id() → por prestador → dedup por SET de
   escribe: cuit espejo, vigencias nuevas vía                   numero_liquidacion → create + bulk_create +
   CreateTarifario (recadenado), zona_maps                      ReanalizarLiquidacion (motor síncrono)
   NUNCA: crear/borrar prestadores, pisar costos                escribe: liquidaciones/incidentes/alertas/observaciones
```

## FASE 1 — Arquitectura y calidad

Corrido dentro de `helpdesk-manager-backend` (2026-08-13):

- `uv run lint-imports` → **19/19 contratos KEPT** ("El dominio de liquidaciones no importa
  frameworks", "domain/application no depende de auth", módulos independientes).
- `uv run ruff check src tests` → All checks passed.
- `uv run mypy src` → Success, 924 archivos.
- `uv run pytest tests/unit -q` → **1018 passed** (18.7s), incl. los 34 de
  `test_motor_reglas.py`.
- §4: ver H-7. §5: zeep y pyodbc quedan detrás de sus puertos; el dominio no los importa
  (verificado por lint-imports, no a ojo). §6: los `except Exception` de ambos gateways
  loguean con contexto y `exc_info` (el de pyodbc además envuelve en `ExternalServiceError`;
  el de zeep degrada a `[]` por diseño ADR-015 — consecuencia H-2). El motor de reglas no
  tiene ningún try/except: propaga, correcto.
- Acoplamiento entre rutas: nulo — comparten solo `PrestadorRepository` y la normalización
  de nombres de dominio; gateways, VOs, use cases y routers separados.

## FASE 2 — Vínculos de prestadores

- DB real: 35 prestadores; **34 con `siges_empresa_id` y 34 con `cd_prestador_id`**; el único
  sin ambos es `ZZTESTUI` (inactivo, fila de prueba). Sin ambigüedades: PERTEX eliminado,
  SUPERNOVA→600, TUCUMAN→491 (NAPA, decisión del usuario).
- **Los 34 vínculos CD verificados contra el SOAP** (sonda read-only `Top=1` por prestador):
  el campo `Prestador` de la respuesta coincide con el nombre local en 34/34 (33 exactos con
  prefijo `PST `; TUCUMAN→`PST Tucuman - NAPA Tucuman`, documentado).
- Dry-run Siges corrido 2 veces → resultados byte-idénticos, 0 cambios (arriba). Corrida real
  con `dryRun=false` → mismo resultado, nada que escribir. Idempotencia verificada.

## FASE 3 — Corrida controlada del sync WS (SM TUCUMAN)

Decisión de método: **no se corrió el sync completo** — H-1 estaba ya confirmado por
aritmética + sonda, y correrlo habría creado ~31 duplicados y ~2.000+ liqs mal numeradas en
la DB en uso real de la TL (además de pre-ejecutar el pendiente #1 que la doc reserva a la
TL). En su lugar: corrida acotada a un prestador con snapshot exacto y limpieza.

Protocolo (todas las escrituras documentadas y revertidas):
1. Backup de los 34 `cd_prestador_id` (tabla temporal) + snapshot exacto (`SELECT *`) de las
   3 liqs de SM TUCUMAN y sus 88 incidentes / 25 alertas / 1 observación / 2 vínculos.
2. `UPDATE` → `cd_prestador_id = NULL` en los otros 33.
3. Click real en "↻ Sincronizar CD" del dashboard (Chromium, capturas 01-03).
4. Resultados: 1ª corrida `{creadas:23, yaExistentes:0, sinPrestador:0}`;
   2ª `{creadas:0, yaExistentes:23, sinPrestador:0}`.
5. Verificaciones: aditividad (diff=0 en 5 tablas), auto-vínculo (23/23 al prestador
   correcto por `cd_prestador_id`, sin matching por nombre), estado `abierta` 23/23, motor
   corrido al crear, dedup roto (H-1), vacías por 502 (H-2), paridad WS↔CSV (`3911-1` ==
   `3911-8` en incidentes e importe).
6. Limpieza: `DELETE` de las 23 creadas (cascade DB), restore de los 34 vínculos, drop de
   temporales. Estado final == inicial: `35 liqs / 1857 incidentes / 763 alertas / 22 obs /
   34+34 vínculos`.

Solo-lectura contra AyC: las únicas operaciones SOAP invocadas en todo el ejercicio fueron
`getTopLiquidations` y `getLiquidationDetails` (visibles en el log zeep del contenedor).

Histórico disponible por prestador (sonda `Top=200`, muestra de 15):
SAN JUAN 189 · PENTACOM 131 · SUPERNOVA 132 · MENDOZA 136 · INFOMAC 131 · JUJUY 115 ·
CDU 84 · CHACO 81 · CHIVILCOY 54 · FORMOSA 50 · CATAMARCA 43 · TANDIL 25 · SM TUCUMAN 23 ·
BAHIA 21 · JUNIN 13 → **1.228 en 15 de 34 prestadores** (base de H-5).

## FASE 4 — Motor de reglas

- Catálogo real: 8 activas (ALT006 inactiva); ALT007 activa sin evaluador (H-8). Las 763
  alertas y 22 observaciones están todas `pendiente` (la TL aún no gestiona estados).
- **ALT001 verificada a mano**: alertas de `3876-6` (SAN JUAN) esperan preventivo $25.126 /
  correctivo $50.231; el tarifario vigente al 2026-06-12 en DB dice exactamente eso
  (vigencia 2026-04-01→2026-06-30, zona genérica); cobrado $1 (regla Centro Cívico) →
  `diferencia` del `datos_contexto` exacta.
- **ALT002 + cambio ceil (commit `1b562e4`)**: caracterización verde (34 tests, incl.
  `test_kms_decimal_cobrado_ceil_no_dispara`). El caso objetivo del fix funciona
  (`830327-7`: 76 cobrado vs 75.7 → ceil 76, sin alerta). Pero ver H-4: en `3849-2` el
  reanálisis real pasó de 8 a 10 alertas por los casos piso/decimal-exacto.
- **Idempotencia del reanálisis**: 2 × `POST /reanalyze` sobre `3849-2` → ambos
  `{totalIncidentes:82, totalAlertas:10, totalObservaciones:0}`; no acumula ni duplica
  (`replace_for_liquidacion` borra por `liquidacion_id` antes de insertar, scoped).
- `datos_contexto` serializa a JSONB sin errores (las 10 alertas persistidas incluyen ALT005
  con `spst_id` string). El motor no traga excepciones (cero try/except en
  `motor_reglas/`).
- La liquidación `3849-2` quedó **restaurada byte a byte** desde el snapshot (diff=0 en
  liq/incidentes/alertas) — el estado de la TL no cambió.

## FASE 5 — Simulación E2E (Chromium, frontend real en :3000)

Sesión: cookie `hdm_session` de una sesión admin minteada en DB (revocada al cierre).

1. `01-dashboard-pre-sync.png` — dashboard con datos reales.
2. `02-sync-1-resultado.png` — toast **"Sync OK — 23 nuevas, 0 ya existentes"** + las filas
   nuevas de SM TUCUMAN `abierta` en "Últimas liquidaciones" (KPIs recalculados: 58 liqs,
   2.321 incidentes, $114.632.313,13 — consistentes con 35+23 y la suma de importes).
3. `03-sync-2-idempotencia.png` — segundo click: "0 nuevas, 23 ya existentes", sin filas
   nuevas.
4. `04-dashboard-estado-real.png` — estado final tras la limpieza (35 liqs).
5. `05-siges-modal-dryrun.png` — modal "Sincronizar con Siges": dry-run automático al abrir,
   0 cambios de campos espejo, 2 nombres distintos informativos, "Aplicar sync"
   **deshabilitado** (nada que aplicar — coherente). El sync real se disparó por API
   (`dryRun=false`): mismo resultado, 0 escrituras.
6. `07-detalle-3849-2.png` — detalle SUPERNOVA `3849-2`: **82 incidentes / 8 alertas /
   $4.579.691,60 / Cerrada** == DB (`total_incidentes=82, total_alertas=8,
   total_importe=4579691.6`) == `SUM(costo_total_cobrado)` de sus incidentes
   (4.579.691,60). Incidente `834702-2` marcado CON ALERTAS (su ALT005 restaurada), link
   webagentes `3849-2 ↗` presente.

Cruce a mano de 2 reglas (punto 4 del flujo): ALT001 (arriba) y ALT002 (`832521-5`:
|71 − ceil(71.3)| = 1 > 0.5 → alerta; `832133-4`: |178−177| = 1 > 0.5 → alerta) — UI, DB y
cálculo manual coinciden.

## Escrituras reales realizadas (todas revertidas o inocuas)

| Escritura | Reversión |
|---|---|
| Sesión admin en `user_session` (user_agent `validacion-pipeline-2026-08-13`) | Revocada al cierre (DELETE) |
| 33 × `cd_prestador_id = NULL` temporales | Restaurados desde backup — verificado 34/34 |
| 23 liquidaciones creadas por el sync controlado (+incidentes/alertas) | DELETE con cascade — conteos finales == iniciales |
| 2 × reanálisis de `3849-2` (8→10 alertas) | Restaurada desde snapshot — diff=0 |
| Sync Siges real (`dryRun=false`) | 0 cambios — no escribió nada |
| Tablas temporales `val_*`, `val2_*`, `cd_backup_validacion_20260813` | DROP |

## Recomendaciones (no aplicadas — decisión posterior)

1. **H-1**: portar `numeracion_ayc` (pesos 3-1-3-1) del legacy al gateway o a un servicio de
   dominio, con los 160 casos parametrizados del legacy como caracterización; re-verificar
   contra los 35 números reales (35/35).
2. **H-2**: en `_procesar`, si `get_incidentes` devuelve `[]` pero `cd_liq.cant_incidentes > 0`,
   **no crear** la liquidación (contarla en un nuevo `fallidas` del resultado) — el dato ya
   viene en el VO.
3. **H-3**: contar los prestadores sin `cd_prestador_id` en `sin_prestador` (y considerar
   exponer los omitidos por nombre).
4. **H-4**: confirmar con la TL si "cobrar el piso de un km decimal" debe alertar; si no,
   tolerancia sobre `max(|cobrado−esperado_raw|, |cobrado−ceil|)` o documentar la decisión
   en el ADR/P1.
5. **H-5**: considerar sync por prestador (`?prestadorId=`) o al menos loguear progreso; con
   H-1/H-2 corregidos, evaluar reintroducir un dry-run (el argumento "no hay nada que
   proteger" quedó refutado por esta validación).
6. Actualizar MIGRACION_ESTADO (33→34 vinculados) y marcar el pendiente #1 como **bloqueado
   por H-1/H-2**.

---

## Estado de hallazgos tras las correcciones (2026-08-13, sesión posterior)

Todos los hallazgos se corrigieron el mismo día (sin tocar la decisión de los ADR,
solo la implementación). Detalle técnico en el Addendum de ADR-015 y en ADR-016.

| Hallazgo | Fix | Verificación |
|---|---|---|
| H-1 numeración | Nuevo servicio de dominio `numeracion_ayc.py` (pesos 3-1-3-1, port del legacy) usado por el gateway; caracterización con los 35 números reales + 3 confirmados contra SOAP (`test_numeracion_ayc.py`, 71 casos) | Re-corrida controlada SM TUCUMAN vía botón del dashboard: `creadas=20, yaExistentes=3` (antes `23/0`) — las 3 liqs CSV reconocidas, **0 duplicados**, los 20 números creados con dv correcto (`3089-8`, `3894-2`, …). Capturas `08-fixes-sync-1.png`/`09-fixes-sync-2-idempotencia.png` |
| H-2 liqs vacías | `_procesar` no crea si el detalle vuelve vacío con `CantIncidentes > 0` declarado; se cuenta en `fallidas` (campo nuevo del resultado y del toast) y se reintenta en el próximo sync | Unit `test_detalle_vacio_con_incidentes_declarados_no_crea_y_cuenta_fallida`; re-corrida real: `fallidas=0`, **0 liqs con `total_incidentes=0`** (la corrida pre-fix había dejado 2) |
| H-3 sinPrestador | Cuenta real de activos sin `cd_prestador_id` | Re-corrida: `sinPrestador=33` (los 33 desvinculados temporalmente); unit dedicado |
| H-4 ALT002 ceil | Tolerancia contra el valor crudo **y** el ceil (alcanza una); docstring documenta ambas formas válidas de facturar | 2 units nuevos (piso 71 vs 71.3; decimal exacto con tolerancia 0); los 36 tests del motor verdes |
| H-5 operación | `POST /sincronizar?prestadorId=` opcional + log por prestador (`sync CD %s: …`) | `curl` con el UUID de SM TUCUMAN → `{creadas:0, yaExistentes:23}`; unit del filtro |
| H-6 inactivos | `list_con_cd_id()` filtra `activo=true` (impl + contrato del Protocol + fake) | Unit `test_prestador_inactivo_con_cd_id_queda_fuera` |
| H-7 §4 | `_liq_csv.py` separado en imports (282 líneas) + `_liq_csv_export.py` (95), funciones de 51/44 líneas descompuestas; el resto de la deuda 21–37 líneas queda aceptada y documentada en **ADR-016** | wc -l: 282/95, ningún archivo >300; gates verdes |
| H-8 ALT007 | Migración `b9f2d47c8e11`: `activa=false` (sin evaluador, igual que legacy — la fidelidad al snapshot de prod cede ante la confusión operativa) | DB: `ALT007 activa=f`; `alembic current` = `b9f2d47c8e11 (head)` |
| Sospecha parser | Los `continue` de `_parse_liquidaciones` ahora loguean warning con el item descartado | Código; sin caso real que lo dispare |

Gates post-fix: lint-imports 19/19 · ruff · mypy (927 archivos) · **1098 unit** (+80).
Escrituras de la re-verificación: mismas del protocolo original (vínculos
temporales + 20 liqs creadas y borradas + sesión admin temporal), todas revertidas
— estado final de DB `35/1857/763/22, 34+34 vínculos`, ALT007 inactiva como único
cambio persistente de datos (intencional, por migración).
