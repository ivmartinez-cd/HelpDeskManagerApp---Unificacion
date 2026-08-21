# Master Prompt — Modo vacaciones: grilla temporal de Turnos integrada al módulo Vacaciones

Cuando un operador sale de vacaciones, hoy la app solo permite **sustituir personas** slot por
slot (coberturas ADR-013), pero no **re-cortar las franjas horarias** — y el caso real
(vacaciones de M. J. Vela, semana 24–28/08/2026) demostró que cubrir a un ausente exige mover
límites de slots: correr aperturas, extender bloques, eliminar franjas y crear nuevas. La única
salida actual es editar la grilla titular a mano y acordarse de revertirla, exactamente el tipo
de operación manual y olvidable que ADR-013 eliminó para contadores/prestadores.

Este prompt implementa el **modo vacaciones**: una *variante de grilla* de Turnos con vigencia
acotada que se resuelve en lectura y vence sola, más la integración con el módulo Vacaciones
para que aprobar una solicitud dispare el armado (asistido, no automático) de esa variante.

Generado el 2026-08-20 a partir del análisis del código real. Todas las piezas citadas en
[CONTEXTO] fueron verificadas contra el repo; lo que no existe está marcado como tal.

---

```text
[ROL]
Actuá como arquitecto/desarrollador senior full-stack del monorepo HelpDeskManager-Unificacion
(FastAPI + SQLAlchemy async + Alembic + Next.js App Router, arquitectura módulo→capa
domain/application/infrastructure/presentation). Conocés y aplicás ARCHITECTURE_GUIDE.md y
CLAUDE.md del repo como reglas obligatorias. Respondés en español de Argentina, directo y sin
relleno.

[CONTEXTO]
Piezas reales verificadas contra el código (no supuestas):

Módulo `turnos` (backend/src/modules/turnos/):
- Entidades: `Casilla` (id, nombre, color, sort_order, is_active — ej. INSUMOS, ST), `Slot`
  (casilla_id, hora_inicio, hora_fin, dia_semana 0=lunes…6=domingo, sort_order), `Asignacion`
  (slot_id, user_id, vigente_desde, vigente_hasta nullable = indefinida).
- Tablas: `turno_casilla`, `turno_slot`, `turno_asignacion`, `turno_asignacion_override` +
  hija `turno_asignacion_override_slot` (infrastructure/models/turno_models.py).
- `TurnoResolver.resolve_shifts` (domain/services/turno_resolver.py): calcula los turnos de
  una fecha/hora — filtra slots por día de semana, mapea asignaciones vigentes a la fecha,
  aplica overrides ADR-013 vía `resolver_operador_efectivo`, marca is_current/is_next.
- Router `/api/turnos` (presentation/turnos_router.py): GET /current, CRUD /casillas, CRUD
  /slots, POST /slots/{id}/asignaciones (replace), GET/POST /overrides,
  PUT /overrides/{id}, POST /overrides/{id}/cancelar, GET /users. Administración gateada con
  `require_permission(MANAGE_ADMIN)`.
- Frontend: features/turnos/ (api/turnos-api.ts, components/admin/casillas-manager.tsx,
  types/turnos.ts), ruta app/(app)/admin/turnos. La home consume /api/turnos/current para el
  timeline "Turnos del día" (features/home/, handoff design_handoff_inicio/).

Coberturas temporales (ADR-013, ya extraídas a shared por ser 3 módulos):
- VO genérico `AsignacionOverride[TOperadorId, TAlcanceId]`
  (shared/domain/value_objects/asignacion_override.py): ausente, reemplazante, desde, hasta
  (obligatorio, nunca vigencia abierta), alcance TOTAL | frozenset, estado ACTIVA/CANCELADA.
- `resolver_override_aplicable` / `resolver_operador_efectivo` / `hay_solapamiento`
  (shared/domain/services/asignacion_override_resolver.py). Se resuelve en lectura, no toca el
  dato titular, vence solo. LIMITACIÓN CLAVE que motiva este prompt: un override reemplaza
  `user_id` en un slot existente — no puede correr hora_inicio/hora_fin, crear ni eliminar
  franjas.

Módulo `vacaciones` (backend/src/modules/vacaciones/, migrado de VacaSync, Fase 3 del plan):
- `Solicitud` (empleado_id, start_date, end_date, days_requested, status EstadoSolicitud,
  método solapa_con). `Empleado.user_id: uuid | None` es el vínculo opcional con `app_user` —
  ESTE es el puente de identidad hacia turnos (turno_asignacion.user_id → app_user.id).
- `DecidirSolicitud` (application/use_cases/decidir_solicitud.py): aprueba/rechaza con
  registro en `RegistradorAuditoria`. Permisos view/create/approve/manage con VO
  `ActorVacaciones`; decisiones D1–D11 en backend/src/modules/vacaciones/README.md (leerlo
  antes de tocar el módulo).
- UI: pantallas de design_handoff_vacaciones/ ya implementadas (dashboard, solicitudes,
  aprobaciones, reportes, asistencias, gestión humana).

Precedentes de cruce entre módulos (NO acoplar módulos directamente, lint-imports lo bloquea):
- ADR-009: patrón dependency_overrides para inyección cruzada.
- `sla` lee datos de prestadores vía puerto propio + implementación en su infraestructura
  (SqlAlchemyPrestadorLookup) — el módulo consumidor define el Protocol, su infra lee las
  tablas del otro módulo. Usar este mismo patrón para vacaciones→turnos.

Lo que NO existe en la app (no inventarlo):
- Jornadas laborales, horarios de ingreso/egreso y almuerzos de los operadores NO están
  modelados en ninguna tabla. No crear un modelo de RRHH para validarlos: las validaciones de
  la variante son estructurales (solapes, continuidad), no de convenio.
- No hay ninguna integración vacaciones↔turnos hoy (verificado por grep cruzado: cero
  referencias).

Caso real que motiva y sirve de aceptación (ver [EJEMPLO]): la grilla titular de INSUMOS/ST
no se pudo cubrir con overrides al salir M. J. Vela de vacaciones — hubo que re-cortar 5 de
7 franjas.

Restricciones del entorno (CLAUDE.md, regla dura): datos de dev reales de producción, SMTP
real configurado, jobs de fondo con efectos reales. Antes de levantar el backend:
DISABLE_BACKGROUND_JOBS=true en .env + docker compose up -d --force-recreate backend +
verificar con printenv. NO hay hot reload: tras editar, recrear/reiniciar y verificar con
curl. No reactivar jobs sin pedido explícito del usuario.

[OBJETIVO]
Implementar el modo vacaciones end-to-end: primero el ADR y la decisión de forma, después el
vertical slice completo.

ADR-025 (docs/adr/025-modo-vacaciones-grilla-variante-turnos.md), documentando esta decisión:

  Elegida — VARIANTE DE GRILLA CON VIGENCIA (extensión natural de ADR-013 al eje horario):
  un conjunto alternativo de slots+asignaciones para un rango de fechas, resuelto en lectura;
  al vencer, la grilla titular vuelve sola sin acción ni job.
  Descartada A — editar slots titulares con snapshot/restore: toca el dato titular, exige
  paso de reversión (manual o job) — es exactamente el problema que se quiere eliminar.
  Descartada B — extender el VO compartido AsignacionOverride con cambio de horarios:
  retuerce una abstracción que contadores/prestadores usan con otra semántica; un override
  seguiría sin poder crear/eliminar franjas.

BACKEND — módulo `turnos` (mismo patrón módulo→capa):
  - Tablas nuevas (migración Alembic reversible, probar upgrade/downgrade/upgrade):
    · `turno_grilla_variante`: id UUID PK, motivo String nullable, desde Date NOT NULL,
      hasta Date NOT NULL, estado Enum(ACTIVA, CANCELADA) default ACTIVA, created_by_user_id
      FK app_user.id, created_at/updated_at. Sin FK a vacaciones (módulos independientes);
      campo opcional `origen_texto` String nullable para trazabilidad humana (ej.
      "solicitud vacaciones M. J. Vela 24–28/08").
    · `turno_grilla_variante_slot`: id, variante_id FK CASCADE, casilla_id FK turno_casilla,
      dia_semana SmallInteger, hora_inicio/hora_fin Time, sort_order.
    · `turno_grilla_variante_asignacion`: variante_slot_id FK CASCADE, user_id FK app_user.
  - Dominio: entidad `GrillaVariante` + invariantes en el caso de uso de creación/edición
    (ValidationError / BusinessRuleViolationError, mismos tipos de error que ya usa el
    módulo):
    · desde <= hasta, ambos obligatorios — temporal por diseño, igual ADR-013.
    · No solapamiento de vigencia entre variantes ACTIVAS (una sola grilla vigente por
      fecha; misma validación en caso de uso que ADR-013, misma ventana de carrera aceptada
      — ABM de baja frecuencia).
    · Dentro de la variante, por casilla+día: hora_inicio < hora_fin y franjas sin solape
      entre sí. Los huecos de cobertura NO son error (pueden ser deliberados, ej. INSUMOS
      abre 8:30 sin nadie 8–8:30) — se reportan como advertencia en el DTO de validación,
      no bloquean.
    · Un mismo user_id en dos franjas que se solapan (cualquier casilla) es error duro.
    · CANCELADA es la única reversión anticipada; sin DELETE físico ni vuelta a ACTIVA
      (mismo criterio de historial que ADR-013). Editar solo variantes ACTIVAS.
  - Resolución en lectura: `GetCurrentShifts`/`TurnoResolver` — si existe variante ACTIVA
    vigente en target_date, los slots del día salen de la variante; si no, de la grilla
    titular. Los overrides ADR-013 con alcance TOTAL siguen aplicando sobre la variante
    (cubren por persona, no por slot); los de alcance parcial referencian turno_slot.id
    titulares y por lo tanto NO aplican a slots de variante — documentar esa asimetría en el
    ADR y en el docstring del resolver.
  - Endpoints (mismo router /api/turnos, misma dependency MANAGE_ADMIN para administrar):
    · GET /grilla-variantes (+ filtro vigentes), POST /grilla-variantes (payload completo:
      cabecera + slots + asignaciones), PUT /grilla-variantes/{id} (reemplazo in-place,
      mismo id, solo ACTIVA — mismo criterio que la edición de overrides del 2026-08-14),
      POST /grilla-variantes/{id}/cancelar.
    · POST /grilla-variantes/precarga?ausente_user_id=&desde=&hasta=: devuelve la grilla
      titular con los slots del ausente marcados (huecos a resolver) como punto de partida
      del editor. Solo lectura, no persiste.
    · GET /current: agregar al DTO `variante_activa: {id, motivo, desde, hasta} | null`
      para el badge de la home. Cambio aditivo, no romper el contrato existente.

BACKEND — integración vacaciones→turnos (patrón PrestadorLookup de sla + ADR-009):
  - En `vacaciones`, puerto `ImpactoTurnosLookup` (Protocol en domain/repositories/):
    `tiene_turnos_en(user_id, desde, hasta) -> bool` (asignaciones vigentes de turnos que
    intersectan el rango). Implementación en infrastructure/ leyendo turno_asignacion +
    turno_slot. Sin imports de código de turnos en domain/application (lint-imports).
  - `DecidirSolicitud`: al aprobar, si el empleado tiene user_id vinculado y
    tiene_turnos_en(rango) es true, incluir en el resultado un aviso
    `afecta_turnos: {user_id, desde, hasta}`. NO crear la variante automáticamente: el caso
    real demostró que re-cortar la grilla exige criterio humano (almuerzos y jornadas no
    están modelados). El aviso alimenta el CTA del frontend.
  - Mejora simétrica en `turnos` (opcional pero barata, decidir y justificar en 1 línea):
    puerto inverso `AusenciasLookup` para que el editor de variante advierta si un user
    asignado como cubriente tiene vacaciones APROBADAS solapadas — dato real disponible
    (solicitudes + ausencias del módulo vacaciones vía Empleado.user_id).

FRONTEND (Next.js App Router, componentes y convenciones existentes del proyecto):
  - Editor de variante en features/turnos/, accesible desde /admin/turnos (tab o sección
    "Modo vacaciones" junto al manager de casillas): elegir ausente + rango (dos BrandInput
    type=date, patrón establecido — no DateRangePicker custom), botón "Precargar" (llama a
    /precarga), edición de franjas por casilla/día (re-cortar límites, crear, eliminar,
    asignar operadores con el mismo GET /users), validación en vivo espejando las reglas del
    backend (solapes = error; huecos = advertencia visible tipo "INSUMOS sin cobertura
    8:00–8:30"), guardar → POST completo. Modales por estado local, no por ruta.
  - Aprobaciones de vacaciones: cuando la decisión devuelve afecta_turnos, banner con CTA
    "Armar grilla de cobertura →" hacia el editor precargado por query params. Mismo estilo
    de banner que ya usa el módulo.
  - Home: badge en la card del timeline cuando /current trae variante_activa ("Grilla de
    vacaciones hasta el DD/MM"), estilo de badges existente. El timeline en sí no cambia —
    ya renderiza lo que /current resuelva.
  - Listado de variantes (vigente + programadas + historial) con cancelar, en la misma
    sección del admin. Estados Programada/Vigente/Vencida derivados por fecha en el cliente
    (la DB solo persiste ACTIVA/CANCELADA — mismo criterio que Coberturas).

TESTS:
  - Unit dominio: resolver con variante vigente (usa slots de variante), sin variante
    (titulares), variante vencida/cancelada (titulares), override TOTAL sobre variante,
    invariantes de creación (solape de vigencias, solape de franjas, user duplicado en
    franjas solapadas, desde>hasta).
  - Integración API: ABM completo + precarga + /current con y sin variante + aviso
    afecta_turnos en la decisión de solicitud.
  - Playwright: spec del editor (precargar caso [EJEMPLO], re-cortar, advertencia de hueco,
    guardar) + badge de home, siguiendo frontend/tests/coberturas.spec.ts como referencia
    de estilo.
  - El caso [EJEMPLO] completo como test de aceptación backend: dada la grilla titular y la
    variante cargada, resolve_shifts de un miércoles dentro de vigencia devuelve exactamente
    la grilla esperada; el miércoles siguiente (vencida), la titular.

[FORMATO]
Trabajá en este orden y reportá al final de cada etapa: (1) leer ARCHITECTURE_GUIDE.md,
CLAUDE.md, ADR-013, backend/src/modules/vacaciones/README.md y el módulo turnos completo;
(2) escribir ADR-025 y validarlo con el usuario antes de codear; (3) migración + dominio +
casos de uso + endpoints con tests en verde; (4) integración vacaciones; (5) frontend;
(6) verificación en vivo (curl + navegador) con el caso [EJEMPLO] cargado en dev y capturas.
Commits en inglés (convención del historial); reportes y textos de UI en español de
Argentina. lint-imports/ruff/mypy/pytest en verde en cada commit.

[RESTRICCIONES]
- NO tocar la grilla titular (turno_slot/turno_asignacion) desde ningún flujo nuevo — la
  variante es una capa aparte que se resuelve en lectura.
- NO modificar el VO compartido AsignacionOverride ni el resolver de shared — el modo
  vacaciones no pasa por ahí.
- NO crear jobs de fondo, ni acciones programadas, ni mails nuevos. El vencimiento es por
  comparación de fechas en lectura, sin job (principio ADR-013). No tocar
  VACACIONES_MAIL_ENABLED.
- NO escribir en Gestión ni en Siges. NO tocar módulos ajenos salvo los puertos descriptos.
- NO crear modelo de jornadas/almuerzos de RRHH — fuera de alcance, no hay dato en la app.
- NO usar DELETE físico para variantes; cancelación como única baja.
- Backend siempre con DISABLE_BACKGROUND_JOBS=true (verificado con printenv) antes de
  levantar contenedores; sin hot reload, recrear y verificar con curl.
- Migraciones reversibles probadas a mano (upgrade/downgrade/upgrade), como todas las del
  repo.
- Aditivo sobre /current: no romper el contrato que ya consume la home.

[EJEMPLO]
Caso de aceptación real — vacaciones de M. J. Vela (user vinculado a "Maria Jose Vela"),
24 al 28/08/2026, con refuerzo puntual de Mariana Rodriguez solo en ST 8–9.

Grilla titular (L–V, igual todos los días):
  INSUMOS: 8–11 Majo · 11–13 Luna · 13–17 Mariano · 17–18 Victor
  ST:      9–13 Victor · 13–15 Majo · 15–18 Luna

Variante esperada (vigencia 2026-08-24 → 2026-08-28, motivo "Vacaciones M. J. Vela"):
  INSUMOS: 8:30–11 Mariano · 11–13 Luna · 13–17 Mariano · 17–18 Victor
  ST:      8–9 Mariana · 9–14 Victor · 14–18 Luna

Comportamiento esperado:
  - Del 24 al 28/08, /current y el timeline de la home muestran la variante + badge
    "Grilla de vacaciones hasta el 28/08"; Majo no aparece en ninguna franja.
  - El editor mostró como advertencia (no error) el hueco INSUMOS 8:00–8:30 — decisión
    consciente del negocio, quedó guardada así.
  - El lunes 31/08 a primera hora, sin que nadie toque nada, /current vuelve a resolver la
    grilla titular con Majo en 8–11 y 13–15.
  - La aprobación de la solicitud de vacaciones de Majo devolvió afecta_turnos y el banner
    con CTA apareció en Aprobaciones.
```

---

## Notas de contexto para quien use este prompt (fuera del prompt en sí)

- **Verificado contra el código el 2026-08-20**: entidades/tablas/endpoints/resolver de
  `turnos`, VO y resolver compartidos de ADR-013, entidades y use case de decisión de
  `vacaciones` (incluido `Empleado.user_id` como puente de identidad), ausencia total de
  integración vacaciones↔turnos, y la limitación de los overrides (sustituyen persona, no
  redefinen franjas). Los detalles finos de DTOs de `/current` y permisos exactos deben
  releerse al implementar — el prompt pide cambios aditivos justamente por eso.
- **Por qué asistido y no automático**: el armado de la grilla de la semana 24–28/08 (ver
  `docs/coberturas/PLAN_COBERTURA_VACACIONES_MAJO_2026-08-24.md`) dependió de reglas que la
  app no conoce (jornadas, almuerzos, "Mariano solo INSUMOS", "Mariana solo ST 8–9"). Con
  esas reglas fuera del sistema, cualquier auto-asignación sería inventada. La precarga +
  validación estructural + advertencias es el máximo honesto automatizable hoy.
- **La semana del 24/08 no espera esta feature**: se resuelve editando la grilla titular a
  mano según el plan de cobertura citado, con reversión manual el 31/08. Este prompt elimina
  esa clase de operación para la próxima vez.
- Numeración ADR: el último es 024 (hay dos 016 en la carpeta — no heredar ese desvío).
