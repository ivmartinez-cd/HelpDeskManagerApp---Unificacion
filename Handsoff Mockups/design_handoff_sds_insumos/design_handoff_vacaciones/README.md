# Handoff: Módulo Gestión de Vacaciones y Asistencias — Canal Directo

## Overview
Módulo que reemplaza a **VacaSync** (app legacy) dentro de la Plataforma Unificada de Operaciones (HelpDeskManager). Cubre tres áreas que conviven bajo un mismo sidebar: **Vacaciones** (dashboard, solicitudes, aprobaciones, reportes, auditoría, configuración), **Asistencias** (calendario anual de bajas, listado, reportes de descuentos) y **Gestión Humana** (ABM de empleados, sectores, cargos, feriados, usuarios y roles).

Usa exactamente el mismo design system que `design_handoff_mesa_de_ayuda/` — no se reespecifica paleta ni tipografía salvo excepciones documentadas en este handoff.

## About the Design Files
Los archivos `.dc.html` son **referencias de diseño de alta fidelidad** (HTML/CSS/JS plano, interactividad mínima: tabs, filtros, modales, toggle de estado). No son código de producción. La tarea es recrear estos diseños dentro del stack Next.js 15 + React + TypeScript + Tailwind, usando los componentes y convenciones ya existentes en el proyecto (routing con App Router, estado con React, llamadas a la API real, etc.).

## Fidelity
**Alta fidelidad (hifi)**: colores, tipografía, espaciados, jerarquías, estados vacío/carga/error y flujos de interacción (modales, tabs, filtros, validaciones) están definidos pixel a pixel. Los datos de ejemplo son ficticios pero representativos del dominio real (empleados argentinos, sectores tipo "Soporte Técnico", "Logística", "Administración").

## Screens / Views

### 1. Dashboard — `01-Dashboard-Vacaciones.dc.html`
- **Layout**: header (64px) + sidebar (224px) + panel principal con scroll.
- **KPI row**: 4 cards en grid 4 cols, gap 16px, radio 12px, padding 20px. Cada card: badge ícono 40×40 radio 10px con fondo tintado, número Montserrat 800 28px en el color del KPI, subtítulo 12px gris. KPIs: Total empleados (naranja), De vacaciones hoy (azul `#2563eb`), Solicitudes pendientes (ámbar `#d97706`), Días disponibles (verde `#059669`).
- **Grid 2fr/1fr**: calendario mensual (izq) + panel "De vacaciones ahora" (der).
- **Calendario**: toolbar ‹ Hoy › + label mes centrado + toggle Mes/Semana/Año; grilla 7 cols; weekends con fondo `rgba(0,0,0,.02)`; día actual (13 ago) con círculo `#F7941D` y número blanco; eventos de vacaciones como mini-chips coloreados por sector dentro de cada celda.
- **Panel lateral**: lista de empleados ausentes hoy con avatar cuadrado (color sector), nombre, rango de fechas y chip de sector; empty state con ícono gris + "Nadie está de vacaciones hoy".

### 2. Mis Solicitudes + Modal — `02-Solicitudes.dc.html`
- **Layout**: title row ("MIS SOLICITUDES" Montserrat 800 25px) + botón primario "+ Nueva solicitud"; buscador + chips de filtro (Todas / Pendiente / Aprobada / Rechazada).
- **Tabla**: columnas Empleado / Rango / Días hábiles / Año de cargo / Estado / Motivo / Acciones. Badges de estado: Pendiente `rgba(217,119,6,.12)` + `#d97706`; Aprobada `rgba(5,150,105,.12)` + `#059669`; Rechazada `rgba(220,38,38,.1)` + `#dc2626`. Pill radio 20px.
- **Empty state**: ícono gris + "No hay solicitudes todavía" + subtítulo + botón primario.
- **Modal "Nueva solicitud"**: card 490px, radio 16px, overlay `rgba(20,20,20,.55)`. Campos: select Empleado, Fecha inicio / Fecha fin (lado a lado), select Ciclo de cargo (default "Automático — año de inicio"), textarea Motivo (opcional). Footer: Cancelar (outline) + "Crear solicitud" (naranja). Variantes de validación (accesibles via tab en el mockup): saldo insuficiente (banner rojo + días disponibles resaltados), solapamiento (banner ámbar + fechas en conflicto), aviso previo insuficiente (banner ámbar + días de aviso requerido).

### 3. Aprobaciones — `03-Aprobaciones.dc.html`
- **Sección "Pendientes"**: header con título + dropdown "Sólo pendientes / Todas". Cards expandibles (chevron ▶): datos del empleado (avatar + nombre + sector), rango solicitado, días, saldo disponible del ciclo, campo de comentario (textarea), botones Aprobar (verde) + Rechazar (rojo) + Cancelar (outline). Al aprobar/rechazar, la card cambia de estado visualmente.
- **Sección "Historial"**: tabla compacta con columnas Empleado / Fecha solicitud / Días / Decisión / Decisor / Comentario; badge de decisión Aprobada/Rechazada.

### 4. Reportes + Auditoría — `04-Reportes-Auditoria.dc.html`
- **Tab bar**: Reportes | Auditoría (tab activo con fondo naranja pill).
- **Reportes**: botones "Excel" (outline) + "PDF" (outline) arriba a la derecha; card de gráfico con título "Días consumidos vs. disponibles por sector" — barras verticales CSS agrupadas por sector (dos colores: naranja = consumidos, gris claro = disponibles), leyenda abajo; dos cards debajo en grid 1/1: tabla "Por empleado" (Empleado / Cons. / Pend. / Disp. — con input de filtro) + tabla "Por sector" (Sector / Empleados / Anuales / Cons. / Disp.).
- **Auditoría**: buscador full-width; tabla con filas expandibles: Fecha / Acción (badge pill) / Entidad / Descripción / Usuario / chevron; fila expandida muestra detalle completo; pie "Mostrando N de N registros".

### 5. Configuración — `05-Configuracion.dc.html`
- **Header**: "CONFIGURACIÓN" + botón "Guardar cambios" (naranja), alineado a la derecha.
- **4 tabs con ícono**:
  - **Antigüedad y Días**: tabla editable de rangos (Desde / Hasta en años / Días de vacaciones); cada fila tiene botón eliminar; botón "+ Agregar rango" al pie.
  - **Reglas de Solicitud**: dos cards — "Aviso Previo Mínimo" (input numérico + "días hábiles") y "Límite de Solapamiento" (slider % máximo del equipo + input "cantidad fija máxima" con nota "0 = usar porcentaje").
  - **Ciclos Anuales**: dos inputs (día y mes de apertura del próximo ciclo) + toggle "Arrastrar días no usados al ciclo siguiente".
  - **Solapamientos**: dos cards — "Exclusiones Mutuas" (par de selects Empleado A / Empleado B + botón "+ Agregar exclusión" + lista de exclusiones con eliminar) y "Límites por Cargo" (select cargo + input límite máx simultáneo + botón "+ Agregar" + lista).

### 6. Asistencias — `06-Asistencias.dc.html`
- **Sub-nav** (tabs internos): Calendario | Listado y registros | Reportes descuentos.
- **Calendario (tab activo)**: fila de 6 KPI mini-cards (Días de baja / Días trabajados / Días enfermedad / De vacaciones / Trámites y estudio / Descuento día); filtros select Empleado + select Año; grilla anual (12 filas = meses, 31 cols = días) con celdas coloreadas por tipo de baja (paleta semántica, ver tokens); panel lateral "Resumen de bajas {año}" con totales por tipo. Modal "Nueva baja" desde botón "+ Registrar baja".
- **Modal "Nueva baja"**: buscador de empleado (autocompletar, multi), Fecha inicio / Fecha fin, select Tipo de baja (7 opciones), checkbox "Medio día", textarea Observaciones, botón "Registrar".
- **Listado**: tabla de todas las bajas con columnas Empleado / Fecha / Tipo / Duración / Observaciones / Acciones (editar/eliminar); filtros arriba.
- **Reportes descuentos**: tabla descuentos por técnico + botón exportar.

### 7. Gestión Humana — `07-Gestion-Humana.dc.html`
- **5 tabs**: Empleados | Sectores | Cargos | Feriados | Usuarios y roles.
- **Empleados**: buscador + filtro sector + botón "+ Nuevo empleado"; tabla: avatar / nombre / email / sector (chip coloreado) / cargo / ingreso y antigüedad / días anuales / estado (Activo/Inactivo); modal de alta/edición.
- **Sectores**: ABM — nombre del sector + selector de color (6 swatches semánticos predefinidos) + empleados asignados; acciones editar/eliminar.
- **Cargos**: lista simple de cargos con nombre + cantidad de empleados + acciones editar/eliminar; botón "+ Nuevo cargo".
- **Feriados**: card destacada "Importar feriados de Argentina" (input año + botón "Importar 2026" naranja, fuente api.argentinadatos.com); botones "Exportar backup" + "+ Nuevo feriado"; tabla del año con Fecha / Nombre / Tipo (Nacional / Provincial) / acciones.
- **Usuarios y roles**: tabla: usuario / nombre / email / rol (Admin/Manager/Empleado chip) / empleado vinculado / sector gestionado (managers) / último acceso; acciones: editar rol / reset contraseña.

## Interactions & Behavior
- **Dashboard**: prev/next cambia label del mes (sin recalcular datos, es referencia); toggle Mes/Semana/Año cambia estado visual del botón.
- **Solicitudes**: chips de filtro filtran la tabla por estado; botón "+ Nueva solicitud" abre el modal; tabs dentro del modal (Normal / Saldo insuf. / Solapamiento / Aviso previo) muestran los distintos estados de validación.
- **Aprobaciones**: click en fila expande el área de acción; Aprobar/Rechazar cambia el badge de la card visualmente; dropdown filtra entre pendientes y todas.
- **Reportes/Auditoría**: tab bar alterna entre las dos vistas; fila de auditoría expande/colapsa con chevron.
- **Configuración**: tab bar alterna las 4 secciones; slider actualiza el porcentaje en tiempo real; "+ Agregar rango" añade una fila; eliminar la quita del array.
- **Asistencias**: sub-tabs alternan entre Calendario / Listado / Reportes; modal "Nueva baja" abre/cierra con botón/backdrop/Escape; checkbox "Medio día" habilita/deshabilita campo de cantidad.
- **Gestión Humana**: tabs alternan las 5 secciones; modal de empleado abre/cierra; botón "Importar 2026" simula estado de carga visual (spinner en botón).

## State Management
| Archivo | Variables de estado clave |
|---|---|
| 01-Dashboard | `monthOffset: 0`, `calView: 'mes'` |
| 02-Solicitudes | `filter: 'todas'`, `modalOpen: false`, `modalTab: 'normal'` |
| 03-Aprobaciones | `expanded: null`, `showAll: false`, `approved: Set`, `rejected: Set` |
| 04-Reportes-Auditoria | `activeTab: 'reportes'`, `expandedAudit: null`, `empFilter: ''` |
| 05-Configuracion | `activeTab: 'antiguedad'`, `ranges: Array`, `sliderVal: 35`, `arrastre: true` |
| 06-Asistencias | `activeView: 'calendario'`, `selectedEmp: 'laura'`, `selectedYear: 2026`, `modalOpen: false` |
| 07-Gestion-Humana | `activeTab: 'empleados'`, `empModalOpen: false`, `importState: 'idle'` |

## Design Tokens

### Colores (manual de marca "Canal Directo" — línea Institucional)
| Token | Valor | Uso |
|---|---|---|
| Naranja institucional | `#F7941D` | Acciones primarias, nav activo, énfasis |
| Gris MPS | `#58595B` | Label de módulo en header |
| Texto principal | `#232323` | Títulos de página, contenido principal |
| Texto secundario | `#6b6b6b` / `#8a8a8a` | Labels, subtítulos, metadatos |
| Fondo página | `#FAFAF8` | Background del panel principal |
| Superficie card | `#ffffff` | Cards, modales, sidebar |
| Borde sutil | `rgba(0,0,0,.06)` | Bordes de cards y separadores |
| Borde input | `rgba(0,0,0,.12)` | Bordes de inputs y dividers más fuertes |
| Nav activo fondo | `rgba(247,148,29,.12)` | Fondo del item de nav activo |
| **Prohibido** | `#662D91` `#3DB1CA` `#E32D91` | No usar ni como acento — otras líneas de negocio |

### Colores semánticos (estados UI, no de marca)
| Estado | Fondo badge | Color texto |
|---|---|---|
| Pendiente | `rgba(217,119,6,.12)` | `#d97706` |
| Aprobada / Activo | `rgba(5,150,105,.12)` | `#059669` |
| Rechazada / Error | `rgba(220,38,38,.1)` | `#dc2626` |
| Info / Warning | `rgba(37,99,235,.1)` | `#2563eb` |

### Colores de sectores (paleta interna — no marca)
| Sector | Color identidad |
|---|---|
| Soporte Técnico | `#2563eb` |
| Logística | `#059669` |
| Administración | `#d97706` |
| RRHH | `#475569` |

### Colores de tipos de baja (Asistencias)
| Tipo | Color |
|---|---|
| Baja por enfermedad | `#f59e0b` |
| Trámites personales | `#2563eb` |
| Home office | `#9ca3af` |
| Vacaciones | `#F7941D` |
| Descuento día | `#ef4444` |
| Guardia | `#475569` |
| Examen / estudio | `#059669` |

### Tipografía
- Títulos de página: Montserrat 800, 25px, `#232323`, `letter-spacing: -.02em`
- Subtítulos de sección: Montserrat 700, 14px
- Labels de nav (módulo header): Montserrat 700, 11.5px, `#58595B`, `letter-spacing: .07em`, uppercase
- Cuerpo: Source Sans 3 (= Source Sans Pro), 400/600/700, 13–14px
- Badges de estado: Source Sans 3 700, 11.5–12px, pill radio 20px

### Radios / espaciados
- Cards: `border-radius: 12px`, padding `20–22px`
- Botones y inputs: `border-radius: 8–10px`
- Badges pill: `border-radius: 20px`
- Gap estándar entre cards: `16px`
- Gap entre elementos inline: `8–10px`
- Padding panel principal: `28px 32px`

## Assets
- Fuentes: Google Fonts — `Montserrat:wght@600;700;800` + `Source+Sans+3:wght@400;600;700`
- No se generaron imágenes nuevas. El logo de Canal Directo ya vive en el frontend del monorepo (`frontend/public/logo.svg`, variante blanca en `logo-white.svg`); en los mockups se usa un placeholder tipográfico para no crear dependencias de path.
- Para íconos de nav, los mockups usan dots (●) simples. En producción usar la librería de íconos del proyecto (Lucide, Heroicons, etc.).

## Files
| Archivo | Área | Pantallas cubiertas |
|---|---|---|
| `01-Dashboard-Vacaciones.dc.html` | Vacaciones | Dashboard + calendario + panel de ausentes |
| `02-Solicitudes.dc.html` | Vacaciones | Mis solicitudes + Modal nueva solicitud (4 estados de validación) |
| `03-Aprobaciones.dc.html` | Vacaciones | Aprobaciones + Historial |
| `04-Reportes-Auditoria.dc.html` | Vacaciones | Reportes (gráfico + 2 tablas) + Auditoría (tabla expandible) |
| `05-Configuracion.dc.html` | Vacaciones | Configuración admin (4 tabs) |
| `06-Asistencias.dc.html` | Asistencias | Calendario anual de bajas + Listado + Reportes descuentos + Modal nueva baja |
| `07-Gestion-Humana.dc.html` | Gestión Humana | Empleados + Sectores + Cargos + Feriados + Usuarios y roles |
| `README.md` | — | Este documento |
