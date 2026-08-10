# Handoff: Portal Mesa de Ayuda — Canal Directo

## Overview
Hub interno para el personal de soporte de Canal Directo que integra varias herramientas de mesa de ayuda: Contadores (con 8 sub-herramientas: SDS, ERS, FTP, DB3, Estimación en 0, Suma Fija, Proyección Contadores, Calculadora) e Insumos. Incluye un modal de ejemplo ("Descargar SDS") con selector de cliente y fecha.

## About the Design Files
El archivo `Portal Mesa de Ayuda.dc.html` es una **referencia de diseño** construida en HTML/CSS/JS plano (no es código de producción). La tarea es **recrear este diseño dentro de HelpDeskManager-Web**, usando el stack, componentes y convenciones ya existentes en ese proyecto (routing, estado, llamadas a API reales de descarga de contadores, etc.) — no copiar el HTML tal cual.

## Fidelity
**Alta fidelidad (hifi)**: colores, tipografía, espaciados e interacciones (navegación Inicio/Contadores, submenú expandible, modal) están definidos y deben respetarse pixel a pixel donde sea posible dentro del stack real.

## Screens / Views
### 1. Inicio (dashboard)
- **Layout**: header fijo (64px) + sidebar fijo (224px) + panel principal con scroll interno.
- **Header**: logo Canal Directo naranja (`assets/logo-naranja.png`, 34px alto), separador vertical, label "MESA DE AYUDA" (Montserrat 700 13px, `#58595B`, letter-spacing .06em), buscador central (borde `rgba(0,0,0,.12)`, radio 8px), ícono de notificación (círculo con punto magenta), avatar circular gris con iniciales + nombre/rol.
- **Sidebar**: nav "Inicio" (activo por defecto, fondo `rgba(247,148,29,.12)`, texto `#F7941D`), nav "Contadores" (expandible, ver Interacciones), nav "Insumos". Footer del sidebar: "Portal interno · Canal Directo" (11px, `#b5b5b5`).
- **Panel principal — vista Inicio**: saludo + CTA "+ Nuevo ticket" (naranja, radio 8px); grid de 2 tiles KPI (Contadores naranja, Insumos gris oscuro `#3A3A3C`) — cada tile: badge de ícono 38×38px radio 9px, título Montserrat 700 14px, número Montserrat 800 26px en el color del tile, subtítulo gris, link "Ver todos →"; abajo, grid 1.7fr/1fr con tabla "Contadores recientes" (columnas N°/Asunto/Sucursal/Prioridad/Estado, badges de estado con color por prioridad) y widget lateral "Insumos" (lista de 3 ítems con estado).

### 2. Contadores (vista, al click en el nav)
- Header de sección: "Centro de Contadores" (Montserrat 800 25px) + subtítulo gris.
- Grid de 3 columnas con 8 cards (una por herramienta: Descargar SDS, Descargar ERS, Descarga FTP, Procesar DB3, Estimación en 0, Suma Fija, Proyección Contadores, Calculadora). Cada card: ícono en badge de color de servicio, título Montserrat 700 14.5px, descripción 13px gris, link "INICIAR PROCESO →" en el color del servicio.
- La card "Descargar SDS" dispara el modal (ver Interacciones).

### 3. Modal "Descargar SDS"
- Overlay `rgba(20,20,20,.55)` fixed inset:0, z-index 50.
- Card blanca 420px, radio 16px: título "DESCARGAR SDS" (Montserrat 800 20px) + botón cerrar (✕); campo "Seleccionar cliente SDS" con link "Gestionar clientes" (naranja) + input tipo selector con botón "+"; campo "Fecha máxima de proceso" con `<input type="date">`; botón primario naranja "⭳ Descargar Contadores" full-width, radio 10px.

## Interactions & Behavior
- Click en "Inicio" / "Contadores" en el sidebar cambia la vista del panel principal (estado `view: 'inicio' | 'contadores'` en el componente).
- El nav activo se resalta con fondo `rgba(247,148,29,.12)` y texto/dot `#F7941D`; inactivo `#4b4b4b` / dot `#d8d8d8`.
- "Contadores" en el sidebar muestra siempre su submenú de 8 links cuando la vista activa es "Contadores" (implementado como visible condicional, no acordeón colapsable — se puede convertir a acordeón real si se prefiere).
- Click en "Descargar SDS" (desde el submenú o desde la card) abre el modal; click en el backdrop o en la "✕" lo cierra. No se implementó cierre con tecla Esc — agregarlo en producción.
- El modal es solo de configuración simple (cliente + fecha) → ejecutar. Los demás ítems del submenú de Contadores son placeholders visuales (sin acción real todavía).

## State Management
- `view`: 'inicio' | 'contadores' — controla qué panel principal se muestra.
- `sdsOpen`: boolean — controla la visibilidad del modal de Descargar SDS.
- En producción: cada herramienta de Contadores necesitará su propio estado de formulario (cliente seleccionado, fecha, estado de descarga/loading/error) y llamada a la API real correspondiente (HP SDS, Epson ERS, FTP del cliente, etc.).

## Design Tokens
**Colores (manual de marca "Canal Directo")**
- Naranja institucional: `#F7941D`
- Gris MPS: `#58595B`
- Magenta Digitalización: `#E32D91` (usado solo para el punto de notificación y algún acento puntual)
- Charcoal (variante propia para Insumos, no oficial de marca): `#3A3A3C`
- Texto principal: `#232323` · Texto secundario: `#8a8a8a` / `#9a9a9a` / `#6b6b6b`
- Fondo de página: `#FAFAF8` · Superficies: `#ffffff`
- Bordes sutiles: `rgba(0,0,0,.06)` a `rgba(0,0,0,.12)`
- **Excluidos a propósito** (no usar): violeta `#662D91` (línea DaaS) y celeste `#3DB1CA` (línea Cartelería Digital) — el pedido del cliente fue no usar esas dos líneas de negocio.

**Tipografía**
- Títulos: Montserrat (600/700/800)
- Cuerpo: Source Sans Pro (400/600/700)
- Google Fonts: `Montserrat:wght@600;700;800` y `Source+Sans+Pro:wght@400;600;700`

**Radios / espaciados**
- Cards: radio 12px · Botones/inputs: radio 8–10px · Badges de estado: radio 20px (pill)
- Gap estándar entre elementos: 10–20px · Padding de cards: 20–22px

## Assets
Todos extraídos del manual de marca del cliente (`uploads/Manual de marca.pdf`) y ubicados en `assets/`:
- `logo-naranja.png` — logo institucional, usar en superficies claras (header actual).
- `logo-blanco.png` — variante blanca, para usar sobre superficies oscuras si se agregan.
- `logo-gris.png` — variante gris (no usada en la versión actual, disponible como alternativa neutra).
- `icon-truck.png`, `icon-invoice.png`, `icon-printer.png`, `icon-folder-docs.png`, `icon-mail.png`, `icon-clock.png`, `icon-chart.png` — íconos de línea blanca (transparentes), pensados para ir sobre fondos de color; en el HTML se les aplica `filter` para recolorear cuando van sobre fondo claro.
- Los logos de partners (Dell, HP, Lenovo, LG, Samsung) del manual de marca **no se usaron** en este diseño; si se necesitan para una sección de partners, están disponibles en el proyecto de diseño original (`pdfpages/`).

## Files
- `Portal Mesa de Ayuda.dc.html` — archivo único con todo el HTML/CSS inline + la lógica de estado (vista activa, modal) en un bloque de script al final. Es la referencia completa del diseño descripta en este README.
- `assets/` — todos los PNG referenciados arriba.
