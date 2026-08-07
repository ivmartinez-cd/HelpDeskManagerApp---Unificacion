# Estado al pausar (2026-08-07, noche) — retomar desde acá

**Resumen en una línea:** Contadores tiene su modelo de datos y **5 de 8 herramientas**
reescritas de punta a punta en `HelpDeskManager-Unificacion/backend/src/modules/contadores/`,
con 116/116 tests pasando. Faltan 3 (SDS, ERS, gestión de clientes FTP) — dejadas para después
a propósito por necesitar credenciales reales y más deliberación, no por falta de tiempo bruto.

## ✅ Hecho y verificado

### Modelo de datos (Fase 3, paso 2 del checklist)
- Tablas `ftp_clients` y `meter_client_configs` migradas al Postgres consolidado (migración
  Alembic `fc502aa52749`, reversible, verificada).
- **231 filas reales de `ftp_clients` + 5 de `meter_client_configs` copiadas desde el Neon de
  producción** con `backend/scripts/migrate_contadores_data_from_neon.py` — confirmado por
  conteo en la DB nueva, sin loguear credenciales.
- Catálogo de permisos actualizado: migración `5c08ab6175a0` agrega el módulo `contadores`
  (`is_enabled=False` — se activa cuando estén las 8 herramientas + UI).

### Lógica de negocio (Fase 3, paso 3) — 5/8 herramientas de exportación

Cada una domain → application → infrastructure → presentation, endpoint propio, gateada con
`require_permission(EXPORT)`, validada contra tests de caracterización (mismos números que la
app vieja) + al menos un test end-to-end con archivo real:

| Herramienta | Endpoint | Domain service principal |
|---|---|---|
| Proyección | `POST /api/contadores/proyeccion` | `counter_projector.py` |
| Calculadora manual | `POST /api/contadores/calc` | `manual_estimation_calculator.py` |
| DB3 → CSV | `POST /api/contadores/db3` | `db3_export_builder.py` |
| Estimación en 0 | `POST /api/contadores/en0` | `estimation_zero_builder.py` |
| Suma Fija | `POST /api/contadores/suma-fija` | `fixed_sum_builder.py` |

### Gestión de clientes FTP (Fase 3, paso 3 — completado 2026-08-07)

CRUD completo + endpoint de descarga/proceso de DB3 vía FTP, portado de la app vieja:

| Endpoint | Descripción |
|---|---|
| `GET    /api/contadores/ftp/clients` | Lista todos los clientes |
| `POST   /api/contadores/ftp/clients` | Crea un cliente |
| `GET    /api/contadores/ftp/clients/{id}` | Obtiene un cliente por ID |
| `PUT    /api/contadores/ftp/clients/{id}` | Actualiza un cliente |
| `DELETE /api/contadores/ftp/clients/{id}` | Elimina un cliente |
| `POST   /api/contadores/ftp/clients/{id}/process` | Descarga DB3 vía FTP y genera CSV |

Todos los endpoints usan `require_permission(EXPORT)`.

**Arquitectura del puerto FTP:**
- `domain/repositories/ftp_db3_downloader.py` — `Protocol` (puerto de dominio), sin `ftplib` en domain.
- `infrastructure/ftp/ftplib_db3_downloader.py` — adaptador concreto (Adapter Pattern).
- El endpoint `/process` reutiliza internamente `RunDb3ExportUseCase` — no duplica lógica CSV.
- `password` nunca se loguea. Passwords en texto plano = decisión consciente documentada en
  `FtpClient` (mismo diseño que la app vieja; cambiar requiere decisión explícita).

**Tests:** 132/132 passing (16 tests nuevos).

### Corrección de arquitectura (ADR-007)
`ModuleKey`/`ActionKey`/`Permission` se movieron de `auth.domain` a `shared/domain/
value_objects/` para que `contadores` (y futuros módulos) puedan declarar sus permisos sin
depender de `auth`. `require_permission`/`get_current_identity` se quedaron en `auth`, con una
excepción de import-linter **acotada a la capa `presentation`**, documentada en
`docs/adr/007-vocabulario-de-permisos-en-shared-excepcion-de-presentation.md`. Contratos en
`backend/.importlinter` — los 4 pasan.

### Verificación (correr esto primero al retomar)
```bash
cd backend
uv run pytest tests/ -q                 # debe dar 132 passed
uv run ruff check src tests scripts     # All checks passed
uv run mypy src                         # Success: no issues found
uv run lint-imports                     # 4 contracts kept, 0 broken
```
Si `pytest` falla con `ConnectionRefusedError` en tests de integración: falta levantar la DB de
test (`docker compose -f docker-compose.test.yml up -d`).

## ❌ Falta para terminar Contadores

### 1. Dos herramientas sin portar: SDS, ERS
No son "más de lo mismo" — cada una tiene una decisión previa a tomar, no solo código:

- **SDS (HP):** credenciales (`SDS_API_KEY`/`SDS_API_SECRET`) están **hardcodeadas en texto
  plano** en `HelpDeskManager-Web/backend/services/sds_api.py` — hay que decidir dónde viven
  las nuevas (`.env` del monolito nuevo, ¿o un secret manager?) antes de portar el cliente HTTP.
- **ERS (Epson):** no tiene API oficial — el login es scraping vía **subproceso Playwright**
  (`ers_token_refresher.py`), verificado en vivo que funciona (~7.5s). Decisión pendiente: ¿se
  porta el subproceso tal cual, o se integra como una tarea async dentro del proceso FastAPI?
  Cualquier timeout debe ser holgado (≥15s).

### 2. Otros pendientes del checklist de Fase 3 (Contadores), sin tocar todavía
- [ ] Portar la UI a Next.js dentro de `(modules)/contadores/` — nada de frontend hecho aún.
- [ ] Prueba end-to-end con Playwright desde el sidebar del padre.
- [ ] Correr en paralelo con la app vieja antes de apagarla.
- [ ] Apagar el módulo Contadores de la app vieja.
- [ ] Flippear `is_enabled=True` en el catálogo cuando todo lo anterior esté listo.

### 3. Deuda simplificada a propósito (no bloquea, pero queda anotada)
- El dashboard de KPIs con celdas coloreadas y las hojas "Leyenda"/"Validación" de la
  Proyección vieja no se portaron (polish visual, no reglas de negocio).
- No hay test e2e por navegador del flujo completo de auth todavía (Fase 2, no bloquea Fase 3).
- El endpoint `/process` de FTP **no se probó contra FTP en vivo** (requiere autorización
  explícita + credenciales reales de clientes). Tests de integración usan stub de FTP.

## Estado del entorno (para no perder el hilo)

**Servidores corriendo, dejados a propósito** (`feedback_leave_servers_running` — no apagar):
- `127.0.0.1:8010` — backend nuevo, del usuario, de una sesión anterior. **No tocar.**
- `127.0.0.1:8011` — backend viejo (`HelpDeskManager-Web`), apuntando a la Neon real de
  producción, de solo lectura. Se puede apagar si molesta, no tiene nada crítico pendiente.
- `127.0.0.1:8012` — instancia mía de verificación del backend nuevo (con el código de hoy ya
  cargado). Se puede matar sin problema, se relanza en 5 segundos con
  `uv run uvicorn src.shared.presentation.app:app --port 8012` desde `backend/`.

**Docker:** `helpdesk-db` (puerto 5439, dev) y `helpdesk-db-test` (puerto 5440, test) corriendo
y con las migraciones de Contadores aplicadas. `docker-compose.test.yml` es el que levanta la
segunda si hace falta reiniciarla.

**Working tree limpio (commits hechos al pausar, 2026-08-07):**
- `2d7dc53` — trabajo de Fase 2 (self-service forgot/reset/change-password) que ya estaba
  suelto desde antes de esta sesión.
- `d234964` — todo lo de Contadores + el refactor de ADR-007, hecho hoy.

`git log --oneline -5` en `HelpDeskManager-Unificacion/` para confirmar al retomar.

---

# Caracterización del módulo Contadores (Fase 3, paso 1)

Resultado de correr la app vieja (`HelpDeskManager-Web`) en vivo — backend local en
`127.0.0.1:8011` contra el **Postgres de producción real (Neon)**, confirmado con
`docker inspect` en la VM (`DATABASE_URL` idéntico al de `PROJECT_CONTEXT.md`, 231 filas
reales en `ftp_clients`) — para fijar el comportamiento actual de las 8 herramientas antes de
reescribirlas. Se ejecutaron solo operaciones de lectura/exportación (nunca los endpoints
`PUT .../config` que escriben en la DB de producción) y no se probó FTP en vivo (231 clientes
reales — requiere autorización separada, no cubierta acá).

Tests nuevos: `HelpDeskManager-Web/backend/tests/test_proyeccion_caracterizacion.py` (8/8 pasan,
junto con el `test_proyeccion.py` preexistente). Estos tests son la referencia a validar cuando
se reescriba el algoritmo en el monolito nuevo — si alguno deja de pasar contra la
reimplementación, es una decisión consciente, no un accidente.

## Hallazgos por herramienta

### Proyección de contadores (`ejecutar_proyeccion`)
- **Reset detectado por caída de contador (sin flag "Reiniciar Contador"):** el consumo diario
  se calcula sobre el tramo posterior al reset, pero la proyección hacia adelante parte de la
  **última lectura conocida**, no del punto de reset. Ej.: reset a 500, última lectura 1500,
  consumo 100/día, 10 días a proyectar → **2500**, no 1500. Fácil de reimplementar mal.
- Umbral mínimo de consumo, antigüedad máxima de lectura, ventana reciente y tolerancia:
  comportamiento confirmado igual a lo que documenta el código (ver tests).
- El CSV de salida ("CSV para SiGes") solo incluye series con método `PROYECTADO` — las `REAL`
  y `SIN DATOS` no van al archivo que alimenta facturación.

### DB3 → CSV (`procesar_db_a_csv`)
- Filtra por `counterclass_id IN (40,10,20)` — cualquier otra clase se descarta silenciosamente.
- `counterclass_id=40` con modelo en `MODELOS_ESPECIALES` (lista hardcodeada de ~17 modelos en
  `db3_to_csv.py`): el mismo valor termina duplicado en **CLASE_10 y CLASE_20 con el mismo
  contador** (verificado en vivo: `TIPO=15;CLASE_10=20;CONTADOR_10=5000;CLASE_20=20;
  CONTADOR_20=5000`). No es un caso de "solo color" — es una duplicación real de la fila.
- `counterclass_id=40` con modelo normal → `CLASE_10=10` únicamente, sin fila en CLASE_20.

### Estimación en 0 (`filtrar_falta_contador_csv`)
- **Corrección (2026-08-07): no es un bug.** `main.py` importa `filtrar_falta_contador_csv`
  desde `services/counters_tools.py`, **no** desde `services/csv_en0.py` — este último es
  código muerto (nunca importado por `main.py`), con una implementación más elaborada que
  incluye el "shift a la izquierda" que documenté antes como bug. La función que de verdad
  corre en producción (`counters_tools.py`) es más simple: filtra `Tipo` por substring
  case-insensitive (`.str.contains("FALTA CONTADOR")`, no una lista exacta), y si hay columna
  `NombreClase` asigna Color→CLASE_20 o Mono→CLASE_10 **sin ningún shift posterior**. Lo que vi
  en vivo (Color queda en CLASE_20, no se mueve a CLASE_10) es el comportamiento correcto de la
  función real, no una desviación. Al portar, usar `counters_tools.py` como referencia, no
  `csv_en0.py`.
- Filtra filas cuyo `Tipo` **contiene** el substring "FALTA CONTADOR" (case-insensitive) —
  más permisivo que una lista cerrada de valores exactos.

### Suma Fija (`procesar_suma_fija`)
- Prioridad de reglas confirmada: `Estado in {"Desaparecida","Backup Fijo"}` → no suma (pasa
  igual). Si no, `Cdor Actual == 1` → no suma, **incluso si `Estado == "Activa en Cliente"`**
  (el chequeo de `== 1` tiene prioridad sobre el de estado). Si no, `Activa en Cliente` → suma
  `hojas_a_sumar`. Cualquier otro estado → contador queda **vacío** (`""`), no se omite la fila.
- Formato de salida distinto al resto: columnas crudas (`SERIE;Estado;Cdor Actual;FECHA;TIPO;
  CLASE;CONTADOR`), no el formato ancho `CLASE_10/CLASE_20` que usan las demás herramientas.

### Calculadora manual (`calcular_estimacion_manual`, en `counters_tools.py`)
- **Corrección (2026-08-07): tampoco es un bug.** También hay dos implementaciones: la que
  corre de verdad (`counters_tools.py`) y una no usada (`estimador_manual.py`, no importada
  por `main.py`). Usa el convenio financiero **días 360** (`dias_360`: cada mes cuenta como 30
  días). El `dias_est=-16` que había documentado salía de un caso de prueba con `fe` (15/01)
  **anterior** a `ff` (01/02) — `dias_360(ff, fe)` calculado "hacia atrás" da negativo, que es
  matemáticamente correcto para ese orden de fechas, no un bug. En el uso real (`fe` posterior
  a `ff`, estimando hacia adelante) da positivo. Al portar: usar días 360, no días de
  calendario — y el signo negativo cuando `fe < ff` es comportamiento esperado, no a corregir.
- **Encontrado pero confirmado código muerto, no se porta:** `ejecutar_autoestimacion` (también
  en `counters_tools.py`) está importada en `main.py` pero nunca se llama desde ningún
  endpoint — no es una de las 8 herramientas de la UI, no tiene ruta que la exponga.

### SDS (HP) y ERS (Epson) — integraciones externas
- Ambas devolvieron datos reales en vivo (login SDS con key/secret, catálogo de clientes, export
  de contadores; login ERS con token cacheado).
- **Renovación forzada del token ERS vía Playwright confirmada funcional:** se borró
  `ers_token.json`, se volvió a pedir `/api/ers/clients`, y el subproceso
  `ers_token_refresher.py` regeneró el token en **~7.5 segundos** con un login real por navegador
  headless. Al reimplementar, cualquier timeout de esta llamada debe dar margen holgado (≥15s).
- Credenciales SDS **hardcodeadas en texto plano** en `sds_api.py` — confirmado, mover a env
  vars al migrar (ya señalado en `INTEGRACION_APPS_PLAN.md`).
- Modo `suma_color` de SDS (mono+color combinado en un solo contador, `engineCycles`) verificado
  con un cliente real que lo tiene activado — el CSV resultante usa `CLASE_10=20` únicamente,
  sin fila `CLASE_20` (consistente con el código).

### FTP — no probado en vivo
231 clientes reales configurados en `ftp_clients` (Neon). Requiere autorización explícita
adicional antes de conectar a servidores de clientes reales — no se hizo en esta pasada.
Comportamiento documentado solo por lectura de código (`ftp_db3.py` / endpoint
`/api/ftp/process-client`), sin verificar en vivo.

## Estado del entorno usado para esta caracterización
- Backend viejo corriendo local en `127.0.0.1:8011` (puerto 8010 ya estaba ocupado por el
  backend nuevo de `HelpDeskManager-Unificacion`), apuntando a la Neon real de producción.
  **Se dejó corriendo** (no se apagó) — es de solo lectura para todo lo probado.
- Archivos de prueba sintéticos usados (DB3, CSV de en0, xlsx de suma fija) quedaron en
  `%LOCALAPPDATA%\Temp\claude\` — no se commitearon al repo, son desechables.
