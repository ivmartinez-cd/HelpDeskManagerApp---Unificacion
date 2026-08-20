# ADR-025: Modo vacaciones de turnos — variante de grilla con vigencia

## Estado: Aceptado (2026-08-20)

## Contexto

Las coberturas temporales de ADR-013 (`turno_asignacion_override`) reemplazan **quién** atiende
una franja existente: sustituyen `user_id` en un `turno_slot` durante un rango de fechas, se
resuelven en lectura y vencen solas. Su límite quedó expuesto con el primer caso real
(`docs/coberturas/PLAN_COBERTURA_VACACIONES_MAJO_2026-08-24.md`): al salir M. J. Vela de
vacaciones del 24 al 28/08/2026 la grilla de INSUMOS/ST no se pudo cubrir con overrides porque
hubo que **re-cortar 5 de 7 franjas** (8–11 → 8:30–11, 9–13 → 9–14, 15–18 → 14–18, eliminar
13–15, crear ST 8–9). Un override no puede correr `hora_inicio`/`hora_fin`, ni crear ni eliminar
franjas. La única opción era editar la grilla titular a mano y acordarse de revertirla el 31/08 —
exactamente la carga operativa (y el riesgo de olvido) que ADR-013 vino a eliminar para el caso
simple.

Se necesita, entonces, poder definir **una grilla completa alternativa** (franjas + operadores)
para un rango de fechas, sin tocar la titular y sin paso de reversión.

## Opciones evaluadas

**A — Editar los slots titulares con snapshot/restore.** Guardar una copia de `turno_slot` +
`turno_asignacion`, editar la titular y restaurar al vencer. Descartada: toca el dato titular
(la "verdad" de la grilla deja de ser estable mientras dura la variante), y exige un paso de
reversión — manual (el olvido es el problema original) o por job (CLAUDE.md: los jobs de fondo
de este repo tienen efectos reales y están desactivados en dev; además `replace_for_slot` cierra
asignaciones con historial, así que restaurar no es un "volver atrás" limpio sino otra edición).

**B — Extender el VO compartido `AsignacionOverride` con cambio de horarios.** Agregar
`hora_inicio`/`hora_fin` opcionales al override. Descartada: el VO vive en `shared` porque lo
usan `contadores` y `prestadores` con otra semántica (ahí no existe "horario"); torcerlo para
turnos rompe la abstracción que justificó extraerlo. Y aun extendido, un override sigue atado a
un `turno_slot` existente: no puede crear ST 8–9 ni eliminar ST 13–15.

**C — Variante de grilla con vigencia (elegida).** Un conjunto alternativo de slots +
asignaciones, con `desde`/`hasta` obligatorios, que el resolver usa **en lugar de** la grilla
titular cuando la fecha consultada cae dentro de la vigencia. Es la extensión natural de
ADR-013 al eje horario: se resuelve en lectura, no toca el dato titular, vence sola por
comparación de fechas.

## Decisión

### Tablas (módulo `turnos`, migración Alembic reversible)

| Tabla | Columnas |
|---|---|
| `turno_grilla_variante` | `id` UUID PK · `motivo` String(200) nullable · `origen_texto` String(200) nullable (trazabilidad humana, ej. "Solicitud de vacaciones M. J. Vela 24–28/08"; **sin FK a vacaciones**, módulos independientes) · `desde` Date NOT NULL · `hasta` Date NOT NULL · `estado` String(20) NOT NULL default `ACTIVA` + CHECK (`ACTIVA`/`CANCELADA`) — mismo almacenamiento que `turno_asignacion_override.estado`, sin tipo enum de Postgres para mantener el downgrade trivial · `created_by_user_id` FK `app_user` RESTRICT · `created_at`/`updated_at` timestamptz · CHECK `desde <= hasta` |
| `turno_grilla_variante_slot` | `id` UUID PK · `variante_id` FK CASCADE · `casilla_id` FK `turno_casilla` CASCADE · `dia_semana` SmallInteger (0=lunes…6=domingo) · `hora_inicio`/`hora_fin` Time · `sort_order` Integer · CHECK `hora_inicio < hora_fin` |
| `turno_grilla_variante_asignacion` | `variante_slot_id` FK CASCADE · `user_id` FK `app_user` CASCADE · PK compuesta |

Las franjas de la variante tienen **ids propios** (no referencian `turno_slot`): la variante es
una grilla completa, no un diff sobre la titular.

### Dominio

Entidad `GrillaVariante` (`domain/entities/grilla_variante.py`) con sus `VarianteSlot`
(cada uno con su lista de `user_ids`). Reglas puras en
`domain/services/grilla_variante_reglas.py`, aplicadas por los casos de uso de alta y edición:

- `desde <= hasta`, ambos obligatorios — temporal por diseño, igual ADR-013
  (`InvalidVarianteRangeError`, `ValidationError`).
- Una sola variante **ACTIVA** vigente por fecha: no se solapan vigencias entre variantes
  activas (`OverlappingVarianteError`, `BusinessRuleViolationError`). Validado en el caso de uso
  con la misma ventana de carrera aceptada en ADR-013 (ABM manual de baja frecuencia). La
  variante que se edita se excluye a sí misma del universo comparado.
- Al menos una franja: una variante vacía haría desaparecer la grilla completa durante la
  vigencia por un click en falso (`VarianteSinFranjasError`).
- Por casilla + día: `hora_inicio < hora_fin` (`VarianteFranjaInvalidaError`) y franjas sin
  solape entre sí (`VarianteFranjasSolapadasError`).
- Un mismo `user_id` en dos franjas que se solapan en el mismo día, en cualquier casilla, es
  error duro (`VarianteOperadorSolapadoError`): una persona no atiende dos casillas a la vez.
- **Los huecos de cobertura NO son error**: pueden ser deliberados (el caso real deja INSUMOS
  sin nadie 8:00–8:30). Se calculan comparando la cobertura titular de esa casilla+día contra la
  de la variante y se devuelven como **advertencias** en el DTO (`AdvertenciaCoberturaDTO`,
  tipo `HUECO`), igual que una franja sin operadores (`SIN_OPERADOR`) o un cubriente con
  vacaciones aprobadas solapadas (`OPERADOR_AUSENTE`, ver abajo). No bloquean el guardado.
- `CANCELADA` es la única reversión anticipada: sin `DELETE` físico ni vuelta a `ACTIVA`
  (mismo criterio de historial que ADR-013). Solo se edita una variante `ACTIVA`
  (`VarianteNoEditableError`); la edición es in-place, mismo `id`, reemplazo completo de
  cabecera + franjas + asignaciones (mismo criterio que la edición de overrides del
  2026-08-14).

### Resolución en lectura

`TurnoResolver.resolve_shifts(..., variante=...)`: si hay una variante ACTIVA vigente en
`target_date`, las franjas y asignaciones del día salen de la variante (materializadas como
`Slot`/`Asignacion` con los ids de la variante); si no, de la grilla titular. `GetCurrentShifts`
busca la variante vigente con `GrillaVarianteRepository.find_vigente(fecha)` y la pasa al
resolver. Al vencer `hasta`, la titular vuelve sola: no hay job, acción programada ni mail.

**Asimetría con los overrides ADR-013, documentada a propósito:** los overrides de alcance
`TOTAL` cubren por persona y siguen aplicando sobre la variante (si Luna está cubierta por Pedro,
Pedro aparece también en las franjas de la variante). Los de alcance parcial referencian
`turno_slot.id` titulares y, como las franjas de la variante tienen ids propios, **no aplican**
mientras la variante está vigente. Es consecuencia directa de "la variante es una grilla
completa, no un diff", y la alternativa (mapear franjas titulares ↔ variante por heurística de
horario) sería frágil: la variante puede recortar o partir franjas. Quien necesite cubrir una
franja puntual de la variante edita la variante.

### Endpoints (`/api/turnos/grilla-variantes`, permiso `admin:manage`)

`GET` (+ `?vigentes=true`), `POST` (cabecera + franjas + asignaciones, devuelve el DTO con
advertencias), `PUT /{id}` (reemplazo in-place, solo ACTIVA), `POST /{id}/cancelar`,
`POST /precarga?ausenteUserId=&desde=&hasta=` (solo lectura: la grilla titular con las franjas
del ausente marcadas como huecos a resolver, punto de partida del editor). Van en un router
propio (`grilla_variantes_router.py`) porque `turnos_router.py` ya supera las 300 líneas de
§4 — mismo prefijo, misma dependency de permiso.

`GET /api/turnos/current` gana `varianteActiva: {id, motivo, desde, hasta} | null` como campo
adicional del envelope (`CurrentShiftsResponse`, subclase de `Page[ResolvedShiftResponse]`):
cambio aditivo, `items/total/page/size` no cambian.

### Integración vacaciones → turnos (patrón `PrestadorLookup` de `sla` + ADR-009)

- `vacaciones` define el puerto `ImpactoTurnosLookup.tiene_turnos_en(user_id, desde, hasta)`
  en su `domain/repositories/`; la implementación vive en `vacaciones/infrastructure/` y lee
  `turno_asignacion` + `turno_slot` (asignaciones vigentes que intersectan el rango y cuyo
  `dia_semana` cae en algún día del rango). Contrato nuevo de import-linter
  `vacaciones-domain-app-independent-from-turnos`.
- `DecidirSolicitud`, al **aprobar**, si el empleado tiene `user_id` vinculado y
  `tiene_turnos_en` es verdadero, devuelve `afecta_turnos: {user_id, desde, hasta}` junto con
  la solicitud; la respuesta de `POST /solicitudes/{id}/decision` lo expone como
  `afectaTurnos` (aditivo). **No se crea la variante automáticamente**: el caso real demostró
  que re-cortar la grilla exige criterio humano (jornadas y almuerzos no están modelados en la
  app y no se van a modelar — fuera de alcance). El aviso alimenta el CTA "Armar grilla de
  cobertura →" de Aprobaciones, que abre el editor precargado por query params.
- Puerto inverso `AusenciasLookup` en `turnos` (implementado): al guardar una variante se
  advierte si un cubriente asignado tiene vacaciones **aprobadas** solapadas con la vigencia.
  Justificación en una línea: es el dato real que más probablemente invalida una grilla de
  cobertura y cuesta un `Protocol` + una query sobre `vacaciones_solicitud`/`vacaciones_empleado`.
  Contrato `turnos-domain-app-independent-from-vacaciones`.

## Consecuencias

- Positivas: cubre el caso real sin tocar `turno_slot`/`turno_asignacion` ni el VO compartido;
  reversible por diseño (vencimiento por fecha, sin job); el historial de variantes queda
  (cancelación, no borrado); la home y cualquier consumidor de `/current` reflejan la variante
  sin cambios propios.
- Negativas: duplicación conceptual entre `turno_slot` y `turno_grilla_variante_slot` (misma
  forma, ids distintos) — aceptada a cambio de no referenciar la titular desde la variante; los
  overrides parciales no aplican durante una variante (ver asimetría); crear la variante exige
  cargar la grilla completa del rango (mitigado por `precarga`).
- Revisar si aparece la necesidad de variantes **parciales** (solo una casilla, o solo algunos
  días): hoy la variante reemplaza la grilla completa del día para todas las casillas. Si hace
  falta, el camino es una variante por casilla, no volver a los overrides con horario.
