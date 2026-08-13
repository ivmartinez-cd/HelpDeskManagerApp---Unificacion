# vacaciones

Migración de VacaSync (`D:\Dev\Trabajo\Calendario-vacaciones-cd`, Express+Prisma). **Entrega 1**
(2026-08-13): Gestión Humana (empleados/sectores/cargos/feriados) + core de vacaciones
(ciclos/saldos, solicitudes, aprobaciones, dashboard, calendario). **Entrega 2** (2026-08-13):
Asistencias (bajas `vacaciones_ausencia`, 7 tipos + medio día + reporte mensual de descuentos),
auditoría (`vacaciones_audit_log` + pantalla) y pantalla Configuración (`PUT /config` +
exclusiones + límites por cargo). Fuente de verdad visual: `design_handoff_vacaciones/` en la
raíz del repo.

Pendiente para entregas siguientes: reportes Excel/PDF (pantalla Reportes del handoff 04 — la
página de Auditoría hoy es standalone y en E3 se le suma el tab Reportes), emails (hoy solo
existe el seam `Notificador` con `LoggingNotificador`), y la migración de datos reales (abajo).

## Entrega 2 — decisiones y paridades

- **Ausencias (Absence legacy)**: nacen `APPROVED`; `days_count` usa el MISMO conteo corrido
  con extensión LCT que las solicitudes (`dias_corridos` — el legacy usaba calendarDaysBetween
  para ambas); `half_day` computa 0.5 solo en reportes/KPIs y la UI solo lo habilita para
  DESCUENTO_DIA (paridad del submit legacy). Valida solape contra bajas del mismo tipo y contra
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
