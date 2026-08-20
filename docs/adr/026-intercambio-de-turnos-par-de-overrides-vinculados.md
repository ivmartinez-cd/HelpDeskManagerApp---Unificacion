# ADR-026: Intercambio de turnos como par de coberturas vinculadas

## Estado: Aceptado (2026-08-20)

## Contexto

El caso operativo que dispara esta decisión: dos operadoras (M. J. Vela y Luna) se cambian el
horario por un día — cada una atiende las franjas de la otra. Las coberturas de ADR-013
(`turno_asignacion_override`) modelan una **sustitución unidireccional**: un ausente, un
reemplazante, un rango de fechas, un alcance. No existe la noción de reciprocidad.

Verificado contra el código antes de decidir:

- `TurnoResolver._operador_efectivo` resuelve **un solo salto** por franja: toma el titular de la
  franja y le aplica los overrides cuyo `operador_ausente_id` es ese titular
  (`turno_resolver.py:130-141`). No encadena overrides. Por eso dos coberturas cruzadas
  (A→B y B→A, mismo rango) ya producen hoy el resultado correcto: las franjas de A las
  muestra B y las de B las muestra A, sin ciclo.
- `hay_solapamiento` compara solo coberturas **del mismo ausente**
  (`asignacion_override_resolver.py:51-67`): las dos cruzadas no conflictúan entre sí.

Es decir, el intercambio ya se puede *reflejar* cargando dos coberturas a mano. Lo que no cierra
es el modelo operativo: quedan registradas como dos "ausencias" de gente que no faltó, el motivo
no lo expresa, y cancelar o editar una sin la otra deja un estado inconsistente (Luna cubriendo a
Majo mientras Majo sigue figurando en sus propias franjas, o al revés).

## Opciones evaluadas

**A — Dejarlo como dos coberturas manuales (status quo).** Descartada: no hay vínculo entre las
dos filas, la cancelación parcial es un error esperable, y el listado no dice que fue un
intercambio.

**B — Entidad nueva `Intercambio` con su propia tabla y su propia resolución.** Descartada:
duplicaría en el resolver exactamente la lógica de sustitución que ya existe, y el resolver de
un solo salto ya produce el efecto deseado a partir de dos overrides — no hay nada nuevo que
resolver, solo algo nuevo que *agrupar*.

**C — Par de overrides vinculados (elegida).** Un intercambio **es** dos coberturas cruzadas
creadas en una misma transacción y unidas por un `intercambio_id` común. El dominio, el resolver
y las validaciones de ADR-013 no cambian; lo que se agrega es el agrupamiento (crear, editar y
cancelar las dos juntas) y su exposición en la UI como una sola fila.

## Decisión

### VO compartido

`AsignacionOverride` (`shared/domain/value_objects/asignacion_override.py`) gana el campo
opcional `intercambio_id: uuid.UUID | None = None` (último, con default — cambio aditivo, ningún
constructor existente cambia). No es una deformación del VO como la descartada en ADR-025
(opción B, horarios): "dos sustituciones cruzadas forman un intercambio" es una relación válida
en los tres módulos que usan el VO (en contadores o prestadores también podrían intercambiarse
carteras). Hoy solo `turnos` lo persiste y lo expone; `contadores` y `prestadores` lo ignoran
(sus repositorios no lo leen ni lo escriben), y el resolver compartido no lo mira.

### Persistencia (módulo `turnos`, migración Alembic reversible)

`turno_asignacion_override.intercambio_id` UUID nullable + índice. Sin tabla nueva: el par se
reconstruye con `list_by_intercambio(intercambio_id)`. Las dos filas del par comparten `desde`,
`hasta`, `motivo` y `created_by_user_id` por construcción (las escribe siempre el mismo caso de
uso).

### Casos de uso (`application/use_cases/`)

- `CreateIntercambio(operador_a, operador_b, desde, hasta, slot_ids_a, slot_ids_b, motivo)`:
  valida `desde <= hasta` y `a != b` (mismos errores de ADR-013), y el no-solapamiento **de cada
  lado** contra las coberturas activas de ese ausente (`OverlappingOverrideError`). Crea los dos
  overrides — `A ausente → B cubre` con alcance `slot_ids_a` (None = TOTAL) y `B ausente → A
  cubre` con alcance `slot_ids_b` — con el mismo `intercambio_id` y motivo por defecto
  "Intercambio". Es atómico por el límite de transacción por request de `get_db`.
- `UpdateIntercambio(intercambio_id, ...)`: reemplazo in-place de las dos filas (mismos ids),
  solo si ambas están `ACTIVA` (`OverrideNoEditableError`); cada lado se excluye a sí mismo y a
  su par del universo de solapamiento. Mismo criterio que la edición de overrides del 2026-08-14.
- `CancelIntercambio(intercambio_id)`: cancela las dos filas. Además, `CancelAsignacionOverride`
  sobre una fila que tiene `intercambio_id` cancela **todo el par** (nunca queda media
  permuta), y `UpdateAsignacionOverride` sobre una fila de intercambio se rechaza
  (`OverrideEsIntercambioError`, `BusinessRuleViolationError`): se edita por el endpoint de
  intercambio. `IntercambioNotFoundError` si el par no existe o no tiene exactamente dos filas.

### Endpoints (`/api/turnos/intercambios`, permiso `admin:manage`)

`POST` (alta, devuelve `{intercambioId, coberturas: [2 × AsignacionOverrideResponse]}`),
`PUT /{intercambio_id}` (mismo body que el alta), `POST /{intercambio_id}/cancelar`. Router
propio (`intercambios_router.py`) porque `turnos_router.py` ya supera las 300 líneas de §4.
`GET /api/turnos/overrides` gana `intercambioId: uuid | null` en cada item (aditivo): el
listado sigue devolviendo las dos filas, el frontend las agrupa.

### Frontend

Mismo modal de Coberturas con un toggle `Cobertura | Intercambio` arriba (decisión del usuario,
2026-08-20: un solo punto de entrada, no un botón aparte), habilitado **solo para `turno`** vía
`COBERTURA_CONFIG` (`intercambio: true/false`). En modo intercambio: "Operador A" / "Operador B",
mismas fechas (default un solo día), alcance Total o "Franjas específicas" con dos selectores
(franjas de A que toma B / franjas de B que toma A), motivo fijo. La tabla agrupa por
`intercambioId` en **una fila** con `⇄` entre ambos operadores; editar y cancelar llaman a los
endpoints de intercambio.

## Consecuencias

- Positivas: ningún cambio en el resolver ni en las reglas de ADR-013; la home y `/current` ya
  reflejan el intercambio sin cambios propios; el historial queda (cancelación, no borrado); el
  estado nunca queda a medias (par atómico en alta, edición y cancelación).
- Negativas: el listado `GET /overrides` sigue siendo plano (dos filas por intercambio) y el
  agrupamiento vive en el cliente — aceptado para no romper el contrato existente; la misma
  asimetría de ADR-025 aplica (un intercambio con alcance parcial no surte efecto mientras hay
  una grilla de vacaciones vigente, porque referencia `turno_slot.id` titulares).
- `contadores` y `prestadores` podrían adoptar el intercambio reutilizando el mismo campo del VO
  si surge el caso; hoy no se habilita (pedido del usuario).
