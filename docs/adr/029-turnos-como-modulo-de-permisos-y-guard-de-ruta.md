# ADR-029: Turnos como módulo de permisos propio, poda del catálogo y guard de ruta en el frontend

## Estado: Aceptado (2026-08-21)

## Contexto

El sistema de permisos (ADR-005: catálogo `module`/`action`/`module_action` en tablas; ADR-007:
vocabulario en `shared/`, `require_permission` en `auth.presentation`) se diseñó con cinco
módulos y después se fueron agregando los demás. Relevamiento del 2026-08-21:

- **`turnos` nunca se sembró como módulo.** Sus 23 endpoints (`/api/turnos*`) se protegían con
  `admin.manage` prestado de auth: dar acceso a la grilla de turnos obligaba a dar acceso a
  usuarios y permisos, y en la grilla de admin no había nada que tildar para turnos.
- **`coberturas`** (feature de frontend con tres pantallas, una por módulo dueño) no tenía
  vocabulario propio; la de turnos heredaba `admin.manage`.
- **Filas muertas en el catálogo**: `stc` (módulo entero, sin una línea de backend),
  `insumos.export`, `analisis-log-hp.export`, `vacaciones.update` — se podían tildar y ningún
  código las chequeaba. `liquidaciones.export` también estaba sembrada sin enforcement, pero sí
  tenía endpoints reales de export CSV (pedían `view`).
- **El frontend no tenía guard de ruta por permiso**: `proxy.ts` solo mira la cookie; cualquier
  logueado abría `/admin/usuarios`, `/liquidaciones`, etc. y solo recibía 403 de la API. Varias
  pantallas no gateaban sus botones de mutación con `can()`.
- El grupo "Servicio Técnico" del sidebar estaba hardcodeado y siempre visible, incluso para
  quien no tenía ninguno de los módulos que agrupa.

## Decisión

1. **`turnos` es módulo del catálogo** con dos acciones: `view` (consultar casillas, franjas,
   coberturas y grillas de vacaciones) y `manage` (toda mutación, incluidas coberturas e
   intercambios). `GET /api/turnos/current` sigue siendo solo-sesión a propósito (es la card de
   Inicio de cada operador). Migración `b9d4e7a1c3f2`: siembra el módulo habilitado
   (backend y pantalla ya estaban en uso) y **backfillea** `turnos.view`+`turnos.manage` a quien
   tuviera `admin.manage`, auditado como `grant` sin actor.
2. **Coberturas no es módulo**: cada pantalla usa la acción de mutación del módulo dueño
   (`turnos.manage`, `contadores.manage`, `prestadores.create/update`). Agregar un cuarto
   módulo de permisos solo para eso duplicaría la decisión de quién puede tocar qué.
3. **Poda del catálogo** (misma migración): se borran `stc` y las tres acciones muertas; los
   grants colgados quedan auditados como `revoke`. `stc` se vuelve a sembrar cuando exista el
   módulo. `liquidaciones.export` se conserva y **pasa a exigirse** en los cinco endpoints de
   export CSV (antes `view`).
4. **Turnos sale de `/admin`**: las páginas pasan de `/admin/turnos[/coberturas]` a
   `/turnos[/coberturas]` (con `redirects()` en `next.config.ts` para links viejos), porque la
   ruta del módulo en el catálogo alimenta el sidebar y no tiene sentido que un módulo con
   permiso propio cuelgue de Configuración.
5. **Guard de ruta por permiso en el frontend**, con una sola fuente de verdad:
   `frontend/src/shared/config/route-permissions.ts` (ruta → `anyOf` permisos). La consumen
   `RouteGuard` (client component en el layout de `(app)`: redirige a `/` con un toast y no
   renderiza la página) y los submenús del sidebar (ocultan ítems inaccesibles). Una ruta sin
   entrada **no se bloquea** (fail-open a nivel página): el enforcement real sigue siendo
   `require_permission` en el backend; esto es UX para no aterrizar en pantallas que solo
   devuelven 403. Es client-side porque los layouts de Next no se re-renderizan en
   navegaciones suaves: solo algo que observe `usePathname()` ve cada cambio de ruta.
6. "Servicio Técnico" se muestra solo si el usuario tiene al menos uno de los módulos que
   agrupa.

## Regla para módulos nuevos (ver también ARCHITECTURE_GUIDE.md §8)

Un módulo o pantalla nueva no está terminado hasta que tenga las cuatro patas:
(a) seed en el catálogo por migración (`module` + `module_action`), (b)
`modules/<m>/domain/well_known_permissions.py` y `require_permission(...)` en cada endpoint,
(c) entrada en `route-permissions.ts`, (d) `can()` en los botones de mutación.

## Consecuencias

- Positivas: turnos se concede sin regalar Configuración; la grilla de admin deja de ofrecer
  permisos que no hacen nada; nadie aterriza en pantallas 403; agregar una pantalla con
  permiso distinto al del módulo es una línea en `route-permissions.ts` y los submenús la
  respetan solos.
- Negativas/costos: usuarios con `liquidaciones.view` pero sin `export` pierden la descarga
  CSV hasta que un admin les tilde `export` (en dev no había ninguno). El `downgrade` de la
  migración borra todos los grants de turnos (no distingue backfilleados de manuales).
  Quedan fuera de este ADR, como deuda conocida: `user_module_scope` (alcance por sector) sigue
  sin lógica; `contadores` muta bajo `manage` sin `create/update/delete`; el link a WATI se
  gatea solo por env.
