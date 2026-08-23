# ADR-033: Preferencias del dashboard de Inicio por usuario, en `auth`, gateadas solo por sesión

## Estado: Aceptado (2026-08-23)

## Contexto

El rediseño de Inicio del 2026-08-22 agregó "Personalizar" (qué paneles ve cada usuario y con
qué vista abre) guardado en `localStorage` por usuario/navegador. La TL quiere que esa
configuración viaje con la cuenta (misma Inicio en la PC de la oficina y en la notebook).
Hay dos precedentes de "dato del propio usuario" en el repo: la nota personal (especificada,
no implementada: `docs/MASTER_PROMPT_NOTA_PERSONAL_INICIO.md`) y la telemetría de rutas de
accesos directos (`/api/me/route-visits`, ADR-028), que ya resolvió la misma pregunta.

## Decisión

1. **Vive en el módulo `auth`**, como `route-visits`: es un atributo del usuario logueado,
   no un módulo de negocio; no se crea un módulo nuevo ni filas en el catálogo de permisos.
2. **Endpoint `/api/me/inicio-prefs` (GET/PUT), gateado solo por `get_current_identity`**:
   todo usuario logueado tiene sus preferencias; el `user_id` sale siempre de la sesión, nunca
   del body ni de la URL (nadie lee ni escribe las de otro). PUT es idempotente y reemplaza el
   conjunto completo.
3. **Tabla `user_dashboard_prefs`** (una fila por usuario, PK = FK a `app_user` con `ON DELETE
   CASCADE`, `hidden_cards JSONB`, `initial_view`, `updated_at`), migración reversible. Los ids
   de card son los del registro del frontend (`dashboard-registry.ts`): se validan por forma
   en la entidad `DashboardPrefs` (slug, ≤32, sin repetidos, vista ∈ {hoy, seguimiento}), no
   contra un catálogo — el frontend ignora ids que ya no existan, así el registro puede
   cambiar sin migración.
4. **Frontend**: el servidor es la fuente de verdad; `localStorage` queda como caché para
   pintar al instante y respaldo si el backend no responde (`use-dashboard-prefs.ts` es el
   único lugar que conoce ambos).

## Consecuencias

- Positivas: la personalización es por cuenta y multi-dispositivo; el vertical slice es chico
  (entidad, repo, 2 use cases, router, migración) y sigue un patrón ya aceptado; cero
  permisos nuevos que administrar.
- Negativas: una tabla más en `auth`; si algún día se quisiera "personalización por rol"
  (defaults por TL/operador), habría que sumar una capa de defaults — no está en este alcance.

## Addendum 2026-08-23: la nota personal sigue el mismo patrón

La nota personal de Inicio (`docs/MASTER_PROMPT_NOTA_PERSONAL_INICIO.md`) se implementó con
esta misma decisión en vez de un módulo `notas` nuevo: entidad `UserNote` (tope 4000
caracteres validado en dominio y espejado en el schema y en el textarea), tabla `user_note`
(una fila por usuario, FK a `app_user` con cascade), `GET/PUT /api/me/nota` solo por sesión,
autosave con debounce de 800 ms + blur (nunca por tecla). La card "Mi nota" entra en la vista
Hoy del registro y se puede ocultar desde Personalizar. Regla general que queda: **los datos
personales del usuario logueado (preferencias, nota, telemetría de rutas) viven en `auth`
bajo `/api/me/...`, gateados solo por identidad de sesión**, sin filas en el catálogo de
permisos.
