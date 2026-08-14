# Master Prompt — Habilitación de equipos para mantenimiento preventivo por zona

Incorporar una búsqueda/habilitación de equipos para **mantenimiento preventivo por zona de
distribución** (SUR, SURESTE, SUROESTE, NORTE 1, NORTE 2, NORTE 3, NORTE 4, CABA): cuando un
técnico se queda sin servicios, el operador tiene que poder buscar rápido, en la zona de ese
técnico, equipos a los que les toca (o está por tocarles) el preventivo, y **habilitarlos** para
que se hagan. La zona y la frecuencia del preventivo son datos que viven en Gestión por cada
par Empresa–Sucursal; las fuentes a investigar son SigesReadOnly (MERCURIO) y el SOAP wsAyC.

Generado el 2026-08-14 a partir del análisis del código real. La arquitectura de acceso a
MERCURIO/wsAyC ya está consolidada (ADR-018: `MercurioQueryRunner` + `WsAycClientProvider`) y este
prompt la usa como base obligatoria. **Dónde viven exactamente la zona y la frecuencia en el
esquema de Siges NO está documentado en el repo — es la Fase 0 bloqueante**, con una pista fuerte:
el usuario llama "distribución" a la zona, y `dbo.Distribucion` está catalogada como
"transportistas" solo por inferencia [CANDIDATA], nunca confirmada con filas reales.

---

```text
[ROL]
Actuá como arquitecto/desarrollador senior full-stack del monorepo HelpDeskManagerApp---Unificacion
(FastAPI + SQLAlchemy async + Alembic + Next.js App Router, arquitectura módulo→capa
domain/application/infrastructure/presentation). Conocés y aplicás ARCHITECTURE_GUIDE.md, CLAUDE.md
y el ADR-018 (acceso compartido a MERCURIO/wsAyC) como reglas obligatorias. Respondés en español de
Argentina, directo y sin relleno. Cero alucinaciones: todo dato de Siges se confirma con filas
reales antes de construir encima; lo que no se pueda confirmar se dice explícitamente.

[CONTEXTO]
Piezas reales verificadas contra el código (no supuestas):

- Acceso a MERCURIO (post ADR-018): `shared/infrastructure/mercurio/` con `MercurioQueryRunner`
  (semáforo global de 3 consultas, `MERCURIO_MAX_CONCURRENT`, warning de espera >10 s,
  `timeout_override` para consultas pesadas) y `require_mercurio_runner()`. Un gateway nuevo es
  SOLO su SQL (`query.py`), su row mapping y su puerto de domain — la plomería ya existe.
- Acceso a wsAyC (post ADR-018): `shared/infrastructure/wsayc/client_provider.py`
  (`get_wsayc_client_provider()` — Document compartido, Session por llamada, sin retries).
  Operaciones ya usadas: lecturas `getMachineBySerial`/`getMachineIncidents`/`getTopSupplies`/
  `getTopLiquidations`/etc.; escrituras `persistNewIncident`/`persistNewSupply`/void* (NUNCA
  dispararlas en pruebas). El inventario completo está en `docs/INTEGRACIONES_EXTERNAS.md`.
- Catálogo de Siges: `docs/siges/SIGES_READONLY_CATALOGO_DATOS.md`. Relevante para esta feature:
  · Tablas SIN explorar que suenan al dominio: `Frecuencia`, `IncidentePreventivo`,
    `TipoPreventivo` (VIEW), `Mantenimiento` (VIEW), `Contrato`/`Anexo` (VIEWs).
  · `dbo.Distribucion` [CANDIDATA, NO confirmada]: catalogada como "transportistas/distribuidoras"
    por sentido de negocio, sin fila real vista. `Id`, `Descripcion`, `Cuit`, `Estado`.
  · `dbo.Empresa` / `dbo.Sucursal` (VIEWs, [USADA]): nunca se listó su set COMPLETO de columnas
    en el doc; `Sucursal` tiene `ID_Prestador`, `Longitud`/`Latitud`, `CostoViaticos` — de zona
    de distribución no hay nada documentado. ⚠️ `Estado` invertido: 0=activo, 1=inactivo.
  · Definición confirmada de "máquina activa" (paridad exacta con el legacy, 2026-08-14):
    `M.Estado = 0 AND M.ID_Estado_Maquina NOT IN (2, 8)` — reusar, no reinventar.
  · `Tipo_Incidente`: sla filtra `IN (101, 108)` pero el catálogo completo (cuál id es
    correctivo, cuál preventivo, qué más hay) NUNCA se volcó al doc.
  · Cadena de modelo ya conocida: `Maquina.ID_Articulo` → `Articulo.Id_ArtGen` →
    `ArtGen.Descripcion`.
- Patrón de scraping de Gestión (último recurso si un dato no está en Siges ni en wsAyC):
  `contadores/infrastructure/gestion/` + settings `gestion_web_*` (precedente: ADR-012).
- Módulos vacíos reservados: `parque_impresoras` ("vacío hasta migración de
  Printer-Logs-Analyzer") y `stc` ("vacío hasta migración de STC Cloud"). Catálogo de módulos
  sembrado en `4c741806341e_seed_catalog.py`; patrón de seed/activación:
  `53826efbc9ed_seed_sla_catalog.py` + `ac5e139e28b4_activate_sla_module.py`.
- Auth: `require_permission(Permission(ModuleKey("<key>"), ActionKey("view"/"update"/...)))`;
  superadmin pasa todo sin grants. Frontend: cards/pantallas gateadas con
  `useSession().modules.some(m => m.key === "<key>")`; envelope `Page[T]` para colecciones.

[OBJETIVO]

FASE 0 — INVESTIGACIÓN EN SIGES/wsAyC (bloqueante; scripts de exploración en `backend/scripts/`
con el patrón de `explore_siges_parque_pst.py`, SOLO SELECT / SOLO lecturas SOAP):
  1. LOCALIZAR LA ZONA DE DISTRIBUCIÓN. Pista principal primero:
     `SELECT Id, Descripcion, Estado FROM dbo.Distribucion` — si sus filas son SUR / SURESTE /
     SUROESTE / NORTE 1..4 / CABA, la tabla es el catálogo de ZONAS (no de transportistas) y hay
     que corregir el catálogo de datos. Después, dump COMPLETO de columnas de `Empresa` y
     `Sucursal` vía `INFORMATION_SCHEMA.COLUMNS` (nunca se hizo) buscando el FK/columna de zona
     (`ID_Distribucion` o similar) — el usuario afirma que el valor está por Empresa Y por
     Sucursal; confirmar cuál manda cuando difieren (hipótesis razonable: la sucursal hereda de
     la empresa salvo valor propio — CONFIRMAR con datos, no asumir). Si no aparece en Siges:
     dump de operaciones del WSDL de wsAyC (via el provider compartido) buscando métodos de
     empresa/sucursal que devuelvan la zona; si tampoco, scraping de Gestión como último recurso
     (precedente ADR-012) — decisión con ADR, no silenciosa.
  2. LOCALIZAR LA FRECUENCIA DEL PREVENTIVO ("cada cuánto le toca"). Explorar columnas + filas
     reales de `Frecuencia`, `Mantenimiento` (VIEW), `TipoPreventivo`, `IncidentePreventivo`,
     `Contrato`/`Anexo`. Determinar la granularidad real del dato (¿por empresa, por sucursal,
     por contrato/anexo, por máquina?) y su unidad (¿meses, visitas/año?). Confirmar con 2-3
     casos reales contrastados contra lo que muestra Gestión.
  3. CATALOGAR `Tipo_Incidente` COMPLETO (`SELECT Id, Descripcion FROM dbo.Tipo_Incidente`) —
     identificar el/los tipos de preventivo, y de paso documentar qué son 101 y 108 (deuda del
     módulo sla). Con eso, la consulta de "último preventivo por máquina":
     `MAX(fecha)` de `Incidente` del tipo preventivo por `ID_Maquina` (definir qué estados
     cuentan como "hecho" — probablemente los terminales; confirmar contra 2-3 máquinas en
     Gestión). `IncidentePreventivo` puede ser la fuente directa de esto — verificar qué guarda.
  4. MEDIR el costo de la consulta candidata "parque activo de una zona + último preventivo +
     frecuencia" (cronometrar 3 corridas). Decisión derivada: si la consulta por zona corre en
     <5 s, la pantalla consulta EN VIVO (runner + semáforo alcanzan); si es más pesada, snapshot
     local + job de fondo (patrón sla, `PREVENTIVOS_REFRESH_INTERVAL_MINUTES`). No elegir por
     intuición: elegir por la medición.
  5. DECISIONES a validar con el usuario (proponer default, no decidir en silencio):
     a. Módulo destino. Default propuesto: módulo NUEVO `preventivos` (key `preventivos`, ruta
        `/preventivos`, ícono `wrench`, seed propio con acciones view/update/export) — porque
        `parque_impresoras` y `stc` están explícitamente reservados para migraciones legacy
        concretas y esto es una feature nueva. Alternativas: colgarlo de `parque-impresoras`
        (es el dominio del parque) o de `stc` (es trabajo de servicio técnico) si el usuario
        prefiere no abrir módulo nuevo.
     b. Qué significa "habilitar" en v1. Default propuesto: marca LOCAL en la app (tabla propia
        con quién/cuándo/nota), SIN escribir nada en Gestión — el listado de habilitados es lo
        que el operador usa para despachar al técnico. Alternativa explícita para una fase
        FUTURA, fuera de este alcance: crear el incidente preventivo real vía wsAyC
        (`persistNewIncident`) — escritura real contra producción, requiere su propio plan.
     c. Ciclo de vida de la habilitación. Default: vigente hasta deshabilitarla a mano o hasta
        que se detecte un preventivo posterior a la habilitación (se limpia sola en el próximo
        sync). Alternativa: vencimiento por días.
     d. Visibilidad. Default: sin filtro por operador — las zonas son geografía local, no
        cartera de PST; todo usuario con permiso `view` del módulo ve las 8 zonas. (Distinto
        criterio que sla/stc, que filtran por prestador asignado — decirlo en el ADR.)
  Salida de la fase: definición operativa escrita de zona + frecuencia + último preventivo
  (tablas, columnas, semántica de herencia Empresa→Sucursal), lo confirmado volcado a
  `SIGES_READONLY_CATALOGO_DATOS.md` §3 (y corregida la entrada de `Distribucion` si era zona),
  y las decisiones a-d validadas por el usuario. FRENAR acá si la zona no aparece en ninguna
  fuente — no construir sobre un dato inventado.

FASE 1 — BACKEND (módulo elegido en 5.a, estructura módulo→capa):
  - domain: entidades `EquipoPreventivo` (máquina + cliente/sucursal + zona + frecuencia +
    fecha_ultimo_preventivo + próximo vencimiento + estado vencido/por_vencer/al_dia) y
    `HabilitacionPreventivo` (maquina siges_id, habilitado_por, habilitado_en, nota, activa);
    servicio de dominio puro que calcula próximo vencimiento y estado a partir de
    (último preventivo, frecuencia, hoy) — testeable sin DB; Protocols `PreventivosQueryGateway`
    (consulta a Siges) y `HabilitacionRepository`; `well_known_permissions.py` (VIEW, UPDATE
    para habilitar/deshabilitar, EXPORT si aplica).
  - application: use cases `ListEquiposPorZona` (filtros zona/estado/habilitado, combina Siges +
    habilitaciones locales), `HabilitarEquipo` / `DeshabilitarEquipo` (con auditoría en la
    fila: quién y cuándo), `ListZonas` (catálogo desde la fuente confirmada en Fase 0) y — solo
    si la medición de Fase 0.4 lo pidió — `RefreshPreventivosSnapshot`.
  - infrastructure: `siges/query.py` (SQL parametrizado, comentado, con la definición confirmada
    de máquina activa) + `siges/row_mapping.py` (acceso por nombre de columna) + gateway fino
    sobre `MercurioQueryRunner` (patrón ADR-018 — nada de plomería propia); modelo + repo
    SQLAlchemy de habilitaciones; migración Alembic reversible (tabla local de habilitaciones,
    FK lógico por `siges_maquina_id` int — no hay tabla local de máquinas).
  - presentation: router `/api/preventivos` (o el prefijo del módulo elegido):
      GET  /equipos            → Page[...] con filtros `zona`, `estado`, `habilitado`, `q`
                                 (búsqueda por cliente/serie), `page`/`size` con tope explícito
      GET  /zonas              → catálogo de zonas
      POST /equipos/{siges_maquina_id}/habilitar    (permiso update; body: nota opcional)
      DELETE /equipos/{siges_maquina_id}/habilitar  (permiso update)
    `require_permission` en todos; registrar el router en `shared/presentation/app.py`. Si hubo
    snapshot: job de fondo con env propia, respetando `DISABLE_BACKGROUND_JOBS`, y `updated_at`
    expuesto en las respuestas.
  - Contratos import-linter nuevos para el módulo (domain-no-frameworks,
    domain-app-independent-from-auth), mismo texto que los existentes. El contrato
    `pyodbc-zeep-solo-infrastructure` ya cubre al módulo por el wildcard — verificar que siga
    en verde.
  - Seed/activación de catálogo según la decisión 5.a (módulo nuevo: seed con is_enabled=False
    primero; activación al final, patrón sla de dos migraciones).

FASE 2 — FRONTEND:
  - `features/preventivos/` (api, types, components) — pantalla principal:
    · Chips/selector de zona (las 8) + filtros de estado (vencido / por vencer / al día) y
      "solo habilitados"; búsqueda por cliente/serie.
    · Tabla paginada: cliente, sucursal, zona, equipo (serie + modelo), último preventivo,
      frecuencia, próximo vencimiento, estado (badge), habilitado (toggle con permiso update —
      el backend valida igual; optimista con rollback ante error).
    · Orden default: vencidos primero, más atrasado arriba — es la vista "se quedó sin
      servicios, qué le doy" que motiva la feature.
    · Sello de frescura si hay snapshot ("actualizado hace X").
  - Página `app/(app)/preventivos/page.tsx` (o la ruta del módulo elegido); gate por
    `modules.some(...)`. Mismo lenguaje visual del repo (`rounded-[12px] border border-border
    bg-card p-5`, tokens de marca, dark-aware). Cuidado ya conocido:
    `react-hooks/set-state-in-effect` — promise-chain como TodayClientsCard.
  - Card de Inicio: NO en esta pasada (Inicio ya tiene 4+ cards) — dejarlo anotado como
    extensión posible en el ADR, salvo que el usuario la pida.

FASE 3 — ACTIVACIÓN Y VERIFICACIÓN:
  - Activar el módulo por migración recién cuando la ruta responda (enciende el sidebar).
  - Verde dentro del contenedor: `uv run lint-imports` · `uv run ruff check src tests` ·
    `uv run mypy src` · `uv run pytest tests/unit -q` (unit tests del servicio de vencimientos
    con casos borde: sin preventivo previo, frecuencia nula, fecha futura). Frontend: `tsc` +
    `eslint` (coordinar con trabajo paralelo en el repo si lo hay).
  - PARIDAD contra Gestión (parte del entregable): elegir 2 sucursales de zonas distintas y
    contrastar (a) la zona que muestra la app vs la de Gestión, (b) la frecuencia, (c) el último
    preventivo de 2-3 máquinas. Si algo no coincide, el criterio de Fase 0 está mal — corregir
    antes de cerrar, no maquillar.
  - E2E real en el navegador: buscar una zona → aparecen equipos con estado coherente; habilitar
    un equipo → persiste tras recargar y queda auditado (quién/cuándo); usuario sin permiso
    update ve la lista pero no puede habilitar; usuario sin view no ve el módulo.
  - Concurrencia: la pantalla en vivo (si quedó en vivo) convive con el semáforo global de
    MERCURIO — verificar que una búsqueda no queda detrás de un refresh pesado sin el warning
    de espera en el log.

[FORMATO]
- Todo texto al usuario en español de Argentina, directo, sin cortesías (regla de CLAUDE.md).
- Commits atómicos en inglés, convención del historial (`feat(preventivos): ...` o el scope del
  módulo elegido).
- Migraciones Alembic reversibles (up y down). Scripts de exploración de Fase 0 commiteados en
  `backend/scripts/` (precedente: explore_siges_*.py, medir_*.py).
- Documentación: hallazgos de Fase 0 en `SIGES_READONLY_CATALOGO_DATOS.md` (incluida la
  corrección de `Distribucion` si aplica); ADR nuevo con las decisiones 5.a-d y el porqué del
  en-vivo vs snapshot; `docs/INTEGRACIONES_EXTERNAS.md` actualizado (consumidor nuevo de
  MERCURIO y, si aplica, de wsAyC/Gestión web); doc corto del módulo en `docs/` con la
  definición operativa (qué es zona, qué es frecuencia, cómo se calcula el vencimiento).
- Al cierre: resumen con comandos exactos y salidas reales (no "debería andar"), incluida la
  paridad contra Gestión con los valores comparados.

[RESTRICCIONES]
Operativas (innegociables, de CLAUDE.md):
- `DISABLE_BACKGROUND_JOBS=true` aplicado de verdad si se agrega o toca cualquier job
  (`docker compose up -d --force-recreate backend` + printenv + log de arranque limpio;
  `docker restart` NO relee `.env`).
- Siges/MERCURIO: SOLO SELECT (cuenta SiGesReadOnly). wsAyC: SOLO lecturas en toda prueba —
  PROHIBIDO `persistNewIncident`/`persistNewSupply`/void*/set* (la DB de dev tiene datos reales;
  un preventivo creado "de prueba" es un incidente real en Gestión).
- Sin hot reload: restart de contenedor tras editar (frontend re-corre `next build`, esperar el
  200); verificar con curl antes de dar por servido. Contenedores arriba al terminar.

De arquitectura (ARCHITECTURE_GUIDE.md + ADR-018):
- Acceso a MERCURIO EXCLUSIVAMENTE vía `MercurioQueryRunner`/`require_mercurio_runner` — un
  gateway nuevo no escribe plomería (to_thread/connect/wrap ya viven en shared). Acceso a wsAyC
  (si hiciera falta) EXCLUSIVAMENTE vía `get_wsayc_client_provider()`.
- Dependencias hacia adentro; el módulo nuevo no importa domain/application de otros módulos;
  puertos en su domain, SQL/parsing en su infrastructure. SQL parametrizado siempre (§8).
- `Page[T]` para toda colección (§11); ningún `except Exception` silencioso (§6); tamaños §4
  (archivo ≤300, clase ≤200, función ≤20). El cálculo de vencimiento es dominio puro con tests.
- Habilitar/deshabilitar pasa por use case con permiso `update` y auditoría — prohibido
  router→repo directo; el `habilitado_por` sale SIEMPRE de la identidad de sesión, nunca del
  body.

De negocio:
- Las 8 zonas son datos de Gestión, no un enum inventado: el catálogo sale de la fuente
  confirmada en Fase 0 (si mañana agregan "NORTE 5", tiene que aparecer sin tocar código). No
  hardcodear la lista salvo como fixture de tests.
- Un equipo sin frecuencia cargada o sin preventivo previo NO se inventa: se muestra con estado
  explícito ("sin frecuencia" / "sin preventivo registrado"), nunca con una fecha calculada de
  aire.
- La feature es de LECTURA + marca local en v1: nada de lo que haga el usuario acá modifica
  Gestión/Siges. Si la decisión 5.b cambia a crear incidentes reales, eso es OTRO master prompt
  con su propio plan de dryRun.

[EJEMPLO]
Nota de cierre esperada:

  Preventivos por zona — cerrado y verificado:
  - Fase 0: zona = <tabla.columna real> (catálogo `<fuente>`: SUR, SURESTE, SUROESTE, NORTE 1-4,
    CABA — <N> filas); herencia Empresa→Sucursal: <regla confirmada>; frecuencia =
    <tabla.columna> en <unidad>; preventivo = Tipo_Incidente <id> (<descripcion>); catálogo
    completo de Tipo_Incidente documentado (101=<desc>, 108=<desc>). Consulta por zona medida:
    <X> s → decisión <en vivo / snapshot>. Decisiones a-d validadas: <resumen>.
  - Backend módulo `<key>`: entidades + servicio de vencimientos (N tests unit), gateway fino
    sobre MercurioQueryRunner, tabla `preventivo_habilitacion` (migración up/down), router con
    permisos view/update, seed + activación de catálogo.
  - Frontend: pantalla `/preventivos` con filtro por zona, tabla paginada, toggle de
    habilitación con permiso.
  - lint-imports (contratos nuevos incluidos) · ruff · mypy · pytest unit · tsc · eslint — verde.
  - Paridad Gestión: sucursal <A> zona <Z1> ✓, sucursal <B> zona <Z2> ✓; frecuencia <casos> ✓;
    último preventivo de <serie1>/<serie2> ✓.
  - E2E: búsqueda por zona <Z> → <n> equipos, vencidos primero; habilitación persiste y audita;
    sin permiso update no se puede habilitar. Cero escrituras SOAP; jobs deshabilitados.
```

---

## Notas de contexto para quien use este prompt (fuera del prompt en sí)

- **La pista de `Distribucion` importa**: el usuario llama "distribución" a la zona
  (SUR/SURESTE/.../CABA), y `dbo.Distribucion` está en el catálogo de datos como
  "transportistas/distribuidoras" **solo por inferencia**, sin una fila real vista. Si el SELECT
  de Fase 0 muestra que sus filas son las zonas, se resuelven de un tiro el catálogo de zonas y
  el FK esperable en Empresa/Sucursal — y hay que corregir el doc del catálogo, que hoy diría
  algo falso.
- **El dump completo de columnas de Empresa/Sucursal nunca se hizo**: el catálogo documenta esas
  vistas por los usos puntuales de sla/prestadores/liquidaciones, no por inspección exhaustiva.
  Es perfectamente posible que la zona esté ahí a la vista y nadie la haya necesitado hasta hoy.
- **Por qué el default es módulo nuevo y no `parque-impresoras`/`stc`**: los dos están
  explícitamente reservados ("vacío hasta migración de X") para apps legacy concretas. Colgar
  una feature nueva ahí mezcla dos historias de migración distintas; un módulo `preventivos`
  chico es más barato que desenredar eso después. Igual queda como decisión del usuario (5.a).
- **"Habilitar" sin escribir en Gestión es la v1 correcta**: la mecánica que describe el usuario
  (buscar por zona cuando un técnico queda libre) se resuelve con lectura + marca local. Crear
  el incidente preventivo real vía `persistNewIncident` es una escritura contra producción con
  las mismas de las que el módulo insumos se protege con reglas duras (no-retry, tope por ciclo)
  — si se quiere, merece su propio master prompt con plan de dryRun, no un "ya que estamos".
- **El cálculo de vencimiento es dominio puro a propósito**: (último preventivo + frecuencia +
  hoy) → estado. Sin DB ni Siges en el medio, se testea con fechas fijas y cubre los bordes
  (sin preventivo previo, sin frecuencia, frecuencia cambiada recientemente).
- **Deuda que esta Fase 0 salda de paso**: el catálogo completo de `Tipo_Incidente` (hoy el
  módulo sla filtra `(101, 108)` sin que ningún doc diga qué son) y el set completo de columnas
  de `Empresa`/`Sucursal`. Ambos van al catálogo de datos aunque la feature no los use todos.
- **Relación con el master prompt de STC (incidentes sin cerrar)**: son features hermanas
  (ambas leen incidentes de Siges y agrupan para operaciones) pero independientes — ninguna
  bloquea a la otra. Si STC ya se implementó cuando se corra este prompt, su Fase 0 puede haber
  catalogado `Estado_Incidente`/`Tipo_Incidente`; reusar eso en vez de re-explorar.
