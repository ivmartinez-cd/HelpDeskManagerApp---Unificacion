# Handoff: Insumos / Despachados — seguimiento de envíos OCA

## Contexto
Pantalla `/insumos/despachados` de HelpDesk Manager: estado en vivo de los remitos de insumos
despachados por OCA. Reemplaza el seguimiento manual guía por guía en la web de OCA.
Mockup aprobado: `despachados.html` (HTML estático autocontenido, datos ficticios y lógica
simulada en JS; **no** es código de producción).

Usa el mismo sistema de diseño que el resto de HDM (`frontend/src/app/globals.css`) y el de
`design_handoff_sds_insumos/`. Solo se especifica acá lo propio de esta pantalla.

Implementación (fase 6): `frontend/src/features/insumos/components/despachados/`,
API en `frontend/src/features/insumos/api/despachados-api.ts`, tipos en
`frontend/src/features/insumos/types/despachados.ts`, ruta
`frontend/src/app/(app)/insumos/despachados/page.tsx`. Backend (fase 5):
`backend/src/modules/insumos/presentation/despachados_*.py`.

## Tokens
| Token | Valor |
|---|---|
| Naranja de marca | `#F7941D` (hover `#D97E0F`; texto naranja sobre fondo claro `#B45F06`) |
| Gris de marca | `#58595B` |
| Radio tarjeta / panel / tabla | `12px` |
| Radio botón | `10px` (chico `8px`) · input/select `8px` · modal `16px` |
| Título de página | Montserrat 800 25px |
| Título de sección | Montserrat 700 16px |
| Cuerpo | Source Sans 3 400/600/700, 13–14px |
| Labels / encabezados de tabla | Source Sans 700 11px, mayúsculas, tracking `.025–.05em` |
| Sombra modal | `0 20px 60px rgba(0,0,0,.25)` |
| Sombra panel lateral | `-12px 0 40px rgba(0,0,0,.14)` (oscuro `.5`) |
| Overlay modal / panel | `rgba(20,20,20,.55)` / `rgba(20,20,20,.35)` |

### Paleta del semáforo (colores de estado, no de marca)
Texto con contraste ≥ 4,5:1 sobre `card` en los dos temas; los fondos de chip salen del mismo
color al 14 %, el recuadro de alerta al 8 % con borde al 35 %.

| Color | Claro | Oscuro | Chip | Ícono (lucide) |
|---|---|---|---|---|
| verde | `#047857` | `#34D399` | En tránsito | `Truck` |
| amarillo | `#A16207` | `#FACC15` | Sin movimiento / Estado desconocido / Sin datos | `Clock` |
| naranja | `#C2410C` | `#FB923C` | Visita fallida | `TriangleAlert` |
| rojo | `#B91C1C` | `#F87171` | En sucursal | `MapPin` |
| gris | `#52525B` | `#A1A1AA` | Devuelto / Cancelado | `Undo2` |
| cerrado | `#1D4ED8` | `#93C5FD` | Entregado | `Check` |

El color nunca va solo: chip = ícono + texto + color. Resultado de una acción: Resuelto (verde),
Pendiente (amarillo), Sin respuesta (gris).

## Pantalla

1. **Cabecera**: migas "Insumos / Despachados", título, subtítulo "Estado en vivo de los envíos
   por OCA." A la derecha, "Última consulta a OCA: HH:MM" (hora de fin de la última corrida
   terminada) y botón primario "Actualizar ahora".
2. **Tarjetas-filtro** (5, grid de 5 → 3 → 2 columnas): Visita fallida · En sucursal · En
   tránsito (verde + amarillo) · Devueltos (30 días) · Entregados (30 días). Cada una: label con
   ícono, número Montserrat 800 26px en el color del semáforo, pista de 12px ("N sin acción
   registrada", "La más próxima vence mañana (25/09)", "N sin movimiento (amarillo)", "Últimos 30
   días") y marca "Filtrando" cuando está presionada.
3. ~~Bandeja "Requieren acción"~~: **sacada por decisión del usuario (2026-09-24)**. Las
   alertas se ven con las tarjetas "Visita fallida" / "En sucursal" (que filtran la tabla) y los
   contadores del menú; "Registrar acción" se abre desde el panel lateral.
4. **Tabla "Todos los despachos"**: filtros (Buscar, Operativa, Fecha de remito, "Limpiar
   filtros"; el color se filtra solo con las tarjetas, sin selector propio — decisión del
   usuario, 2026-09-24), columnas Color, Guía, Remito (+ fecha), Cliente, Incidente, Estado OCA, Sucursal,
   Fecha estado, Límite / aviso; paginación 25/50/100.
5. **Panel lateral** (`min(480px, 100vw)`): chip, "Guía N" con botón copiar, cliente · incidente;
   secciones Estado OCA actual (con recuadro de alerta), Remito(s), Cliente e incidente, Cambios
   de estado observados (timeline, el primero con marca "Actual"), Acciones registradas (+ botón
   "Registrar acción"); pie "Ver en OCA" y la guía seleccionable.
6. **Modal "Registrar acción"** (520px): tipo como tarjetas de opción (Llamado al cliente, Mail al
   cliente, Reclamo a OCA, Otro), Detalle obligatorio, Resultado (segmentado, default Pendiente),
   "Cerrar la alerta al guardar esta acción" (solo si hay alerta abierta), recuadro "Registra
   <usuario>", Cancelar / Guardar acción.
7. **Menú**: item "Despachados" (`Truck`) en Insumos › Principal, después de Historial, con pills
   de alertas rojas y naranjas abiertas.

## Interacciones
- Tocar una tarjeta filtra la tabla por su color y la desplaza a la vista (sin animación con
  `prefers-reduced-motion`); tocarla de nuevo saca el filtro. Tarjetas y `<select>` de color
  comparten el mismo estado; el subtítulo de la tabla avisa "Filtrado por la tarjeta …".
- Búsqueda con debounce (350 ms); todos los filtros y la paginación se resuelven en el backend.
  Cambiar un filtro vuelve a la página 1.
- Filas clickeables y enfocables (Tab, Enter/Espacio abren el panel); la fila abierta queda
  resaltada.
- Panel: Escape o click en el fondo cierran; foco inicial en "Cerrar panel", Tab atrapado
  adentro, al cerrar el foco vuelve a la fila. "Cerrar alerta" queda deshabilitado (con la
  explicación) hasta que haya al menos una acción.
- "Actualizar ahora": POST → 202, el botón pasa a "Actualizando…" y se pollea
  `/despachados/actualizacion` cada 3 s; al terminar se refresca todo y aparece un toast con el
  resultado. 409 (ya hay una corrida) → toast informativo y se sigue esa corrida.
- Registrar acción / cerrar alerta: toast de confirmación y refresco de tarjetas, tabla y
  panel. Los errores del backend se muestran en el banner del modal.
- Botones de escritura (Actualizar ahora, Registrar acción, Cerrar alerta) solo con
  `insumos:update` (o superadmin); la ruta la cubre `insumos:view`.

## Decisiones y desvíos respecto del mockup
- **Azul "cerrado" (`#1D4ED8` / `#93C5FD`) — confirmado por el usuario (2026-09-24).** Es un
  color de estado, no de marca, y no es ninguna de las líneas excluidas (violeta, celeste,
  magenta). Se usa solo en el semáforo para "Entregado/cerrado".
- **"Ver en OCA" abre el seguimiento de la guía** en
  `https://oca.com.ar/Seguimiento/Paquetes/<guía>` (decisión del usuario, 2026-09-24; el mockup
  tenía un link genérico a la home de OCA).
- **La pantalla lee de HDM y nunca espera a OCA**: todo sale de lo que el job de fondo ya guardó.
  "Actualizar ahora" no bloquea: lanza la corrida en el backend y la pantalla la sigue por
  polling.
- **Los días hábiles los calcula el backend** (con feriados): la pantalla solo formatea
  `diasHabilesParaLimite` ("vence hoy", "vence mañana", "quedan N días hábiles", "vencido el …").
  El mockup los calculaba en JS sin feriados.
- El texto "sin movimiento hace N días hábiles" y "Estado nuevo, revisar" / "Sin datos en OCA"
  salen de la `observacion` del backend, no se recalculan en la pantalla.
- Fecha de remito: se usa el selector de rango compartido (`DateRangePickerPopover`) en vez de dos
  `<input type="date">`.
- Remito e incidente: el backend manda el número de remito (entero, sin el prefijo `0003-` del
  mockup) y la cantidad; si una guía agrupa varios se muestra "+N".
- Pills del menú: se usan los tonos existentes del submenú (rojo `#EF4444`, naranja de marca) en
  vez de `#DC2626` / `#C2410C` del mockup, por consistencia con Solicitudes y Equipos offline. Se
  refrescan cada 60 s (fetch propio, aislado de los otros contadores).
- "(30 días)" en las tarjetas de Devueltos/Entregados es copy fijo; la ventana real es
  configurable en el backend (`DESPACHADOS_DIAS_VENTANA`).
- Modal: el foco inicial queda en la X (mecánica de `BrandModal`), no en el primer tipo como en el
  mockup. El recuadro automático muestra el usuario; la fecha/hora la pone el backend al guardar.
- Primitivas nuevas en `shared/components/ui/`: `BrandDrawer` (`brand-drawer.tsx`) y
  `BrandTextarea` (en `brand-form.tsx`).
