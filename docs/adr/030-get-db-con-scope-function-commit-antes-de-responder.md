# ADR-030: `get_db` se inyecta con `scope="function"` — el commit corre antes de enviar la respuesta

## Estado: Aceptado (2026-08-21)

## Contexto

`get_db` (`src/shared/infrastructure/database/session.py`) es el límite de transacción del
backend: entrega una `AsyncSession` por request y, al cerrar la dependencia, hace el único
`commit` (o rollback si el endpoint lanzó). Todos los routers la inyectan con `Depends(get_db)`.

FastAPI ≥ 0.118 agregó el parámetro `scope` a `Depends` para las dependencias con `yield`:

- `"request"` (**default**): el código después del `yield` corre **después** de enviar la
  respuesta al cliente.
- `"function"`: corre al terminar la *path operation*, **antes** de enviar la respuesta.

Con el default, el commit quedaba después de la respuesta. Consecuencias observadas el
2026-08-21 (FastAPI 0.141.1):

- **Login → `/api/auth/me` daba 401.** El navegador recibía la cookie, hacía `router.push("/")`
  y el layout consultaba `/me` en milisegundos, antes de que la fila de `user_session`
  estuviera commiteada. Reproducido 15/15 con el backend bajo carga (dashboards y poller de
  WATI abiertos); 0/5 con 300 ms de espera. El síntoma visible: toast "Bienvenido" y rebote a
  `/login`.
- Cualquier "escribo en un request y leo en el siguiente" (crear y listar, guardar permisos y
  recargar) podía perder la misma carrera.
- Un error en el `commit` (p. ej. una violación de integridad diferida) ocurría **después** de
  haber respondido 200: el cliente creía que la escritura existía.

## Decisión

Toda inyección de la sesión se declara `Depends(get_db, scope="function")`. Es un cambio
mecánico en los 63 archivos que la usaban (286 sitios), sin tocar la lógica de `get_db` ni
agregar commits explícitos en los endpoints (el de `login` que se había puesto como fix
puntual se retiró).

Se agrega `tests/unit/infrastructure/test_get_db_scope.py`, que recorre `src/` y falla si
aparece un `Depends(get_db)` sin scope — FastAPI no ofrece un default a nivel app, así que la
convención se hace cumplir por test.

Riesgos revisados antes de cambiar: ningún endpoint usa `BackgroundTasks` con la sesión
(quedaría cerrada antes de correr la tarea) y todas las `StreamingResponse` (CSV de
liquidaciones, Excel/PDF de vacaciones) arman el archivo en memoria antes de responder (no
leen de la DB mientras streamean).

## Consecuencias

- Positivas: semántica correcta de "respondí 200 ⇒ está commiteado"; los errores de commit
  llegan al handler de errores y se reportan como 500 en vez de perderse; desaparece la carrera
  del login.
- Negativas/costos: la respuesta espera al commit (milisegundos; era el comportamiento de
  FastAPI < 0.106 de todos modos). Si en el futuro un endpoint necesita usar la sesión después
  de responder (streaming perezoso desde la DB, background task con la misma sesión), no puede
  apoyarse en `get_db`: tiene que abrir su propia sesión y documentarlo.
