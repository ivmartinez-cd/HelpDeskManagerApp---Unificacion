# ADR-028: Telemetría de navegación por usuario, en `auth`, sin permiso nuevo

## Estado: Aceptado

## Contexto

La pantalla de Inicio necesita una fila de "accesos directos" a las pantallas que cada
operador más usa, con un ranking **real** (no una lista adivinada): las rutas más visitadas
por el usuario logueado en los últimos 30 días.

Esto exige registrar, para cada usuario, qué rutas visita y con qué frecuencia — un endpoint
que persiste una lectura del comportamiento de navegación de la propia sesión. `ARCHITECTURE_GUIDE.md`
§8 exige "autorización verificada (no solo autenticación)" en su checklist de endpoints, y
CLAUDE.md es taxativo: una desviación consciente del texto literal de la guía se documenta acá
o es una violación, no una decisión.

Se evaluaron dos preguntas de diseño: **dónde vive la feature** y **cómo se autoriza**.

### Dónde vive

1. **Módulo nuevo** (`telemetria`/`navegacion`). Exige: fila seed en `module` + pares en
   `module_action` + migración de activación + dos contratos nuevos en `.importlinter`
   (`*-domain-no-frameworks`, `*-domain-app-independent-from-auth`). Sobrecosto real para una
   feature que no tiene ni necesita control de acceso diferenciado.
2. **Dentro de `auth`**. El ranking es por usuario (`app_user` vive ahí) y la validación de
   cada ruta necesita confirmar que su primer segmento sea un módulo habilitado — es decir,
   necesita leer el catálogo `module`, que también vive en `auth`. Leerlo desde cualquier otro
   módulo sería un import de `auth.domain`/`auth.application` prohibido por todos los
   contratos `*-domain-app-independent-from-auth` del `.importlinter` (ADR-007). No hace falta
   ningún contrato nuevo: `auth-domain-no-frameworks` ya cubre el VO agregado.

### Cómo se autoriza

1. **Permiso nuevo** `(module="me"|"telemetria", action="view"|"record")`. Implicaría una fila
   de `module` con `is_enabled`, y `require_permission` es fail-closed contra `is_enabled`
   **incluso para superadmin** (ver `ForbiddenError` en `auth/domain/errors.py`) — un módulo
   deshabilitado por error rompería la fila de accesos directos de todos los usuarios, para
   una feature que no distingue roles.
2. **Solo autenticación** (`get_current_identity`), sin permiso. El `user_id` sale siempre de
   la identidad de la sesión, nunca del body ni de la query — un usuario no puede escribir ni
   leer el ranking de otro por construcción. Mismo criterio que ya usan `GET /api/auth/me`,
   `GET /api/auth/modules` y `POST /api/auth/password/change` en el mismo módulo: recursos
   sobre el propio usuario, gateados por identidad de sesión y nada más.

## Decisión

La feature vive en `auth`, en un router separado (`auth/presentation/route_visits_router.py`,
`auth_router.py` ya está en 202 de 300 líneas) con prefijo **`/api/me/route-visits`** — no
`/api/auth/...`, para que la URL exprese el modelo de autorización real: el recurso es el
propio usuario, no una operación de autenticación. Se autoriza únicamente con
`get_current_identity`, sin permiso `(module, action)`.

Contra el abuso, sin rate limiting HTTP (no hay middleware de ese tipo en el repo y la app no
está expuesta a internet — §8 lo condiciona a eso), tres guards estructurales baratos:

- `RoutePath` (VO de dominio) valida forma y tamaño de cada ruta antes de persistirla.
- El primer segmento tiene que ser un `ModuleKey` de un módulo habilitado en el catálogo.
- Tope de 60 rutas *distintas* por usuario y día, y purga inline (mismo POST) de filas con más
  de 90 días — sin job de fondo aparte. Cota dura resultante: 60 × 90 = 5.400 filas por
  usuario.

El esquema es un contador agregado `user_route_visit (user_id, visit_date, route,
visit_count)` con upsert (`ON CONFLICT DO UPDATE ... visit_count + 1`), no un event log — una
fila por navegación no aporta nada al ranking y crece sin techo.

## Consecuencias

- Positivas: cero migraciones de catálogo, cero contratos nuevos de import-linter, URL que no
  miente sobre qué protege el endpoint, tabla acotada por diseño sin scheduler adicional.
- Negativas: si en el futuro este endpoint necesitara distinguir comportamiento por rol (por
  ejemplo, un superadmin viendo el ranking de otro usuario), hay que revisitar esta decisión y
  sumar el permiso que hoy se evitó a propósito.
- Riesgo aceptado y no mitigado acá: `Field(max_length=128)` en el schema Pydantic no impide
  que Starlette lea un body grande antes de validar — no hay middleware de límite de tamaño de
  body en el repo; agregarlo excede el alcance de esta feature.
- POSTs repetidos a la misma ruta el mismo día cuestan una tupla muerta cada uno (MVCC) aunque
  no crean fila nueva — mitigación del lado del frontend (postear una vez por montaje de ruta,
  no por cada render); autovacuum se ocupa del resto.
