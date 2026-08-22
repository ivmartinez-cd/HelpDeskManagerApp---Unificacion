# Handoff: Inicio — Dashboard principal (rediseño)

## Contexto
Rediseño de la home del portal HelpDeskManager (dark). Reemplaza el panel anterior de "Turnos + Clientes de hoy + SLA" por un dashboard ejecutivo con KPIs, timeline de turnos y gráficos. Mockup interactivo: `Inicio-Dashboard.dc.html` (abrir en navegador; autocontenido, usa Chart.js 4.4 por CDN).

Ruta: `/` (Inicio). Header y sidebar globales sin cambios funcionales.

---

## Librería de gráficos
**Chart.js 4.4** (`chart.umd.min.js`). Gráficos usados: `line` (sparklines, tendencia SLA), `doughnut` (SLA, parque, contadores), `bar` (pendientes por antigüedad). Todas las configs exactas están en el `<script>` del mockup (función `initCharts()`), listas para copiar.

---

## Design tokens

| Token | Valor |
|---|---|
| Fondo página | `#0f0f0f` |
| Card | `#1a1a1a` · borde `rgba(255,255,255,.07)` · radio `13-14px` |
| Naranja principal / CTA | `#F7941D` (hover `#e08010`) |
| Título card | Montserrat 800 15px blanco + subtítulo Source Sans Pro 12px `rgba(255,255,255,.35)` |
| Ícono card | caja 34×34 radio 9 `rgba(247,148,29,.15)`, stroke `#F7941D` |
| Verde/rojo semánticos (badges) | `#22c55e` / `#ef4444` |
| Tendencias KPI (apagados, NO neón) | subida `#8fb59a` · bajada `#c98484` · ámbar `#c4a35a` |

### Colores por operador (consistentes en TODO el panel)
| Operador | Color | Tinte fondo |
|---|---|---|
| Maria Jose Vela | `#a855f7` | color + alpha `22` |
| Victor Paez | `#d69e08` | idem |
| Luna Torres | `#d08ea1` | idem |
| Mariana Rodriguez | `#9aa832` | idem |
| Mariano Villegas | `#94a3b8` | idem |

Sparklines KPI (versiones muted): `#b87a2a` `#8e6ab0` `#6f9c7f` `#b06a6a` `#a68a4e`.

---

## Layout
1. Título "Inicio" + estado "● Viernes 14 · actualizado hace X h" (derecha).
2. **Franja KPI**: grid 5 columnas, gap 14.
3. **Grid principal**: `grid-template-columns: 1.4fr 1fr 1fr`, gap 16, `align-items:start`.
   - Col A: Turnos del día · Contadores por operador
   - Col B: Clientes de hoy · Clientes por operador (semana) · Pendientes por antigüedad
   - Col C: SLA del mes · Distribución del parque

---

## Cards

### 1) KPIs (×5)
Label uppercase 10.5px + tendencia (derecha) · valor Montserrat 800 25px · sub 11.5px · sparkline (línea 1.5px, `tension .45`, degradé de relleno alpha `26`→`00`, sin ejes ni tooltip, altura 34px).

| KPI | Valor | Sub | Tendencia | Origen del dato |
|---|---|---|---|---|
| Parque total | 7.121 | impresoras | +71 | suma parque de PSTs |
| Clientes del mes | 186 | activos | +4 | clientes con contadores activos |
| SLA del mes | 96,42% | de 614 | ▼ 0,03% | incidentes correctos/total |
| Vencidos | 22 (rojo) | incidentes | −1 | incidentes fuera de SLA |
| Pendientes | 26 (ámbar) | **facturación sin cerrar** | −1 | ver definición abajo |

**Definición "Pendientes"**: clientes ya procesados a los que se les solicitaron contadores faltantes; hasta que el cliente responde no se cierra la facturación ni salen del calendario.

### 2) Turnos del día (timeline)
- Dos pistas de 46px (Turnos Insumos / Turnos Servicio Técnico), eje 08:00–18:00 con ticks cada 2 h.
- Cada turno = segmento posicionado por %: `left=(desde−8)/10`, `width=(hasta−desde)/10`. Fondo = color operador alpha `22`, borde derecho 2px del fondo del card.
- Rango compacto ("8–11h", color del operador) **oculto si el segmento ocupa <12%**; nombre del operador con ellipsis. Tooltip nativo (`title`) con operador + horario completo.
- **Línea "ahora"**: 2px blanca con glow, posición = hora actual sobre el eje, **recalculada cada 30 s**; oculta fuera de 08–18. Badge verde "Ahora HH:MM" (o "Fuera de horario · HH:MM").
- Leyenda de operadores al pie.

### 3) Clientes de hoy
Lista scrolleable (max-height 230). Fila: fondo tinte operador + borde izquierdo 3px color operador; nombre Montserrat 700 12.5px + operador debajo en su color. Fuente: planificación del día (Calendario de Contadores).

### 4) Clientes por operador · semana (heatmap)
Grid `86px + 6 columnas` (Lun–Sáb) × 4 operadores. Celda 26px radio 5 con el número.
Intensidad naranja: 0 → `rgba(255,255,255,.03)` (vacía) · 1-2 → `rgba(247,148,29,.14)` · 3-4 → `.38` · 5+ → `#F7941D` sólido (texto blanco). Tooltip "Operador · Día: N clientes procesados". Leyenda menos→más al pie.
Subtítulo: "Clientes procesados por día según calendario · si faltan contadores, la facturación queda pendiente".

### 5) Pendientes por antigüedad
- Badge rojo con total (26).
- Gráfico de barras verticales por bucket: `1-2 / 3-4 / 5-7 / 8-10 / +10 días` con colores `#22c55e #9aa832 #d69e08 #c2410c #ef4444`.
- Lista (dot semántico por antigüedad: ≥10 rojo, ≥5 ámbar, <5 verde): "Cliente · Operador" + "hace N días". Link "Ver los 26 pendientes →".

### 6) SLA del mes
- **Dona completa** (cutout 74%): correctos `#F7941D` / vencidos `#ef4444`; centro 96,42% + "592 de 614 correctos".
- Tres tiles: Vencidos 22 (rojo) · Mes ant. 96,45% · Variación ▼ 0,03% (rojo).
- Tendencia 6 meses: línea naranja `tension .4` con degradé, eje Y oculto (min 94 max 97).
- CTA naranja "Ver detalle →" (a /sla).

### 7) Distribución del parque
Dona (cutout 70%, borde 2px `#1a1a1a`, hoverOffset 5), centro "7.121 impresoras". Leyenda: cuadradito color · "Operador · N PST" · % · valor. Datos: V. Paez 3.314/46,5%/13 PST · M. J. Vela 2.224/31,2%/12 · L. Torres 832/11,7%/9 · M. Rodriguez 751/10,6%/1. CTA "Ver prestadores →".

### 8) Contadores por operador
**Misma vista que Distribución del parque**: dona con centro "13.514 impresoras" + leyenda "Operador · N clientes · % · valor". Datos: M. Rodriguez 5.638/41,7%/37 cl · M. J. Vela 3.664/27,1%/55 · L. Torres 2.267/16,8%/49 · V. Paez 1.945/14,4%/45. CTA "Ver calendario →".

---

## Contratos de datos sugeridos (API)

```ts
GET /api/dashboard/inicio
{
  kpis: { parqueTotal, clientesMes, sla: {pct, total, correctos}, vencidos, pendientesFacturacion,
          trends: { parque:number[], clientes:number[], sla:number[], vencidos:number[], pendientes:number[] } },
  turnos: { insumos: [{operadorId, desde:"08:00", hasta:"11:00"}], st: [...] },
  clientesHoy: [{cliente, operadorId}],
  semana: [{operadorId, porDia:number[6]}],          // clientes procesados Lun..Sáb
  pendientes: { total, buckets:[5,6,9,3,3], items:[{cliente, operadorId, dias}] },
  sla: { mesAnterior:{pct,total,correctos}, tendencia6m:number[] },
  parque: [{operadorId, impresoras, psts}],
  contadores: [{operadorId, impresoras, clientes}]
}
```
Los colores se resuelven en el front con el mapa operador→color (arriba). No hardcodear colores por cliente.

## Comportamiento
- Reloj del timeline: `setInterval` 30 s → re-render de la posición de la línea y el badge.
- Listas (clientes/pendientes): scroll interno, scrollbar fina 7px `rgba(255,255,255,.14)`.
- Hover en sidebar y filas: `rgba(255,255,255,.05)` / `.02`.
- Los CTAs navegan: Ver detalle → SLA · Ver prestadores → Prestadores · Ver calendario → Calendario de Contadores · Ver los 26 pendientes → listado filtrado.

## Accesibilidad
Contraste AA en textos principales; los números del heatmap acompañan al color (no solo color); tooltips `title` en segmentos y celdas; tamaños mínimos de texto 10.5px solo en ejes/leyendas.

## Preguntas abiertas
1. ¿"Actualizado hace X h" viene del último proceso de contadores o de un refresh del dashboard?
2. ¿Los buckets de antigüedad de pendientes (1-2/3-4/5-7/8-10/+10) son los correctos para el negocio?
3. ¿El sábado siempre forma parte de la semana laboral (heatmap de 6 días)?

## Decisiones de implementación (2026-08-14)

Implementado en `frontend/src/features/home/` (orquestador `inicio-dashboard.tsx`, una card
por archivo) sin backend nuevo: cada card consume endpoints ya migrados.

- **Solo datos reales.** La única serie histórica disponible es la de SLA (resúmenes
  mensuales), así que solo el KPI de SLA lleva sparkline/tendencia (6 meses reales, misma serie
  que la card). Los otros 4 KPIs muestran el valor actual sin sparkline — no se inventó
  historia. Tendencia de "Vencidos": diferencia real contra el mes anterior.
- **Colores de operador**: los reales de Gestión (ADR-009), no el mapa fijo de este README; el
  mapa queda solo como referencia visual del mockup.
- **Pregunta abierta 1**: "actualizado hace X h" sale del sync manual del calendario de
  Contadores (`/calendario/sync/status`), con el mismo aviso de sync viejo (>24 h) que antes.
- **Preguntas 2 y 3**: buckets de antigüedad y semana Lun–Sáb quedaron tal cual el handoff.
- **"Ver los N pendientes →"** navega al calendario de Contadores — no existe (todavía) un
  listado filtrado propio.
- **Timeline**: las pistas son las casillas reales de Turnos (una por casilla, no dos fijas);
  el eje 08–18 se extiende si algún turno real se sale del rango.
- **Heatmap**: cuenta eventos del calendario de la semana en curso; los días ya pasados pueden
  subcontar porque Gestión borra los eventos realizados.
- Se conservó la funcionalidad previa de la home que el mockup no dibuja: degradación cuando
  Siges no responde, badge "N sin cruce" + modal Resolver, y gating por módulo (cada card/KPI
  solo aparece si el usuario ve ese módulo).

## Decisiones de implementación (rediseño 2026-08-22)

Análisis y plan en `docs/MASTER_PROMPT_REDISENO_DASHBOARD_INICIO.md`; capturas "antes" en
`docs/home/capturas-analisis-2026-08-22/`. Motivo: la pantalla dejaba 45–60 % del alto vacío,
las pestañas ocultaban 3/4 del estado y en 1366×768 ya había overflow. Lo que cambia respecto
de este handoff (y de la implementación del 2026-08-14):

- **Layout de viewport fijo** (`dashboard-registry.ts` → `LAYOUT`, `dashboard-grid.tsx`): tres
  filas de alto proporcional; cada card llena su celda y scrollea adentro. Sin pestañas en
  escritorio; por debajo de `xl` las filas se apilan y scrollea el `<main>`.
- **Vuelve la franja de KPIs** (`kpi-tiles.ts`, `kpi-strip.tsx`), con el dato actual y su
  contexto (sin sparklines inventadas; la única variación real es la de SLA).
- **Fusiones**: "Cierre mensual" + "Pendientes por antigüedad" → *Facturación sin cerrar*;
  "Contadores por operador" + "Clientes por operador · semana" → *Operadores*; "Distribución
  del parque" → KPI *Parque*. Las donas se reemplazan por barras ordenadas (longitud, no
  ángulo) y el % de SLA por número + barra.
- **Un solo shell** (`dashboard-card.tsx`): ícono 28, título 14, cuerpo con scroll interno,
  pie con frescura unificada (`Freshness`) y link textual; botón primario solo en WhatsApp y
  solo con chats esperando. Colores semánticos por tokens (`--success/--warning/--destructive`),
  Chart.js lee `--chart-tick/--chart-grid` (antes `rgba(255,255,255,…)`, invisible en claro).
- Accesos directos pasan a chips de navegación en el encabezado; el banner personal de turno
  vive en el header de "Turnos del día" y el de WhatsApp dentro de su card.
- Refresco automático de todos los datos cada 5 min (`use-dashboard-data.ts`).

## Archivos
```
design_handoff_inicio/
├── README.md                  ← este archivo
├── Inicio-Dashboard.dc.html   ← mockup interactivo final (abrir en navegador)
├── support.js                 ← runtime del mockup
└── assets/logo-naranja.png
```
