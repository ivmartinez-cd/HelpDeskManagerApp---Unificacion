# Auditoría de cumplimiento de ARCHITECTURE_GUIDE.md — 2026-08-14

Alcance: todo el repo (backend `src/modules/*` + `src/shared/`, frontend `src/`).
Método: medición con herramientas (import-linter, ruff, mypy, pytest --cov, scripts AST,
tsc, eslint, grep dirigido), no lectura impresionista. Cada número sale del comando que lo
acompaña, corrido en esta sesión. Sin cambios de código.

Condiciones de la corrida: `DISABLE_BACKGROUND_JOBS=true` verificado con
`docker exec helpdesk-manager-backend printenv DISABLE_BACKGROUND_JOBS` → `true`, y cero
líneas `background_jobs: N job(s) iniciados` en el log del contenedor. `helpdesk-db-test`
se levantó para la corrida de integración (estaba apagado) y queda corriendo.

Los 16 ADRs (`docs/adr/001`–`016` — nota: viven en `docs/adr/`, no en `backend/docs/adr/`)
se leyeron completos antes de clasificar hallazgos. `stc` y `parque_impresoras` son
placeholders vacíos (solo `__init__.py` de 0 líneas) — quedan fuera de la matriz.

---

## FASE 1 — Números duros

### §2/§3 Capas y módulos — `uv run lint-imports` (en el contenedor)

```
Analyzed 926 files, 3892 dependencies.
Contracts: 19 kept, 0 broken.
```

Los 19 contratos KEPT: domain-no-frameworks para auth, contadores, insumos, turnos, sla,
prestadores, liquidaciones y vacaciones; independencia domain/application respecto de auth
para los 7 módulos de negocio; independencia contadores↔insumos; y la excepción
unidireccional de ADR-007 en ambas direcciones. `stc`/`parque_impresoras` no tienen
contrato porque no tienen código.

### Gates de calidad

| Gate | Comando | Resultado |
|---|---|---|
| Lint backend | `uv run ruff check src tests` (reglas E,F,I,UP,B,SIM,N) | All checks passed |
| Tipos backend | `uv run mypy src` | Success: no issues in 928 files |
| Unit (contenedor) | `uv run pytest tests/unit -q` | 1098 passed |
| Suite completa (host, con db-test) | `uv run pytest tests -q --cov=src` | 1288 passed |
| Tipos frontend | `npx tsc --noEmit` (contenedor frontend) | exit 0, sin errores |
| Lint frontend | `npx eslint src --max-warnings=0` | exit 0; `react-hooks/set-state-in-effect` confirmada activa vía `--print-config` |

Nota operativa (no hallazgo de arquitectura, sí trampa de método): los tests de
integración **no corren dentro del contenedor** — `tests/integration/infrastructure/conftest.py:12`
hardcodea `localhost:{DB_TEST_PORT}` y desde el contenedor `localhost:5440` no resuelve
(154 errors de conexión). Corren desde el host contra `helpdesk-db-test` (5440). El único
knob es el puerto, no el host.

### §4 Tamaños — script AST sobre `backend/src` (span físico, `end_lineno - lineno + 1`)

Totales crudos: funciones >20: **272** · clases >200: **2** · archivos >300: **6** ·
firmas >3 params: **252** · anidamiento >3: **4**.

Separando migraciones Alembic (`migrations/versions/`, que concentran los `upgrade()`
gigantes): **25** funciones >20 son migraciones; quedan **247** en código real, con esta
distribución (21–30 / 31–50 / >50 líneas):

| Módulo | 21–30 | 31–50 | >50 | Total | Clases >200 | Archivos >300 (no migración) |
|---|---|---|---|---|---|---|
| insumos | 75 | 23 | 4 | 102 | 1 (`SqlAlchemyAuditStatisticsRepository`, 215) | 2 (`get_dashboard.py` 327, `list_pending_orders.py` 305) |
| liquidaciones | 33 | 8 | 0 | 41 | 0 | 0 |
| contadores | 24 | 10 | 3 | 37 | 1 (`HttpxSdsClientProvider`, 222) | 1 (`ftplib_db3_downloader.py`, 313) |
| vacaciones | 20 | 10 | 2 | 32 | 0 | 0 |
| prestadores | 12 | 5 | 0 | 17 | 0 | 0 |
| auth | 5 | 0 | 0 | 5 | 0 | 0 |
| turnos | 4 | 2 | 0 | 6 | 0 | 0 |
| sla | 5 | 0 | 0 | 5 | 0 | 0 |
| shared (sin migr.) | 1 | 0 | 1 | 2 | 0 | 0 |
| **Total** | **179** | **58** | **10** | **247** | **2** | **3** |

Las 10 funciones >50 líneas (complejidad real, no firmas largas):
`contadores/infrastructure/sds/httpx_sds_client_provider.py:54 export_meters_to_csv` (106),
`contadores/infrastructure/ers/httpx_ers_client_provider.py:67 export_meters_to_csv` (85),
`insumos/infrastructure/repositories/sqlalchemy_request_alert_repository.py:25 sync_pending` (67),
`contadores/infrastructure/ers/httpx_ers_token_refresher.py:23 refresh_ers_token` (65),
`insumos/domain/services/zone_contact_import.py:46 preview_zone_contacts` (65),
`shared/presentation/app.py:128 create_app` (64),
`insumos/application/use_cases/list_audit.py:62 _row_from` (58),
`vacaciones/application/use_cases/decidir_solicitud.py:55 execute` (58),
`insumos/application/use_cases/verify_offline_devices.py:79 _run` (52),
`vacaciones/application/use_cases/gestionar_solicitudes.py:189 execute` (52).

Anidamiento >3 (los 4, todos profundidad 4): `httpx_ers_client_provider.py:33` y `:67`,
`ftplib_db3_downloader.py:270`, `insumos/domain/services/availability_windows.py:33`.

Params >3 (252): concentrados en endpoints FastAPI (parámetros `Depends`/`Query`
inyectados — idiom del framework, no un objeto agrupable real) y constructores/firmas
keyword-only de repos y schemas de muchas columnas. Nomenclatura: cubierta por
herramienta (ruff `N` activo, 0 hits) + ADR-006 (snake_case en paquetes Python).

Frontend, archivos >300 líneas (find + wc): **9**, máx. 459
(`insumos/components/dashboard/consumable-detail-modal.tsx`); resto entre 308 y 450.
No se midió AST de funciones/componentes TS en esta pasada (no medido, no afirmado).

### §5 Dependencias — grep de terceros en domain/application

```
grep -rnE "^(import|from) (zeep|pyodbc|pandas|httpx|sqlalchemy|fastapi|pydantic|aiosmtplib|openpyxl|ftplib|alembic|dbf)" modules/*/domain modules/*/application shared/domain
→ 0 hits
```

Cero imports de librerías de terceros en `domain` y `application` de todos los módulos,
consistente con los 8 contratos domain-no-frameworks KEPT. Los adapters (zeep, pyodbc,
pandas, httpx, ftplib, openpyxl) viven todos en `infrastructure/` (o `presentation/` en el
caso documentado por ADR-010).

### §6 Manejo de errores — AST sobre todos los `except Exception`/`except:`

86 handlers amplios en `backend/src`, clasificados por su cuerpo:

| Clase | Cantidad |
|---|---|
| Relanzan (envuelven en error de dominio / `ExternalServiceError`) | 18 |
| Loguean en el punto de manejo | 66 |
| "Silenciosos" según el AST | 2 |

Los 2 "silenciosos" (`insumos/application/use_cases/load_order.py:87` y `:186`) delegan a
`_handle_creation_failed` (`load_order.py:123`), que hace `logger.exception(...)` y
registra el fallo en el resultado — **no hay ningún silenciamiento real**. Los `except`
de infraestructura de vacaciones (`email_notificador.py`, `sqlalchemy_auditoria.py`)
loguean con `exc_info` y su no-propagación es contrato comentado en el código (paridad
legacy / auditoría no rompe flujo), mismo patrón que ADR-010 documenta para
`LoggedMailDispatcher`.

### §7 Cobertura — `pytest tests -q --cov=src` (branch=true, unit+integración, 1288 tests)

Total: **79.0%**. Por capa global y contra los mínimos de la guía
(domain 90 / application 85 / infra 70 / presentation 60):

| Capa | Global | ¿Mínimo? |
|---|---|---|
| domain | 95.0% | ✅ |
| application | 86.3% | ✅ |
| infrastructure | **67.8%** | ❌ (<70) |
| presentation | 74.0% | ✅ |

Celdas módulo/capa **por debajo del mínimo** (el resto cumple):

| Módulo/capa | Cobertura | Mínimo |
|---|---|---|
| contadores/infrastructure | 49.9% | 70 |
| turnos/infrastructure | 50.6% | 70 |
| prestadores/infrastructure | 52.4% | 70 |
| sla/presentation | 58.4% | 60 |
| auth/application | 64.7% | 85 |
| sla/infrastructure | 68.9% | 70 |
| vacaciones/application | 70.6% | 85 |

Pirámide: unit 1098 + integración ~190 = proporción sana en la base, pero **no existe
suite e2e** (el mínimo de presentation que la guía define "60% (e2e)" se está midiendo acá
con tests de unit/integración, no e2e).

### §8 Seguridad

- **AuthZ**: script AST sobre los routers — **170 endpoints**; 167 llevan
  `require_permission`/`Identity` en la firma; los 3 restantes son pre-auth por diseño
  (`auth_router.py`: `logout`, `forgot_password`, `reset_password`).
- **SQL**: grep de f-strings/concatenación en queries → 3 hits, ninguno con input de
  usuario: 2 `server_default=text(f"'{CONSTANTE}'")` en `ftp_client_model.py:22,25`
  (constantes de módulo) y 1 `text(f"interval '{int(within_seconds)} seconds'")` en
  `sqlalchemy_supply_cache_repository.py:152` (coerción `int()` previa — sin vector).
  Todo lo demás es ORM/parametrizado (pyodbc con `?` en los gateways Siges).
- **Secretos**: grep de literales password/secret/api_key/token → 0 hardcodeados. `.env`
  y variantes en `.gitignore` (líneas 2–4); `.env.example` en la raíz.
- **XSS**: 1 único `dangerouslySetInnerHTML` en todo el frontend —
  `frontend/src/features/contadores/components/event-detail-modal.tsx:147` inyecta
  `event.content_tooltip` **sin sanitizar**. Ese HTML viene del scraping de Gestión
  (Symfony de terceros) vía sync → es contenido externo persistido que se renderiza crudo.
  Hallazgo (ver Fase 4). No hay DOMPurify ni equivalente en `package.json`.

### §11 Paginación y N+1

- `Page[T]` de `shared/presentation/schemas/pagination.py` se usa en **24 routers** (grep
  `Page[`), es el default real del repo.
- Endpoints que devuelven `list[...]` sin `Page[T]` (grep `response_model=list|-> list[`
  sobre presentation, excluyendo schemas y funciones no-endpoint): **8** —
  `insumos/customers_router.py`: `/customers` (:57), `/customers/{id}/contacts` (:103),
  `/customers/{id}/sds-contacts` (:168), `/customers/{id}/zones` (:180);
  `auth/admin_permissions_router.py`: catálogo de módulos (:53) y acciones (:63);
  `auth/auth_router.py:103` (módulos habilitados del usuario);
  `liquidaciones/liquidaciones_router.py:93` `/periodos` (`list[str]`).
  Todos son catálogos chicos, pero la excepción operativa de CLAUDE.md exige que el
  contrato siga siendo paginado — no lo es. Sin ADR (ADR-011 cubre solo el resumen de
  prestadores, que por eso **no** es hallazgo).
- N+1 (heurística AST: loops en `application/` con `await` de repo/gateway adentro):
  **39 hits**. Revisados por patrón: la gran mayoría son escrituras por fila en
  imports/syncs deliberadamente secuenciales (patrón ADR-014/015: todo pasa por el use
  case, no bulk) o llamadas SOAP por prestador que ADR-015 diseña así a propósito.
  Quedan como **sospecha** (sin medición de latencia) unos pocos reads por ítem sobre
  catálogos acotados: `vacaciones/gestionar_sectores.py:104,121` (`list_jefes` por
  sector), `vacaciones/gestionar_empleados.py:162`, `insumos/get_device_supplies.py:88`
  (`get_created_by_serial` por serie). Cardinalidades chicas (sectores/series de un
  equipo); ninguno es un hot path demostrado.
- Caching: el único cache identificado (`supply_cache`) usa ventana explícita en segundos
  (`within_seconds`) — expiración explícita, cumple. Índices por PR: no medible ex post.

### §9 Control de versiones

- Últimos 30 commits: **30/30 Conventional Commits** (`feat|fix|docs|chore(scope): ...`,
  imperativo, inglés).
- Flujo real: single-dev, commits directos a `main` (no existen ramas feature ni PRs en
  el remoto). Las reglas de PR de la guía (≤400 líneas, reviewer, CI verde) no aplican a
  este flujo; como dato: 4 de los últimos 12 commits superan 400 líneas cambiadas (524,
  531, 864, 1832 según `git log --shortstat`). Informativo, no bloqueante — pero es una
  desviación estructural del flujo Gitflow+PR que la guía describe, sin ADR que lo diga.

### §10 Documentación

- **16 ADRs** en `docs/adr/`, todos con Estado/Contexto/Decisión/Consecuencias, varios con
  addendums de validación adversarial (015) — por encima del estándar de la guía.
- README: existe en la raíz. **No hay `backend/README.md` ni `frontend/README.md`** — la
  guía pide README por proyecto con setup/tests/variables de entorno.

---

## FASE 2 — Veredicto por sección

| Sección | Veredicto | Evidencia |
|---|---|---|
| §1 Principios | CUMPLE (indirecto) | No medible directo; DIP verificada por lint-imports 19/19, SRP aproximada por tamaños (ver §4) |
| §2 Estructura | CUMPLE-CON-DESVIACIÓN-DOCUMENTADA | módulo→capa es ADR-003 (y la guía misma lo incorpora); snake_case ADR-006 |
| §3 Capas | **CUMPLE** | lint-imports 19 kept / 0 broken; excepciones acotadas con ADR (007, 009, 010) |
| §4 Convenciones/tamaños | **NO-CUMPLE (deuda parcialmente documentada)** | 247 funcs >20 (solo las 41 de liquidaciones tienen ADR-016; **206 sin ADR**), 2 clases >200, 3 archivos >300, 252 firmas >3 params sin ADR; nomenclatura sí cumple (ruff N limpio) |
| §5 Dependencias | **CUMPLE** | 0 imports de terceros en domain/application; uv.lock (ADR-001) |
| §6 Errores | **CUMPLE** | 86 handlers amplios: 18 relanzan, 66 loguean, 0 silenciamientos reales; jerarquía AppError en shared |
| §7 Testing | **NO-CUMPLE en mínimos** | 7 celdas módulo/capa bajo mínimo (peores: contadores/infra 49.9%, turnos/infra 50.6%, prestadores/infra 52.4%, auth/app 64.7%); sin suite e2e; sin ADR que ajuste los mínimos |
| §8 Seguridad | CUMPLE-CON-1-HALLAZGO | 167/170 endpoints con authz (3 pre-auth legítimos), SQL parametrizado, 0 secretos; 1 XSS potencial (tooltip sin sanitizar) |
| §9 Versionado | CUMPLE-CON-DESVIACIÓN-NO-DOCUMENTADA | Commits 30/30 convencionales; flujo sin PRs/review (single-dev) difiere del Gitflow de la guía sin ADR |
| §10 Documentación | CUMPLE-CON-DESVIACIONES | ADRs excelentes; faltan READMEs de backend/ y frontend/ |
| §11 Rendimiento | CUMPLE-CON-DESVIACIONES | Page[T] en 24 routers; 8 endpoints catálogo sin paginar sin ADR; N+1: sin casos confirmados en hot paths (39 hits heurísticos, mayoría por diseño documentado) |
| §12 Checklist PR | N/A como proceso | Sin flujo de PR; los ítems del checklist se auditan arriba sección por sección |

---

## FASE 3 — Matriz sección × módulo

VERDE = cumple con evidencia · AMARILLO = desviación menor o cubierta por ADR ·
ROJO = violación sin ADR con impacto real.

| Módulo | §2/3 capas | §4 tamaños | §5 deps | §6 errores | §7 cobertura | §8 seguridad | §11 paginación |
|---|---|---|---|---|---|---|---|
| auth | VERDE (contratos KEPT) | VERDE (5 funcs 21–30) | VERDE | VERDE | **ROJO** (app 64.7% < 85) | VERDE (3 endpoints pre-auth por diseño) | AMARILLO (3 catálogos `list[...]` sin Page) |
| contadores | VERDE | **ROJO** (37 funcs, 3 de >50, clase 222, archivo 313, 3 nest>3 — sin ADR) | VERDE | VERDE | **ROJO** (infra 49.9% < 70) | VERDE (backend; el XSS del tooltip es del frontend del feature) | VERDE (Page en 4 routers) |
| insumos | VERDE | **ROJO** (102 funcs, clase 215, 2 archivos >300 en application — sin ADR) | VERDE | VERDE | VERDE (todas las capas sobre mínimo) | VERDE | AMARILLO (4 endpoints customers sin Page) |
| liquidaciones | VERDE | AMARILLO (41 funcs 21–37, **cubierto por ADR-016**) | VERDE | VERDE | VERDE (app 99.2, dom 97.8, infra 82.3, pres 74.5) | VERDE | AMARILLO (`/periodos` list[str] sin Page) |
| prestadores | VERDE | AMARILLO (17 funcs, ninguna >50) | VERDE | VERDE | **ROJO** (infra 52.4% < 70) | VERDE | VERDE (resumen agregado = ADR-011; /operadores e /historial paginan) |
| sla | VERDE | VERDE (5 funcs 21–30) | VERDE | VERDE | AMARILLO (infra 68.9 y pres 58.4, ambas marginales) | VERDE | VERDE |
| turnos | VERDE | AMARILLO (6 funcs) | VERDE | VERDE | **ROJO** (infra 50.6% < 70) | VERDE | VERDE |
| vacaciones | VERDE | **ROJO** (32 funcs, 2 de >50 — sin ADR) | VERDE | VERDE | AMARILLO (app 70.6% < 85; resto cumple) | VERDE | VERDE |
| shared | VERDE | AMARILLO (`create_app` 64 líneas; migraciones fuera de alcance razonable de §4) | VERDE | VERDE | VERDE (dom 100, infra 78.9, pres 84.4) | VERDE | n/a |
| **frontend** | n/a | AMARILLO (9 archivos >300, máx 459) | VERDE (tsc 0, eslint 0) | n/a | no medido (sin suite de tests frontend) | **ROJO** (1 `dangerouslySetInnerHTML` sin sanitizar) | n/a (consume Page del backend) |

**Patrones sistémicos** (mismo smell en ≥3 módulos → problema de práctica, no local):

1. **§4 funciones >20 sin ADR** en insumos, contadores, vacaciones, prestadores (206 en
   total fuera de liquidaciones). ADR-016 resolvió esto para liquidaciones con un criterio
   razonable (span físico ≠ complejidad; límite vigente para código nuevo) — el mismo
   criterio no está extendido al resto.
2. **§7 infraestructura subcubierta** en contadores/turnos/prestadores (49–52%): los
   adapters de scraping/FTP/ERS/SDS y repos de sync casi no tienen tests de integración.
   Coincide con el código más frágil del repo (scraping HTML, FTP, tokens).
3. **§4 firmas >3 params** transversal (252): mezcla de idiom FastAPI inevitable y
   firmas keyword-only de repos — mismo fenómeno que ADR-016 describe, sin decisión
   escrita que lo cubra fuera de liquidaciones.

Módulos con más deuda: **contadores** (tamaños + cobertura infra, el único con las dos en
rojo estructural), **insumos** (volumen de §4: 102 funcs), **vacaciones** (§4 + app 70.6%).
Módulo modelo: **liquidaciones** (deuda §4 documentada, cobertura sobresaliente) y
**sla** (chico y limpio, con dos marginales de cobertura).

---

## FASE 4 — Hallazgos priorizados

| Sev | Sección | Módulo | Evidencia | Impacto | ¿ADR? | Acción |
|---|---|---|---|---|---|---|
| ALTO | §7 | contadores, turnos, prestadores (infra) | `pytest --cov`: 49.9% / 50.6% / 52.4% vs mínimo 70% | Los adapters más frágiles del repo (scraping Gestión, FTP DB3, ERS/SDS, sync Siges) son los menos protegidos; una rotura upstream se detecta en producción, no en tests | No | Backlog dirigido de tests de integración; si los mínimos de la guía se consideran inalcanzables para adapters de scraping, ADR que lo diga |
| ALTO | §8 | frontend (feature contadores) | `event-detail-modal.tsx:147` `dangerouslySetInnerHTML={{ __html: event.content_tooltip }}` — HTML scrapeado de Gestión, persistido por el sync, renderizado sin sanitizar | Stored XSS si el contenido de Gestión (editable por terceros fuera de esta app) trae markup malicioso; mitigado por ser fuente interna, pero es la única brecha de §8 y el fix es barato | No | Fix inmediato: sanitizar (DOMPurify) o renderizar como texto |
| MEDIO | §4 | insumos, contadores, vacaciones (y menor en resto) | AST: 206 funcs >20 fuera de liquidaciones; 10 de >50 líneas (máx 106); 2 clases >200; 3 archivos >300; 4 anidamientos de 4 | Deuda de legibilidad; las 10 >50 son complejidad real (export CSV, sync alerts, refresh de token), no firmas largas | Solo liquidaciones (ADR-016) | Refactor puntual de las 10 >50 al tocarlas; extender el criterio de ADR-016 al resto del repo con un ADR general (inventario congelado + límite vigente para código nuevo) |
| MEDIO | §7 | auth, vacaciones (application) | cov 64.7% y 70.6% vs mínimo 85% | Use cases con ramas sin probar en los dos módulos que manejan permisos y decisiones de RRHH | No | Tests unitarios dirigidos a las ramas no cubiertas |
| MEDIO | §7 | app completa | Sin suite e2e (`tests/` solo unit + integration) | El mínimo "presentation 60% (e2e)" se cumple hoy con tests que no son e2e; ningún flujo completo navegador→API→DB está automatizado | No | Decidir: suite e2e mínima de flujos críticos, o ADR que redefina la pirámide para este monorepo |
| BAJO | §11 | insumos, auth, liquidaciones | 8 endpoints `list[...]` sin `Page[T]` (customers ×4, catálogos auth ×3, `/periodos`) | Catálogos chicos y acotados; el riesgo real es bajo, pero la excepción de CLAUDE.md exige contrato paginado y no lo hay | No (ADR-011 no los cubre) | Paginar el contrato con size generoso, o ADR estilo 011 que los declare catálogos-recurso |
| BAJO | §10 | backend, frontend | No existen `backend/README.md` ni `frontend/README.md` | Onboarding depende del README raíz y de docs/ | No | Crear ambos con el template de §10 |
| BAJO | §9 | repo | Flujo single-dev sin PRs/review; 4/12 últimos commits >400 líneas | Las garantías de §9 (review, PR acotado) no existen como proceso | No | ADR corto que documente el flujo real single-dev, o adoptar PRs |
| BAJO (opinable) | §8 | contadores, insumos | 3 f-strings en SQL (`ftp_client_model.py:22,25` constantes; `supply_cache:152` con `int()`) | Sin vector de inyección (sin input de usuario); es estilo, no vulnerabilidad | No | Opcional: pasar a `bindparam` al tocar esos archivos |
| SOSPECHA | §11 | vacaciones, insumos | Heurística AST: reads por ítem en loop (`gestionar_sectores.py:104,121`, `gestionar_empleados.py:162`, `get_device_supplies.py:88`) | Posible N+1 sobre cardinalidades chicas; sin medición de latencia que lo confirme como problema | No | Medir antes de optimizar (§11 regla 1); no accionar sin dato |

**No-hallazgos verificados** (desviaciones ya cubiertas por ADR, se listan para que no se
re-reporten): estructura módulo→capa (ADR-003), snake_case en paquetes (ADR-006),
`require_permission` importado desde presentation de otros módulos (ADR-007), inyección
cruzada auth←contadores por `dependency_overrides` (ADR-009), `LoggedMailDispatcher` en
presentation con excepts que no propagan (ADR-010), `GET /api/prestadores` como resumen
agregado no paginado (ADR-011), funciones 21–37 líneas de liquidaciones (ADR-016).

---

## Veredicto

**¿La app cumple ARCHITECTURE_GUIDE.md hoy? SÍ, CON DEUDA ACOTADA Y PARCIALMENTE
DOCUMENTADA.** Lo estructural —lo que la guía marca como no opinable— está limpio y
medido: capas y módulos 100% (lint-imports 19/19 sobre 926 archivos), ruff/mypy/tsc/eslint
en cero, 0 imports de terceros en domain/application, 0 errores silenciados reales sobre
86 handlers, 167/170 endpoints con autorización y SQL parametrizado. La deuda se concentra
en dos frentes: **§4** (206 funciones >20 líneas sin ADR — solo liquidaciones documentó
las suyas) y **§7** (7 celdas módulo/capa bajo el mínimo de cobertura, con la
infraestructura de contadores/turnos/prestadores al 50%, y sin e2e), más un hallazgo
puntual de §8 (tooltip sin sanitizar).

**Focos de mayor retorno:**

1. Sanitizar `event.content_tooltip` (1 línea + dependencia) — cierra la única brecha de §8.
2. Tests de integración para la infraestructura de contadores/turnos/prestadores — cubre
   el código más frágil del repo justo donde hoy está más desnudo.
3. ADR general de tamaños §4 (criterio ADR-016 extendido: inventario congelado, límite
   vigente para código nuevo) + refactor oportunista de las 10 funciones >50 líneas.
4. Subir `auth/application` (64.7%→85) — es el módulo de seguridad, es chico (382
   statements), es el mejor ratio esfuerzo/riesgo cubierto.
5. Regularizar los 8 catálogos sin `Page[T]` (paginar o ADR estilo 011) — barato y elimina
   la ambigüedad de "cuándo aplica §11" para el próximo módulo que se porte.

---

## Addendum 2026-08-14 (misma jornada): corrección de la deuda

Los 5 focos se ejecutaron el mismo día de la auditoría. Números re-medidos tras el fix,
con los mismos comandos de la Fase 1:

| Frente | Antes | Después | Cómo |
|---|---|---|---|
| §8 XSS tooltip | `dangerouslySetInnerHTML` sin sanitizar | **Cerrado** — se renderiza como texto plano (`whitespace-pre-line`), sin dependencia nueva | Verificado contra la DB de dev: los 822 `content_tooltip` son texto plano; los únicos "<tags>" son mails en ángulos (`<x@y.com>`) que el innerHTML además se tragaba — el fix corrige XSS **y** un bug de display |
| §4 sin ADR | 206 funcs >20 fuera de liquidaciones sin documentar | **Documentado** — `docs/adr/017-deuda-tamano-funciones-repo-completo.md` (criterio ADR-016 extendido a todo el backend: inventario congelado, límite vigente para código nuevo, refactor oportunista de las 10 >50) | ADR nuevo |
| §11 catálogos | 8 endpoints `list[...]` sin envelope | **0** — los 8 sirven `Page[T]` (verificado en el OpenAPI en vivo: `Page_str_`, `Page_CustomerOut_`, `Page_ModuleCatalogResponse_`) | Contrato paginado con `size` default generoso + consumidores frontend desenvuelven `.items` en la capa api (sin cambios en componentes) |
| §7 auth/application | 64.7% | **100%** | 36 tests unitarios nuevos (`tests/unit/application/auth/`, fakes en memoria para los 12 use cases) |
| §7 contadores/infra | 49.9% | **81.7%** | 21 tests de integración (repos calendario + overrides) + 49 unit con `httpx.MockTransport` (ERS/SDS/Gestión: providers, telemetría, refreshers de token/sesión) |
| §7 turnos/infra | 50.6% | **100%** | 7 tests de integración (4 repos) |
| §7 prestadores/infra | 52.4% | **91.8%** | 9 tests de integración (4 repos + user provider) |
| §7 sla/infra · sla/pres | 68.9% · 58.4% | **≥70 · ≥60** | Integración de snapshot + prestador-lookup (incluye resolución de overrides ADR-013) y unit de los builders de wiring |
| §7 vacaciones/application | 70.6% | **≥85** | 20 tests nuevos (catálogos, empleados, ciclos, lecturas, calendario, dashboard, reporte de descuentos) |

**Estado final re-medido** (`pytest tests -q --cov=src`, 2026-08-14):

- **1427 tests** pasan (antes 1288). Cobertura total **84.7%** (antes 79.0%).
- **0 celdas módulo/capa bajo mínimo** (antes 7). Global por capa: domain 95.3% (≥90),
  application 94.0% (≥85), infrastructure 78.6% (≥70), presentation 74.1% (≥60).
- Gates: `lint-imports` 19/19 KEPT · `ruff check src tests` limpio · `mypy src` limpio ·
  `tsc` limpio · eslint limpio en todo lo tocado por esta corrección.
- Contenedores reiniciados y verificados: backend sirve los contratos `Page[T]` nuevos
  (OpenAPI en vivo), `DISABLE_BACKGROUND_JOBS=true` confirmado tras el restart, cero
  líneas `background_jobs` en el log de arranque.

**Deuda que queda abierta a propósito** (fuera de los 5 focos):

- Sin suite e2e — sigue pendiente la decisión producto/ADR (hallazgo MEDIO original).
- Las 10 funciones >50 líneas, 2 clases >200 y 3 archivos >300: cubiertas por ADR-017
  como refactor oportunista, no se tocaron en bloque a propósito.
- READMEs de backend/ y frontend/ (§10, BAJO) y el ADR del flujo single-dev (§9, BAJO).
- `sla/presentation/background_jobs.py` sigue en 0% — probar jobs de fondo requiere
  cuidado especial (CLAUDE.md); queda fuera del alcance de esta pasada.

Nota de la corrida: durante la verificación final apareció trabajo en curso ajeno a esta
corrección en el working tree (feature `get_pending_clients` de contadores:
`calendario_router.py`, `today-clients-card.tsx`, `contadores-api.ts`,
`calendario-format.ts` + script `inspect_estado_soap.py`). Ese código compila (tsc OK) y
pasa ruff/mypy/pytest, pero tiene **1 error de eslint propio**
(`today-clients-card.tsx:81`, `react-hooks/purity`: `Date.now()` en render) — no se tocó
por no ser parte de esta corrección.
