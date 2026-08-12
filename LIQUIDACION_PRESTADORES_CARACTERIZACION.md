# Caracterización — Liquidacion-Prestadores (legacy)

Reconocimiento previo a migrar el módulo (Fase 3 de `INTEGRACION_APPS_PLAN.md`), hecho
leyendo la documentación funcional del repo legacy (`Docs importantes/`) y cruzándola
contra el código real (`backend/app/`, `frontend/app/`) — no se toma ningún documento
como verdad sin verificar contra código, varios están desactualizados (ver §4).

Repo legacy: `C:\Users\imartinez.CDSA\Desktop\Proyectos\Liquidacion-Prestadores`
(Next.js 14 + FastAPI + SQLAlchemy + SQLite, sin Alembic, sin auth, CORS abierto).

## 1. Qué hace la app

Asistente de validación de preliquidaciones de 4 PST (Pentacom/Córdoba,
Pertex-Supernova/Rosario, Infomac/Villa Mercedes+Gral. Roca-Neuquén, Gestión
Integral/San Juan). Reemplaza el control manual de una Team Leader cruzando el CSV
exportado del sistema web contra 4 planillas Excel distintas.

Flujo: Prestador genera preliquidación → CSV → Importación → Motor de reglas →
Alertas/Observaciones → Team Leader revisa y resuelve → prestador corrige → nueva
liquidación → reanálisis.

## 2. Arquitectura real del backend (4.434 líneas, 62 archivos `.py`)

Ya tiene separación por capas (no es un `main.py` monolítico):

```
backend/app/
├── api/routers/     ← presentación (7 routers: prestadores, spst, tarifarios,
│                       tabla_km, liquidaciones, liquidaciones_ws, dashboard)
├── core/            ← dominio: motor_reglas.py, numeracion_ayc.py,
│                       evaluadores/ (7 evaluadores ALT001-009, Strategy pattern),
│                       puertos/ (2 interfaces abstractas)
├── models/          ← 10 modelos SQLAlchemy
├── schemas/         ← Pydantic por área
├── importers/       ← CSV, Excel, sync WS (orquestación de casos de uso)
├── services/ws_ayc/ ← cliente SOAP (zeep) hacia el WS externo AyC
├── database.py, db_migraciones.py (migraciones aditivas a mano, sin Alembic)
└── main.py          ← bootstrap, CORS abierto, create_all
```

Mapeo sugerido a domain/application/infrastructure/presentation del monorepo nuevo:
`models/` + `core/evaluadores/` + `core/motor_reglas.py` → domain · `importers/` →
application · `services/ws_ayc/`, `database.py` → infrastructure · `api/routers/` +
`schemas/` → presentation.

Sin autenticación de ningún tipo, CORS `allow_origins=["*"]`. Sin scheduler/cron/
APScheduler en ningún punto del backend — el motor de reglas corre **sincrónicamente
dentro del request HTTP** al importar o reanalizar, no como job de fondo.

### Endpoints (≈30, por router)
- **`/prestadores`**: CRUD + `POST /sync-ws` (crea/vincula desde AyC, nunca sobreescribe
  campos ya vinculados) + `POST /importar-excel` (plantilla legacy PST completa).
- **`/spsts`**: CRUD estándar, filtro `prestador_id`.
- **`/tarifarios`**: CRUD + plantilla Excel + import Excel (rebuild de cadena temporal
  de vigencias en cada write).
- **`/tabla-km`**: CRUD + plantilla Excel + import Excel (crea SPST on-the-fly).
- **`/liquidaciones`**: listar/detalle/importar CSV/cambiar estado de
  observación/reanalyze/cambiar estado de liquidación/delete.
- **`/liquidaciones/ws`**: disponibles/preview/importar/sync/enriquecer/prepoblar-tabla-km
  — router separado a propósito del flujo CSV.
- **`/dashboard/stats`**: totales + últimas 8 liquidaciones.
- **Sin router `reglas.py`** — existe el modelo/schema pero no hay CRUD expuesto; la
  única forma de tocar `reglas_alerta` hoy es DB directa o re-correr `seed.py`.

### Modelo de datos (10 tablas)
`Prestador` 1:N `SPST` 1:N `TablaKM` (también `Prestador`→`TablaKM` directo) ·
`Prestador` 1:N `Tarifario` (por `tipo_servicio`×`zona`×vigencia) · `Prestador` 1:N
`Liquidacion` 1:N `Incidente` 1:N `Alerta` 1:N `Resolucion` · `Liquidacion` 1:N
`Observacion` N:M `Incidente` (vía `ObservacionIncidente`, con `rol`) · `ReglaAlerta`
(catálogo de reglas, standalone).

`empresa_nombre`/`sucursal_nombre` son **texto libre comparado con `ilike`**, no FKs a
entidades Cliente/Sucursal — distinto del modelo conceptual que describen los docs.

Campos de integración AyC ya presentes en varias tablas: `Prestador.ayc_tecnico_id`,
`SPST.ayc_tecnico_id`, `TablaKM.ayc_sucursal_id`/`kms_pendientes`,
`Liquidacion.origen`(csv|ws)/`ayc_liquidacion_id`,
`Incidente.ayc_incidente_id`/`ayc_tecnico_id`/`costo_servicio_acuerdo`/`costo_km_acuerdo`.

### Tests
192 passed (backend/tests), sesgados casi enteramente a la integración WS AyC
(numeración módulo-10: 160 casos parametrizados, mapeo, ws_importer). **Sin cobertura
automatizada de los evaluadores ALT001-009, de los routers CRUD, ni del motor de
reglas en sí** — cualquier regresión ahí no tiene red de seguridad hoy.

## 3. Motor de reglas — catálogo real (fuente de verdad: `backend/seed.py`, no los docs)

| Código | Nombre | Riesgo | Config | Activa | Evaluador | Notas |
|---|---|---|---|---|---|---|
| ALT001 | Precio Incorrecto | 100 | `{}` | Sí | `alt001_precio.py` | Tolerancia `0.01` **hardcodeada**, no en config |
| ALT002 | KMs Incorrectos | 100 | `tolerancia_km: 0.5` | Sí | `alt002_km.py` | Ignora `kms_pendientes`; anti-falso-positivo por "corredor" (≤50km) |
| ALT003 | Posible Viático Duplicado | 80 | `ventana_dias: 30` | Sí | `alt003_viatico.py` | **`ventana_dias` es config muerta** — compara por fecha exacta, no por ventana |
| ALT004 | Servicio Duplicado | 90 | `{}` | Sí | `alt004_duplicado.py` | Mismo `numero_incidente` en cualquier otra liquidación del prestador |
| ALT005 | Ruta Compartida | 40 | `{}` | **No** (desactivada) | `alt005_ruta.py` | El más elaborado (agrupa por corredor, severidad dinámica); apagada por default pese a ser la de mayor dolor operativo real (RN006) |
| ALT006 | Segunda Visita | 30 | `ventana_dias: 30` | No | **No existe** | Fila fantasma, nunca se ejecuta |
| ALT007 | Agrupación de Incidentes | 40 | `{}` | No | **No existe** | Fila fantasma, nunca se ejecuta |
| ALT008 | Tarifario Inexistente | 100 | `{}` | Sí | `alt008_tarifario.py` | El FDD llama "SPST No Determinado" a este código — está invertido respecto al código real |
| ALT009 | Par Empresa-Sucursal no encontrado en Tabla KM | 80 | `{}` | Sí | `alt009_spst.py` | Ídem, invertido respecto al FDD |

**Es data-driven solo a medias.** Sí vienen de `reglas_alerta`: activación, riesgo base,
algunos umbrales. NO: el algoritmo de cada evaluador (clases Python fijas), el registro
`EVALUADORES` (dict hardcodeado en `motor_reglas.py`, agregar ALT010 requiere código),
`UMBRAL_CORREDOR_KM=50` (constante duplicada en 2 archivos con comentario "must match"),
tolerancia de ALT001. La promesa de `ARQUITECTURA_FUNCIONAL.md` ("la TL ajusta
comportamiento sin pedir desarrollo") no está implementada — no hay API de reglas.

Las reglas de negocio de dominio completas (RN001-RN016: tarifas por tipo/zona,
Pre-Correctivo/Centro Cívico a $0,01, doble tarifa instalación en San Juan, umbral de
viático variable por excepción, SLA/descuentos **nunca implementado ni encontrado en
código**, estructura INFOMAC con sub-totales) están en
`Liquidacion-Prestadores/Docs importantes/ANALISIS_FUNCIONAL_LIQUIDACION_PRESTADORES.md`
entregable 4 — leer ese documento antes de portar el motor, no re-derivar desde cero.

## 4. Integración WS AyC — no mencionada en ningún doc funcional, no está en producción

Hallazgo importante: existe una integración SOAP completa (`services/ws_ayc/`, `zeep`)
que ninguno de los 5 documentos funcionales menciona — cambia el alcance real de lo que
esos docs llaman "Fase 2 (futuro)": ya está construida.

- **No está activa en producción** — triple confirmado: vive en la rama
  `feature/ws-ayc-liquidaciones` (no mergeada a `main`), `WS_AYC_ENABLED` default
  `False`, el `docker-compose.yml` de producción no define esa variable.
- **Sin scheduler** — todo el sync es manual, vía botón (una liquidación puntual) o
  `curl`/`/docs` (`POST /liquidaciones/ws/sync`, sin botón en UI).
- **Dígito verificador módulo-10** (`core/numeracion_ayc.py`): dígitos del `id` de AyC
  de izquierda a derecha, pesos alternados 3-1-3-1…, `(10 - suma%10) % 10`. Número final
  `"{id}-{dígito}"`. Permite que CSV y WS convivan sin romper la dedup de ALT004.
- **El riesgo de "pisar el estado local"** (ADR-001 punto 4) es real como decisión de
  diseño consciente, pero la vía de disparo hoy es *manual y rara*: el sync automático
  (`/liquidaciones/ws/sync`) solo **agrega** liquidaciones nuevas, nunca reimporta una
  existente. Lo que sí pisa (borra la fila y la recrea con el estado que reporte AyC,
  perdiendo observaciones por `cascade="all, delete-orphan"`) es la reimportación manual
  forzada (`sobrescribir=true`), que **no tiene botón en el frontend** — solo alcanzable
  por API directa. El riesgo se vuelve serio el día que se automatice un re-sync
  periódico; ese mecanismo de reconciliación de estado (separar estado-workflow-TL de
  estado-AyC en dos columnas, hoy es una sola `Liquidacion.estado`) queda sin resolver
  y hay que diseñarlo antes de automatizar, no asumir que el código actual ya lo cubre.
- Limpieza de datos pendiente en el backfill real: ~29 prestadores creados fuera de
  alcance real del negocio, 1 SPST sin PST padre reconocido, 1 duplicado
  (PERTEX/SUPERNOVA) sin resolver.

## 5. Frontend (Next.js 14, App Router, todo `"use client"`)

9 rutas: `/` (dashboard), `/liquidaciones` (listado), `/liquidaciones/nueva` (import
CSV), `/liquidaciones/importar-ws`, `/liquidaciones/[id]` (detalle, 634 líneas — la
pantalla más grande), `/configuracion/{prestadores,spst,tarifarios,tabla-km}` (CRUD +
import/export CSV/Excel, patrón repetido en las 4).

Sin librería de componentes (no shadcn/Radix/HeadlessUI) — JSX + Tailwind a mano,
`lucide-react` para iconos, `clsx`. Fetch manual sobre `fetch` nativo (`lib/api.ts`, sin
axios/react-query), parser/exportador CSV casero (`lib/utils.ts`, sin papaparse).

Paleta de marca en `tailwind.config.ts`: `brand.{50-900}` (naranja, 600 `#F7941D`
primario) y `graybrand` (`DEFAULT #58595B`, `light #E2E6E6` fondo general) — **misma
línea Institucional de Canal Directo** que ya rige toda la app unificada
([[feedback_brand_purity_canal_directo]] en memoria), así que no hay conflicto de marca
al portar, solo aplicar los primitivos ya establecidos del monorepo nuevo en vez de
recrear esta paleta aparte.

`components/tarifarios/` (card agrupadora + timeline de vigencias + modal) y
`components/ui/ObservacionCard.tsx` son los únicos componentes con lógica no trivial
para portar con handoff propio.

## 6. Decisiones de alcance — resueltas (2026-08-12)

1. **WS AyC: FUERA de alcance de esta migración.** Confirmado por el usuario y
   verificado en vivo contra los contenedores de producción reales
   (`liquidacion-prestadores-backend-1`/`-frontend-1`, puertos 8002/3002): el backend
   productivo (imagen creada 2026-07-02, **antes** de que existiera cualquier commit de
   WS AyC) **no tiene ninguna ruta `/liquidaciones/ws/*`** (`GET
   /liquidaciones/ws/disponibles` → 404, no aparece en su `openapi.json`). El frontend
   sí se reconstruyó más reciente (imagen 2026-08-11) y **sí sirve**
   `/liquidaciones/importar-ws` (200 OK) — es una página muerta hoy: apunta a endpoints
   que el backend real no implementa. Todo el trabajo de `services/ws_ayc/`,
   `core/numeracion_ayc.py`, `importers/ws_importer.py`, `importers/entidad_sync.py` y
   los campos `ayc_*` del modelo (§4) vive en la rama `feature/ws-ayc-liquidaciones`
   (checked out en el filesystem del repo legacy, por eso los 3 agentes de
   reconocimiento la vieron) — es un experimento propio del usuario para automatizar
   más la app, no lo que la Team Leader usa. **No portar nada de §4 en esta migración.**
   El módulo `liquidaciones` del monorepo nuevo caracteriza y migra el flujo CSV tal
   como corre hoy en producción real.
2. **ALT005/ALT006/ALT007: portar tal cual.** ALT005 se porta pero queda desactivada
   por default (igual que hoy); ALT006/ALT007 se documentan como no implementadas, sin
   evaluador — no se completan en esta migración.
3. **Motor de reglas: mantener el patrón híbrido actual.** Evaluadores como código
   Python + algunos parámetros en tabla de config, igual que el legacy — no se invierte
   en un motor interpretado ni en CRUD de reglas en esta migración.

**Nota importante sobre qué código es "el legacy real" a caracterizar de acá en más:**
dado que WS AyC queda afuera, el código de referencia para el resto de la migración es
el que corre en producción hoy (backend ~commit `de23969`/`0e4e1b2`, antes de la rama
WS AyC), no el checkout actual de `feature/ws-ayc-liquidaciones` ni siquiera el HEAD de
`main` (que en realidad ya tiene un commit — `e94de85`, 2026-08-04 — no desplegado
todavía, aunque ese commit específico tampoco toca el flujo CSV). Antes de asumir el
comportamiento de un endpoint/regla como "lo que hace producción", verificar contra los
contenedores reales (`localhost:8002`/`:3002`) igual que se hizo acá, no solo contra el
código fuente — ya hubo una discrepancia real (frontend con página muerta) que el
código fuente solo no hubiera revelado.

## 7. Tests de caracterización del motor de reglas (2026-08-12) — 22/22 verdes

Escritos y corridos contra `main` del legacy en un worktree aislado (`C:/wt/liq-main`,
`git worktree add ... main` desde el repo legacy — no toca el checkout del usuario en
`feature/ws-ayc-liquidaciones` ni los contenedores de producción reales). Archivos
nuevos (sin commitear, pendiente decidir si se incorporan al repo legacy):
`C:/wt/liq-main/backend/tests/conftest.py` y
`C:/wt/liq-main/backend/tests/test_motor_reglas_caracterizacion.py`. Verificado de
forma independiente (releído el código de ALT003 y `seed.py` a mano, y re-corrida la
suite): **22 passed**.

Todos los tests corren `ejecutar_motor()` de punta a punta (no las clases evaluador
sueltas), así que reflejan el comportamiento real de producción incluido el filtro
`ReglaAlerta.activa==True`.

| ALT | Caso sin alerta | Caso con alerta | Riesgo | Nota |
|---|---|---|---|---|
| ALT001 Precio Incorrecto | cobrado==tarifario; diferencia=exactamente 0.01 (tolerancia estricta `>0.01`) | cobrado 1800 vs tarifario 1500 | 100 | Descripción con formato moneda **en-US** (`$1,800.00`, coma miles/punto decimal), no es-AR |
| ALT002 KMs Incorrectos | dentro de tolerancia 0.5 | 60 vs esperado 100, sin ruta compartida | 100 | — |
| ALT002 ruta compartida | — | incidente cobrado=0 se **suprime** correctamente cuando hay otro del mismo corredor/día ya cobrado; el otro incidente sí dispara la suya | — | Confirma que la heurística anti-falso-positivo funciona |
| ALT003 Viático Duplicado | fechas distintas | mismo día + misma sucursal, 2 incidentes con km>0 | 80 | Genera **2 alertas mutuas** (una por incidente), no una compartida |
| ALT003 `ventana_dias` | — | dos incidentes a 5 días (dentro de la ventana de 30) → **0 alertas** | — | **Confirmado empíricamente: `ventana_dias` es config muerta**, el evaluador compara `fecha_cierre` exacto, nunca lee `self.regla.configuracion` (releído el código fuente, línea por línea, no hay ninguna referencia a `configuracion` en `alt003_viatico.py`) |
| ALT004 Servicio Duplicado | numero_incidente único | mismo `numero_incidente` en 2 liquidaciones del mismo prestador | 90 | — |
| ALT005 Ruta Compartida | 1 solo incidente en el corredor | `activa=True` forzado + 2 incidentes mismo corredor, suma cobrada > tabla | Observacion `CRITICO` | Mismo escenario con `activa=False` (**default real, confirmado en `seed.py`**) → 0 observaciones pese a ameritarlo |
| ALT008 Tarifario Inexistente | tarifario existe para tipo/fecha | tarifario existe pero para otro `tipo_servicio` | 100 | — |
| ALT009 Par Empresa-Sucursal | fila TablaKM con el par exacto | sin fila para el par | 80 | Si `cant_km_cobrado==0`, **nunca dispara** aunque no exista la fila — corta antes de buscar, pese a que el nombre de la regla sugiere validación siempre |

**Comportamientos transversales del motor confirmados:**
- Regla `activa=False` → ni se instancia el evaluador (filtrado en la query SQL de
  `reglas_alerta`).
- `ejecutar_motor` es idempotente: correrlo 2 veces sobre la misma liquidación borra
  alertas/observaciones previas antes de recalcular, no las acumula ni duplica.
- Liquidación inexistente → `{"error": "..."}`, no excepción.

**Hallazgo nuevo, no detectado en la ronda de documentación (§1-6):** `motor_reglas.py`
traga excepciones en silencio en las dos fases de evaluación
(`except Exception: continue`, confirmado leyendo el archivo — no se pudo ejercitar con
un test sin tocar código fuente, prohibido en esta ronda). Un evaluador que rompe por un
dato mal formado no deja ningún rastro: simplemente no genera esa alerta/observación, sin
loguear nada. **Al portar el motor de reglas al monorepo nuevo, esto viola directamente
§6 de `ARCHITECTURE_GUIDE.md`** (ningún `except Exception` puede quedar en silencio) —
no replicar tal cual; loguear con `logging.getLogger(__name__)` y contexto (regla,
incidente, excepción) en el punto donde se atrapa, aunque el legacy no lo hiciera.

## 8. Referencias

- `Liquidacion-Prestadores/Docs importantes/ADR_001_integracion_ws_ayc.md` — riesgos y
  correcciones a los docs de diseño originales del WS AyC.
- `Liquidacion-Prestadores/Docs importantes/PENDIENTE_WS_AYC.md` — gaps conocidos del
  WS AyC (funcionalidad sin UI, limpieza de datos, automatización).
- `Liquidacion-Prestadores/Docs importantes/ANALISIS_FUNCIONAL_LIQUIDACION_PRESTADORES.md`
  — reglas de negocio RN001-RN016 completas, riesgos de implementación heredados del
  proceso Excel.
- `Liquidacion-Prestadores/Docs importantes/FDD.md` — actores, proceso TO-BE (ojo:
  numeración ALT008/ALT009 invertida respecto al código real).
- `Liquidacion-Prestadores/Docs importantes/BACKLOG.md` — épicas MoSCoW, US-001 a
  US-081 (ojo: numeración ALT006 usada dos veces con significados distintos, error de
  redacción propio del doc).
- `Liquidacion-Prestadores/Docs importantes/ARQUITECTURA_FUNCIONAL.md` — principio
  "no hardcodear reglas de negocio", parcialmente incumplido (ver §3).
