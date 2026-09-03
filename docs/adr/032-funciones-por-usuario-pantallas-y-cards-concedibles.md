# ADR-032: "Funciones" por usuario — pantallas y cards concedibles desde la grilla de permisos

## Estado: Aceptado (2026-08-21)

## Contexto

El modelo de permisos es usuario × módulo × acción (ADR-005/007/029): `view`, `create`,
`update`, `delete`, `approve`, `export`, `manage`. Con eso, qué **pantalla o card** veía cada
usuario quedaba decidido por reglas en código sobre las acciones (p. ej. "Coberturas de
contadores requiere `manage`", "Dashboard de Personal requiere `approve|manage`", "la card
'Distribución del parque' requiere `prestadores.update`"). Funcionaba, pero el admin no podía
decidir por usuario "a este operador sí Coberturas, a aquel no" sin tocar código. El usuario pidió
explícitamente (2026-08-21) que **todo lo que se fue sacando/poniendo sea editable por UI**.

Alternativa descartada: hacer editables las reglas globales (una pantalla de Configuración que
diga "Coberturas requiere Ver/Administrar"). Es más chica, pero sigue siendo global: no permite
excepciones por usuario, que es justo lo pedido.

## Decisión

1. Segunda capa de permisos, **por usuario**: **funciones** (`module_feature`, sembrado por
   migración como `module_action`) con grants propios (`user_feature_grant`). Una función es una
   pantalla o card concreta de un módulo. Las **acciones siguen mandando para crear/editar/
   aprobar**; las funciones deciden **qué pantallas/cards se ven**. Superadmin las tiene todas
   implícitas.
2. Catálogo inicial (14): Contadores → coberturas, anexos sin facturar, clientes nuevos, "Sin
   contador real: ver todos los clientes", card "Contadores por operador"; Prestadores →
   coberturas, card "Distribución del parque"; Gestión de Personal → dashboard, registro de
   asistencias, gestión humana, reportes, auditoría, configuración, card "Próximos días del
   equipo". Solicitudes/Aprobaciones quedan como acciones (`create`/`approve`); "Automatización"
   de Contadores queda atada a `export` (ya era una casilla de la grilla).
3. **Backfill sin sorpresas** (migración `c3e5a7b9d1f2`): cada función se concede a quien la
   veía por la regla vigente hasta hoy (`manage`, `approve|manage`, `create|update` según el
   caso), auditado en `permission_audit` con `module_key='feature'`. Nadie ve ni más ni menos
   hasta que un admin edite.
4. Enforcement:
   - Frontend: `useSession().hasFeature(key)`; el mapa central de rutas admite `feature` además
     de `anyOf` (acciones); las cards de Inicio se gatean por función; los submenús se filtran
     solos.
   - Backend: `require_feature(FeatureKey)` / `tiene_feature(identity, key)` en los endpoints
     donde el dato cambia o es sensible (anexos, clientes nuevos, "sin contador real" todos vs.
     míos, reportes/auditoría/configuración de Personal). Donde la API ya acota por actor (p. ej.
     ausencias), la función gatea solo la pantalla.
   - `/api/auth/me` devuelve `features`; admin: `GET /api/admin/catalog/features`,
     `GET|PUT /api/admin/users/{id}/features`.
5. **Grilla de permisos**: debajo de cada módulo con funciones aparece la fila "Pantallas y
   funciones" con sus casillas; mismo "Guardar" (permisos y funciones se guardan juntos). Las
   plantillas Team leader / Team leader + Configuración incluyen todas las funciones; Operador y
   Solo lectura, ninguna.

## Ampliaciones del catálogo

- **2026-09-03 — Insumos → "Administración"** (`insumos-administracion`, migración
  `d4f6a8b2c0e1`): el apartado Administración del submenú (Clientes, Configuración,
  Estadísticas) se abría con `insumos.view`, así que cualquier operador podía tocar clientes y
  parámetros. Pasa a ser una función; el backend la exige a nivel router en
  `customers_router`, `config_router` y `statistics_router`. Backfill **deliberadamente
  restrictivo** (excepción al punto 3): se concede a quien tiene `insumos.delete` (nivel Team
  leader en las plantillas); los operadores la pierden, que es lo pedido.

## Regla para módulos nuevos (complementa ARCHITECTURE_GUIDE §8)

Si una pantalla/card debe poder concederse por usuario independientemente de las acciones del
módulo: fila en `module_feature` (migración, con backfill si reemplaza una regla), constante en
`modules/<m>/domain/well_known_features.py`, `require_feature` en su endpoint cuando expone datos
propios, entrada `feature:` en `route-permissions.ts` o guard de card, y sumarla a `FUNCIONES_TL`
en las plantillas.

## Consecuencias

- Positivas: el admin decide por usuario qué ve cada uno, sin código; se conserva el modelo
  módulo × acción para las mutaciones; auditoría única.
- Negativas/costos: dos listas que mantener al agregar pantallas (catálogo + plantilla); la grilla
  es más larga. Una función sin `require_feature` en backend es solo UX (el mapa de rutas), por
  eso se documenta cuáles tienen enforcement de API.
