# Master Prompt — Nota personal en la pantalla de Inicio

Agregar a la pantalla de Inicio (`/`, `app/(app)/page.tsx`) una tarjeta de **nota personal**: cada
usuario autenticado puede escribir texto libre que se guarda y persiste entre sesiones y dispositivos.
Es una utilidad por-usuario (scratchpad), privada, NO un recurso compartido ni un módulo con permisos.

Generado el 2026-08-13 a partir del análisis del código real. Viabilidad y costo en DB ya evaluados
(ver "Notas de contexto" al final): es una feature barata y de bajo riesgo; el único cuidado real es la
cadencia de escritura (MVCC) y el tope de longitud, no el almacenamiento.

---

```text
[ROL]
Actuá como arquitecto/desarrollador senior full-stack del monorepo HelpDeskManagerApp---Unificacion
(FastAPI + SQLAlchemy async + Alembic + Next.js App Router, arquitectura módulo→capa
domain/application/infrastructure/presentation). Conocés y aplicás ARCHITECTURE_GUIDE.md y CLAUDE.md
del repo como reglas obligatorias. Respondés en español de Argentina, directo y sin relleno.

[CONTEXTO]
Se quiere una tarjeta de "nota personal" en la pantalla de Inicio para que cada usuario registrado
anote cosas y se guarden. Piezas reales verificadas contra el código (no supuestas):
- Identidad: `Identity` (`auth/application/dtos/results.py`) trae `user.id` (UUID), `user.email`,
  `user.is_superadmin`. Se obtiene con la dependency `get_current_identity`
  (`auth/presentation/dependencies/identity.py`), que valida la cookie de sesión opaca. La tabla de
  usuarios es `app_user` (`auth/infrastructure/models/user_model.py`).
- Autorización: existe `require_permission(...)` (`auth/presentation/dependencies/permissions.py`) +
  módulos con `is_enabled`, PERO esta feature NO va por ahí: es personal y la tiene que ver TODO
  usuario logueado. El gate correcto es solo `get_current_identity` (estar autenticado), sin grant de
  módulo ni fila en el catálogo de módulos.
- Home: `app/(app)/page.tsx` renderiza una grilla de cards (`ShiftDashboardCard`, `TodayClientsCard`,
  `SlaSummaryCard`). Las cards viven en `features/<x>/components/*.tsx` y son `"use client"`. Estilo:
  `rounded-[12px] border border-border bg-card p-5`, tokens de marca (`brand-orange`), dark-aware.
- HTTP client del frontend: `services/http-client.ts` (`httpClient.get/post/put/patch`), cookies con
  `credentials: "include"`, ya manda el header CSRF cuando exista la cookie.
- Backend: módulos en `backend/src/modules/<módulo>/`, cada uno domain/application/infrastructure/
  presentation; migraciones Alembic reversibles; routers se registran en
  `shared/presentation/app.py`. Postgres (`helpdesk-db`).

Restricciones del entorno (CLAUDE.md): datos de dev reales de producción, backend comparte contenedor
con jobs que mandan mails reales, y NO hay hot reload — tras editar hay que reiniciar el contenedor y
verificar con curl/navegador.

[OBJETIVO]
Implementar la nota personal end-to-end, en una decisión de forma tomada primero y luego el vertical
slice completo:

DECISIÓN DE FORMA (tomar antes de codear; default recomendado si no hay respuesta de la TL):
  - Una nota por usuario (scratchpad único que se pisa) [RECOMENDADO por simplicidad y costo] vs varias
    notas por usuario (lista con alta/baja). Este prompt asume la nota única; si se elige lista, agregar
    un cap por usuario (ej. 50) y endpoints de alta/baja.
  - Guardado: autosave con debounce (guardar tras N segundos de inactividad o al perder foco) vs botón
    "Guardar" explícito. Cualquiera sirve; NO guardar por tecla (genera bloat MVCC). Default: debounce
    ~800 ms + guardado al blur.
  - Tope de longitud del contenido (default: 8 KB / ~4000 caracteres), validado en backend y frontend.

BACKEND (módulo nuevo mínimo `notas`, módulo→capa; alternativa: carpeta bajo un módulo existente de
utilidades — justificar en 1 línea, no crear un módulo con permisos/catálogo):
  - domain: entidad `UserNote` (user_id, content, updated_at) + Protocol `UserNoteRepository`
    (get_by_user / upsert). Regla de dominio: validar tope de longitud (error de dominio propio, no
    HTTPException).
  - application: use cases `GetUserNote` y `SaveUserNote` (upsert) con DTOs de entrada/salida.
  - infrastructure: modelo SQLAlchemy `user_note` (`user_id UUID` PK y FK a `app_user(id)` ON DELETE
    CASCADE, `content TEXT NOT NULL DEFAULT ''`, `updated_at timestamptz`), repo SQLAlchemy con upsert
    (`INSERT ... ON CONFLICT (user_id) DO UPDATE`), y migración Alembic reversible.
  - presentation: router `GET /api/notas/me` y `PUT /api/notas/me` (upsert), ambos protegidos SOLO por
    `get_current_identity`; el `user_id` sale SIEMPRE de la identidad de la sesión, NUNCA del body/query
    (un usuario no puede tocar la nota de otro). Registrar el router en `shared/presentation/app.py`.

FRONTEND:
  - `features/home/components/personal-note-card.tsx` (`"use client"`): textarea con el contenido,
    estado de carga, indicador "Guardado"/"Guardando…", debounce + guardado al blur, tope de longitud
    con contador. Mismo lenguaje visual que `TodayClientsCard`.
  - `features/home/api/notas-api.ts`: `getMyNote()` / `saveMyNote(content)` sobre `httpClient`.
  - Montar la card en la grilla de `app/(app)/page.tsx`.

VERIFICACIÓN (parte del entregable, no opcional):
  - Backend en verde dentro del contenedor: `uv run lint-imports` + `ruff check src tests` +
    `mypy src` + `pytest tests/unit -q`; tests de integración del repo desde el HOST si aplica el patrón
    del repo (Postgres de test).
  - Frontend: `tsc` + `eslint` en verde; e2e Playwright si el módulo mantiene esa cobertura.
  - End-to-end real en el navegador: escribir, recargar la página → la nota persiste; loguearse con OTRO
    usuario → ve su propia nota vacía/distinta (aislamiento por usuario confirmado); llamada directa al
    endpoint intentando leer la nota de otro user_id → imposible por diseño (el id sale de la sesión).

[FORMATO]
- Todo texto al usuario en español de Argentina, directo, sin cortesías (regla de CLAUDE.md).
- Commits atómicos en inglés con la convención del historial (`feat(notas): ...`).
- Migración Alembic con up y down (reversible, §9 de la guía y ADR-002).
- Si se elige crear un módulo nuevo en vez de reusar uno, ADR corto en `backend/docs/adr/` explicando
  por qué (y por qué SIN permisos/catálogo de módulos), con el formato de los existentes.
- Al cierre: resumen de lo verificado con los comandos exactos corridos y su resultado real (no
  "debería andar"), incluida la verificación de aislamiento entre usuarios.

[RESTRICCIONES]
Operativas (innegociables, de CLAUDE.md):
- `DISABLE_BACKGROUND_JOBS=true` aplicado de verdad si se va a levantar el backend con jobs
  (`docker compose up -d --force-recreate backend`, verificado con printenv y el log de arranque —
  `docker restart` no relee `.env`).
- Sin hot reload: tras editar backend `docker restart helpdesk-manager-backend`; tras editar frontend
  `docker restart helpdesk-manager-frontend` (re-corre `next build`). Verificar con curl antes de dar
  por servido un cambio.

De arquitectura (ARCHITECTURE_GUIDE.md):
- Dependencias hacia adentro (Presentation→Application→Domain←Infrastructure); ningún módulo importa
  domain/application de otro (solo `shared/` y, para el FK, el modelo `AppUser` desde infrastructure).
- Toda escritura pasa por el use case; prohibido router→repo directo. SQL parametrizado / ORM, nunca
  concatenación (§8). Endpoint autenticado y autorizado por identidad de sesión (§8 checklist).
- Ningún `except Exception` silencioso (§6); archivo ≤300 líneas, clase ≤200, función ≤20 (§4). Si un
  endpoint devolviera colección (caso "varias notas"), envelope `Page[T]` (§11).
- Frontend: cuidado con `react-hooks/set-state-in-effect` (ya mordió en este repo) — nada de setState
  síncrono en efectos ni en catch alcanzable desde un efecto; usar promise-chain.

De negocio / privacidad:
- La nota es estrictamente por-usuario y privada: el `user_id` SIEMPRE viene de la sesión, jamás de
  input del cliente. No hay endpoint que liste notas de otros ni que las exponga.
- Tope de longitud validado en backend (fuente de verdad) y espejado en frontend. Rechazo prolijo
  (error de dominio → 4xx con code propio) si se excede, no un 500.
- Guardado con debounce/explícito, NO por tecla, para no generar bloat MVCC (ver Notas de contexto).
- Al eliminar un usuario, su nota se borra en cascada (FK ON DELETE CASCADE) — sin filas huérfanas.

[EJEMPLO]
Nota de cierre esperada:

  Nota personal en Inicio — cerrado y verificado (forma: nota única, autosave debounce 800ms + blur,
  tope 8 KB):
  - Backend módulo `notas`: entidad + use cases Get/Save (upsert), modelo `user_note` (PK=user_id FK
    app_user ON DELETE CASCADE), migración `xxxx` up/down aplicada a helpdesk-db.
  - Endpoints `GET/PUT /api/notas/me` protegidos por get_current_identity; user_id tomado de la sesión.
  - Frontend: `personal-note-card.tsx` montada en la grilla de Inicio; contador de caracteres; estado
    "Guardando…/Guardado".
  - lint-imports · ruff · mypy · pytest unit (+N nuevos) · tsc · eslint — en verde.
  - E2E real: escribí "probando", recargué → persiste; me logueé con otro usuario → nota vacía (aislada);
    PUT con content de 20 KB → 4xx por tope, sin 500.
  - Costo DB medido/estimado: fila ~<contenido>+~52 bytes overhead; con debounce, ~M updates por sesión.
```

---

## Notas de contexto para quien use este prompt (fuera del prompt en sí)

- **¿Es buena idea? Sí, y es barata.** La feature encaja en la arquitectura existente sin fricción:
  identidad ya resuelta por sesión, Home ya arma cards, Alembic ya está. Es un vertical slice chico.
- **El costo en DB es despreciable en almacenamiento.** Con el modelo de una nota por usuario, cada
  fila pesa ≈ 52 bytes de overhead fijo de Postgres (header de tupla + line pointer + `user_id` 16 +
  `updated_at` 8 + header del TEXT) más el contenido. Estimación por usuario: nota corta (~200 chars)
  ≈ 0,3 KB; nota típica (~1 KB) ≈ 1,1 KB; nota generosa con tope de 8 KB ≈ 8 KB. Aun con 500 usuarios y
  el tope al máximo, son ~4 MB totales: irrelevante para Postgres. El texto además comprime (Postgres
  TOAST-ea/comprime contenido por encima de ~2 KB).
- **El gasto real a cuidar es la frecuencia de escritura, no el espacio.** Cada `UPDATE` en Postgres
  crea una versión nueva de la fila (MVCC) y deja una tupla muerta que limpia autovacuum; autoguardar
  por tecla generaría bloat. Con debounce (o botón Guardar) son unos pocos updates por sesión — nada.
  Que `content` no esté indexado habilita HOT updates, que abaratan aún más el update.
- **Si se elige "varias notas por usuario"**, el costo por fila es el mismo pero deja de estar acotado:
  agregar un cap por usuario (ej. 50 notas) y el tope de longitud por nota. Sin el cap, un usuario podría
  crecer sin límite; con el cap, sigue siendo trivial.
- **Lo más importante no es el costo sino la privacidad**: el `user_id` tiene que salir siempre de la
  sesión, nunca del cliente. Es la única forma de garantizar que la nota de cada uno es suya y solo suya.
- **Decisión de no meterla en el sistema de permisos**: los módulos con `is_enabled`/`require_permission`
  son para features de negocio con acceso diferenciado. Una nota personal la tiene todo usuario logueado;
  meterla en el catálogo de módulos agregaría fricción (habría que grantearla) sin ningún beneficio.
