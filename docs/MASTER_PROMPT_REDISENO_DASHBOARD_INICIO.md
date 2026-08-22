# Master Prompt — Rediseño del dashboard de Inicio (cards, jerarquía y "todo en una pantalla")

Análisis completo de cómo está construida hoy la pantalla de Inicio (`/`) — el orquestador,
el registro de cards, el grid auto-ajustable y cada una de las 13 cards — contrastado con lo
que hacen los dashboards profesionales del mercado, y una propuesta concreta de cómo aplicarlo
sin romper la regla dura del usuario: **la pantalla tiene que caber entera en cualquier monitor,
sin scrollbars**.

Generado el 2026-08-22 a partir del código real (`frontend/src/features/home/**` y las cards
de `wati`, `sla`, `vacaciones` que se montan en Inicio), la captura del usuario en tema claro a
~1920 px (pestaña Planificación), el mockup original del handoff
(`Handsoff Mockups/design_handoff_inicio/`), el historial de git del feature y fuentes externas
de diseño de dashboards (listadas al final). Feedback textual del usuario: *"La veo poco
profesional"*.

**Es un rediseño de presentación y de layout, no de datos**: los endpoints que consumen las
cards no se tocan; lo que cambia es qué se muestra primero, con qué peso, y cómo se reparte la
pantalla.

---

```text
[ROL]
Actuá como Senior Product Designer + Frontend Engineer del monorepo HelpDeskManager-Unificacion
(Next.js App Router + TypeScript + Tailwind v4, design system propio en
frontend/src/shared/components/ui/ y tokens en frontend/src/app/globals.css), con expertise en
diseño de dashboards operativos (Few, NN/g, patrones de Grafana/Datadog/Linear/Stripe) y en
layouts de viewport fijo. Conocés y aplicás ARCHITECTURE_GUIDE.md y CLAUDE.md como reglas
obligatorias. Respondés en español de Argentina, directo y sin cortesías. Cero alucinaciones:
cada afirmación sobre la pantalla actual se verifica en vivo (curl + captura Playwright), no de
memoria.

[CONTEXTO]
Cómo está construido Inicio hoy (verificado contra el código al 2026-08-22):

- Ruta: app/(app)/page.tsx → <InicioDashboard/> (features/home/components/inicio-dashboard.tsx,
  287 líneas). El layout de app (sidebar.tsx) deja un <main overflow-y-auto> y el dashboard se
  monta como flex-col h-full: título "Inicio" + subtítulo fijo, banner personal de turno
  (MiTurnoBanner, a la derecha del título), banner personal de WATI (MisChatsWatiBanner),
  fila de 6 Accesos Directos (ranking 30 días + respaldo), SegmentedControl con 4 pestañas
  (Planificación / Contadores / SLA / Administración) y un grid de cards.
- Registro: config/dashboard-registry.ts declara 13 cards con col (pestaña), order y guard por
  módulo/feature (ADR-032). Reparto: Planificación = turnos, wati-pendientes, clientes-hoy,
  insumos · Contadores = contadores-donut, pendientes-antig, cierre-mensual, heatmap-semana ·
  SLA = sla-mes, pendientes-cerrar · Administración = liquidaciones, parque, proximos-equipo.
  Las "fractions" de COLUMNS (1.4fr/1fr/0.9fr/0.9fr) quedaron sin uso desde que las columnas
  pasaron a ser pestañas (commit 64e383c, que además eliminó la franja de KPIs del handoff).
- Grid: hooks/use-auto-grid.ts + utils/grid-packing.ts (commit fd434bf). Mide con
  ResizeObserver el alto disponible y el alto NATURAL de cada card, y elige la MENOR cantidad
  de columnas (entre 1 y floor(ancho/300)) con la que todo entra sin scroll, prefiriendo cards
  ≤760 px de ancho; reparte las cards en grupos contiguos por columna minimizando la suma de
  máximos por fila; histéresis para no oscilar; `items-start` (las cards no se estiran,
  commit 2370fb4); `invisible` hasta la primera medición; scroll solo como último recurso.
  Consecuencia: el algoritmo optimiza "que entre", no "que ocupe bien la pantalla" — en la
  captura del usuario (1920 px, pestaña Planificación) las cards ocupan ~45 % del alto útil y el
  55 % inferior queda vacío, con bordes inferiores desalineados (dientes de sierra).
- Shell de card: components/dashboard-card.tsx — ícono 34 px naranja al 15 %, título
  Montserrat 800 15 px, subtítulo 12 px, headerRight libre, loading = spinner centrado, error =
  texto rojo; sin footer, sin variantes de tamaño, sin min-h-0/overflow interno. Skeleton de
  next/dynamic = mismo shell con spinner (sin forma del contenido → layout shift al cargar, y
  el auto-grid mide y re-reparte dos veces).
- Datos: hooks/use-inicio-data.ts — useRemote genérico (fetch al montar, sin cache, sin polling,
  refetch manual solo en 3 cards); 11 fetches independientes por carga de Inicio (turnos,
  accesos, calendario×5 requests, contadores resumen, pendientes período, SLA×6 meses, parque,
  pendientes a cerrar, insumos dashboard, liquidaciones, próximos equipo) + el provider de WATI
  que sí pollea. No hay "actualizado hace" global: cada card resuelve su frescura con un texto
  distinto (3 formatos) o no la muestra.
- Visuales: 4 donas Chart.js (contadores, parque, liquidaciones, SLA), 1 barra (pendientes por
  antigüedad), 1 línea (tendencia SLA), 1 heatmap CSS, 1 timeline CSS (turnos), 5 listas.
  Ticks/grids de Chart.js y algunos fondos están hardcodeados para tema oscuro
  (`rgba(255,255,255,.4)`, `bg-white/[.03]`, `text-red-400`/`emerald-400`/`amber-400`), y el
  usuario trabaja en tema claro (captura).
- 7 de 13 cards terminan en un botón primario naranja de ancho completo ("Ver detalle →", "Ver
  calendario →", "Ver solicitudes →"…) aunque la card esté vacía; la card de WhatsApp vacía
  muestra "Sin chats esperando respuesta." seguido de DOS botones grandes.
- Tipografías en uso dentro de las cards (sin escala): 9.5, 10, 10.5, 11, 11.5, 12, 12.5, 13,
  15, 18, 22, 25, 36, 42 px. Colores en una misma pantalla: naranja de marca (ícono, badge,
  CTA, dona "correctos", heatmap, tinte, links), rojo/ámbar/verde hex sueltos (#ef4444,
  #eab308, #22c55e, #d69e08…) en vez de los tokens --destructive/--warning/--success que ya
  existen en globals.css, más los 5 colores de operador de Gestión, más una PALETTE propia en
  liquidaciones distinta a todo lo demás.
- El mockup original del handoff (Inicio-Dashboard.dc.html, dark, 1.4fr 1fr 1fr + franja de 5
  KPIs) tampoco entra en 1920×1080: renderizado con Playwright se corta "Pendientes por
  antigüedad" y "Distribución del parque" — la regla "sin scroll" nunca se diseñó desde el
  origen, se parchó después con pestañas + auto-grid. Y el parche ya no alcanza: medido con
  Playwright (docs/home/capturas-analisis-2026-08-22/results.json), en 1366×768 la pestaña
  Contadores tiene overflow interno (626/489 px, heatmap cortado), y en 1920×1080 las cuatro
  pestañas dejan entre el 45 % y el 60 % del alto vacío.

Qué hacen los dashboards profesionales (síntesis de las fuentes del final del documento):
- Una sola pantalla, sin scroll de página: "la información más importante, consolidada en una
  sola pantalla para monitorearse de un vistazo" (Few). Si algo no entra, scrollea ADENTRO de
  su panel, nunca la página (modelo app-shell: marco fijo, paneles con scroll interno).
- Tres capas: (1) franja de estado con 3–7 KPIs arriba (el primer lugar que mira el ojo en el
  patrón F/Z), (2) un panel "hero" con la visual más importante del día, (3) paneles
  secundarios de general a específico. Test del entrecerrar los ojos: lo que sigue viéndose
  borroso es la jerarquía; hoy todas las cards pesan igual.
- Grid consistente (12 columnas; Datadog/Grafana), alturas consistentes por fila, paneles
  agrupados por tema; "inconsistent card sizing or grid misalignment" es el primer marcador de
  dashboard amateur.
- Color por capas: semántico SOLO para estado (éxito/atención/crítico), paleta de datos de 4–6
  colores, y UI en neutros; el acento de marca se gasta en un lugar. "Color = state only"
  (Stripe); 10+ colores visibles anulan el énfasis.
- Anatomía de KPI: período · nombre corto · valor grande · contexto/delta · sparkline opcional ·
  indicador. Cada número con su comparación o no dice nada.
- Visuales: posición y longitud se leen mejor que ángulo/área — barras ordenadas antes que
  donas; donas solo con 3–5 categorías; un % de dos partes (SLA) es un número + barra, no una
  dona (NN/g).
- Texto mínimo 11–12 px; "last updated" visible por panel; skeletons con la forma del contenido
  y estados vacíos diseñados (Vercel/Retool) — no un texto gris bajo un título grande.
- Densidad tipo Linear: filas de 32–36 px, mínimo chrome, un solo CTA primario por pantalla;
  el resto son links.

[OBJETIVO]
Rediseñar Inicio para que se lea como un dashboard operativo profesional y ocupe SIEMPRE el
100 % del viewport sin scroll de página, en 5 fases verificables:

F0 — Medir (antes de tocar nada): capturas Playwright de cada pestaña actual en 1920×1080,
  1536×864, 1440×900, 1366×768 y 1280×720, tema claro y oscuro, con registro de si hay scroll
  de página y cuánto alto queda vacío. Son la línea base del "antes".

F1 — Layout de viewport fijo (reemplaza use-auto-grid/grid-packing):
  - Contenedor: grid de filas `auto auto minmax(0,1fr)` = encabezado · franja KPI · cuerpo.
  - Cuerpo: CSS grid de 12 columnas × 6 filas de `minmax(0,1fr)`; cada card declara en el
    registro su celda (colSpan/rowSpan por breakpoint), así el alto lo dicta el viewport, no
    el contenido. Cards = `flex h-full min-h-0 flex-col`, cuerpo `flex-1 min-h-0 overflow-auto
    thin-scrollbar`: lo que no entra scrollea adentro de la card.
  - Breakpoints por ancho: ≥1536 → 12 col; 1280–1535 → 8 col con rowSpans recalculados;
    <1280 → 1 columna con scroll de página (fallback declarado, no silencioso).
  - Resultado verificable: `main.scrollHeight === main.clientHeight` en todas las resoluciones
    de F0, y ninguna card con contenido cortado sin scroll interno.

F2 — Jerarquía en 3 capas y fin de las pestañas (≥1280 px):
  - Franja de estado: 5–7 tiles KPI (56–64 px de alto) con label · valor · contexto · estado
    semántico: WhatsApp sin responder (n · peor espera), Insumos sin cargar (n · críticos),
    Pendientes a cerrar (n), Facturación sin cerrar (n · +10 días), SLA del mes (% · Δ mes
    ant.), Liquidaciones sin aprobar (n), Clientes de hoy (n). Cada tile es clickeable y lleva
    a la pantalla del módulo. Se guardan por módulo/feature igual que las cards.
  - Hero: "Turnos del día" a 8/12 de ancho en la primera fila del cuerpo + "Clientes de hoy"
    a 4/12 (lo que se mira cada mañana); banner personal "Ahora estás en:" queda como chip
    dentro del header del hero, no flotando junto al título.
  - Secundarios: las 13 cards pasan a 8 paneles sin pestañas: fusionar Cierre mensual +
    Pendientes por antigüedad (misma historia: facturación sin cerrar, número grande + buckets
    + top 5), fusionar Contadores por operador + Clientes por operador·semana (mismo eje:
    operador → barras ordenadas + heatmap), Distribución del parque pasa a KPI o barra dentro
    del panel de operadores, WhatsApp y Pendientes a cerrar quedan como listas compactas,
    Liquidaciones y Próximos días del equipo como listas compactas de 32 px/fila. Accesos
    directos dejan de ser 6 cards con borde: pasan a una fila de chips sin borde bajo el título
    (o a la sidebar), porque son navegación, no datos.
  - Si el usuario no tiene un módulo, su celda la ocupa el vecino (colSpan dinámico por fila),
    nunca queda un hueco.

F3 — Sistema visual normalizado (un solo lenguaje para todas las cards):
  - DashboardCard con variantes `tile | panel | hero`, header compacto (ícono 28 px, título
    14 px Montserrat 700, subtítulo opcional 12 px, acciones a la derecha como íconos de 28 px),
    cuerpo `min-h-0 overflow-auto`, footer opcional con "Actualizado hace X" + link textual
    "Ver todo →". Un ÚNICO formato de frescura en toda la pantalla; tono warning cuando el dato
    supera su umbral; refresh global cada 5 min con indicador discreto en el header de la página.
  - Escala tipográfica cerrada: 11 (labels caps, tracking .05em) · 12 (meta) · 13 (cuerpo) ·
    14 (título card) · 20 (valor en panel) · 28 (valor KPI). Nada por debajo de 11 salvo ticks
    de chart (10.5 con color token).
  - Color: naranja solo como acento (ícono, selección, links, máximo un CTA primario visible
    por pantalla y solo si n>0); estados con los tokens --success/--warning/--destructive (ya
    existen, con variante .dark); colores de operador solo en visuales por operador; la PALETTE
    de liquidaciones se elimina (usa tokens de datos). Chart.js lee colores de tokens vía
    getComputedStyle (ticks, grid, borde de gajos), nada hardcodeado para dark.
  - Estados: skeleton con la forma del contenido (líneas/bloques, no spinner); vacío = una línea
    con ícono tenue, sin botones grandes; error = mensaje + botón "Reintentar" (refetch).
  - Visuales: SLA = número grande + barra de cumplimiento + Δ + sparkline (no dona de 2 gajos);
    donas de operadores → barras horizontales ordenadas con valor y %; heatmap y timeline se
    conservan; barra de antigüedad se conserva con tokens.
  - Botones: brandButtonClasses primario solo para la acción que sí hay que hacer ahora; el
    resto links de 13 px naranja sin borde.

F4 — Accesibilidad y contraste: AA en claro y oscuro (revisar badges *-400 sobre fondo claro),
  números acompañan al color, foco visible en tiles y links, `prefers-reduced-motion` para la
  línea "ahora".

F5 — Tests y cierre: ampliar frontend/tests/inicio.spec.ts con un test por resolución/tema que
  falle si hay scroll de página o una card sin overflow interno con contenido cortado; capturas
  "después" junto a las de F0; `tsc` + eslint en verde; `make check` no aplica (sin backend).

[FORMATO]
- Todo texto visible en español de Argentina, UX writing llano; commits atómicos en inglés con
  la convención del historial (`feat(home): …`, `refactor(home): …`), un commit por fase.
- El registro sigue siendo la única fuente de verdad del layout (ahora con celdas por
  breakpoint); inicio-dashboard.tsx solo renderiza. Archivos ≤300 líneas, funciones ≤20 (§4):
  separar el grid, la franja KPI y el shell en módulos propios.
- Cada fase se cierra con capturas en las 5 resoluciones × 2 temas y la tabla "hay scroll /
  alto vacío" antes y después.
- Las desviaciones del handoff original (franja KPI distinta, sin donas, sin pestañas) se
  documentan al pie del README del handoff como "Decisiones de implementación (rediseño
  2026-08)", igual que se hizo el 2026-08-14.

[RESTRICCIONES]
Operativas (CLAUDE.md, innegociables):
- Sin hot reload: tras editar frontend/ correr `bash scripts/wsl/reiniciar.sh frontend` y
  verificar con `curl -s --noproxy '*' http://localhost:3000/ | grep <algo nuevo>` antes de dar
  por servido. No tocar backend ni jobs; no reactivar DISABLE_BACKGROUND_JOBS.
- Varias sesiones sobre el mismo checkout: consultar el registro de ediciones antes de tocar
  features/home (otra sesión editó inicio-dashboard.tsx el 2026-08-22); `git add` explícito.
- Playwright corre en el host WSL (PATH de nvm, sin proxy, `PW_PORT=3011`).

De diseño (reglas duras de este rediseño):
- CERO scroll de página en ≥1280 px de ancho, en cualquier alto de 720 a 1440+: el alto de
  las cards lo dicta el viewport, nunca el contenido. Si un contenido no entra, scrollea dentro
  de su card; si una card queda sin contenido, se colapsa a tile (no deja un hueco).
- No hay pestañas en escritorio: el estado de TODOS los módulos que el usuario tiene se ve de
  un vistazo. Las pestañas solo pueden quedar como fallback <1280 px.
- Un solo shell de card, una sola escala tipográfica, un solo formato de frescura, un solo
  CTA primario como máximo. Nada hardcodeado para un tema (ni `rgba(255,255,255,…)`, ni
  `text-red-400` sin par claro): todo sale de tokens.
- No inventar datos ni series (sigue la decisión del 2026-08-14: solo SLA tiene historia; los
  KPIs sin historia no llevan sparkline).
- No cambiar contratos ni endpoints; no agregar fetches por card (si hace falta consolidar,
  es un paso aparte con backend y no entra en este alcance).
- No reformatear ni reordenar nada que no sea de Inicio; las cards que viven en otros
  features (wati, sla, vacaciones) se adaptan al shell nuevo pero no cambian su lógica.

[EJEMPLO]
Cierre esperado de F1+F2:

  Inicio — layout de viewport fijo + franja KPI (F1–F2) cerrado y verificado:
  - use-auto-grid/grid-packing eliminados; registro con celdas {col, row, colSpan, rowSpan}
    por breakpoint (lg 12 col / md 8 col); cards h-full min-h-0 con scroll interno.
  - Franja de 6 tiles KPI (WhatsApp 0 · Insumos 0 · Pend. a cerrar 14 · Fact. sin cerrar 26,
    +10 días 3 · SLA 96,4 % ▼0,03 · Liquidaciones 7) · hero Turnos 8/12 + Clientes de hoy 4/12
    · 6 paneles secundarios; sin pestañas ≥1280.
  - Capturas antes/después en 5 resoluciones × 2 temas en docs/home/capturas-rediseno-2026-08/;
    tabla: scroll de página = NO en las 10 combinaciones; alto vacío ≤ 0 px (antes: 55 % en
    1920×1080 Planificación).
  - tests/inicio.spec.ts: +10 casos de no-scroll (verde); tsc + eslint en verde; curl confirma
    el build nuevo servido.
```

---

## Estado de implementación (2026-08-22)

Implementado el mismo día en un solo bloque (F1–F5 son interdependientes: el shell nuevo, el
grid y la franja KPI no tienen estado intermedio funcional). Archivos:

| Pieza | Archivo |
|---|---|
| Layout (filas/celdas, guards, acceso por módulo) | `features/home/config/dashboard-registry.ts` |
| Grid de viewport fijo | `features/home/components/dashboard-grid.tsx` |
| Franja KPI | `features/home/config/kpi-tiles.ts`, `components/kpi-strip.tsx` |
| Shell único + piezas (link, vacío, frescura, badge, barra) | `components/dashboard-card.tsx`, `dashboard-card-bits.tsx`, `dashboard-card-skeleton.tsx` |
| Datos unificados + refresh 5 min | `hooks/use-dashboard-data.ts` (+ `refreshKey` en `use-inicio-data.ts`) |
| Card ↔ datos | `components/card-slot.tsx` |
| Fusiones | `facturacion-sin-cerrar-card.tsx` (+ `facturacion-parts.tsx`), `operadores-card.tsx` (+ `heatmap-semana.tsx`) |
| Tokens nuevos | `globals.css`: `--surface-2`, `--chart-tick/grid/empty`, variante `short` (max-height 820) |
| Eliminados | `use-auto-grid.ts`, `grid-packing.ts`, `operador-donut.tsx`, `parque-donut-card.tsx`, `contadores-donut-card.tsx`, `cierre-mensual-card.tsx`, `pendientes-antiguedad-card.tsx`, `heatmap-semana-card.tsx` |
| Tests | `tests/inicio.spec.ts`: +10 casos "cabe en la pantalla sin scroll" (5 resoluciones × 2 temas) |

Verificación "después" (Playwright contra el contenedor real, superadmin, datos reales;
capturas `despues-*.png` en `docs/home/capturas-analisis-2026-08-22/`):

| Resolución | Scroll página / main / grid | Alto vacío | Cards con scroll interno |
|---|---|---|---|
| 1920×1080 | 0 / 0 / 0 | 0 | Clientes de hoy (lista), Facturación (lista "y N más") |
| 1536×864 | 0 / 0 / 0 | 0 | + Turnos (leyenda), SLA (tendencia), Operadores (heatmap) |
| 1440×900 | 0 / 0 / 0 | 0 | ídem |
| 1366×768 | 0 / 0 / 0 | 0 | ídem + Insumos, Pendientes a cerrar (listas) |
| 1280×720 | 0 / 0 / 0 | 0 | ídem |

Igual en claro y oscuro. Limitación conocida: por debajo de ~900 px de alto la pantalla es
densa — el encabezado, los subtítulos y el ícono de cada card se compactan (`short:`) y lo
que no entra scrollea adentro de su card; la regla "sin scroll de página" se cumple en todas.
`tsc`, eslint y los 16 tests de `inicio.spec.ts` en verde.

## Anexo A — Diagnóstico detallado de la pantalla actual

### A.1 Arquitectura (qué archivo hace qué)

| Pieza | Archivo | Qué hace | Observación |
|---|---|---|---|
| Ruta | `app/(app)/page.tsx` | Monta `<InicioDashboard/>` | — |
| Orquestador | `features/home/components/inicio-dashboard.tsx` (287 l.) | Resuelve acceso por módulo/feature, llama 11 hooks de datos, `renderCard(id)` con switch de 13 casos, pestañas, grid | Cerca del tope de 300 líneas (§4); el switch y los hooks deberían vivir en el registro |
| Registro | `config/dashboard-registry.ts` | 13 `CardDef {id, col, order, guard}` + `COLUMNS` con fractions | Las fractions no se usan desde 64e383c (columnas → pestañas) |
| Grid | `hooks/use-auto-grid.ts` + `utils/grid-packing.ts` | Elige columnas y reparto midiendo alturas naturales | Optimiza "que entre", no "que ocupe"; alturas dispares; `invisible` hasta medir |
| Shell | `components/dashboard-card.tsx` | Ícono 34 · título 15 · subtítulo 12 · spinner/error | Sin variantes, sin footer, sin `min-h-0`, no puede scrollear adentro |
| Skeleton | `components/dashboard-card-skeleton.tsx` | Spinner en caja vacía | Sin forma → layout shift + doble medición del grid |
| Datos | `hooks/use-inicio-data.ts` | `useRemote` sin cache ni polling; 11 fetches | Sin frescura global; solo WATI pollea |
| Accesos | `components/accesos-directos.tsx` + `config/accesos-catalogo.ts` | 6 tiles con borde, ranking 30 días | Mismo peso visual que las cards de datos |
| Banners | `mi-turno-banner.tsx`, `wati/…/mis-chats-wati-banner.tsx` | Avisos personales | Dos "franjas" más encima del grid cuando aplican |
| Pestañas | `shared/components/ui/segmented-control.tsx` | 4 pestañas | Ocultan 3/4 del dashboard |

### A.2 Inventario de cards

| # | Card (id) | Pestaña | Visual | CTA | Estados | Problemas visuales |
|---|---|---|---|---|---|---|
| 1 | Turnos del día (`turnos`) | Planif. | Timeline CSS por casilla, línea "ahora" c/30 s, leyenda | — | loading/error | La más trabajada; es el hero natural |
| 2 | WhatsApp sin responder (`wati-pendientes`) | Planif. | Lista ≤6 con semáforo | 2 botones grandes (primario + outline) | vacío, vencido (aviso ámbar) | Vacía muestra igual 2 botones; aviso de desactualización con 3er formato de frescura |
| 3 | Clientes de hoy (`clientes-hoy`) | Planif. | Lista tintada por operador, `max-h-170` scroll | — | vacío, sync viejo | OK; frescura formato 1 |
| 4 | Insumos sin cargar (`insumos`) | Planif. | Número 42 px + 4 filas severidad | Botón primario | vacío | Vacía = título grande + una línea gris (card de 80 px) |
| 5 | Contadores por operador (`contadores-donut`) | Contad. | Dona 130 px + leyenda | Botón primario | vacío, degradación Siges, "sin cruce" + Resolver | Dona para comparar operadores (mejor barras) |
| 6 | Pendientes por antigüedad (`pendientes-antig`) | Contad. | Barra Chart.js 110 px + top 6 | Link | vacío | Ticks `rgba(255,255,255,.4)` invisibles en claro; sin ícono en el header |
| 7 | Cierre mensual (`cierre-mensual`) | Contad. | Número 36 px + barra + arrastre | Botón primario | cerrado/arrastre | Cuenta la misma historia que #6 (facturación sin cerrar) |
| 8 | Clientes por operador · semana (`heatmap-semana`) | Contad. | Heatmap CSS 6 días | — | vacío | Subtítulo de 2 líneas; sin ícono; celda 0 con `rgba(255,255,255,.03)` |
| 9 | SLA del mes (`sla-mes`) | SLA | Dona 2 gajos + 3 tiles + sparkline 44 px | Botón primario + botón refresh | vacío | Dona de 2 gajos = un %; tiles `bg-white/[.03]` y texto 9.5 px; ticks dark |
| 10 | Pendientes a cerrar (`pendientes-cerrar`) | SLA | Lista expandible `max-h-220` | Botón primario | vacío | Frescura 10 px formato 2; hover `bg-white/[.03]` |
| 11 | Liquidaciones sin aprobar (`liquidaciones`) | Admin | Dona + leyenda | Botón primario + refresh | vacío | PALETTE propia distinta al resto |
| 12 | Distribución del parque (`parque`) | Admin | Dona + leyenda | Botón primario | vacío | Dato casi estático; pide ser KPI |
| 13 | Próximos días del equipo (`proximos-equipo`) | Admin | Lista ≤6 con iniciales | Link | vacío | OK; compacta |

### A.3 Hallazgos de las capturas (línea base "antes")

Capturas en `docs/home/capturas-analisis-2026-08-22/` (Playwright, host WSL, usuario superadmin
con todos los módulos; `results.json` tiene las métricas crudas de 4 pestañas × 3 resoluciones
× 2 temas). Medición de scroll:

| Pestaña | 1920×1080 | 1536×864 | 1366×768 |
|---|---|---|---|
| Planificación | sin scroll · ~55 % del alto vacío | sin scroll | sin scroll |
| Contadores | sin scroll · heatmap solo en fila 2/col 3, hueco bajo col 1–2 | sin scroll | **grid con overflow 626/489 px: el heatmap queda cortado** |
| SLA | sin scroll · 2 cards, ~60 % vacío | sin scroll | sin scroll |
| Administración | sin scroll · 3 donas, ~55 % vacío | sin scroll | sin scroll |

El tema no cambia ninguna medida. Es decir: la regla "sin scroll" ya se rompe hoy en
1366×768 (Contadores), y donde se cumple lo hace dejando entre la mitad y dos tercios de la
pantalla vacíos.

Observaciones por captura (1920 px, tema claro):

1. **Planificación — ocupación vertical ~45 %**: 3 columnas, cards de 236 / 150 / 215 / 80 px
   de alto natural, `items-start`; el resto es fondo. El algoritmo cumple "sin scroll" pero
   produce una pantalla medio vacía que se lee como "falta contenido".
2. **Sin jerarquía**: título de página, 6 accesos con borde, pestañas y 4 cards con el mismo
   shell → nada manda. La franja KPI del handoff (la capa "resumen") se eliminó en 64e383c y el
   dashboard quedó solo con la capa "detalle".
3. **Naranja saturado repetido**: botón primario de ancho completo en WhatsApp (vacía), ícono
   de cada card, pestaña activa, accesos — el color de marca deja de señalar acción. En SLA y
   Administración hay 2–3 botones primarios de ~480 px de ancho a la misma altura.
4. **Pestañas**: el estado de SLA, Contadores y Administración no se ve sin click. Un dashboard
   operativo se mira, no se navega. SLA tiene 2 cards y Administración 3: no justifican una
   pestaña cada una.
5. **Contadores**: "Pendientes por antigüedad" se ve sin etiquetas de ejes (ticks
   `rgba(255,255,255,.4)`, invisibles en claro); "Cierre mensual" (264 clientes, arrastre 2) y
   "Pendientes por antigüedad" (5) cuentan la misma historia en dos cards; la dona de
   operadores exige leer la leyenda para comparar (barras ordenadas lo resolverían de un
   vistazo); el heatmap cae suelto en la fila 2.
6. **SLA**: una card de ~440 px de alto para comunicar un solo número (96,8 %) — dona de 2
   gajos + leyenda + 3 tiles + sparkline + botón; "Pendientes a cerrar" dice "Actualizado hace
   140 h" en 10 px gris sin ningún aviso de dato viejo.
7. **Administración**: tres cards-dona (una con 2 gajos al 50 %/50 %) y una lista de 2 filas;
   "Distribución del parque" es un dato casi estático que pide ser un KPI, no un panel.
8. **Detalles**: subtítulo de página sin información ("Panel principal con turnos de operadores
   y planificación diaria."); frescura en 3 formatos; avisos ámbar y badges con tonos `-400`
   pensados para dark sobre fondo claro.
9. **Mockup original** (`mockup-handoff-1920x1080.png`): el diseño de partida tampoco entra en
   1080 px de alto — se cortan "Pendientes por antigüedad" y "Distribución del parque".

### A.4 Problemas de tema (solo se ven en claro — el tema del usuario)

| Archivo | Línea aprox. | Hardcodeado para dark |
|---|---|---|
| `pendientes-antiguedad-card.tsx` | ticks/grid Chart.js | `rgba(255,255,255,.4)` / `.06` |
| `sla-mes-card.tsx` | ticks tendencia, tiles | `rgba(255,255,255,.3)`, `bg-white/[.03]` |
| `pendientes-a-cerrar-card.tsx` | hover fila | `hover:bg-white/[.03]` |
| `inicio-format.ts` `heatCellStyle(0)` | celda vacía | `rgba(255,255,255,.03)` |
| varias | badges | `text-red-400`, `text-emerald-400`, `text-amber-400` sin par claro |
| `insumos-sin-cargar-card.tsx`, `sla-mes-card.tsx`, `inicio-format.ts` | colores semánticos | hex sueltos en vez de `--destructive/--warning/--success` |

## Anexo B — Referencias de mercado usadas

- Stephen Few, *Information Dashboard Design*: dashboard = una sola pantalla; reducir píxeles
  sin dato; agrupar; énfasis arriba-izquierda — resumen en
  [SAP Community](https://blogs.sap.com/2011/04/14/a-few-dashboard-design-principles/) y
  [Biztory](https://www.biztory.com/blog/2016/04/06/information-dashboard-design-lessons-learned).
- NN/g, *Data Visualizations for Dashboards / preattentive attributes*: posición y longitud
  antes que ángulo/área; evitar donas y gauges; color como refuerzo, no como codificación
  primaria — [nngroup.com](https://www.nngroup.com/articles/dashboards-preattentive/).
- Setproduct, *Dashboard UI design*: 3–7 KPIs arriba, el bloque más grande para la visual más
  importante, squint test, tabs solo para 3–7 vistas paralelas —
  [setproduct.com](https://www.setproduct.com/blog/dashboard-ui-design).
- 5of10, *Dashboard design best practices*: grid 12 col, 5–7 métricas, anatomía de KPI,
  color por capas (semántico / datos / UI), lista de marcadores "amateur" —
  [5of10.com](https://5of10.com/articles/dashboard-design-best-practices/).
- A. Kuznetsova, *Anatomy of the KPI card*: período · nombre · valor · contexto · sparkline ·
  indicador — [substack](https://nastengraph.substack.com/p/anatomy-of-the-kpi-card).
- Datadog, *effective-dashboards/guidelines*: 12 columnas, agrupar widgets, anchos mínimos,
  high-density mode — [github](https://github.com/DataDog/effective-dashboards/blob/main/guidelines.md).
- Grafana, *Dashboard best practices*: de general a específico, consistencia, documentación
  en el panel — [grafana.com](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/).
- Patrones de producto (Linear, Vercel, Stripe, Retool): densidad de 36 px por fila, mínimo
  chrome, "color = state only", skeletons y empty states como parte del diseño —
  [925studios](https://www.925studios.co/blog/saas-dashboard-design-examples-2026),
  [artofstyleframe](https://artofstyleframe.com/blog/dashboard-design-patterns-web-apps/).
- UXPin / Context.dev / Toptal, principios generales (F-pattern, 5 segundos, ≤7 elementos
  compitiendo) — [uxpin](https://www.uxpin.com/studio/blog/dashboard-design-principles/),
  [context.dev](https://www.context.dev/blog/dashboard-design-best-practices),
  [toptal](https://www.toptal.com/designers/data-visualization/dashboard-design-best-practices).
