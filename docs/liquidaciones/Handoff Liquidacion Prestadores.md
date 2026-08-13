# Handoff: Asistente de Liquidaciones (legacy → HelpDeskManager)

## Contexto
App standalone legacy en React + Node (`localhost:3002`) que gestiona las liquidaciones de Prestadores de Servicio Técnico (PST). Se migra como **módulo PST** dentro de HelpDeskManager-Web, respetando el mismo sistema de diseño dark del portal (naranja `#F7941D`, Montserrat + Source Sans Pro).

El módulo tiene 5 pantallas + 1 dashboard:

```
/pst                           → Dashboard
/pst/liquidaciones             → Listado de liquidaciones
/pst/configuracion/prestadores → CRUD de prestadores
/pst/configuracion/spsts       → CRUD de sub-prestadores (SPSTs)
/pst/configuracion/tarifarios  → Estructura de tarifas por prestador
/pst/configuracion/tabla-km    → Tabla de kilómetros por PST-cliente
```

---

## Navegación (sidebar del módulo)

El legacy tiene dos secciones en el sidebar: navegación principal y configuración.
Migrar con el mismo patrón de submenú agrupado que Insumos:

```
● PST  ∨                     ← activo/expandido en el sidebar global

  PRINCIPAL
  ■ Dashboard
    Liquidaciones

  CONFIGURACIÓN
    Prestadores
    SPSTs
    Tarifarios
    Tabla KM
```

Botón de cabecera del módulo: igual al del portal (logo + "MESA DE AYUDA"). No llevar el "ASISTENTE DE LIQUIDACIONES" del legacy.

---

## Pantalla 1: Dashboard (`/pst`)

### KPI tiles (4 columnas)
| Tile | Label | Color acento | Notas |
|---|---|---|---|
| 1 | Liquidaciones pendientes | `#eab308` | muestra count + "de X total" |
| 2 | Total importadas | `#e0e0e0` | número grande |
| 3 | Total incidentes | `#22c55e` | suma de todos los incidentes |
| 4 | Total facturado | `#e0e0e0` | importe en ARS con formato `$ 88.117.657,65` |

Cada tile: `background:#1e1e1e border-radius:10px padding:20px`. Label 11px Montserrat uppercase `#9a9a9a`. Número Montserrat 800, grande. Subtítulo 12px Source Sans Pro `rgba(255,255,255,.35)`.

### Tabla "Últimas liquidaciones"
- Header: "Últimas liquidaciones" (Montserrat 700 16px blanco) + link "Ver todas" (naranja, alineado a la derecha).
- Columnas: **PRESTADOR · PERÍODO · ESTADO · INCIDENTES · IMPORTE · FECHA DE CARGA**
- Ordenamiento por columna: flechitas `↑↓` al lado del header (ambas direcciones, activa resalta en naranja).
- Estados con badge:
  - `abierta` → sin badge, texto plano `rgba(255,255,255,.6)`
  - `recibida` → sin badge, texto plano `rgba(255,255,255,.6)`
  - `aprobada` → pill verde `rgba(34,197,94,.15)` / `#4ade80`
  - `cerrada` → pill gris `rgba(255,255,255,.1)` / `rgba(255,255,255,.5)`
- IMPORTE: alineado a la derecha, formato ARS.
- Sin paginación en el dashboard (muestra últimas 8–10).

### Botón primario
`+ Importar liquidación` — naranja, esquina superior derecha, abre modal de importación.

---

## Pantalla 2: Liquidaciones (`/pst/liquidaciones`)

### Filtros
- Select "Estado": -- Todos -- / abierta / recibida / aprobada / cerrada

### Tabla principal
Columnas: **ARCHIVO · PRESTADOR · PERÍODO · TIPO · ESTADO · INCIDENTES · IMPORTE · FECHA · (Eliminar)**

- **ARCHIVO**: link naranja, nombre del archivo `.xls` (formato `liquidacion_NNNN-N_AAAAMMDD.xls`). Al click abre/descarga el archivo.
- **PRESTADOR**: texto plano — formato "Ciudad - Nombre PST".
- **PERÍODO**: formato `AAAA-MM`.
- **TIPO**: badge pill gris `rgba(255,255,255,.08)` / texto `rgba(255,255,255,.5)` — "regular" / "complementaria".
- **ESTADO**: igual que en Dashboard.
- **INCIDENTES**: número, alineado derecha.
- **IMPORTE**: formato ARS, alineado derecha.
- **FECHA**: `DD/M/AAAA`, texto `rgba(255,255,255,.4)`.
- **Eliminar**: botón/link rojo `#ef4444`, abre modal de confirmación destructiva (Patrón 6 del handoff de Insumos).

Paginación: scroll infinito o paginación simple (anterior / siguiente + "Mostrando X de Y").

### Botón primario
`+ Importar` — esquina superior derecha, mismo estilo que Dashboard.

**Modal de importación**: Patrón 6 (simple), campos:
- Select "Prestador" (obligatorio)
- Input "Período" tipo `month` (`AAAA-MM`)
- Input "Tipo" — radio: regular / complementaria
- File picker `.xls / .xlsx`
- Botón "Importar liquidación" (naranja)

Al importar exitoso → toast verde "Liquidación importada correctamente" + recarga la tabla.

---

## Pantalla 3: Prestadores (`/pst/configuracion/prestadores`)

### Formulario "Nuevo prestador" (inline, top de la página)
4 campos en grid 2×2:
- **Nombre completo** \* — text input
- **Nombre corto (clave)** \* — text input, placeholder "PENTACOM", uppercase automático al guardar
- **CUIT** — text input (sin guiones, hint bajo el campo)
- **Región / Plaza** — text input, placeholder "Córdoba, Rosario..."

Checkbox "Activo" (checked por defecto).  
Botón `Crear prestador` (naranja, outline o sólido).

### Acciones bulk CSV (header)
Dos botones esquina derecha:
- `Descargar planilla CSV` — outline gris
- `Cargar Planilla CSV` — naranja sólido

### Tabla de prestadores
Columnas: **CLAVE · NOMBRE · CUIT · REGIÓN · ESTADO · (Editar / Eliminar)**

- **CLAVE**: Montserrat 700, uppercase, `rgba(255,255,255,.8)`.
- **NOMBRE**: texto plano — "Ciudad - Nombre completo".
- **CUIT**: `—` si vacío.
- **REGIÓN**: uppercase, `rgba(255,255,255,.5)`.
- **ESTADO**: badge `Activo` verde / `Inactivo` gris.
- **Editar**: link naranja → abre el formulario pre-poblado en modo edición (inline o modal).
- **Eliminar**: link rojo → modal destructivo (Patrón 6).

Sin paginación visible en el legacy — implementar scroll o paginación simple si la lista supera 50 registros.

---

## Pantalla 4: SPSTs (`/pst/configuracion/spsts`)

Sub-prestadores de servicio técnico — técnicos y zonas de cobertura.

### Formulario "Nuevo SPST" (inline, top)
Campos:
- **Prestador** \* — select (lista de prestadores activos), placeholder "Seleccioná..."
- **Nombre** \* — text input, placeholder "PST Córdoba - Pentacom S.A."
- **Domicilio base** — text input
- **Localidad** — text input
- **Provincia** — text input
- **Zona** — text input, placeholder "Córdoba Capital, Río Cuarto..."

Checkbox "Activo" (checked por defecto). Botón `Crear` (naranja).

### Acciones bulk CSV — igual que Prestadores.

### Filtro + contador
Select "Todos los PSTs / por PST" + label "49 SPSTs" a la derecha.

### Tabla de SPSTs
Columnas: **PST · NOMBRE · LOCALIDAD · ZONA · ESTADO · (Editar / Eliminar)**

- **PST**: clave del prestador padre (CALETA, PENTACOM…), Montserrat 700 uppercase.
- **NOMBRE**: link naranja — "PST Ciudad - Nombre". Al click abre detalle/edición.
- **LOCALIDAD / ZONA**: texto `rgba(255,255,255,.6)`.
- **ESTADO**: badge Activo/Inactivo.

---

## Pantalla 5: Tarifarios (`/pst/configuracion/tarifarios`)

Estructura de costos por prestador — incluye viáticos, traslados y tipos de servicio.

### Header
Título "Estructura de Tarifarios" + subtítulo. Botones:
- `Descargar planilla CSV` (outline)
- `Cargar Planilla CSV` (naranja)
- `+ Nueva Tarifa` (naranja)

### Filtro
Select "Filtrar por prestador": Todos / por prestador. Contador "X tarifas cargadas en total".

### Estado vacío por prestador
Cuando un prestador no tiene tarifas: card `background:#1e1e1e border-radius:12px padding:32px` centrado, ícono maletín SVG `rgba(255,255,255,.15)`, título del prestador (Montserrat 700), texto "Este prestador no tiene tarifas cargadas actualmente.", botón `+ Configurar tarifas iniciales` (outline naranja).

### Estado con tarifas (a implementar)
Cuando tiene tarifas: tabla con columnas TIPO DE SERVICIO · PRECIO BASE · KM INCLUIDOS · PRECIO/KM EXTRA · VIGENCIA · (Editar/Eliminar). Cada fila es una tarifa. El prestador actúa de encabezado de sección (accordion, expandido por defecto).

### Modal "Nueva Tarifa"
Campos: Prestador (select) · Tipo de servicio (select: visita, traslado, emergencia…) · Precio base (number ARS) · KM incluidos (number) · Precio por KM extra (number) · Fecha de vigencia desde (date). Botón "Guardar" naranja.

---

## Pantalla 6: Tabla KM (`/pst/configuracion/tabla-km`)

KMs pre-acordados por par **PST + cliente/sucursal**. Fuente de verdad para validación de distancias en liquidaciones.

### Header
Título "Tabla KM" + subtítulo. Botones: Descargar CSV / Cargar CSV / Exportar CSV / `+ Nueva Entrada`.

### Filtros
- Select "Todos los prestadores / por PST"
- Input "Buscar por cliente o sucursal..."
- Contador "1633 entradas en total" (alineado derecha)

### Lista agrupada por PST (accordion)
Cada grupo:
```
▾  PST CORRESPONDIENTE          ← label 10px uppercase naranja
   Bahia Blanca - Eduardo Lledos  (BAHIA)  15 clientes    + Agregar Entrada
```

- Header del grupo: fondo `#1e1e1e`, chevron `▾/▸`, clave del PST en badge gris pequeño, count de clientes en badge gris, botón `+ Agregar Entrada` alineado a la derecha.
- Grupos sin asignación: badge rojo "Sin asignar" en lugar del count.
- Al expandir: tabla de entradas con columnas **CLIENTE/SUCURSAL · KM IDA · KM VUELTA · TOTAL KM · (Editar / Eliminar)**.

### Modal "Nueva Entrada"
Campos: PST (select) · Cliente (select o búsqueda) · Sucursal (text) · KM ida (number) · KM vuelta (number, calculado automáticamente = mismo valor si es simétrico). Botón "Guardar" naranja.

---

## Estados de liquidación

| Estado | Badge | Color fondo | Color texto |
|---|---|---|---|
| `abierta` | sin badge | — | `rgba(255,255,255,.6)` |
| `recibida` | sin badge | — | `rgba(255,255,255,.6)` |
| `aprobada` | pill | `rgba(34,197,94,.15)` | `#4ade80` |
| `cerrada` | pill | `rgba(255,255,255,.08)` | `rgba(255,255,255,.45)` |

---

## Design tokens (herencia del portal)

| Token | Valor |
|---|---|
| Naranja principal | `#F7941D` |
| Fondo página | `#111` |
| Superficie card/tabla | `#1e1e1e` |
| Superficie header tabla | `rgba(0,0,0,.2)` |
| Borde sutil | `rgba(255,255,255,.07)` |
| Texto principal | `#e0e0e0` |
| Texto secundario | `rgba(255,255,255,.5)` |
| Texto muted | `rgba(255,255,255,.3)` |
| Link | `#F7941D` |
| Verde éxito | `#4ade80` |
| Rojo error/eliminar | `#ef4444` |
| Amarillo advertencia | `#eab308` |
| Radio card | `12px` |
| Radio botón/input | `8px` |
| Fuente título | Montserrat 700–800 |
| Fuente cuerpo | Source Sans Pro 400/600 |
| **Prohibido** | celeste `#3DB1CA` / violeta `#662D91` |

---

## Diferencias clave legacy → HelpDeskManager

| Aspecto | Legacy | HelpDeskManager |
|---|---|---|
| Tema | Gris claro / blanco | Dark `#111` total |
| Logo | CANAL DIRECTO + "ASISTENTE DE LIQUIDACIONES" | Logo naranja + "MESA DE AYUDA" |
| Sidebar | Flat list blanco | Submenú agrupado dark con badges |
| Tipografía | Sistema / sans genérica | Montserrat + Source Sans Pro |
| Naranja | `#F7941D` (igual) | `#F7941D` |
| Modales | Alerts del browser / inline | Patrón 6 del handoff de Insumos |
| Toasts | N/A | Toast verde/rojo esquina inferior derecha |
| Tabla ordenable | ↑↓ texto plano | ↑↓ con activa en naranja |
| Acciones bulk CSV | Botones verdes/naranja | Outline gris (↓) + naranja sólido (↑) |
| "Eliminar" inline | Link rojo en la fila | Link rojo → modal destructivo |
| Estado "aprobada" | Badge verde claro sobre fondo blanco | Badge `rgba(34,197,94,.15)` / `#4ade80` |

---

## Archivos de referencia

```
design_handoff_liquidaciones/
└── README.md               ← este archivo (specs completas)

Screenshots legacy (en uploads/):
  pasted-1786563078239-0.png  → Dashboard
  pasted-1786563089464-0.png  → Liquidaciones
  pasted-1786563095691-0.png  → Prestadores
  pasted-1786563101273-0.png  → SPSTs
  pasted-1786563106854-0.png  → Tarifarios
  pasted-1786563124739-0.png  → Tabla KM

Mockups del portal (referencia de estilo):
  Portal Mesa de Ayuda.dc.html
  PST - Prestadores.dc.html
  design_handoff_mesa_de_ayuda/README.md
  design_handoff_sds_insumos/README.md
```
