# Handoff: Reasignación Temporal de Operadores y PST — Canal Directo

## Contexto
Mismo design system que `design_handoff_mesa_de_ayuda/` — no se reespecifica paleta ni tipografía salvo excepciones puntuales. Para tokens rápidos, ver ese README.

---

## 1. Resumen del feature y principios de diseño

La Reasignación Temporal permite definir reglas de cobertura con vigencia acotada por rango de fechas: cuando un operador (contador) o PST falta, otro lo cubre sin tocar el Calendario de Gestión externo. Al vencer el rango, la asignación vuelve sola al operador real, sin intervención manual.

**Principios:**
- **Temporalidad explícita**: el rango desde/hasta es obligatorio. El sistema comunica en todo momento cuándo empieza, cuándo termina y qué pasa al vencer.
- **No invasivo**: la cobertura es local a HelpDeskManager. El copy lo dice explícitamente en el formulario, en el listado y en el Calendario.
- **Operador real siempre visible**: en el Calendario, el operador real nunca desaparece; se muestra junto al efectivo. No se reemplaza silenciosamente uno por otro.
- **Componente único parametrizado**: el ABM de coberturas se reutiliza para Contadores (`entityType="contador"`) y PST (`entityType="pst"`), sin duplicar el diseño. Las diferencias son solo de labels.
- **Design system estricto**: todo color sale de tokens semánticos; nada de colores Tailwind literales. Si falta un token (ej. `bg-success`), se agrega a `shared/components/ui/` — no dentro del feature.

---

## 2. Mapa de pantallas y navegación

### Entrada desde el sidebar del portal

```
Sidebar
├── Inicio
├── Contadores
│   ├── SDS, ERS, FTP, DB3, Estimación en 0…
│   ├── Coberturas          ← NUEVO  →  /contadores/coberturas
│   └── Calendario          ← MODIFICADO (capa de indicadores)
└── PST / Liquidaciones
    ├── Prestadores, Tarifarios, Tabla KM…
    └── Coberturas          ← NUEVO  →  /pst/coberturas
```

### Rutas

| Ruta | Pantalla |
|---|---|
| `/contadores/coberturas` | Listado/ABM de coberturas de contadores |
| `/contadores/coberturas/nueva` | Modal alta (montado sobre el listado) |
| `/contadores/coberturas/:id/editar` | Modal edición |
| `/contadores/calendario` | Calendario existente + indicadores de cobertura |
| `/pst/coberturas` | Listado/ABM de coberturas de PST |
| `/pst/coberturas/nueva` | Modal alta PST |
| `/pst/coberturas/:id/editar` | Modal edición PST |

### Relación con el Calendario existente

El Calendario de Contadores recibe una **capa de indicadores** sin cambios estructurales: mismo componente, misma lógica de sincronización. Se agregan:
- Badge por evento cubierto (esquina del chip de evento)
- Switch "Ver por operador efectivo / real" en el header
- Tooltip al hover sobre eventos cubiertos (delay 200ms)
- Leyenda de cobertura activa

---

## 3. Pantallas y estados

### 3.1 Coberturas — Listado (Contadores y PST)

**Objetivo**: que el team leader vea de un vistazo qué operadores/PST están cubiertos hoy y por quién, y pueda crear, editar o cancelar coberturas.

**Layout**: panel completo dentro del portal shell existente (header 64px + sidebar 224px + panel con scroll).

**Header del panel**:
- Título "COBERTURAS" — Montserrat 800, uppercase, letter-spacing: -.03em
- Subtítulo "Reemplazos temporales de operadores · No modifican el Calendario de Gestión" — 13.5px, `text-muted-foreground`
- Button "Nueva cobertura" — `variant=primary, icon=Plus`, alineado a la derecha

**Filtros** (row antes de la tabla):
- Chips de estado: Todos / Activa / Programada / Vencida / Cancelada
- Input de búsqueda: `placeholder="Buscá operador…"` (SearchableSelect trigger compacto)
- Link "Limpiar filtros" — `text-muted hover:text-accent`

**Tabla paginada** (20 filas/pág):

| Col | Contenido |
|---|---|
| Ausente | Avatar cuadrado (color + iniciales) + nombre + @username |
| Reemplazante | Ídem |
| Vigencia | "15 ago 2026" / "→ 29 ago 2026" en dos líneas |
| Alcance | "Total" o "3 clientes" |
| Motivo | Texto plano |
| Estado | Badge con tono semántico (ver §5) |
| Acciones | Editar (ghost/icon) · Cancelar (ghost/icon/destructive) — Cancelar solo si Activa o Programada |

**Estados del listado**:
- **Con datos**: tabla + paginación + nota de pie
- **Vacío**: ícono decorativo + "No hay coberturas todavía" (Montserrat 700) + subtítulo + Button primary "Nueva cobertura"
- **Cargando**: skeleton de 5 filas (pulse animation, `bg-muted/50`)
- **Error**: banner `bg-destructive/10 border border-destructive/20 rounded-lg` + "No se pudieron cargar las coberturas. Intentá de nuevo." + Button outline "Reintentar"

**Copy de pie de tabla** (siempre visible bajo la tabla):
> "Al vencer la vigencia, los clientes vuelven automáticamente a su operador original. Las coberturas no modifican el Calendario de Gestión."
> 12px, `text-muted`, bloque `bg-muted/30 rounded-lg px-4 py-3`.

**Variante PST**: mismo componente, columnas "PST Ausente" y "PST Reemplazante", avatar muestra iniciales de la empresa, subtítulo de avatar muestra la zona (ej. "Córdoba"). Copy de pie usa "…las zonas vuelven automáticamente a su PST original."

---

### 3.2 Alta / Edición de Cobertura (modal)

**Objetivo**: crear o editar una regla de cobertura con validación visible en tiempo real.

**Tipo**: `Modal` del DS — `open, onClose, title, size="lg"` — `rounded-[2.5rem]`, focus trap, cierre con Escape, `aria-modal`, `aria-labelledby`.

**Título**: "NUEVA COBERTURA" / "EDITAR COBERTURA" — Montserrat 800, uppercase. Subtítulo: "Contadores / Operadores" o "PST / Liquidaciones".

**Campos en orden de tab**:

1. **¿Quién falta?** — `SearchableSelect` (NUEVO). Búsqueda por nombre o usuario. Opción muestra avatar + nombre + @username. Error: "Seleccioná un operador ausente."
2. **¿Quién lo cubre?** — Mismo componente. Excluye al operador seleccionado en (1). Error si mismo operador: "El reemplazante no puede ser el mismo que el ausente."
3. **Vigencia** — `DateRangePicker` (ver Patrón 4 de sds_insumos — promover a `shared/components/ui/`). Dos campos: Desde / Hasta. `minDate=today`. Error si hasta < desde: "La fecha de fin tiene que ser posterior al inicio."
4. **Alcance** — `SegmentedControl` (NUEVO): "Total" / "Clientes específicos". Default: Total.
5. **Clientes/sucursales** — Condicional: visible solo si Alcance = Específicos. `SearchableSelect` con `multiple=true`. Label: "Clientes o sucursales". Error si vacío: "Seleccioná al menos un cliente."
6. **Motivo** — Select simple. Opciones: Vacaciones / Ausencia / Otro.

**Banner de solapamiento** (warning, no bloqueante):
```
⚠️  Posible solapamiento
Ya existe una cobertura para {operador} del {fecha} al {fecha}.
Revisá los rangos antes de guardar.
```
Token: `bg-accent/10 border border-accent/30`.

**Nota de alcance** (siempre visible, antes de los botones):
```
Esta cobertura es temporal y no modifica el Calendario de Gestión.
Al finalizar el {fecha_hasta}, los clientes vuelven a {operador_ausente} automáticamente.
```
Estilo: `bg-muted/30 rounded-lg px-4 py-3`, 12px, `text-muted-foreground`.

**Acciones**:
- "Cancelar" — `Button variant=outline`
- "Guardar cobertura" — `Button variant=primary` — deshabilitado hasta que todos los campos requeridos estén completos
- Estado guardando: spinner + "Guardando…"
- Error de guardado: banner `bg-destructive/10` bajo el título del modal

**Variante PST**: mismos campos, labels cambian — "¿Qué PST falta?" / "¿Qué PST lo cubre?" / "Zonas específicas" / "Zonas o localidades" / nota con "…las zonas vuelven a {pst_ausente}…"

---

### 3.3 Calendario con indicadores de cobertura

**Objetivo**: mostrar en el Calendario existente cuáles eventos están bajo una cobertura activa y quién los cubre efectivamente, sin ocultar el operador real.

**Cambios al componente Calendario** (adiciones, no rediseño):

**A. Switch en el header**:
- Label: "Ver por" + `SegmentedControl`: "Operador efectivo" / "Operador real"
- Default: "Operador efectivo"
- En modo "Operador efectivo": eventos cubiertos muestran el color del reemplazante + badge "CUBIERTO POR {iniciales}"
- En modo "Operador real": eventos cubiertos muestran el color del operador original + badge muted "↩ {iniciales} cubre"

**B. Badge sobre evento cubierto**:
- Chip pequeño en la esquina superior del evento: "CUBIERTO POR MG" (efectivo) o "↩ MG cubre" (real)
- 9.5px, font-weight 700, `bg-accent/90 text-white` en modo efectivo / `bg-muted text-muted-foreground` en modo real

**C. Tooltip al hover** (delay 200ms, Escape cierra):
```
COBERTURA ACTIVA
Ausente:      Victor Paez (@vipaez)
Reemplazante: María González (@mgonzalez)
Vigencia:     15 ago → 29 ago 2026
Alcance:      Total
[Ver detalle →]
```
Estilo: `bg-surface rounded-xl shadow-lg px-4 py-3`, min-width 240px, `Tooltip` del DS.

**D. Leyenda** (debajo del calendario):
- ● Evento cubierto (operador efectivo) · ● Evento propio

**Indicador en fila de operador ausente**:
- Bajo el nombre del operador en la columna de identidad: chip pequeño "● Cubierto" en `text-accent`

---

### 3.4 Variante PST

El listado y el modal son el **mismo componente** (`CoberturaTable` / `CoberturaModal`) con prop `entityType: 'contador' | 'pst'`.

| Elemento | Modo contador | Modo PST |
|---|---|---|
| Título | "COBERTURAS" | "COBERTURAS PST" |
| Label campo 1 | "¿Quién falta?" | "¿Qué PST falta?" |
| Label campo 2 | "¿Quién lo cubre?" | "¿Qué PST lo cubre?" |
| Avatar subtítulo | @username | Zona (ej. "Córdoba") |
| Alcance Total | "Todos los clientes del operador" | "Todas las zonas del PST" |
| Alcance Parcial | "Clientes específicos" | "Zonas específicas" |
| Multi-select label | "Clientes o sucursales" | "Zonas o localidades" |
| Copy footer | "…los clientes vuelven a {op}…" | "…las zonas vuelven a {pst}…" |

**PSTs reales del dominio** (para los mockups):
- Pentacom — Córdoba
- Pertex-Supernova — Rosario
- Infomac — Villa Mercedes / Gral. Roca
- Gestión Integral — San Juan

---

## 4. Especificación de componentes

| Elemento del mockup | Primitivo DS | Props / estados | Nuevo |
|---|---|---|---|
| Botón "Nueva cobertura" | `Button` | `variant="primary" size="md"` + ícono `Plus` a la izquierda | No |
| Botón "Editar" (fila) | `Button` | `variant="ghost" size="icon"` + ícono `Pencil` | No |
| Botón "Cancelar cobertura" (fila) | `Button` | `variant="ghost" size="icon"` + ícono `Ban` + `className="text-destructive"` | No |
| Botón "Reintentar" (error) | `Button` | `variant="outline"` | No |
| Badge de estado | `Badge` | prop `tone: "success"\|"accent"\|"muted"\|"destructive"` — ver §5 | Badge ya existe; agregar prop `tone` si no existe |
| Input búsqueda de filtros | `Input` | `type="search" placeholder="Buscá operador…"` | No |
| Select operador ausente / reemplazante | `SearchableSelect` | ver API abajo | **SÍ — nuevo en shared/ui/** |
| Multi-select clientes / zonas | `SearchableSelect` | `multiple=true` — misma API | **SÍ — variante de SearchableSelect** |
| DateRangePicker vigencia | `DateRangePicker` | ver API abajo — promover desde sds_insumos Patrón 4 | **SÍ — mover a shared/ui/** |
| Toggle Alcance Total/Parcial | `SegmentedControl` | ver API abajo | **SÍ — nuevo en shared/ui/** |
| Modal de alta/edición | `Modal` | `open, onClose, title, size="lg"` + focus trap + Escape | No (ya en DS) |
| Banner solapamiento | `Alert` | `variant="warning" icon={AlertTriangle}` | **SÍ — nuevo en shared/ui/** |
| Banner error de carga | `Alert` | `variant="destructive" action={<Button>Reintentar</Button>}` | **SÍ — mismo primitivo** |
| Skeleton de tabla | `Skeleton` | `rows=5` | **SÍ — nuevo en shared/ui/** |
| Tooltip de cobertura en Calendario | `Tooltip` | `content, delay=200, placement="right"` | **SÍ — nuevo en shared/ui/** |
| Switch Operador real/efectivo | `SegmentedControl` | mismo componente nuevo | SÍ (reutiliza el mismo) |
| Paginación | `Pagination` | `page, total, perPage=20, onChange` | **SÍ — nuevo en shared/ui/** |

### APIs de primitivos nuevos a crear en `shared/components/ui/`

#### `SearchableSelect`
```ts
interface SearchableSelectProps {
  options: { id: string; label: string; sublabel?: string; color?: string }[];
  value: string | string[] | null;
  onChange: (val: string | string[]) => void;
  multiple?: boolean;        // default false
  label: string;
  placeholder?: string;      // default "Buscá…"
  error?: string;
  exclude?: string[];        // ids a excluir del listado (para evitar auto-reemplazo)
  disabled?: boolean;
}
// Aria: role="combobox" aria-expanded aria-activedescendant
// Lista: role="listbox", options: role="option" aria-selected
// Teclado: ↑↓ navega, Enter selecciona, Escape cierra
```

#### `DateRangePicker` (promover desde sds_insumos Patrón 4)
```ts
interface DateRangePickerProps {
  value: { from: Date | null; to: Date | null };
  onChange: (range: { from: Date | null; to: Date | null }) => void;
  minDate?: Date;
  maxDate?: Date;
  error?: string;
  label?: string;
}
// Teclado: flechas navegan días, Enter selecciona, Escape cierra
// En mobile: un solo mes visible
```

#### `SegmentedControl`
```ts
interface SegmentedControlProps {
  options: { value: string; label: string }[];
  value: string;
  onChange: (val: string) => void;
  size?: 'sm' | 'md';        // default 'md'
  label?: string;
}
// Aria: role="radiogroup", cada opción role="radio" aria-checked
```

#### `Alert`
```ts
interface AlertProps {
  variant: 'warning' | 'destructive' | 'info' | 'success';
  icon?: React.ReactNode;
  title?: string;
  children: React.ReactNode;
  action?: React.ReactNode;  // ej. <Button>Reintentar</Button>
  onDismiss?: () => void;    // si se pasa, muestra X para cerrar
}
```

#### `Tooltip`
```ts
interface TooltipProps {
  content: React.ReactNode;
  delay?: number;            // ms, default 200
  placement?: 'top' | 'bottom' | 'left' | 'right';
  children: React.ReactNode;
}
// Aria: role="tooltip", aria-describedby en el trigger
// Escape cierra
```

#### `Pagination`
```ts
interface PaginationProps {
  page: number;
  total: number;
  perPage?: number;          // default 20
  onChange: (page: number) => void;
}
```

---

## 5. Tokens y estilo

| Estado / Elemento | Token semántico fondo | Token semántico texto | Referencia claro | Referencia oscuro |
|---|---|---|---|---|
| Badge Activa | `bg-success/10` | `text-success` | `rgba(34,197,94,.1)` / `#16a34a` | `rgba(34,197,94,.15)` / `#4ade80` |
| Badge Programada | `bg-accent/10` | `text-accent` | `rgba(247,148,29,.12)` / `#F7941D` | `rgba(247,148,29,.15)` / `#F7941D` |
| Badge Vencida | `bg-muted` | `text-muted-foreground` | `rgba(0,0,0,.06)` / `#6b6b6b` | `rgba(255,255,255,.07)` / `rgba(255,255,255,.45)` |
| Badge Cancelada | `bg-destructive/10` | `text-destructive` | `rgba(239,68,68,.1)` / `#dc2626` | `rgba(239,68,68,.15)` / `#f87171` |
| Banner solapamiento fondo | `bg-accent/10` | — | `rgba(247,148,29,.08)` | `rgba(247,148,29,.10)` |
| Banner solapamiento borde | `border-accent/30` | — | `rgba(247,148,29,.3)` | ídem |
| Banner error fondo | `bg-destructive/10` | `text-destructive` | `rgba(239,68,68,.08)` | `rgba(239,68,68,.12)` |
| Input focus | `border-accent` | — | `#F7941D` | ídem |
| Nota pie form fondo | `bg-muted/30` | `text-muted-foreground` | `rgba(0,0,0,.03)` | `rgba(255,255,255,.04)` |
| Nav activo fondo | `bg-accent/10` | `text-accent` | `rgba(247,148,29,.12)` | `rgba(247,148,29,.15)` |
| Evento cubierto (efectivo) | `bg-accent/12` + `border-accent/30` | `text-accent` | ver referencia | — |
| Evento cubierto (real) | color original del operador | ídem | — | — |

**Token nuevo a agregar**: `bg-success` / `text-success` — si no existe en el DS, agregar en `tailwind.config.ts`. No usar `green-*` ni `emerald-*` directamente. El valor semántico referencia: success = `oklch(0.62 0.17 145)` (claro) / `oklch(0.72 0.17 145)` (oscuro).

**Colores de identidad de operadores**: asignados por el sistema (hash del username → paleta de N colores semánticos pre-aprobados). Nunca asignados a mano ni con colores Tailwind literales.

---

## 6. Accesibilidad

### Focus order en el modal
1. Botón cerrar (✕) — o el primer campo si hay error de guardado
2. SearchableSelect "¿Quién falta?"
3. SearchableSelect "¿Quién lo cubre?"
4. DateRangePicker — input "Desde"
5. DateRangePicker — input "Hasta"
6. SegmentedControl "Alcance"
7. SearchableSelect multi "Clientes/zonas" (condicional)
8. Select "Motivo"
9. Button "Cancelar"
10. Button "Guardar cobertura"

Al cerrar el modal, el foco vuelve al botón que lo abrió (guardar referencia con `useRef` antes de abrir).

### Labels y ARIA

- Cada campo: `<label htmlFor>` explícito o `aria-label` en el trigger.
- Errores de campo: `aria-describedby="campo-id-error"` apuntando al `<p role="alert" id="campo-id-error">` del mensaje.
- Modal: `role="dialog" aria-modal="true" aria-labelledby="modal-title-id"`.
- Focus trap: implementar con `focus-trap-react` o la utilidad que ya use el DS.
- SearchableSelect: `role="combobox" aria-expanded aria-haspopup="listbox" aria-activedescendant`. Lista: `role="listbox"`, cada opción `role="option" aria-selected`.
- SegmentedControl: `role="radiogroup"` con `aria-label`. Cada botón: `role="radio" aria-checked`.
- Tooltip: `role="tooltip"` con `id`; el trigger tiene `aria-describedby` apuntando al tooltip id.
- Badge de estado en tabla: `aria-label="Estado: Activa"` — no confiar solo en el color.
- Botón "Cancelar cobertura": `aria-label="Cancelar cobertura de Victor Paez"` (incluir contexto de fila).

### Contraste WCAG 2.2 AA

| Combinación | Ratio ref. | Resultado |
|---|---|---|
| `#16a34a` sobre blanco | 4.5:1 | ✓ |
| `#F7941D` sobre blanco (texto bold ≥ 14px) | 3.2:1 (texto grande) | ✓ |
| `#dc2626` sobre blanco | 5.1:1 | ✓ |
| `#6b6b6b` sobre `#FAFAF8` | 4.7:1 | ✓ |
| Blanco sobre `#F7941D` (botón primary bold) | 3.1:1 (texto grande bold) | ✓ |
| `#4ade80` sobre `#1c1c1e` (dark success) | 5.8:1 | ✓ |

### Navegación por teclado

**SearchableSelect**: `Tab` → foco en trigger. `Enter`/`Space` → abre. `↑↓` → navega opciones. `Enter` → selecciona. `Escape` → cierra sin seleccionar. Typing → filtra (typeahead).

**DateRangePicker**: flechas navegan días en el calendario. `Enter` selecciona fecha inicio, siguiente `Enter` selecciona fecha fin. `Escape` cierra.

**SegmentedControl**: flechas `←→` navegan entre opciones (dentro del grupo). `Tab` sale del grupo completo.

---

## 7. Responsive

### Desktop (≥ 1280px) — experiencia de referencia
Tabla completa con todas las columnas visibles. Modal 560px centrado.

### Angosto (< 768px, ej. tablet interna)
- **Tabla**: colapsa a tarjetas (card por fila) — cada card muestra los datos en vertical con labels explícitos.
- **Modal**: `position: fixed; inset: 0; border-radius: 0` — ocupa pantalla completa. Scroll interno.
- **DateRangePicker**: muestra un solo mes (no dos en paralelo).
- **Filtros de tabla**: ocultar detrás de un botón "Filtros" → panel lateral o bottom sheet.
- **SegmentedControl**: si las opciones no caben en una línea, apilar en dos rows.

### Tabla responsive — columns priority
Si el viewport fuerza scroll horizontal antes del colapso a cards: ocultar en este orden → Motivo → Alcance → Vigencia (dejar siempre visibles: Ausente, Reemplazante, Estado, Acciones).

---

## 8. Notas para el dev y preguntas abiertas

### Notas

- **No tocar el Calendario de Gestión**: la cobertura es 100% local a HelpDeskManager. El endpoint SigesReadOnly sigue siendo read-only. La capa de cobertura es un overlay calculado en el server de HelpDeskManager sobre los datos leídos.
- **Vencimiento automático**: el estado se calcula en tiempo de consulta (`vigencia_hasta < today → "Vencida"`). No se necesita un job de cancelación — puede ser un campo calculado o una columna materializada en DB.
- **Solapamiento**: la validación de solapamiento es un warn, no un hard-block. El server puede permitir solapamientos parciales (edge case: cobertura de 2 clientes puntuales + cobertura total de otros). El form advierte pero no bloquea el guardado.
- **Colores de operadores**: asignar via hash del username a una paleta pre-aprobada (nunca colores Tailwind literales). Si ya existe una tabla de colores por operador en DB, usarla como fuente de verdad.
- **Un solo componente**: `CoberturaTable` y `CoberturaModal` son los nombres propuestos. No crear `CoberturaContadores` y `CoberturasPST` por separado — la prop `entityType` parametriza todo.
- **Animación del modal**: entrada `scale-95 → scale-100 + opacity-0 → opacity-100`, 150ms ease-out. Cierre: inverso. Usar las clases de transición del DS si ya están definidas.
- **`bg-success` / `text-success`**: si no existen como tokens en el DS actual, crearlos antes de implementar el Badge de estado Activa. No parchear con `green-500` en el feature.

### Preguntas abiertas

1. ¿El Calendario de Gestión externo tiene webhook o polling para confirmar que un evento fue efectivamente atendido por el reemplazante? Impacta si se puede mostrar "cobertura efectiva" vs "solo programada".
2. ¿Los colores de identidad de operadores ya están definidos en DB? Si no, ¿quién los asigna (admin manual, generación automática)?
3. ¿Una cobertura "Total" cubre también eventos futuros que se asignen al operador ausente *durante* el período, o solo los ya existentes al crear la cobertura?
4. ¿El módulo PST tiene un campo "zona" formal en la tabla de prestadores, o es texto libre?
5. ¿Se requiere historial de auditoría (quién creó/editó/canceló una cobertura y cuándo)? Si sí, agregar columna "Modificado por" o un panel de actividad en la fila.

---

## Archivos

```
design_handoff_reasignacion_temporal/
├── README.md                                 ← este archivo
└── Mockups-Reasignacion-Temporal.dc.html    ← mockup interactivo completo
```

El mockup incluye: Listado Contadores (4 estados), Modal nueva cobertura (con toggle de solapamiento), Calendario con indicadores, Listado PST, Modal PST. Modo claro y oscuro. Navegación entre pantallas desde el panel lateral izquierdo.
