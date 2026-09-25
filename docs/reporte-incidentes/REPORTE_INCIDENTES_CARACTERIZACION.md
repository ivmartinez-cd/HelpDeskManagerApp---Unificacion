# Reporte de Incidentes — caracterización y plan de migración

Legacy: `~/proyectos/canal/reporte-incidentes` (Next.js 15 + TS, sin DB). Hay una copia
hermana `reporte-incidentes-siges` con el mismo origen y un experimento revertido
("tipificación real de SiGes, apertura vs. cierre"); **la referencia es `reporte-incidentes`**
(último commit `d4ee5d4`, 2026-09-10, rango multi-mes).

Objetivo (Iván, 2026-09-25): migrarlo completo a HDM **con la misma funcionalidad**.

## 0. Decisiones tomadas (2026-09-25)

| Tema | Decisión |
|---|---|
| IA de tipificación | **Gemini, como hoy**: mismo modelo, prompt y reglas. La caché de 2.457 tipificaciones sigue válida y se migra. Adaptador nuevo en HDM (hoy solo existe Anthropic). |
| Fuente de incidentes | **wsAyC por SOAP, igual que hoy**, reusando `shared/infrastructure/wsayc/`. Mismas operaciones y mismos filtros, para que los números coincidan. |
| Diseño | **Estilo HDM con la misma estructura**: mismas secciones, KPIs, gráficos, filtros y PDF, con los componentes de HDM (`KpiTile`, `StatsTable`, chart.js). Sin handoff previo. |
| Extras (costos IA persistidos, precalentado automático, herramientas de evaluación, bandeja de sugerencias) | **Se deciden al final.** No entran en las fases 1–4. |

## 1. Qué hace hoy (mapa funcional)

Flujo: login → selección de cliente y período → dashboard → versión imprimible (PDF).

**Selección** (`/seleccion`): buscador de clientes por nombre o ID (sin acentos, máx. 50, teclado),
5 clientes recientes (localStorage), mes final (últimos 24), presets de rango 1/3/6/12/24 meses o
"Personalizado" (Desde–Hasta).

**Dashboard** (`/dashboard?empresa&period&months[&sucursal&categoria&subcategoria]`), de arriba abajo:
1. Título (+ tag "DATOS DEMO" en modo mock).
2. Barra: cliente + "Cambiar", selector Hasta, presets/Desde, leyenda del rango, Exportar PDF.
3. Chips de filtros activos + "Limpiar todo".
4. KPIs: **Total incidentes**, **Categoría principal** (N casos, %), **Sucursal principal** (N).
5. "Oportunidades de Mejora" (ver §3.4).
6. Evolución diaria (línea; `DD` o `DD/MM` si el rango pasa de un mes).
7. Donut por categoría + barras top 10 subcategorías (color de su categoría).
8. Barras top 6 sucursales.
9. Tabla de incidentes (ver §3.5).
10. Panel "Pendientes de revisión (N)" (ver §3.3).
11. Pie "Confidencial — Uso exclusivo del Directorio".
12. Toast de tipificación en curso (ver §3.2).

Los filtros viven en la URL y se activan clickeando donut, barras, filas del panel de mejoras o celdas
de la tabla. **Los gráficos y el panel de mejoras usan el período completo sin filtrar** (siguen
sirviendo para navegar); KPIs, evolución y tabla usan la selección filtrada.

**Configuración** (engranaje del header): ABM de categorías — nombre (único, sin distinguir
mayúsculas), color, "Pauta e instrucciones para la IA" (obligatoria, **hoy no se manda al modelo**),
subcategorías como tags. Cambiar la taxonomía invalida los reportes cacheados.

**PDF**: abre `/dashboard/print` en pestaña nueva, **sin los filtros interactivos**, y llama a
`window.print()` al segundo. Layout claro "tinta sobre papel": encabezado (cliente, período, cantidad
de meses, fecha de generación, logo), 3 KPIs, tablas de mejoras, los 4 gráficos a alto fijo y, en
página nueva, "Detalle de Incidentes (Top 50)": Número, Fecha, Sucursal, Tarea realizada,
Tipificación. Diseño en `docs/exportar-pdf-ejecutivo.md` del legacy.

**Auth**: un único usuario por variables de entorno, sin roles. En HDM se reemplaza por permisos
del módulo.

## 2. Datos: wsAyC

Servicio RPC/encoded; cada respuesta es un `xsd:string` con JSON adentro.

| Operación | Uso |
|---|---|
| `getEmpresas{usuario_id}` | Lista de clientes. Solo activos: `FechaRestriccionServicio` = `"19990101"` o ≥ hoy (YYYYMMDD). Id: `id`/`IdEmpresa`/`empresa_id`; nombre: `Nombre`/`RazonSocial`/`name`. |
| `getTopIncidents{IdEmpresa, IdSucursal:"", IdSector:"", OrderBy:"", Top, IdEstado:""}` | **Sin filtro de fecha**: trae los N más recientes. `Top` = meses entre el mes más viejo pedido y hoy × `SOAP_TEST_INCIDENT_LIMIT`. Se descarga una vez por rango. |
| `getIncidentInstances{id, top:"50"}` | Trabajos del incidente → `trabajos[]`, `solucion`, `observaciones`. |
| `getIncidentById{id}` | `causa`, `tecnico` (o Prestador), `fechaCierre`, `tipoTrabajo`. |

Filtro por mes: `fecha` empieza con el período **y** estado ∈ {`Resuelto`, `Cerrado`}. Costo: 1 + 2×N
llamadas por mes. Límite de concurrencia 4, reintentos con backoff solo en 429/5xx/timeouts, caché
en memoria de 15 min (empresas: 1 h).

**Mapeo de campos del incidente** (a portar fiel, con sus alias):
- `numero` = `NroIncidente` + `-` + **dígito verificador** (pesos EAN 3/1, mod 10; `calcCheckDigit`).
- `fecha` ← `Fecha` DD/MM/YYYY → ISO; fechas 1900-01-01 → vacío.
- `sucursal` ← `Sucursal`; `maquina` ← `NroSerie`; `estado` ← `EstadoWeb` o `Estado`.
- `descripcion` ← `Motivo`, si no `Articulo`/`ArtGen`/`Tipo`; se le agrega `" — " + observaciones`
  de la primera instancia Pendiente/Ingresado/Abierto/Creado.
- `solucion` = descripciones de instancias Finalizado/Resuelto/Cerrado unidas con `" · "`; si no
  hay, todas.
- `trabajos[]` = `{descripcion ← Tareas/Descripcion, observ ← Observaciones, fecha, estado, tecnico}`,
  sin filas vacías, en orden cronológico (el SOAP las devuelve al revés).
- Valores que cuentan como vacíos: `" "`, `"-"`, `","`.
- `costo`, `solicitante`, `tipoTrabajo` (`Tipo`), `articulo`, `fechaCierre`
  (`FechaCierre`/`FechaResolucion`/`FechaFin`).

Link del número: `https://webagentes.canaldirecto.com.ar/incidents/view/{numero}`.

**A verificar al portar**: el legacy se autentica con `SOAP_USER`/`SOAP_PASSWORD` y pasa
`usuario_id` a `getEmpresas`; HDM usa login JWT (`WsAycTokenManager`) con el usuario de web
services. Hay que confirmar que ese usuario ve `getEmpresas` y `getTopIncidents` de todos los
clientes.

## 3. Lógica de negocio

### 3.1 Tipificación con IA (Gemini)
- Modelo `GEMINI_MODEL` (default `gemini-3.5-flash`), fallback `GEMINI_FALLBACK_MODEL`
  (`gemini-3.5-flash-lite`), `thinking budget` 1, salida JSON con schema
  `[{i, categoria, subcategoria, confianza}]`.
- Prompt: rol ("experto en soporte técnico de impresión"), taxonomía (nombres de categorías y
  subcategorías, **sin las descripciones**), `TAXONOMY_RULES_V1` (orden de desempate: primero la
  solución, después el reclamo original, ignorar la causa; ~15 reglas puntuales), instrucciones de
  confianza, determinismo, "solo ASCII", few-shot (el archivo no existe hoy: no se mandan ejemplos)
  y los casos `"{i}. Reporte del cliente: … | Solucion/trabajo del tecnico: …"`.
- Casos deduplicados por contenido, lotes de 25, 4 lotes en paralelo, 1 reintento por lote y luego
  el modelo de fallback.
- Ajuste a la taxonomía sin acentos ni mayúsculas: categoría desconocida → Pendiente;
  subcategoría desconocida → `"Otros - {cat}"`.
- **Umbral de confianza**: solo se muestra `alta`. `media`/`baja` → "Pendiente de revision".
- Sin clave de API **no hay clasificador heurístico** (el README miente): lo que no está en caché
  queda Pendiente.

### 3.2 Render en dos fases
1. El reporte se arma solo con la caché (sin llamar a la IA) y devuelve cuántos quedaron pendientes.
2. Si hay pendientes, el cliente dispara la tipificación con IA de cada mes; si algo se tipificó,
   refresca; si no, muestra "IA saturada" con "Reintentar". El toast muestra un cronómetro.

### 3.3 Caché de tipificación y revisión manual
- Clave: `descripcion|causa|solucion`. Valor: `{categoria, subcategoria, confianza}` (respuesta cruda;
  el umbral se aplica al leer). 2.457 entradas (~950 KB) → **se migran a una tabla**.
- Revisión manual (panel de pendientes y detalle del incidente): selects categoría → subcategoría,
  valida contra la taxonomía, guarda `confianza: alta` bajo la misma clave e invalida los reportes
  del cliente.

### 3.4 Oportunidades de Mejora
- Total y % de incidentes **fuera del equipo** (subcategoría ∈ `OFF_EQUIPMENT_SUBCATEGORIES`, 9).
- Titular: visitas **sin reparación** (subcategoría ∈ `NO_REPAIR_SUBCATEGORIES`, 3) con cantidad, %
  y desglose.
- Resto: top 4 subcategorías fuera del equipo con cantidad, % y sucursal principal; marca
  "concentrado" si una sucursal tiene ≥30% de los casos de esa subcategoría.

### 3.5 Tabla de incidentes
Búsqueda sobre número, descripción, causa, solución, sucursal, técnico, categoría y subcategoría;
orden por número, fecha, sucursal, causa, categoría (en HDM: todas las columnas, ver regla de tablas
ordenables); 50 por página; expandir/colapsar todo. Detalle expandido: estado, tipificación,
solicitante, técnico, tipo de trabajo, equipo y serie, fechas de apertura y cierre, reporte del
cliente, causa diagnosticada, bitácora de trabajos y editor "Nueva Tipificación".

### 3.6 Taxonomía
5 categorías (Medio de Impresión, Insumos y Tóner, Hardware y Desgaste, Software Firmware y Red,
Gestión de Soporte) con color, descripción y subcategorías; "Recambio Definitivo" extra en Gestión de
Soporte. Fuente viva: `src/lib/data/categories.json` → **se migra a tablas**. Reglas y conjuntos
especiales: `src/lib/ai/taxonomy.v1.ts` (`TAXONOMY_VERSION = v1.6-2026-06-24`).

## 4. Qué va a HDM

- **Módulo backend** `reporte_incidentes` (capas según ADR-003, plantilla: `sla`).
  - Domain: entidades Incidente/Trabajo, taxonomía, servicios puros (dígito verificador, mapeo
    de estados, umbral de confianza, agregados, oportunidades de mejora, rango de meses).
  - Application: armar reporte (fase caché), tipificar pendientes, resolver tipificación manual,
    ABM de categorías, listar clientes.
  - Infrastructure: gateway wsAyC (zeep, sobre el provider compartido), adaptador Gemini
    (`google-genai`), repos SQLAlchemy de taxonomía y caché, caché TTL en memoria para SOAP.
  - Presentation: router con `require_permission`, colecciones paginadas con `Page[T]`.
- **Tablas**: `reporte_incidentes_categoria`, `reporte_incidentes_subcategoria`,
  `reporte_incidentes_tipificacion_cache`. Migración Alembic con los datos reales (taxonomía +
  2.457 entradas de caché).
- **Settings**: grupo `ReporteIncidentesSettings` (`GEMINI_API_KEY`, `GEMINI_MODEL`,
  `GEMINI_FALLBACK_MODEL`, `GEMINI_THINKING_BUDGET`, concurrencia, lote, límite de incidentes
  por mes, TTLs). `.env.example` ya declara `GEMINI_API_KEY`/`GEMINI_MODEL`, sin uso hoy.
- **Permisos**: catálogo del módulo (`VIEW`, `UPDATE` para tipificación manual y taxonomía),
  migración de seed y de activación, entrada en `route-permissions.ts`, `can()` en botones.
- **Frontend** `features/reporte-incidentes/` + `app/(app)/reporte-incidentes/`: selección,
  dashboard, configuración de categorías y reporte imprimible (patrón `useExportPdf` de
  analisis-log-hp). Gráficos con chart.js cargados de forma diferida.

**Divergencias del legacy a corregir, no copiar**: rutas `/api/*` sin login; usuario único por env;
estado en JSON en disco; costos de IA solo en consola; archivos de 300–550 líneas (ConfigModal,
IncidentDetails, IncidentsTable) → partir según §4 de la guía.

## 5. Plan por fases

1. **Caracterización ejecutable**: portar los 56 tests puros del legacy (normalización SOAP,
   formato, filtros, agregados, insights) como tests unitarios del dominio nuevo; capturar
   respuestas reales de wsAyC de un cliente/mes como fixtures (solo lectura).
2. **Backend núcleo**: gateway wsAyC + armado de reporte desde caché + taxonomía y caché en DB con
   migración de datos. Validar contra el legacy: mismo cliente y mes → mismos totales, top
   categoría y top sucursal.
3. **Tipificación con Gemini** + revisión manual + ABM de categorías.
4. **Frontend**: selección → dashboard con filtros → configuración → PDF.
5. **Extras** (a decidir): costos de IA persistidos, precalentado automático como job de fondo,
   herramientas de evaluación, bandeja de sugerencias.
6. Activación del módulo, uso en paralelo con el legacy y apagado del legacy.

## 6. Bloqueantes conocidos

- **No hay clave de Gemini cargada** ni en el `.env` de HDM (`GEMINI_API_KEY=` vacío) ni en el
  legacy de esta máquina (no hay `.env.local`). Sin clave se puede avanzar todo con la caché
  migrada, pero la tipificación nueva queda en Pendiente.
- Confirmar que el usuario wsAyC de HDM puede llamar `getEmpresas` / `getTopIncidents` para todos
  los clientes (§2).

## 7. Estado (2026-09-25)

**Fases 1 y 2: hechas.**

- Módulo `backend/src/modules/reporte_incidentes` (domain / application / infrastructure /
  presentation), contratos de import-linter propios, settings en
  `settings_groups_reporte_incidentes.py` (`REPORTE_INCIDENTES_LIMITE_POR_MES` = 500,
  `..._CONCURRENCIA_SOAP` = 4, `..._CACHE_TTL_SEGUNDOS` = 900).
- Migración `d1a4c8e2f6b3`: tablas `reporte_incidentes_categoria`, `_subcategoria`,
  `_tipificacion`; taxonomía del legacy sembrada; módulo `reporte-incidentes` en el catálogo
  (acciones view/update) **deshabilitado** hasta tener frontend.
- Caché del legacy importada con `backend/scripts/importar_tipificaciones_reporte_incidentes.py`:
  2.457 tipificaciones (2.378 alta, 60 media, 19 baja), origen `legacy`.
- Endpoints (todos con `require_permission(VIEW)`): `GET /api/reporte-incidentes/empresas`,
  `/reporte`, `/incidentes`, `/pendientes` (colecciones con `Page[T]`).
- Tests de caracterización: los del legacy portados (resumen, oportunidades, filtros,
  formato/dígito verificador, normalización SOAP) + bitácora, tipificación desde caché y
  ventana del `Top`: 54 tests en `tests/unit/*/reporte_incidentes`.
- Prueba real (solo lectura) con el cliente 452, jun–ago 2026: 288 incidentes, 7 pendientes de
  IA, 6 categorías, 118 fuera del equipo / 44 sin reparación. En frío tarda ~27 s
  (1 + 2×288 llamadas SOAP a 4 en paralelo, igual que el legacy); después, caché 15 min.

**Validación contra el legacy**: no se pudo correr lado a lado. El legacy llama a wsAyC sin
token y wsAyC exige login JWT desde sep-2026, así que hoy el legacy no trae datos reales. La
equivalencia se apoya en los tests portados y en el mapeo campo a campo de §2.

**Divergencias conscientes**
- Reintentos: el transporte compartido de wsAyC no reintenta nunca (por las escrituras de
  insumos); el gateway del reporte, que solo lee, reintenta 2 veces ante errores de red/proxy
  (el legacy, 3). Se agregó el 2026-09-25 tras un corte momentáneo de `proxy.cdsa.com.ar` que
  tiró un reporte entero de ~600 llamadas.
- Cliente inexistente → 404 (el legacy caía al primer cliente de la lista).
- En la tabla, los valores vacíos van al final en ambos sentidos (convención de HDM).

**Fase 3: hecha (backend). Probada contra Gemini real el 2026-09-25**: cliente 452, jun–ago 2026,
7 casos pendientes → 1 llamada, 7 tipificados con confianza alta, 2.577 tokens de entrada y 359 de
salida (≈ US$ 0,0017 con los precios configurados).

- Prompt portado literal (`reglas_prompt.py` copiado de `TAXONOMY_RULES_V1`; rol, confianza,
  determinismo y ASCII textuales), ajuste a la taxonomía y lectura de la respuesta en
  `domain/services/prompt_tipificacion.py`.
- Adapter `infrastructure/gemini/gemini_clasificador.py` sobre la API REST con httpx (sin SDK
  nuevo): JSON con schema, `thinkingBudget` 1, modelo `gemini-3.5-flash` con fallback
  `gemini-3.5-flash-lite`, 1 reintento ante 429/5xx/red por modelo. Settings
  `REPORTE_INCIDENTES_GEMINI_*` e `..._IA_LOTE`/`..._IA_CONCURRENCIA` (25 / 4), precios para
  informar el costo. La clave es `GEMINI_API_KEY`; `GEMINI_MODEL` del .env NO se usa (lo tiene
  en `gemini-2.5-pro` para otra cosa).
- Endpoints: `POST /tipificar` (UPDATE; devuelve casos, tipificados, fallidos, tokens y costo
  USD, y lo loguea), `PUT /tipificacion` (corrección manual, confianza alta, origen `manual`),
  `GET/POST /categorias`, `PUT/DELETE /categorias/{nombre}`.
- Como el legacy: solo van a la IA los casos sin nada guardado (media/baja guardados quedan para
  revisión manual); lo que la IA no ubica en la taxonomía no se guarda.
- Diferencia: sin clave, `POST /tipificar` responde 502 `IA_NO_CONFIGURADA` en vez de dejar
  todo pendiente en silencio y mostrar "IA saturada".
- Color de categoría validado como hexadecimal (el legacy no lo validaba).

**Fase 4: hecha (frontend) y módulo habilitado en dev** (migración `e5b2d7a9c1f4`, 2026-09-25).

- Rutas: `/reporte-incidentes` (selección de cliente y rango) y `/reporte-incidentes/reporte`
  (dashboard; estado en la URL: `empresa`, `periodo`, `meses`, `sucursal`, `categoria`,
  `subcategoria`). Código en `frontend/src/features/reporte-incidentes/`.
- Menú: Servicio Técnico › Incidentes › "Reporte ejecutivo" (grupo virtual, junto a SLA). Ruta
  protegida con `reporte-incidentes:view`; Categorías, corrección y tipificación con `update`.
- Referencia visual: mockup en claude.ai Design con el design system "HelpDesk Manager"
  (https://claude.ai/artifact/7pXFLAv41fu76vkf5HP1bD). Sin handoff: decisión del usuario
  (estilo HDM, misma estructura que el legacy).
- **Tipificación con IA automática, como el legacy** (decisión de Iván 2026-09-25): al abrir un
  reporte con casos sin tipificar se dispara sola, solo para quien tiene `update`. Quien solo
  tiene `view` ve un aviso. Sin clave: aviso `IA_NO_CONFIGURADA`, sin reintentos en bucle.
- PDF: mismo mecanismo que Análisis Logs HP (`shared/hooks/use-export-pdf.ts`, movido desde
  analisis-log-hp): popup con el reporte A4 claro sin filtros + `window.print()`; los canvas de
  Chart.js se reemplazan por imágenes antes de copiar el HTML.
- Probado en el navegador con el cliente 452 (jun–ago 2026): selección, dashboard, filtros por
  click, detalle expandido, categorías y contenido del PDF (288 incidentes, 4 gráficos como
  imagen, top 50). No se probó el diálogo de impresión real (el panel no abre popups).

**Diferencias de UI con el legacy (a propósito)**
- Gráfico de sucursales en naranja de marca (el legacy usaba 6 colores; regla de marca).
- Tabla ordenable por cualquier columna, en el backend (regla de tablas de HDM).
- El panel "Pendientes de revisión" es una lista de trabajo (como el mockup), no tabla ordenable.
- Clientes recientes dentro del desplegable del buscador, no como chips.
- Sin la bandeja de sugerencias de subcategorías (el legacy nunca la alimentaba).

## 8. Decisiones de cierre (Iván, 2026-09-25)

- **Costo de la IA: no se muestra.** Ni en pantalla ni en la respuesta de `POST /tipificar`
  (igual que el legacy, que lo dejaba solo en la consola del servidor). Queda en el log del
  backend (`ia_costo`: casos, llamadas, tokens y costo estimado de cada corrida).
- **Legacy apagado.** No se usa (además, sin el token JWT de wsAyC no trae datos reales desde
  sep-2026). HDM queda como única versión; los repos `reporte-incidentes` y
  `reporte-incidentes-siges` se conservan como archivo, sin borrarlos. No hay período de
  convivencia.

## 9. Backlog

- Persistir el historial de costos de IA (hoy solo log) — si algún día se quiere controlar saldo
  o poner un tope mensual.
- Precalentado de reportes (legacy: `/api/prewarm` manual): hoy la primera apertura de un
  cliente/rango tarda ~30 s y después queda 15 min en caché. Opciones evaluadas: botón manual
  para admins o job nocturno (este último gasta IA solo y carga wsAyC a diario).
- Herramientas de evaluación del clasificador (legacy: `/api/corpus`, `/api/classify-eval` y
  `scripts/score.mjs`): retomar si cambian las reglas del prompt o el modelo. Los archivos de
  casos etiquetados (`_fewshot.json`, `_test.json`, `_labels.json`) no están en el repo legacy.
- Bandeja de sugerencias de subcategorías (el legacy la tenía armada pero nunca la alimentaba).
- Probar el diálogo de impresión real del PDF (el contenido está verificado; el popup no).
