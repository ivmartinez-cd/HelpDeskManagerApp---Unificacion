# Handoff: Módulo Insumos / SDS — Canal Directo

## Contexto
Módulo que integra gestión de contadores de impresión (SDS, ERS, FTP, DB3), insumos, historial y estadísticas al portal de mesa de ayuda.  
Usa exactamente el mismo sistema de diseño que `design_handoff_mesa_de_ayuda/` — no re-especificamos paleta ni tipografía salvo excepciones.

## Tokens rápidos (herencia del handoff principal)
| Token | Valor |
|---|---|
| Naranja principal | `#F7941D` |
| Gris MPS | `#58595B` |
| Charcoal (Insumos) | `#3A3A3C` |
| Magenta (acento puntual) | `#E32D91` |
| Fondo página | `#FAFAF8` |
| Superficie card | `#ffffff` |
| Borde sutil | `rgba(0,0,0,.06)` |
| Radio card | `12px` |
| Radio botón / input | `8px` |
| Título | Montserrat 700–800 |
| Cuerpo | Source Sans Pro 400/600 |
| **Prohibido** | Celeste `#00a4e4` / violeta `#662D91` |

---

## Patrones nuevos (mockups interactivos en `patrones/`)

### Patrón 1 — Tabla con fila expandible (`Patron1-TablaExpandible.dc.html`)
- Fila padre: grid `2fr 1fr 1fr 1fr 120px`. Caret `▶` rota 90° cuando está abierta (`transform: rotate(90deg)`).
- Avatar cuadrado 32×32 radio 8px en color del grupo, iniciales blancas Montserrat 700 12px.
- Badge de estado: pill `border-radius:20px`, 3 estados — Activo (`rgba(247,148,29,.12)` / `#F7941D`), Atención (`rgba(239,68,68,.1)` / `#dc2626`), OK (`rgba(34,197,94,.1)` / `#16a34a`).
- Fila expandida: fondo `#FAFAF8`, padding-left 58px (alineada post-caret), sub-grid `1.5fr 1fr 1fr 1fr 80px`.
- Barra de tóner: height 6px, radius 4px, fondo `#eee`. Color por nivel — verde `#22c55e` (>30%), naranja `#F7941D` (10–30%), rojo `#ef4444` (<10%).
- Interacción: toggle por fila independiente; múltiples filas pueden estar abiertas simultáneamente.

### Patrón 2 — Gráfico de tendencia con anotaciones (`Patron2-GraficoTendencia.dc.html`)
- Librería: **Chart.js 4.4** vía CDN (`https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js`).
- Dataset principal: line, `borderColor: #F7941D`, `backgroundColor: rgba(247,148,29,.08)`, `fill: true`, `tension: 0.4`.
- Dataset proyección: line, `borderColor: #58595B`, `borderDash: [6,4]`, sin fill.
- Anotaciones (puntos sobre el gráfico): reposición `#E32D91` radius 6px, falla `#ef4444` radius 6px — implementar como puntos extras en un tercer dataset o con `chartjs-plugin-annotation`.
- Selector de período: botones pill, activo `background:#F7941D color:#fff`, inactivo `border:1px solid rgba(247,148,29,.3) color:#F7941D`.
- KPI tiles debajo: grid 3 cols, fondo `#FAFAF8`, número Montserrat 800 22px en color de la métrica.

### Patrón 3 — Secciones colapsables + alertas multi-nivel (`Patron3-AlertasColapsables.dc.html`)
- 3 niveles de severidad, cada uno con su borde izquierdo y fondo tintado:
  - 🔴 **Crítico**: `border: 1.5px solid #ef4444`, fondo header `rgba(239,68,68,.08)`. Siempre expandido, no colapsable.
  - 🟡 **Advertencia**: `border: 1.5px solid #eab308`, fondo `rgba(234,179,8,.07)`. Toggle con chevron.
  - ℹ️ **Informativo**: `border: 1.5px solid rgba(0,0,0,.08)`. Toggle con chevron.
- El banner crítico incluye botón "Ver detalles" (`border:1px solid #ef4444 color:#dc2626`); los otros solo expand/collapse.
- Rows dentro de las alertas: `background:#FAFAF8 border-radius:8px padding:8px 12px`.

### Patrón 4 — Selector de rango de fechas (`Patron4-DateRangePicker.dc.html`)
- Panel de presets (sidebar 200px): 6 opciones — Hoy, Esta semana, Este mes, Mes pasado, Último trimestre, Personalizado. Activo: `background:rgba(247,148,29,.1) color:#F7941D border-left:3px solid #F7941D`.
- Calendario: 2 meses en paralelo, grid 7 cols × 5 rows, celda 36×36px.
  - Inicio/fin del rango: `background:#F7941D color:#fff border-radius:50%`.
  - Días en rango: `background:rgba(247,148,29,.12) color:#F7941D border-radius:0`.
  - Conexión visual: ajustar `border-radius` en extremos para efecto continuo (inicio `50% 0 0 50%`, fin `0 50% 50% 0`).
- Footer del picker: muestra "Desde / Hasta" con Montserrat 700 14px, botones "Limpiar" (outline gris) y "Aplicar" (naranja).
- Presets aplicados sobreescriben la selección manual y viceversa.

### Patrón 5 — Formulario largo multi-sección (`Patron5-FormularioMultiSeccion.dc.html`)
- Sidebar de navegación sticky (220px), lista las 7 secciones. Sección activa: `border-left:3px solid #F7941D background:rgba(247,148,29,.06) color:#F7941D font-weight:700`. Completadas: checkmark circular verde `#22c55e` a la derecha.
- Secciones como acordeón: header expandible, fondo activo `rgba(247,148,29,.04)`, título activo `color:#F7941D`.
- Tipos de campo: `input` text, `select`, `textarea` (resize:vertical). Todos comparten el mismo estilo base: `padding:10px 12px border-radius:8px border:1px solid rgba(0,0,0,.15)`. Focus: `border-color:#F7941D`.
- Hints de campo alineados a la derecha del label, 12px `#9a9a9a`.
- Botones de acción sticky al final o fijos al pie: "Cancelar" outline gris + "Guardar cambios" naranja.
- Las 7 secciones: Datos generales, Contactos, Equipos y sucursales, Configuración SDS, Umbrales de alerta, Facturación, Notas internas.

### Patrón 6 — Modal de confirmación (`Patron6-ModalConfirmacion.dc.html`)
Esqueleto compartido: `border-radius:16px padding:28px box-shadow:0 4px 24px rgba(0,0,0,.07)`. Header: título Montserrat 800 17px + botón ✕ `color:#9a9a9a`. Footer: dos botones flex, "Cancelar" outline gris + botón primario.
- **Variante simple** (SDS, ERS, FTP, Procesar DB3, Proyección, Calculadora): descripción 14px `#4b4b4b`, botón naranja.
- **Variante warning** (Estimación en 0, Suma Fija): bloque de alerta `background:rgba(234,179,8,.08) border:1px solid rgba(234,179,8,.3) border-radius:10px`, ícono ⚠️ en círculo amarillo, texto `color:#92400e`, botón `background:#eab308`.
- **Variante destructiva** (eliminación): bloque rojo `rgba(239,68,68,.07) / border rgba(239,68,68,.25)`, input de confirmación con `border:1.5px solid rgba(239,68,68,.4)`, botón `background:#ef4444`. El botón destructivo debe estar deshabilitado hasta que el input contenga el texto de confirmación.

---

## Las 9 pantallas

### 1. Dashboard (`/`) — principal
**Patrones**: Patrón 1 (tabla expandible) + Patrón 6 (5 modales de confirmación)

**Layout**: mismo shell del portal (header 64px + sidebar 224px + panel principal con scroll).

**Encabezado del panel**: row de 4 tiles KPI (heredar de Inicio, solo cambiar íconos/colores/labels):
- Clientes activos (naranja)
- Equipos monitoreados (gris `#58595B`)
- Solicitudes en curso (charcoal `#3A3A3C`)
- Alertas activas (rojo `#ef4444` — excepción puntual)

**Barra de acciones**: buscador + filtro de cliente (select) + date range picker compacto (trigger → popover con Patrón 4) + botón "Procesar todo" (naranja).

**Tabla de clientes** (Patrón 1): cuerpo principal. Al click en los botones de acción de la fila (SDS, ERS, FTP, Reset, Eliminar) se disparan los respectivos modales (Patrón 6, variante según acción).

**5 modales del Dashboard**:
1. Descargar SDS → variante simple
2. Descargar ERS → variante simple
3. Descarga FTP → variante simple (agrega campo host/puerto)
4. Estimación en 0 → variante warning
5. Suma Fija → variante warning (agrega campo de valor fijo en hojas)

---

### 2. Clientes
**Patrones**: tabla simple + modal CRUD de contactos (Patrón 6 extendido)

**Layout**: panel completo, sin sidebar anidado.

**Tabla**: columnas — Nombre, CUIT, Equipos, Contrato, Último proceso, Estado, Acciones. Sin filas expandibles. Paginación simple (anterior / siguiente + "Mostrando X de Y").

**Acciones por fila**: Editar (→ abre Formulario, Patrón 5, pre-poblado), Ver detalle (→ navega a Estadísticas del cliente), Eliminar (→ modal destructivo).

**Modal CRUD de contactos**: extiende el esqueleto del Patrón 6 con una lista de contactos inline (nombre + email + teléfono + rol). Agregar/eliminar contacto dentro del modal. Botón "Guardar contactos" naranja.

---

### 3. Equipos Nuevos
**Patrones**: tabla simple

**Descripción**: lista de equipos incorporados recientemente (últimos 30 días) aún no configurados en SDS.

**Tabla**: columnas — Modelo, N° de serie, Cliente asignado, Sucursal, Fecha de alta, Estado configuración. Badge de estado: "Sin configurar" (gris), "Configurando" (naranja), "Listo" (verde).

**Acción principal**: botón "Configurar" por fila → abre Formulario multi-sección (Patrón 5) en modo "nuevo equipo" (secciones: Datos del equipo, Asignación de cliente, Configuración SDS).

---

### 4. Equipos Offline
**Patrones**: Patrón 3 (secciones colapsables + alertas multi-nivel)

**Descripción**: 6 grupos de alertas agrupados por cliente/sucursal, ordenados por severidad (crítico arriba).

**Lógica de agrupación**:
- Un grupo por cliente activo con equipos offline.
- El nivel del grupo es el nivel máximo de cualquier equipo dentro de él.
- Grupos sin alertas no aparecen.

**Acciones dentro de cada alerta**: "Reintentar lectura" (botón outline naranja), "Marcar como revisado" (outline gris), "Crear ticket" (link).

**Header de la pantalla**: contador de equipos offline en tiempo real (badge rojo animado), botón "Reintentar todos" (naranja).

---

### 5. Configuración
**Patrones**: Patrón 5 (formulario multi-sección, 7 secciones)

**Contexto**: pantalla de configuración de un cliente específico (navegar desde Clientes → Editar).

**Las 7 secciones** (ver Patrón 5 para detalle de campos):
1. Datos generales
2. Contactos
3. Equipos y sucursales
4. Configuración SDS (URL colector, intervalo, credenciales)
5. Umbrales de alerta (% tóner crítico, % advertencia, días sin reporte)
6. Facturación (centro de costo, modalidad, precio por hoja)
7. Notas internas

**Sidebar**: navigation sticky con estado completado por sección (checkmark verde).

---

### 6. Historial
**Patrones**: tabla con filtros combinados (Patrón 4 para rango de fechas + chips de tipo de evento)

**Descripción**: log de todas las operaciones realizadas (descargas SDS/ERS/FTP, reposiciones, resets, modificaciones de config).

**Filtros en header**: tipo de evento (chips multi-select: SDS, ERS, FTP, DB3, Insumos, Config), cliente (select), rango de fechas (Patrón 4 compacto), usuario que ejecutó.

**Tabla**: columnas — Fecha/hora, Tipo (badge con color), Cliente, Equipo, Usuario, Resultado (OK / Error / En proceso), Detalles (link → modal de log completo).

**Modal de log**: extiende Patrón 6 simple con un bloque de código `<pre>` monoespacio para el output del proceso. Sin botón de acción secundario, solo "Cerrar".

---

### 7. Estadísticas (vista global)
**Patrones**: Patrón 2 (gráfico de tendencia) + tiles KPI (herencia de Inicio)

**Descripción**: vista agregada de consumo de toda la flota.

**Header**: selector de cliente (todos / uno específico) + Patrón 4 para rango de fechas.

**Tiles KPI**: Hojas totales período, Reposiciones realizadas, Equipos sin datos, Tóner promedio de flota.

**Gráfico de tendencia** (Patrón 2): consumo mensual por cliente (multi-línea, máximo 5 clientes simultáneos para legibilidad). Toggle de vista: por cliente / por modelo.

**Tabla inferior**: ranking de equipos por consumo (top 10), columnas Equipo · Cliente · Hojas del período · Δ vs período anterior.

---

### 8. Detalle de cliente — Estadísticas
**Patrones**: Patrón 2 (gráfico por equipo individual) + modo impresión

**Descripción**: pantalla de detalle de un cliente, navegable desde Clientes → Ver detalle. URL: `/clientes/:id/estadisticas`.

**Layout**: header con nombre del cliente + período (Patrón 4) + botón "Imprimir reporte" (outline gris).

**Sección superior**: tiles KPI del cliente (Equipos activos, Hojas del período, Reposiciones, Tóner promedio).

**Gráfico de tendencia** (Patrón 2): un gráfico por equipo (tab o select para cambiar entre equipos). El gráfico muestra hojas impresas + proyección + marcas de reposición.

**Tabla de equipos**: cada equipo del cliente con barra de tóner (Patrón 1, solo la sub-fila, sin acordeón).

**Modo impresión** (`@media print`): ocultar sidebar, header, botones de acción. Mostrar logo Canal Directo naranja, nombre del cliente, período, tiles KPI y gráficos en blanco y negro (`filter:grayscale(1)`). Pie de página: "Generado por Mesa de Ayuda · Canal Directo · {fecha}".

---

### 9. Detalle de consumible (modal)
**Patrones**: Patrón 6 extendido con contenido custom

**Descripción**: modal que se abre desde la fila expandida del Dashboard (Patrón 1) al hacer click en "Ver" en una solicitud de tóner.

**Contenido del modal** (ancho 520px):
- Header: modelo + N° de serie.
- Barra de tóner grande (height 12px, radio 6px) con el nivel actual y color por severidad.
- Sección "Historial de reposiciones": lista de las últimas 5 (fecha, insumo, quién lo procesó).
- Sección "Próxima reposición estimada": fecha calculada según tendencia de consumo + botón "Generar solicitud" (naranja).
- Footer: botón "Cerrar" outline gris. Sin acción destructiva.

---

## Pantalla: Solicitudes de Insumos sin Cargar (`Insumos-Solicitudes-sin-Cargar.dc.html`)

Corrige una implementación que se había desviado del diseño original. Ruta: Insumos → Solicitudes.

- **Título** "Solicitudes de Insumos sin Cargar" (Title Case, no todo en minúscula salvo la primera letra).
- **Header de página**: "Actualizado HH:MM" + punto verde en vivo (`#22c55e`, glow `0 0 0 3px rgba(34,197,94,.15)`) + botón outline "↻ Actualizar". Campana de notificaciones ya vive en el header global (badge rojo), no se duplica en el body.
- **Franja de 7 KPIs**, grid parejo, cada tile con **borde de 1.5px del color semántico** (no solo el filtro activo): Pendientes `#F7941D` · Críticos ≤3d `#ef4444` · Urgentes ≤7d `#f97316` · Atención ≤14d `#eab308` · OK `#22c55e` · Con pedido `#3b82f6` · Cargados hoy `#F7941D`. Número grande centrado arriba, label uppercase debajo — **no** el layout label-arriba/número-abajo alineado a la izquierda de la implementación anterior.
- **Tabla de clientes**: fila de cliente **sin avatar/iniciales** (esa variante con círculo "SD" no es del diseño original) — solo chevron + nombre en negrita + los 6 contadores a la derecha (Pendientes/Críticos/Urgentes/Atención/OK/Cargados).
- **Panel expandido**: título "Solicitudes de {cliente} (N)" + botones "Cargar seleccionados (N)" (ámbar) / "Descartar seleccionados (N)" (rojo). Tabla interna con columna **"%"** (no "Nivel") para el nivel de tóner, barra + porcentaje + "Ini: X%"; columna Días rest. con valor + "Ini: N". **Acción tiene solo Cargar/Descartar** — el botón "Ver" adicional no corresponde a este diseño (esa acción vive en el modal de detalle de consumible, patrón aparte).
- **Leyenda**: 4 estados con su color real — Crítico rojo, Urgente naranja, Atención **amarillo** (`#eab308`, no confundir con el naranja de Urgente), OK verde.
- **Sección "Scan de supplies (Canal Directo)"**: card colapsable al pie de la pantalla, chevron + título a la izquierda, botón outline "Ejecutar scan" a la derecha — se había perdido en la implementación anterior; dispara un relevamiento manual de niveles vía HP SDS.

## Archivos

```
design_handoff_sds_insumos/
├── README.md                                    ← este archivo
├── Insumos-Solicitudes-sin-Cargar.dc.html        ← mockup interactivo de la pantalla corregida
├── support.js
├── assets/logo-naranja.png
└── patrones/
    ├── Patron1-TablaExpandible.dc.html
    ├── Patron2-GraficoTendencia.dc.html
    ├── Patron3-AlertasColapsables.dc.html
    ├── Patron4-DateRangePicker.dc.html
    ├── Patron5-FormularioMultiSeccion.dc.html
    └── Patron6-ModalConfirmacion.dc.html
```

Cada `.dc.html` es un mockup interactivo autocontenido — abrirlo directamente en el navegador muestra el patrón funcionando con datos de ejemplo.  
Las 9 pantallas son **composición** de estos patrones: no se requiere mockup adicional por pantalla.
