# ADR-013: Override temporal de asignación de operadores (contadores y prestadores)

## Estado: Aceptado

## Contexto

Hoy, cuando un operador se va de vacaciones o falta, la única forma de que sus clientes/PST
queden atendidos por otro operador es modificar la fuente externa:

- En `contadores`, editar el calendario de Gestión (la web scrapeada) — lento, invasivo sobre
  un sistema de terceros, y contamina el dato "real" de quién tiene asignado cada evento.
- En `prestadores`, `AssignOperador` (`application/use_cases/assign_operador.py`) sí es una
  operación propia del monorepo, pero es **permanente y secuencial por diseño**: reasignar
  cierra el tramo vigente de `AsignacionHistorial` (`hasta = None` → `hasta = fecha`) y abre uno
  nuevo. No hay forma de decir "durante estas dos semanas, además de Juan, que también vea estos
  PST Pedro" sin perder el registro de que Juan es el titular real.

Se necesita una capa de sustitución/override propia de HelpDeskManager, con vigencia acotada por
rango de fechas, que se resuelva en lectura sobre la copia local (`contadores_calendar_events` /
`contadores_operadores` en un caso, `prestador` / `prestador_asignacion_historial` en el otro)
sin escribir nunca en Gestión ni en Siges, sin borrar la asignación original, y reversible al
vencer sin intervención manual.

`contadores` y `prestadores` modelan "operador" de forma incompatible — no hay forma limpia de
compartir una única tabla:

- `contadores`: el operador es un username externo de Gestión (`Operador.id: str`, tabla
  `contadores_operadores`), **poblada por sync y podada** (`prune_operadores_not_in`) cada vez
  que un operador deja de tener eventos en la ventana de ±90 días sincronizada. Una FK dura a
  esta tabla se rompería cada vez que el sync poda una fila.
- `prestadores`: el operador es un `AppUser` real del monorepo (`Prestador.operador_id: UUID`,
  FK a `app_user.id`, ya usado así en `prestador_asignacion_historial`). Es un catálogo durable,
  no se poda nunca.

No existe (ni se justifica crear) un contrato `.importlinter` entre `contadores` y
`prestadores` — son módulos de negocio independientes (mismo principio que
`contadores-independent-from-insumos`). El patrón de `dependency_overrides` de ADR-009 resuelve
cruces donde un módulo necesita un dato que vive en otro; acá no hace falta: cada módulo
resuelve su propio "operador efectivo" con su propia tabla, sin que ninguno necesite leer datos
del otro.

## Decisión

Dos tablas nuevas, una por módulo, mismo patrón conceptual, sin tabla ni FK compartida entre
módulos.

### `contadores_asignacion_override` (Postgres, migración Alembic nueva)

| Columna | Tipo | Notas |
|---|---|---|
| `id` | UUID PK | `gen_random_uuid()` |
| `operador_ausente_id` | String NOT NULL | username de Gestión — **sin FK** a `contadores_operadores.id` (se poda con el sync; ver Contexto). Se valida contra el catálogo vigente solo en el momento de creación, en el caso de uso, no en el schema. |
| `operador_reemplazante_id` | String NOT NULL | ídem, sin FK |
| `vigente_desde` | Date NOT NULL | |
| `vigente_hasta` | Date NOT NULL | obligatorio — nunca vigencia abierta, por diseño (ver Invariantes) |
| `alcance_tipo` | Enum(`TOTAL`, `CLIENTE`) NOT NULL | |
| `estado` | Enum(`ACTIVA`, `CANCELADA`) NOT NULL default `ACTIVA` | cancelación manual antes de vencer |
| `motivo` | String nullable | texto libre ("vacaciones", "licencia") |
| `created_by_user_id` | UUID FK `app_user.id` | auditoría de quién cargó la regla — sí tiene FK, `app_user` es durable |
| `created_at` / `updated_at` | timestamptz | |

`contadores_asignacion_override_cliente` (tabla hija, solo si `alcance_tipo = CLIENTE`):
`override_id` (FK CASCADE), `cliente` (String). El campo `cliente` de `CalendarEvent` es texto
libre, sin catálogo con ID propio (mismo tipo de aproximación ya aceptado para `Operador.color`
en `contadores`) — el matching de alcance es por igualdad exacta de string, no por FK.

### `prestadores_asignacion_override`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | UUID PK | |
| `operador_ausente_id` | UUID FK `app_user.id` NOT NULL | catálogo durable → FK real |
| `operador_reemplazante_id` | UUID FK `app_user.id` NOT NULL | |
| `vigente_desde` / `vigente_hasta` | Date NOT NULL | |
| `alcance_tipo` | Enum(`TOTAL`, `PRESTADOR`) NOT NULL | |
| `estado` | Enum(`ACTIVA`, `CANCELADA`) NOT NULL default `ACTIVA` | |
| `motivo` | String nullable | |
| `created_by_user_id` | UUID FK `app_user.id` | |
| `created_at` / `updated_at` | timestamptz | |

`prestadores_asignacion_override_prestador` (tabla hija, solo si `alcance_tipo = PRESTADOR`):
`override_id` (FK CASCADE), `prestador_id` (FK `prestador.id` CASCADE — acá sí hay catálogo
durable, FK real igual que `prestador_asignacion_historial.prestador_id`).

### Entidad de dominio (forma equivalente en ambos módulos, ejemplo `contadores`)

```python
@dataclass(slots=True, eq=False)
class AsignacionOverride:
    id: uuid.UUID
    operador_ausente_id: str
    operador_reemplazante_id: str
    vigente_desde: date
    vigente_hasta: date
    alcance: Literal["TOTAL"] | frozenset[str]  # frozenset de clientes si es alcance parcial
    estado: Literal["ACTIVA", "CANCELADA"]
    motivo: str | None
```

### Algoritmo de resolución — "operador efectivo en fecha X"

```
operador_efectivo(operador_original, fecha, criterio_alcance):
    reglas = repo.find_vigentes(
        operador_ausente=operador_original, fecha=fecha, estado="ACTIVA"
    )  # vigente_desde <= fecha <= vigente_hasta
    for r in reglas:
        if r.alcance == "TOTAL":
            return r.operador_reemplazante_id
        if criterio_alcance in r.alcance:  # criterio_alcance = evento.cliente o prestador_id
            return r.operador_reemplazante_id
    return operador_original
```

Se resuelve **en lectura**, evaluado por caso de uso contra la copia sincronizada existente
(`event_date` en `contadores_calendar_events`, o la fecha de consulta en `prestadores`) — nunca
se reescribe `operador_id` en los eventos ni se toca `prestador.operador_id` /
`prestador_asignacion_historial`. Al vencer `vigente_hasta`, el sistema vuelve solo al operador
original sin ninguna acción adicional, porque la regla simplemente deja de matchear la fecha.

### Invariantes

- `vigente_desde <= vigente_hasta`, ambos obligatorios: valida `ValidationError` en el caso de
  uso de creación — nunca vigencia abierta (`hasta = NULL`), a diferencia de
  `AsignacionHistorial.hasta`, que sí admite `NULL` para "tramo vigente". Acá la regla del
  negocio es "temporal por diseño", así que se refuerza en el modelo, no solo por convención.
- No solapamiento de vigencia para el mismo `operador_ausente_id`: se evaluó un `EXCLUDE
  USING gist` de Postgres (`btree_gist`, `daterange(vigente_desde, vigente_hasta, '[]') &&`) para
  forzarlo a nivel de schema, pero se descartó — el alcance `CLIENTE`/`PRESTADOR` vive en una
  tabla hija de valores múltiples, y un `EXCLUDE` no puede expresar "no solapan si el conjunto de
  clientes/PST no se pisa" de forma limpia. Se valida en el caso de uso
  (`CreateAsignacionOverride`: leer reglas activas del mismo `operador_ausente_id` con rango
  solapado y, si alguna es `TOTAL` o comparte al menos un elemento de alcance, rechazar con
  `BusinessRuleViolationError`). Ventana de carrera aceptada a propósito: es un ABM de baja
  frecuencia (altas manuales, no un hot path), no justifica una `SELECT ... FOR UPDATE`.
- Cancelar (`estado = CANCELADA`) es la única forma de revertir antes de que venza
  `vigente_hasta` — no hay `DELETE`, para no perder el registro de que la regla existió.

## Consecuencias

- Positivas: reversible por diseño (vencimiento automático por fecha, sin job ni acción
  manual); no toca Gestión ni Siges ni la asignación permanente (`AssignOperador`,
  `AsignacionHistorial`); mismo patrón conceptual en los dos módulos sin forzar una tabla
  compartida que no tiene sentido de dominio (los dos "operador" no son el mismo tipo de dato).
- Negativas: dos implementaciones separadas (una por módulo) del mismo concepto, con la
  duplicación de código que eso implica — aceptado porque forzar una abstracción común hoy
  significaría o bien una tabla con una columna `operador_id` polimórfica (string a veces, UUID
  otras — mala idea) o bien introducir un tercer módulo compartido sin necesidad real todavía.
  El alcance por `cliente` en `contadores` es frágil (string libre, sin catálogo) — mismo tipo de
  aproximación ya aceptado para `Operador.color`; si en algún momento `cliente` pasa a tener ID
  propio en la copia sincronizada, migrar el alcance a ese ID.
- Revisar esta decisión si aparece un tercer módulo con la misma necesidad: en ese punto sí
  vale la pena extraer un value object/servicio de resolución genérico a `shared` (no una tabla
  compartida, solo el algoritmo de resolución y las validaciones de invariantes).
