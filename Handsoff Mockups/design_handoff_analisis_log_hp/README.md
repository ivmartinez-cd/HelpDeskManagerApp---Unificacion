# Design handoff — Análisis de Log HP (parque-impresoras)

Fuente: capturas de mockups armados por el usuario (2026-08-15), montados sobre el shell
real de Mesa de Ayuda (sidebar, topbar, tema oscuro por defecto). Referencia funcional:
`docs/parque-impresoras/PRINTER_LOGS_ANALYZER_CARACTERIZACION.md`.

Estado: **parcial** — cubre las 2 pantallas troncales. Las pantallas/modales faltantes se
derivan del mismo sistema visual salvo que el usuario entregue mockups propios (ver
"Pendientes" al final).

## Ubicación en la app

Sidebar → sección **HERRAMIENTAS** → entrada **"Análisis de Log HP"** (ícono de documento,
estado activo con fondo naranja translúcido y texto naranja, como el resto del sidebar).

## Pantalla 1 — Bienvenida / búsqueda (`assets/01-bienvenida-busqueda.png`)

- Centrada, sin cards de fondo: título display **"HP Logs ANALYZER"** ("HP Logs" blanco +
  "ANALYZER" naranja, bold), bajada gris en dos líneas: "Análisis técnico avanzado de logs
  HP con detección inteligente de errores y estado de hardware en tiempo real."
- **Toggle de modo de búsqueda** (segmented pill): "Buscar por Serie" (activo, fondo
  naranja, texto oscuro) | "Buscar por Cliente" (inactivo, borde gris). ⚠️ Ver pregunta
  abierta #2.
- Input grande redondeado con placeholder "Ingrese Serie de Impresora (ej: MXBCN...)" +
  botón primario naranja **"Analizar"** + botón circular "?" (ayuda).
- Hint con 💡: "Pegá un número de serie para un diagnóstico instantáneo vía HP Insight API."
- **Empty state** en card de borde punteado: ícono de documento-lupa, "Sin diagnóstico
  todavía", subtexto "Ingresá un número de serie o un cliente para traer los últimos logs
  desde HP SDS."
- Nota de alcance (decisión previa del usuario): el scraping SDS es la entrada principal;
  **pegar TSV es el backup** — en esta pantalla debe existir como camino secundario visible
  pero no protagonista (no aparece en el mockup; resolver con el usuario cómo se accede —
  p.ej. link discreto bajo el input).

## Pantalla 2 — Panel de errores (`assets/02...png` arriba, `assets/03...png` abajo)

**Header**: título "Panel de errores" + subtítulo con modelo y serie
("HP LaserJet Managed E82650z · S/N B4H29A#302"). Botonera a la derecha:
`←` (volver) · `📅 Todo el período` (filtro de fechas) · `SDS` · `Guardar` ·
**`Exportar PDF`** (primario azul en el mockup — ver pregunta #3) · `EWS Remoto` ·
`Manual CPMD` · `Actualizar caché HP`.

**Fila de 4 KPIs** (cards):
1. **Último error crítico**: código en rojo grande (13.DA.EE), "hace 2 h · Fusor"
   (recencia + módulo de hardware por familia). Card con borde rojo sutil.
2. **Errores críticos**: número grande (9) + "Alertas menores: 3 advert. · 12 info".
3. **Incidencias activas**: número grande (17) + "en el período".
4. **Tasa de errores**: "1 c/17 pág." naranja + "Por período: 8.478 pág. · Contador
   total: 221.678 pág." ⚠️ Métrica nueva, ver pregunta #4.

**Filtro de severidad**: barra con "FILTRAR ANÁLISIS:" + pills ERROR (rojo), WARNING
(amarillo), INFO (azul) — toggles.

**Gráficos** (fila 2 columnas):
- "Volumen de incidencias (registro completo)": chart temporal apilado por severidad con
  toggle **Área | Barras | Líneas**. Leyenda ERROR/WARNING/INFO.
- "Errores más frecuentes": barras horizontales por código, coloreadas por severidad.

**Distribución temporal de fallas**: heatmap día-de-semana × franja horaria (Dom–Sáb ×
0h/3h/6h/9h/12h/15h/18h/21h), celdas rojas con intensidad por frecuencia, punto blanco en
los picos, leyenda "menos → más". Subtítulo con el rango de fechas detectado.

**Timeline de errores**: filtros de rango `1 día | 3 días | 7 días | 14 días | Todo`
(activo naranja pill). Contadores por severidad ("9 críticos · 6 warnings · 17 info").
Lista cronológica (más recientes primero): punto de severidad, fecha-hora, código
coloreado por severidad, descripción, y edad relativa a la derecha ("hace 2 h").

**Diagnóstico con IA (Recomendado)**: card colapsable con ✨, texto del diagnóstico.
⚠️ En el mockup tiene tinte violeta — ver pregunta #1 (marca).

**ANÁLISIS DETALLADO** (sección de collapsibles, cada uno con punto de color, título,
contador a la derecha y chevron):
- "Incidencias detectadas" (rojo) — resumen + tabla de incidentes al expandir.
- "Eventos del período" (azul) — tabla de eventos.
- "Estado de consumibles en tiempo real (N)" (amarillo) — panel Insight.
- "Alertas del portal SDS" (amarillo) — "información (287)".

## Tokens visibles

- Fondo app `~#0e0e10` / cards `~#1a1a1d` con borde `~#2a2a2e`, radios generosos (~12-16px
  en cards, pills full-round).
- Naranja institucional para acciones primarias, estados activos y acentos (título).
- Severidades: rojo (ERROR), amarillo (WARNING), azul (INFO) — consistentes en pills,
  charts, timeline y KPIs.
- Tipografía del shell (RNS Sanz vía el design system existente del monorepo).

## Puntos resueltos (2026-08-15 — casi todos estaban ya en la app legacy)

Lección registrada: los mockups espejan la app real (`frontend/src` del legacy actualizado
a `3d28a96`) — ante una duda de comportamiento, **mirar el código legacy primero**, no
preguntar al usuario.

1. **Colores**: decisión del usuario — **todo con colores institucionales**. El tinte
   violeta del card "Diagnóstico con IA" del mockup NO se replica (violeta = línea DaaS,
   excluida); recolorear a naranja/neutral. Ídem cualquier acento fuera de paleta.
2. **"Buscar por Cliente" — existe en el legacy** (`WelcomeView.tsx`, actualización jul):
   tabs Serie/Cliente; en modo cliente, select de clientes (`listFleetClients` →
   "{nombre} ({N} equipos)") → select de equipos del cliente (`getFleetClient` →
   "{serial} - {ubicación} ({modelo})") → botón Analizar dispara el mismo flujo por
   serial. **Entra en el alcance.** Nota de migración: el legacy lo resuelve con los
   endpoints de fleet (excluidos); en el monolito se implementa como lookup read-only de
   clientes/equipos vía Insight (`get_customers` / `get_devices` ya existen en el gateway
   de insumos — patrón ADR-018), sin portar el módulo fleet.
3. **"Exportar PDF" — existe en el legacy** como botón primario de la botonera. Color:
   según paleta institucional (punto 1), no azul.
4. **KPI "Tasa de errores" — existe en el legacy** (`KPICards.computeErrorRate`):
   `pagesPerError = round((counter_max − counter_min) / errores del período)` → label
   `1 c/{N} pág.` (o `{N} err.` si <1); sub = código de error más frecuente; líneas "En
   periodo: X págs." y "Contador total: Y págs.". Estados: "—" sin datos/rango de
   contador, "Sin errores" en verde. "Incidencias activas" = `filteredIncidents.length`
   (incidentes dentro del filtro de fechas activo).
5. **"Último error crítico · Fusor" — no hay mapeo**: el subtítulo es
   `code_description` del catálogo truncada a 48 chars (el "Fusor" del mockup es una
   descripción de ejemplo). El timestamp es el `lastErrorLabel` relativo.
6. **Pegar TSV — existe en el legacy**: card **"Análisis Manual"** en la grilla bento de
   la bienvenida ("Sube o pega logs históricos para un diagnóstico profundo fuera de
   línea" → "Comenzar ahora →") que abre el modal **"Análisis Manual de Logs"** (textarea
   con placeholder "Pegar logs HP aquí para analizar...", botón "🚀 Iniciar Análisis",
   aviso de server lento). Ese es el acceso backup — mantenerlo con esa jerarquía.
7. **Datos de ejemplo**: los números de los mockups (77/834/287, `W-041`) son
   placeholders — todo se alimenta del pipeline real; no se replican datos falsos.

## Pantallas/estados aún sin mockup (derivar del sistema visual o esperar entrega)

- Modal/vista de **pegar logs TSV** (backup).
- **Análisis guardados**: lista, detalle, comparación (contra log nuevo y entre dos
  snapshots), badge de salud del equipo, historial con gráfico.
- Modales de **catálogo**: alta/edición de código, banner de códigos nuevos, contenido de
  solución.
- **Selector de modelo de IA** (decisión 2026-08-15: listar modelos vía `GET /v1/models`).
- Visor **Manual CPMD** (PDF) y modal de subida.
- Estado/feedback de **"Actualizar caché HP"** (el mecanismo de aviso se rediseña — el
  centro de notificaciones del legacy no se porta tal cual).
- Diseño del **PDF exportado** (A4).
- Estados de carga (extracción SDS ~25 s) y de error (SDS caído → sin mocks, error claro
  + sugerir pegar TSV).
