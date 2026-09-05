# vacaciones

Migración de VacaSync (`D:\Dev\Trabajo\Calendario-vacaciones-cd`, Express+Prisma). **Entrega 1**
(2026-08-13): Gestión Humana (empleados/sectores/cargos/feriados) + core de vacaciones
(ciclos/saldos, solicitudes, aprobaciones, dashboard, calendario). **Entrega 2** (2026-08-13):
Asistencias (bajas `vacaciones_ausencia`, 7 tipos + medio día + reporte mensual de descuentos),
auditoría (`vacaciones_audit_log` + pantalla) y pantalla Configuración (`PUT /config` +
exclusiones + límites por cargo). **Entrega 3** (2026-08-13): pantalla Reportes + export
Excel/PDF y emails del seam `Notificador`. Fuente de verdad visual:
`design_handoff_vacaciones/` en la raíz del repo.

Pendiente: la migración de datos reales (abajo) y el paralelo con VacaSync/apagado.

**Nombre visible** (2026-08-13, migración `c7d1f92e4a68`): el módulo se muestra como
**"Gestión de Personal"** en el menú (engloba Vacaciones + Asistencias + ABM) y el subítem
del ABM pasó de "Gestión Humana" a **"Personal"**. Solo cambió el `label`: la key
`vacaciones`, la ruta `/vacaciones` y los paths de API siguen igual.

## Integración con turnos — modo vacaciones (ADR-025, 2026-08-20)

- Puerto `ImpactoTurnosLookup` (`domain/repositories/impacto_turnos_lookup.py`) implementado en
  `infrastructure/repositories/sqlalchemy_impacto_turnos_lookup.py` leyendo `turno_asignacion`
  + `turno_slot` (patrón `PrestadorLookup` de sla; contrato import-linter
  `vacaciones-domain-app-independent-from-turnos`).
- `DecidirSolicitud` devuelve `DecisionResultado(solicitud, afecta_turnos)`: al **aprobar**, si el
  empleado tiene `user_id` vinculado (D3) con franjas de turno en el rango, viaja
  `afectaTurnos {userId, desde, hasta}` en la respuesta de `POST /solicitudes/{id}/decision`
  (aditivo sobre `SolicitudResponse`). **No se crea la grilla de cobertura automáticamente**: el
  frontend muestra un banner con CTA hacia el editor del modo vacaciones de `/admin/turnos`.

## Entrega 3 — decisiones y paridades

- **Reportes** (`/api/vacaciones/reportes` + `/excel` + `/pdf`, pantalla
  `/vacaciones/reportes` con tab pills Reportes|Auditoría): paridad de
  `report.controller.ts` — solo admin (`manage`, el legacy era ADMIN-only), incluye
  empleados **inactivos**, empleados ordenados por nombre y sectores por nombre, saldos del
  año en curso vía `SaldosService` (mismo `getEmployeeBalance`); `annual` es el del ciclo
  (sin carry) y `available` sí descuenta carry/used/pending. Excel con openpyxl (mismas dos
  hojas y columnas del legacy, "Departamento" renombrado a "Sector"); PDF con **fpdf2**
  (layout de texto del PDFKit legacy; fuentes core = latin-1, lo no representable se
  degrada con `replace`).
- **Emails (D8 activado)**: `EmailNotificador` (infrastructure) sobre el mailer de auth,
  que ganó un `html_body` opcional (multipart texto+HTML; ConsoleMailer lo ignora).
  Destinatarios de nueva solicitud = jefes del sector del empleado (`user_module_scope`)
  + admins (grant `manage` o superadmin, igual que `get_actor_vacaciones`), solo cuentas
  activas, deduplicados — el equivalente de MANAGERs del sector + ADMINs del legacy. Decisión → email del empleado. Templates
  portados de `utils/email.ts` (mismos subjects, fechas dd/mm/aa, link a
  `/vacaciones/aprobaciones`); un fallo de envío se loguea y **nunca** corta el use case
  (paridad del `sendMail` legacy). `NuevaSolicitudNotif` ganó `department_id` para poder
  resolver a los jefes.
- **Gate `VACACIONES_MAIL_ENABLED` (default `false`)**: con el flag apagado se cablea
  `LoggingNotificador`; solo con `true` se mandan emails reales. Deliberado: el .env de
  dev tiene SMTP real de Canal Directo (ver CLAUDE.md) — activar los emails es una
  decisión por entorno, no un default.

## Entrega 2 — decisiones y paridades

- **Ausencias (Absence legacy)**: nacen `APPROVED`; `days_count` usa el MISMO conteo corrido
  con extensión LCT que las solicitudes (`dias_corridos` — el legacy usaba calendarDaysBetween
  para ambas); `half_day` computa 0.5 en el reporte de descuentos solo para DESCUENTO_DIA
  (paridad del submit legacy). Desde 2026-09-03 la UI también habilita el checkbox para
  HOME_OFFICE, pero ahí es puramente informativo (gradiente del calendario y texto "Medio día"
  del listado): HOME_OFFICE no entra en `dias_descontados_en_mes` ni en el gateway de días
  sugeridos de bono_tecnicos, así que `half_day=True` en ese tipo no descuenta ni afecta
  liquidación. Valida solape contra bajas del mismo tipo y contra
  solicitudes activas (409). Editar/eliminar: dueño o admin (el jefe crea pero NO toca ajenas);
  no-admin solo PENDING y nunca cambia `status`.
- **Reporte de descuentos**: jefe clavado a su sector; admin elige sector (default el llamado
  "Técnico"); descuentos = días hábiles (sin finde/feriado, 0.5 si medio día) — algoritmo
  exacto del legacy; las columnas extra del handoff (enfermedad/guardias) cuentan días corridos
  del mes (semántica de los contadores por tipo del legacy).
- **Auditoría**: puerto `RegistradorAuditoria` (bound al usuario actuante, nunca lanza) cableado
  en todos los use cases mutantes; **conserva el vocabulario legacy** (acciones
  CREATE/UPDATE/DELETE/APPROVE/REJECT/IMPORT, entidades Department/Employee/Position/Holiday/
  VacationRequest/SystemConfig/Absence) para que la migración de datos de `AuditLog` quede
  uniforme. El login NO se audita acá (es de la plataforma auth). La UI traduce a castellano y
  arma la descripción desde `metadata` (`frontend/.../lib/auditoria.ts`).
- **Config**: los campos dormidos (`min_advance_notice_days`, `max_overlap_percent`,
  `max_overlap_count`) ahora se exponen en GET/PUT y en la pantalla (tab Reglas) por paridad,
  pero **ninguna validación los usa** (el legacy tampoco). PUT es merge parcial + audit de
  claves cambiadas.
- **Límites por Cargo** (tab Solapamientos): la UI edita `vacaciones_cargo.max_simultaneos` vía
  el PUT de cargos existente (D10) — no hay endpoint nuevo.
- KPIs/grilla anual de Asistencias se computan client-side (port de `getStatsForYear` del
  legacy, con fechas string para evitar su off-by-one de `toISOString`).

## Decisiones de diseño (D1–D11 del plan aprobado)

- **D1** Sector = tabla `department` compartida con auth, extendida con `color`. Un solo modelo
  mapeado (el de auth); vacaciones lo importa solo desde infrastructure.
- **D2** Jefe↔sector = fila en `user_module_scope` con `module_key='vacaciones'`:
  `scope_department_id=X` significa "este usuario es jefe del sector X". Si auth activa un
  `ScopePolicy` real más adelante, revisar que esta semántica siga siendo compatible.
- **D3** Empleado↔cuenta = `vacaciones_empleado.user_id` (UUID NULL UNIQUE, FK `app_user` SET
  NULL). Reemplaza al `User.employeeId` legacy invertido.
- **D4** Roles legacy → matriz de permisos: `view` (lecturas, alcance por actor), `create`
  (solicitudes propias), `approve` (decidir; con fila en scope ⇒ solo su sector y nunca la
  propia), `manage` (admin RRHH + bypass). `update` quedó sembrada sin uso en E1. El "rol"
  efectivo es el VO `ActorVacaciones` que arma `presentation/dependencies/actor.py`.
- **D5** Config singleton sembrada con los defaults de producción del legacy (7 tiers del
  default de Prisma). Solo GET en E1.
- **D6** Carry-over **iterativo** desde `ANIO_BASE_CARRY_OVER=2026` (equivalente exacto a la
  recursión legacy, que estaba marcada frágil), con write-behind del carry en el ciclo.
- **D7** Apertura de ciclos **lazy** (`ciclo_policy`), sin background jobs. `POST
  /ciclos/abrir-proximo` conserva la apertura forzada manual.
- **D8** Notificaciones: Protocol `Notificador` en domain; para activar emails, implementar
  sobre el mailer de auth cableado desde presentation (patrón insumos) sin tocar contratos.
- **D9** Calendario mensual propio del feature en frontend (no se reutiliza el de contadores).
- **D10** Límite por cargo = `vacaciones_cargo.max_simultaneos` (absorbe PositionOverlapLimit).
  Exclusiones mutuas: tabla + endpoints en E1, UI en la pantalla Configuración de E2.
- **D11** Fechas conceptuales como `DATE` + `Clock` inyectable (el legacy usaba timestamps
  medianoche-UTC comparados contra hora local: fuente de off-by-one).

## Paridades no obvias con el legacy (a conservar)

- Días pedidos = corridos inclusive + extensión LCT (fin viernes +2, sábado +1); el único
  descuento es un feriado `deducts_vacation=false` que caiga exactamente en el inicio (−1).
- La **edición** de una solicitud NO re-valida año ni apertura de ciclo (solo solape,
  exclusiones, límite por cargo y saldo con add-back); siempre vuelve a PENDING.
- `decide` permite **re-decidir** (no chequea el status actual) y acumula historial.
- El empleado ve el **calendario completo**; solo el jefe lo ve acotado a su sector.
- `min_advance_notice_days` / `max_overlap_percent` / `max_overlap_count` existen en la config
  por paridad de datos pero **ninguna validación los usa** (el legacy tampoco).
- **Desvío consciente (2026-09-05)**: un no-admin no puede crear una solicitud con
  `start_date` anterior a hoy (400 `FECHA_PASADA`, después del chequeo de año y antes de la
  agenda); el admin sigue cargando histórico. El legacy solo rechazaba el año pasado.
- **Desvío consciente (2026-09-05)**: un empleado sin `manage` ni sector que manda
  `empleadoIds` con ids ajenos recibe 403 (el legacy reescribía en silencio al propio).

## Migración de datos reales (pendiente — corre en la PC del trabajo)

La DB productiva de VacaSync (Postgres `vacasync`) no es accesible desde este entorno. El
script futuro (estilo `backend/scripts/migrate_liquidaciones_data_from_sqlite.py`) consume un
dump y mapea:

| Legacy (Prisma)              | Nuevo                                                        |
|------------------------------|--------------------------------------------------------------|
| `Department`                 | `department` — **upsert por nombre** (puede chocar con sectores ya creados a mano) + `color` |
| `Position` + `PositionOverlapLimit` | `vacaciones_cargo` (+ `max_simultaneos` del limit 1:1) |
| `Employee`                   | `vacaciones_empleado` — `hireDate`/fechas `timestamp::date` **cuidado**: los timestamps legacy son medianoche UTC; castear en UTC, NO con `AT TIME ZONE` argentina (restaría un día) |
| `User.employeeId`            | `vacaciones_empleado.user_id` (previa alta de esas cuentas en `app_user` + grants `view/create`) |
| `User.managedDepartmentId` (MANAGER) | fila en `user_module_scope` (module `vacaciones`) + grant `approve` |
| `User.role=ADMIN`            | grant `manage` (+ `view/create/approve`)                     |
| `VacationCycle`              | `vacaciones_ciclo` (el carry_over persistido se recalcula solo en la primera lectura) |
| `VacationRequest`            | `vacaciones_solicitud` (`chargedToYear` se conserva; NULL = año de start) |
| `ApprovalHistory`            | `vacaciones_aprobacion` (approver por email → `app_user.id`; sin match ⇒ NULL) |
| `VacationExclusion`          | `vacaciones_exclusion` — normalizar `a < b`                  |
| `Holiday`                    | `vacaciones_feriado` (`date::date`, upsert por fecha)        |
| `SystemConfig`               | `vacaciones_config` (tiers: renombrar claves a snake_case)   |
| `Absence`, `Notification`, `AuditLog` | fuera de E1 (Asistencias/auditoría llegan después) |
