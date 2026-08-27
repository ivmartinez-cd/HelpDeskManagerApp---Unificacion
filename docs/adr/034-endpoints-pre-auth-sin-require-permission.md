# ADR-034: Endpoints pre-auth sin `require_permission`/`require_feature`

## Estado: Aceptado (2026-08-27)

## Contexto

`scripts/guards-baseline.json` acepta como deuda conocida un grupo de endpoints
detectados por `check_guards.py` como `no-authz` (sin `require_permission`,
`require_feature` ni siquiera `get_current_identity`):

- `backend/src/modules/auth/presentation/auth_router.py::login`
- `backend/src/modules/auth/presentation/auth_router.py::logout`
- `backend/src/modules/auth/presentation/auth_router.py::forgot_password`
- `backend/src/modules/auth/presentation/auth_router.py::reset_password`
- `backend/src/shared/presentation/health/router.py::get_health`
- `backend/src/shared/presentation/health/router.py::get_health_db`
- `backend/src/shared/presentation/health/router.py::post_echo`

ARCHITECTURE_GUIDE.md §8 pide documentar como ADR toda desviación consciente de
las reglas de autorización, en vez de dejarla como una entrada muda en el
baseline. Estas siete nunca tuvieron ADR propio — se agregaron directo al
baseline al escribir `check_guards.py` (2026-08-22) porque el motivo parecía
obvio, pero "obvio" no es lo mismo que "por escrito".

## Decisión

Los siete endpoints quedan **exceptuados de la autorización por permiso/feature**
por diseño, no por descuido:

1. **`login`**: es el único endpoint que *establece* la identidad — no puede
   exigir una identidad previa. Rate limiting y validación de credenciales son
   su propio control de acceso.
2. **`logout`**: opera sobre la cookie de sesión del propio caller (ADR-004,
   sesión opaca por cookie); no expone ni muta datos de otro usuario. Un caller
   sin sesión válida no tiene nada que cerrar.
3. **`forgot_password` / `reset_password`**: flujo de recuperación — por
   definición se ejecuta cuando el usuario **no puede** autenticarse. El
   control de acceso es el token de un solo uso enviado por mail, no un
   permiso de módulo.
4. **`get_health` / `get_health_db`**: probes de infraestructura (usados por
   Docker healthcheck / orquestación) que no exponen datos de negocio, solo
   `{"status": "ok"}`. Exigir sesión rompería el healthcheck del propio
   contenedor.
5. **`post_echo`**: sonda de desarrollo que ejercita el envelope de errores de
   validación 422 (la usa `tests/integration/test_error_handling.py`); devuelve
   únicamente el payload que el caller mandó, sin leer ni escribir estado.

Condición que revierte esta decisión (por endpoint): si alguno empieza a leer o
exponer datos que no sean explícitamente públicos (ej. `login` devolviendo más
que el resultado de autenticar, o `health` sumando métricas internas), ese
endpoint sale de la excepción y pasa a exigir `require_permission`/
`require_feature` o, como mínimo, `get_current_identity`.

## Consecuencias

- La entrada `no-authz` de estos siete endpoints en
  `scripts/guards-baseline.json` queda amparada por este ADR en vez de ser una
  excepción implícita — coincide con el patrón ya usado para las entradas
  `sql-fstring` (ADR-018) y `list-no-page` (ADR-021).
- Cualquier endpoint nuevo que aparezca como `no-authz` en `check_guards.py`
  sin encajar en una de las cinco razones de arriba necesita su propio ADR, no
  sumarse a esta lista por analogía.
