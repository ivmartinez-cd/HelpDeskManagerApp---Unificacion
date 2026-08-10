# Caracterización del frontend de SDSInsumos (Vue 3 → Next.js)

Relevamiento de `C:\Users\imartinez.CDSA\Desktop\proyectos\SDSInsumos\frontend` (Vue 3 +
Composition API + Vite + TypeScript + Tailwind 3), hecho para preparar la migración de
**SDSInsumos** — el siguiente módulo en la cola según `INTEGRACION_APPS_PLAN.md`, después de
Contadores. A diferencia del resto del monolito legacy (que ya era HTML/JS servido por
FastAPI, o en el caso de STC Cloud otro stack), SDSInsumos es la única app legacy que ya es una
SPA moderna con su propio framework — Vue en vez de React — así que el trabajo acá es de
**traducción de framework**, no de reconstrucción visual desde cero como en Contadores (que
partía de HTML/CSS estático).

Fuentes: lectura completa de `frontend/src/` (pages, components, composables, api/types.ts,
utils), `frontend/package.json`, `SDSInsumos/CLAUDE.md`, y ejecución real de la suite de tests
(`npm test -- --run`): **61/61 tests pasando en 13 archivos**, confirmando el comportamiento de
los composables más importantes (`usePolling`, `useSortableTable`, `useAlerts`) contra
implementación real, no solo lectura de código.

**Nota sobre `SDSInsumos/CLAUDE.md`:** el diagrama de `frontend/src/` en ese archivo está
desactualizado — dice `pages/ ← vistas (DashboardView, PedidosView, ClientesView,
ConfiguracionView)`, pero `PedidosView.vue` no existe en el árbol real (fue absorbida por
`HistorialView.vue`, pestaña "Pedidos Pendientes") y hay 4 vistas más no listadas
(`EquiposNuevosView`, `EquiposOfflineView`, `EstadisticasView`, `ClienteEstadisticasView`). Este
documento refleja el árbol real, verificado con `find src -type f`.

---

## 0. Lo más urgente: no hay handoff de diseño para este módulo

Se buscó en la raíz de `HelpDeskManager-Unificacion` cualquier carpeta `design_handoff_*` o
`MASTER_PROMPT_UI_UX_*` que mencione "insumos" o "SDS". **No existe ninguna.** Las únicas
carpetas `design_handoff_*` del repo son `Portal mesa de ayuda corporativo/design_handoff_mesa_de_ayuda`
y su duplicado `Portal mesa de ayuda corporativo_1/design_handoff_mesa_de_ayuda` — para el
módulo de mesa de ayuda, no para insumos. `MASTER_PROMPT_UI_UX_CONTADORES.md` tampoco es un
handoff: es un prompt de corrección de deuda de UI ya escrita en React para Contadores (después
de portado), no un diseño de referencia previo a portar.

Según la skill `ui-design-handoff` (regla del proyecto: "si no existe un handoff, parar y pedir
uno — nunca inventar colores/spacing/layout"), esto es **bloqueante** antes de escribir un solo
componente nuevo en `frontend/src/app/(app)/insumos/` o `frontend/src/features/insumos/`.

Hay una segunda razón, más específica que "no hay handoff", para no improvisar acá: **la UI
legacy de SDSInsumos ya tiene una identidad visual propia que rompe la regla de pureza de marca**
del resto del monolito. `frontend/src/style.css` define `--accent: #f7941d` (naranja
Institucional, correcto) pero también un segundo color protagonista, `--sds-blue: #00a4e4`, que
se usa extensivamente: estado activo de la sidebar, la píldora "Validando" completa (fondo +
borde + texto), el link "Ver diagnóstico", los tiles de Estadísticas ("Pedidos creados"), el
gráfico de tendencia (`TrendChart.vue`) y el `DateRangePicker`. Ese celeste no es ninguna de las
4 líneas de marca de Canal Directo documentadas (`#F7941D` Institucional, `#662D91` DaaS,
`#3DB1CA` Cartelería Digital, `#E32D91` Digitalización) — es casi seguro el azul del propio
portal HP Insight/SDS (no confirmado contra el manual de marca HP, pero coincide visualmente con
la paleta de HP PrintOS/Insight). Portarlo tal cual sería repetir el error ya documentado en
memoria del proyecto (`feedback_brand_purity_canal_directo`: notificación magenta y badge "Alta"
que hubo que recolorear a naranja). **Antes de la próxima sesión de UI, alguien tiene que decidir
explícitamente si ese celeste se mantiene (podría estar justificado como "color del proveedor
HP", no de Canal Directo, en piezas que representan datos de HP específicamente) o se reemplaza
por gris `#58595B`/naranja** — no es una decisión que se pueda tomar sola durante el port.

Acción recomendada para la próxima sesión: pedir al usuario un handoff nuevo (`design_handoff_sds_insumos/`)
con captura o export real de las 8 pantallas, o al menos una decisión explícita sobre el celeste
`--sds-blue` antes de tocar componentes.

---

## 1. Inventario de pantallas

Rutas definidas en `frontend/src/router.ts`. Todas menos el Dashboard son lazy (`import()`).

| Ruta | Vista | Propósito |
|---|---|---|
| `/` | `DashboardView.vue` | Pantalla principal: solicitudes de insumos de HP SDS pendientes de cargar en Canal Directo, agrupadas por cliente |
| `/pedidos` | *(redirect)* | Compat con bookmarks/notificaciones viejas → `/historial?tab=pendientes` |
| `/clientes` | `ClientesView.vue` | Habilitar/deshabilitar monitoreo por cliente + gestión de contactos por zona |
| `/equipos-nuevos` | `EquiposNuevosView.vue` | Equipos descubiertos en SDS sin registrar (no generan avisos de insumos hasta registrarse) |
| `/equipos-offline` | `EquiposOfflineView.vue` | Equipos sin reportar +72hs, candidatos a baja en SDS tras verificación contra Canal Directo |
| `/configuracion` | `ConfiguracionView.vue` | Umbrales de criticidad, auto-carga, alertas, notificaciones de escritorio, import de contactos SDS |
| `/historial` | `HistorialView.vue` | 5 pestañas: Pedidos Pendientes, Solo Pedidos, Acciones del Sistema, Todos, Mails enviados |
| `/estadisticas` | `EstadisticasView.vue` | Tendencia global de pedidos + ranking de clientes/SKUs, con selector de rango de fechas |
| `/estadisticas/clientes/:customerId` | `ClienteEstadisticasView.vue` | Detalle de un cliente: tiempos de atención, fallos, top SKUs/equipos, imprimible |

### 1.1 DashboardView (`/`) — la pantalla más compleja de la app

Archivo: `frontend/src/pages/DashboardView.vue`. Endpoints: `GET /api/dashboard`,
`GET /api/health`, `GET /api/requests?customerId=`, `POST /api/requests/{id}/load`,
`POST /api/requests/{id}/dismiss`, `GET /api/supply-scan/status`, `POST /api/supply-scan/run`,
más los que dispara el modal de detalle (ver 1.3).

- Tiles de resumen (Pendientes/Críticos/Urgentes/Atención/OK/Con pedido/Cargados hoy) con
  skeleton mientras carga.
- Tabla de clientes con solicitudes pendientes; cada fila es expandible (accordion) y muestra
  una tabla anidada de solicitudes individuales con checkbox de selección, carga individual o en
  lote, descarte individual o en lote, barra de progreso de nivel de tóner, badges de estado.
- **5 modales de confirmación distintos** disparados según la respuesta del backend a
  `POST /requests/{id}/load`: pedido duplicado (hoy / activo en CD), insumo ambiguo (elegir SKU
  entre varias opciones), equipo posiblemente en bodega (offline), ventana de validación
  pendiente (nivel sospechoso, countdown en vivo), confirmación de descarte.
- Countdown en vivo por fila "Validando" (reloj compartido de 1s, ver `useValidationCountdown`),
  con auto-refetch cuando el countdown llega a 0.
- Notificaciones de escritorio (Web Notifications API) al detectar nuevas solicitudes entre
  polls, más notificación in-app persistida en un store en memoria.
- Deep-link: `/?customerId=123` (desde una notificación) expande automáticamente ese cliente.
- Polling cada 60s (silencioso, sin toast) vía `useDashboardMetrics` + `usePolling`.
- Sección colapsable "Scan de supplies" (trigger manual de un re-scan del cache de Canal
  Directo) independiente del resto.

### 1.2 ClientesView (`/clientes`)

Endpoints: `GET /api/customers`, `POST /api/sync-customers`, `PATCH /api/customers/{id}`,
`POST /api/customers/bulk-toggle`, `GET/PUT/DELETE /api/customers/{id}/contacts`,
`GET /api/customers/{id}/sds-contacts` (piloto gateado a un solo `customerId` hardcodeado,
`8255`, ver línea 100 del componente).

- Buscador por nombre, toggle individual de monitoreo, toggle masivo (con `confirm()` nativo del
  navegador — dos `confirm()` de este tipo en toda la app, ver §5).
- Modal de contactos por zona con CRUD completo (crear/editar/renombrar/eliminar zona), más una
  sub-sección de solo lectura "Detectados en SDS" (piloto).
- Renombrar una zona es una operación no atómica desde el cliente: crea la zona nueva por PUT y
  después borra la vieja por DELETE — si el DELETE falla, queda duplicada. No hay compensación
  del lado del cliente.

### 1.3 EquiposNuevosView / EquiposOfflineView

Ambas comparten forma: tabla ordenable (`useSortableTable`, con persistencia de sort en
`localStorage`), búsqueda por texto, filtro, polling de 5 min, toggle ignorar/restaurar
por fila.

- **EquiposNuevosView**: filtro adicional por año de descubrimiento (default = año actual, para
  no tapar lo accionable con backlog histórico). Botón "Registrar" linkea al portal SDS externo.
- **EquiposOfflineView** es más compleja: agrupa filas en 6 secciones colapsables por estado
  verificado contra Canal Directo (bodega / otro cliente / en cliente / error / sin verificar /
  caída de colector), cada sección con su propio criterio de expandido-por-defecto. Selección
  múltiple + baja masiva (solo filas `deletable`, es decir confirmadas "en bodega"), con modal de
  confirmación (`OfflineDeleteModal`) y modal de ayuda estático (`OfflineHelpModal`, contenido
  puramente informativo). Banner de "caídas de colector" con 3 niveles de certeza (confirmado /
  aviso / posible).

### 1.4 ConfiguracionView

Endpoints: `GET/PUT /api/config`, más 2 endpoints propios para la herramienta de import
(`GET /api/customers/{id}/zone-contacts-import/preview`,
`POST /api/customers/{id}/zone-contacts-import/apply`).

Formulario largo (7 secciones) con `reactive()` + `v-model.number` para todos los umbrales
numéricos. Incluye lógica de UI sin contraparte de backend: test de notificaciones de escritorio
del navegador (Web Notifications API + Clipboard API para copiar la URL de ajustes de Chrome),
enlaces `ms-settings:` que abren paneles nativos de Windows. Esa sub-sección **no tiene
equivalente de backend que portar** — es pura interacción de browser/OS, hay que decidir si tiene
sentido en el contexto de una app corporativa servida por Next.js (probablemente sí, es soporte
real para el operador).

### 1.5 HistorialView — la vista con más estados de filtrado

Endpoints: `GET /api/audit`, `GET /api/orders/pending`, `GET /api/mail-log`,
`POST /api/requests/{id}/cancel`, `POST /api/requests/{id}/reconcile`.

5 pestañas sincronizadas con `?tab=` en la URL (vía `router.replace`, no `push`, para no ensuciar
el historial del navegador). Cada pestaña tiene su propio composable/componente:

- **Pedidos Pendientes** (default): `useSupplyPendingOrders` + `PendingOrdersTable.vue`, polling
  90s **solo mientras la pestaña está activa** (`pending.start()`/`.stop()` en un `watch` sobre
  `categoryFilter`) — es el endpoint más caro de la app (SOAP + Insight en paralelo).
- **Solo Pedidos / Acciones del Sistema / Todos**: comparten una tabla plana con filtro por tipo
  de evento, rango de fechas, búsqueda de texto y paginación client-side (25/50/100 filas). Cada
  fila puede tener una acción condicional: "Anular" (con `confirm()` nativo) si el pedido está
  activo, o "Vincular" (reconciliar un pedido huérfano que falló en apariencia pero puede haberse
  creado igual en Canal Directo) si aplica.
- **Mails enviados**: `MailLogTable.vue`, log de backups/alertas/avisos, carga lazy (recién al
  entrar a la pestaña).

### 1.6 EstadisticasView / ClienteEstadisticasView

Endpoints: `GET /api/estadisticas?start_date=&end_date=`,
`GET /api/estadisticas/clientes/{id}?start_date=&end_date=`.

- `DateRangePicker.vue`: selector de rango completamente custom (sin librería), con 8 presets y
  calendario de 2 meses navegable, sincronizado con querystring (`start_date`/`end_date`, para
  que el link sea compartible/recargable).
- `TrendChart.vue`: gráfico de área con ApexCharts, franjas de fin de semana como anotaciones de
  fondo (`weekendBands.ts`, lógica pura testeada).
- `ClienteEstadisticasView` agrega: tiempo de atención (horario laboral), tiempo
  Pendiente→Despachado, top SKUs/equipos, motivos de fallo, fallos recientes, y un modo de
  impresión completo (`@media print`, con `window.print()` y un header alternativo que solo se
  muestra al imprimir).

---

## 2. Mapa de manejo de estado / reactividad

**No hay Pinia, ni Vuex, ni ninguna librería de estado.** Tampoco hay websockets ni SSE en
ningún lugar del frontend — **todo el "tiempo real" de esta app es polling con `setInterval`**.
Dos patrones conviven:

### 2.1 Composables "de instancia" (estado local a quien los llama)

`useApi<T>()`, `useCustomerRequests()`, `useDashboardMetrics()`, `useDashboardModals()`,
`useOrderActions()`, `useSortableTable()`, `useSupplyPendingOrders()` — cada uno crea sus propios
`ref`/`reactive` internos y se instancia una vez por vista que lo necesita.
`DashboardView.vue` es el caso extremo: compone 5 de estos composables y les pasa dependencias
cruzadas entre sí (`useOrderActions` recibe `modals` de `useDashboardModals` y `selection` de
`useCustomerRequests`).

**Equivalente React directo:** un custom hook por composable (`useApi` → `useApi.ts` con
`useState`/`useRef` para el `AbortController`, igual al patrón ya usado en
`frontend/src/features/admin-users/hooks/use-admin-users.ts` del monolito nuevo — `useState` +
`useEffect` + un service de API, sin librería de fetching). La composición de 5 hooks en un solo
componente es más incómoda en React que en Vue (no hay nada como pasar un objeto composable
entero como prop de forma natural) — probablemente conviene colapsar `useDashboardMetrics` +
`useCustomerRequests` + `useDashboardModals` + `useOrderActions` en **un solo hook**
`useDashboardData()` que devuelva todo, en vez de 4 hooks separados que se pasan entre sí.

### 2.2 Estado "de módulo" (singleton compartido entre toda la app, patrón poor-man's-store)

`useNotificationStore.ts`, `useAlerts.ts`, `useTheme.ts`, `useToast.ts`,
`useValidationCountdown.ts` (el reloj compartido) declaran su `ref()` **fuera** de la función
exportada, a nivel de módulo — todas las instancias del composable en cualquier componente leen
y escriben el mismo estado. Es el mecanismo que reemplaza a Pinia acá.

**Esto no tiene equivalente directo con `useState` en React** (cada componente tendría su propia
copia). Opciones para el port, en orden de preferencia dado que el monolito nuevo no usa ninguna
librería de estado global todavía:
1. Un módulo con estado fuera de React + `useSyncExternalStore` (el equivalente literal en React
   del patrón Vue de este archivo — mismo mecanismo, sin dependencias nuevas).
2. Un React Context montado en el layout de `(app)/insumos/` si el estado es exclusivo del
   módulo (probablemente el caso de notificaciones/alertas de insumos).
3. Si `useTheme` termina siendo compartido con el resto del monolito (dark mode global), verificar
   primero si ya existe un mecanismo de tema en `frontend/src/app` antes de portar el de
   SDSInsumos — el monolito nuevo ya es "dark-by-default" con clase `.dark` en `<html>` según la
   skill `ui-design-handoff`, así que puede que no haga falta portar `useTheme.ts` en absoluto,
   solo homologar los tokens de color al sistema existente.

**Toasts:** `useToast.ts` es un mini-store de un solo mensaje con auto-hide — el monolito nuevo
ya usa `sonner` (visto en `use-admin-users.ts`: `import { toast } from "sonner"`). No portar
`useToast.ts`/`Toast.vue` tal cual: reemplazar por `sonner`, que ya es el estándar del resto de
la app.

### 2.3 Polling — inventario completo (todo vía `usePolling.ts`, `setInterval` + `visibilitychange`)

| Quién pollea | Endpoint | Intervalo | Condición |
|---|---|---|---|
| `useDashboardMetrics` (Dashboard) | `GET /api/dashboard` | 60s | Siempre que la vista esté montada |
| `TheSidebar` (global, toda la app) | `GET /api/dashboard` (badge) | 60s | Siempre (sidebar nunca se desmonta) |
| `TheSidebar` | `GET /api/new-devices/summary` | 5 min | Siempre |
| `TheSidebar` | `GET /api/offline-devices/summary` | 5 min | Siempre |
| `TheSidebar` | `GET /api/alerts` (+ ack tracking) | 60s | Siempre |
| `EquiposNuevosView` | `GET /api/new-devices` | 5 min | Solo si la vista está montada |
| `EquiposOfflineView` | `GET /api/offline-devices` | 5 min | Solo si la vista está montada |
| `HistorialView` (pestaña Pendientes) | `GET /api/orders/pending` | 90s | Solo si `categoryFilter === 'pendientes'` |

`usePolling.ts` refresca inmediatamente al volver a la pestaña (`visibilitychange` → si estaba
activo, dispara un tick ya) porque el navegador puede pausar/throttlear `setInterval` en pestañas
ocultas — esto importa particularmente para las notificaciones de escritorio, que dependen del
poll. Al portar a React, replicar con un hook `useInterval` + listener de
`document.visibilitychange`, o evaluar si conviene una librería de polling (`useSWR`/TanStack
Query con `refetchInterval` + `refetchOnWindowFocus`) — sería la primera vez que el monolito
nuevo introduce una librería de data-fetching, así que es una decisión a validar con el usuario,
no a tomar en silencio durante el port (el resto del monolito no usa ninguna hoy).

**La sidebar sola dispara 4 pollers simultáneos apenas se monta la app** (dashboard, equipos
nuevos, equipos offline, alertas) — en React eso implica un layout de módulo (`(app)/insumos/layout.tsx`)
que los levante todos una sola vez, no un hook por página, para no duplicar el polling si el
usuario navega entre vistas del módulo.

---

## 3. Ranking de pantallas por costo de migración

### Complejo

1. **`ConsumableDetailModal.vue`** (modal de detalle abierto desde el Dashboard, no es una vista
   propia pero es el componente más caro de todo el frontend). ApexCharts con:
   - Anotaciones custom en el eje X (línea de la solicitud actual, ventanas "sin contacto",
     marcas de otras solicitudes) que requieren tooltips propios posicionados a mano con
     coordenadas de `MouseEvent` (no el tooltip nativo de ApexCharts).
   - Una clave de `:key` calculada a propósito para forzar remount completo del chart cuando
     llegan datos async después del render inicial — comentario explícito en el código: "ApexCharts
     solo conecta los mouseEnter/mouseLeave de las anotaciones en el render INICIAL". Si se porta
     sin entender este detalle, el hover de las anotaciones se rompe silenciosamente.
   - 5 llamadas a API en paralelo por apertura de modal, layout de 3 columnas fijo tipo portal HP.
   - React tiene wrapper oficial de ApexCharts (`react-apexcharts`), así que la librería en sí
     migra bien; lo caro es replicar el patrón de remount forzado + tooltip manual sin que
     rompa con el ciclo de vida de React (los `useEffect` con dependencias van a necesitar el
     mismo cuidado que el `computed` de `chartKey` acá).

2. **`useOrderActions.ts` + `CustomerRequestsTable.vue` (Dashboard)**. Es la lógica de negocio
   de UI más densa de la app: 5 flujos de modal distintos disparados por distintos `conflictType`
   de la misma respuesta HTTP, cada uno con su propio estado de "pendiente" (fila + cliente +
   nombre) que hay que administrar sin pisarse entre sí; carga individual, carga en lote con
   contador de progreso, descarte individual y en lote reusando el mismo modal
   (`DismissConfirmationModal` recibe `requestRow` XOR `batchCount`); un `watch` sobre un reloj
   compartido que dispara refetch automático cuando un countdown de validación llega a 0. Todo
   esto vive hoy repartido en 3 composables que se pasan referencias circulares entre sí — portar
   1:1 la separación en 3 hooks va a ser más trabajoso en React que colapsarlos, ver §2.1.

3. **`EquiposOfflineView.vue`**. Agrupación en 6 secciones con reglas de precedencia no triviales
   (`groupKeyOf`: caída de colector manda primero sin importar el resto), selección múltiple con
   reglas de "seleccionable" distintas de "visible", banner de caídas de colector con 3 niveles de
   certeza a texto libre construido con template strings condicionales.

4. **`HistorialView.vue`**. No es compleja por lógica de negocio sino por superficie: 5 pestañas
   con 3 fuentes de datos distintas, paginación client-side, filtros combinados (categoría + tipo
   de evento + rango de fechas + texto), 2 acciones condicionales por fila con su propia regla de
   "cuándo mostrar" (`canCancelRow`/`canReconcileRow`), sincronización de pestaña activa con
   querystring, y arranque/parada de polling condicionado a qué pestaña está activa.

### Medio

5. **`DateRangePicker.vue`**. Ningún concepto de framework complejo (es matemática de fechas +
   un popover con click-outside), pero es grande (~300 líneas de lógica) y de uso compartido por
   2 vistas — vale la pena portarlo una sola vez como primitivo compartido antes que duplicarlo.
6. **`ClienteEstadisticasView.vue`**. Mayormente presentación de datos ya calculados por el
   backend, pero con el modo impresión (`@media print`, layout condicional) que no es trivial de
   trasladar 1:1 a Next.js (el `@media print` con `.no-print` en un `App.vue` global no tiene
   equivalente automático en un layout de Next — hay que decidir dónde vive ese CSS).
7. **`ConfiguracionView.vue`**. Formulario largo pero sin lógica rara, salvo la sub-herramienta de
   "importar contactos por zona desde SDS" (flujo de 2 pasos preview→apply con estado de qué filas
   overwritear) y la integración con Web Notifications/Clipboard/`ms-settings:` que es pura
   interacción de browser, no requiere backend.
8. **`ClientesView.vue`**. CRUD de contactos por zona con la operación de "renombrar zona" no
   atómica (crear+borrar) que ya es frágil en Vue — al portar, vale la pena resolverlo del lado
   del backend (un endpoint de rename) en vez de replicar la fragilidad en React.

### Trivial

9. **`EquiposNuevosView.vue`**. Tabla ordenable + búsqueda + filtro de año + toggle — mismo
   esqueleto que EquiposOfflineView pero sin el agrupamiento ni la selección múltiple.
10. **`EstadisticasView.vue`**. Tiles + tabla + `TrendChart` reutilizado; sin estado propio
    complejo más allá del rango de fechas sincronizado con la URL.
11. **Los 7 modales de confirmación** (`DuplicateOrderModal`, `AmbiguousInsumoModal`,
    `StaleDeviceModal`, `ValidationOverrideModal`, `DismissConfirmationModal`,
    `OfflineDeleteModal`, `OfflineHelpModal`). Comparten exactamente el mismo esqueleto
    (backdrop + panel + header + body + footer + transición fade/scale) — visto una vez que se
    porta el primero, los otros 6 son variaciones de contenido, no de estructura. **Vale la pena
    construir un solo primitivo `Modal` compartido antes de tocar el primero** (mirar si
    `shared/components/ui/modal.tsx` o `brand-modal.tsx` del monolito nuevo ya cubre esta forma —
    por la skill `ui-design-handoff`, no reimplementar un modal dentro del feature si ya existe
    uno compartido).
12. **`NotificationBell.vue`, `AlertBanner.vue`, `OfflineBanner.vue`, `ErrorBanner.vue`,
    `StatusDot.vue`, `Toast.vue`**. Todos triviales; `Toast.vue` en particular no debería
    portarse (reemplazar por `sonner`, ver §2.2).

---

## 4. Dependencias Vue-específicas sin equivalente directo en React

| Paquete/API Vue | Uso en SDSInsumos | Nota para el port |
|---|---|---|
| `vue-router` (`useRoute`/`useRouter`, `RouterLink`, `router.replace` vs `push`) | Deep-links con querystring en Dashboard/Historial/Estadísticas, redirect de compat en `/pedidos` | Next.js App Router cubre todo esto (`useSearchParams`, `useRouter().replace`, `<Link>`) — mapeo 1:1, sin librería nueva |
| `<Teleport to="body">` | Los 8 modales (incluye `ConsumableDetailModal`) | `createPortal` de `react-dom`, o el primitivo `Modal` compartido si ya lo resuelve internamente |
| `<Transition name="...">` (CSS transition components) | Fade/scale de todos los modales, panel de `NotificationBell` | Sin equivalente automático — replicar con clases condicionales + `transition` CSS, o una librería si el monolito ya usa una (no se detectó ninguna en `shared/components/ui/`, revisar antes de agregar) |
| `v-model` en formularios grandes (`ConfiguracionView`, modal de contactos de `ClientesView`) | ~30 inputs controlados por `reactive()` | React: `useState` + `onChange` explícito por campo, o `useReducer` para el formulario de Configuración (7 secciones, 15+ campos) — más verboso que Vue acá, sin atajo directo |
| `vue3-apexcharts` | `ConsumableDetailModal`, `TrendChart` | `react-apexcharts` (mismo `apexcharts` core, wrapper oficial React) — la migración de la librería es directa, lo caro es la lógica alrededor (ver §3.1) |
| `watch()` con reloj compartido (`useCountdownClock`) | Countdown de validación en `CustomerRequestsTable` | `useEffect` + `setInterval` compartido vía contexto o módulo externo, igual razonamiento que §2.2 |
| Referencia a componente hijo vía `ref` + `defineExpose` (`scanSectionRef.value?.refreshIfExpanded()` en Dashboard) | `SupplyScanSection.vue` expone un método imperativo | `useImperativeHandle` + `forwardRef` en React, o mejor: levantar ese estado al padre y evitar el patrón imperativo si se puede (más idiomático en React) |
| Estado de módulo (`ref()` a nivel de archivo, fuera del composable exportado) | `useNotificationStore`, `useAlerts`, `useTheme`, `useToast`, `useValidationCountdown` | Ver §2.2 — el punto de mayor fricción real del port, no hay traducción mecánica |
| `confirm()` nativo del navegador | Bulk toggle de clientes, eliminar zona, anular pedido desde Historial (3 usos) | Reemplazar por un modal propio (más consistente con el resto de la app, que ya usa modales custom para todo lo demás) — no portar el `confirm()` nativo |

---

## 5. Otros hallazgos relevantes para portar

- **`localStorage` usado en 2 lugares**: `useSortableTable` (persiste sort de cada tabla, key
  distinta por vista: `equipos-nuevos-sort`, `equipos-offline-sort`, `historial-sort`) y
  `useTheme`/tema inicial (leído también desde `index.html` antes del mount, para evitar flash).
  Ambos son portables directo a Next.js con cuidado de SSR (leer `localStorage` solo en cliente).
- **Feature flag hardcodeado en código**, no en config: `ClientesView.vue` línea 100,
  `SDS_CONTACTS_PILOT = new Set([8255])` — piloto de "contactos detectados en SDS" habilitado
  para un solo `customerId`. Al portar, decidir si sigue siendo un literal en el componente o pasa
  a configuración real.
- **Zona horaria de negocio**: todo el formateo de fecha/hora pasa por `ARG_TZ =
  'America/Argentina/Buenos_Aires'` (`utils/date.ts`) — criterio explícito de mostrar siempre hora
  argentina sin importar el huso del navegador. Portar esta constante y el cuidado de no usar
  `new Date(string)` sin sufijo `Z` en las respuestas del backend (mismo patrón de bug que ya
  documenta el código fuente en varios comentarios).
- **Tests existentes** (Vitest + Vue Test Utils, 13 archivos / 61 tests, todos verdes al correr
  `npm test -- --run`): cubren `usePolling`, `useSortableTable`, `useAlerts`,
  `AmbiguousInsumoModal`, `StaleDeviceModal`, `DateRangePicker`, `weekendBands`,
  `ClienteEstadisticasView`, `EquiposOfflineView`, `EstadisticasView`, `HistorialView`. Son la
  referencia de comportamiento real a validar contra la reimplementación en React, mismo
  criterio que los tests de caracterización de Contadores.
- **No hay backend propio de autenticación** en SDSInsumos (app interna, sin login visible en el
  frontend relevado) — falta confirmar contra `SDSInsumos/backend/` cómo se protege hoy el acceso
  y cómo debe integrarse con el auth ya migrado del monolito nuevo (fuera del alcance de este
  relevamiento, que fue solo de frontend).
