# Rediseño UX del Asistente de KM — Fase 0 (relevamiento + propuesta)

Estado: **Fase 1 implementada y Fase 2 verificada el 2026-08-20** (rama `feat/asistente-km-ux`,
commits `2b259d5` docs Fase 0 · `068d8f2` rediseño · `0e3844f` pulido + specs). Recorridos en vivo
PENTACOM y SAN JUAN hechos (capturas `despues/`). Pendiente: validación final del usuario mirando
las capturas y la rama. Ver §8.

Alcance de este doc: inventario real del wizard actual (pantalla por pantalla, con PENTACOM
y SAN JUAN en vivo), propuesta de rediseño organizada por el modelo mental del operador
(Traer de Gestión → Revisar pendientes → Calcular km), tabla de mapeo "elemento actual →
dónde queda", decisiones a validar y hallazgos del relevamiento. El backend NO se toca;
todo lo que la UI nueva muestra sale de los mismos endpoints que hoy.

Docs relacionados (las secciones de UI se actualizan al cerrar Fase 2):
`GEOVALIDACION_TABLA_KM.md`, `MATCHING_SUCURSALES_TABLA_KM.md`, `GEOLOCALIZACION_TABLA_KM.md`.

---

## 0. Cómo se relevó (y qué NO se tocó)

- Código leído completo: los 12 archivos `frontend/src/features/liquidaciones/components/tabla-km-wizard*.tsx`
  (1708 líneas), `tabla-km-lugar-modal.tsx` (`CandidatosPicker`), `tabla-km-config.tsx`
  (botón de entrada), los clientes API (`geolocalizacion-api.ts`, `matching-sucursales-api.ts`,
  `siges-api.ts`) y los tipos en `types/liquidaciones.ts`.
- Recorrido **en vivo** (contenedores levantados, `DISABLE_BACKGROUND_JOBS=true` verificado
  con `printenv` dentro del contenedor) con Playwright contra `http://localhost:3000`, login
  real, prestadores **PENTACOM** (`9f39c270-…`) y **SAN JUAN** (`eda1e000-…`). Se navegó
  por el stepper paso a paso, se abrió el toggle de ex-clientes, el modal "Este paso quedó
  incompleto" y los modales de costo de Google (**y se cancelaron**). Capturas + volcado de
  texto en pantalla en `docs/liquidaciones/capturas-e2e-wizard-2026-08-20/antes/`
  (31 PNG + 13 TXT).
- **Cero escrituras y cero llamadas a Google**: el script registró todas las requests no-GET
  de la sesión; la única fue `POST /api/auth/login`. No se tocó ningún botón con estimación
  0 (esos ejecutan sin modal — ver §5.3) ni ninguna acción que escriba.
- Números de respaldo: GETs directos al backend (`asistente-km/estado`, `siges/sucursales`
  paginado de a 200, `matching/propuestas`, `coordenadas`, `geovalidacion/tier0|tier1|tier1b|worklist`,
  `pines-sospechosos`).

---

## 1. Datos reales al 2026-08-20 (lo que ve el operador hoy)

| Dato (`asistente-km/estado`) | PENTACOM | SAN JUAN |
|---|---:|---:|
| Vinculado a Gestión | sí | sí |
| Sucursal base configurada / con coordenadas | **no** / no | sí / sí |
| Sucursales activas en Gestión / ex-clientes | 332 / 430 | 871 / 77 |
| Sucursales nuevas para importar | 132 | 427 |
| Filas en Tabla KM | 276 | 616 |
| Sin coordenadas (activas) | 71 | 2 |
| Direcciones ambiguas pendientes | 0 | 17 |
| Filas sin km | 0 | 130 |
| Filas que no aparecen en Gestión | 29 | 66 |
| Pines sospechosos cacheados | 0 | 66 |
| Estimación geocodificar / distancias / auditar pines | 70 / 522 / 261 | 0 / 1738 / 560 |
| Tope por corrida | 200 | 200 |

Otros conteos (GET directos):

| Fuente | PENTACOM | SAN JUAN |
|---|---:|---:|
| `siges/sucursales` total (nuevas activas · nuevas ex-cliente · ya cargadas activas · ya cargadas ex-cliente) | 762 (132 · 383 · 200 · 47) | 948 (427 · 66 · 444 · 11) |
| Propuestas N2 (filas con candidato · candidatos totales) | 8 · 11 | 61 · 131 |
| `coordenadas` (ambiguas · resueltas por geocode) | 0 · 0 | 17 · 26 |
| Tier 0 (total · alta · media · baja) | 329 (7 · 67 · 255) | 663 (4 · 616 · 43) |
| Tier 1 (provincia distinta según Georef) | 2 | 192 |
| Tier 1b (confirmado por Georef + Nominatim) | 2 | 192 |
| Worklist: certeza absoluta · requiere verificación · est. Google | 7 · 61 · 61 | 4 · 299 · **0** (ya auditado) |
| Pines sospechosos (confirmados por Google) | 0 | 69 |

Nota de alcance: Tier 0 corre sobre **todas** las sucursales del PST en Gestión (incluye
ex-clientes — por eso PENTACOM muestra 255 "sin coordenadas" en Tier 0 contra 71 en el
diagnóstico, que cuenta solo activas; verificado en `estado_asistente_km.py`, `_contar`).

---

## 2. Inventario real del wizard actual + mapeo a la propuesta

Clasificación: **(a)** decisión humana imprescindible · **(b)** maquinaria automatizable
(corre sola o agrupada en un solo botón) · **(c)** información plegable a "ver detalle" ·
**(d)** redundante/eliminable (siempre con destino explícito). La columna **Destino** es
el contrato de paridad que Fase 2 verificó ítem por ítem (columna "✓ F2": verificado el 2026-08-20 —
en vivo con SAN JUAN para todo lo de solo lectura y modales de costo, y con el spec Playwright
`tests/tabla-km-wizard.spec.ts` (mocks) para lo que escribe: Traer de Gestión, confirmar/rechazar,
elegir ubicación, preview/aplicar y cierre).

### 2.1 Marco del modal (todas las pantallas) — `tabla-km-wizard.tsx`

| # | Elemento actual (texto literal) | Clase | Destino en la propuesta | ✓ F2 |
|---|---|---|---|---|
| M1 | Título "Asistente de KM — {nombreCorto}" | a | Se mantiene. | ✓ |
| M2 | Stepper de 6 círculos: Diagnóstico · Importar · Sin match · Ubicar · Distancias · Pines, con estados actual/ok(✓)/pendiente/bloqueado(🔒) y tooltip con motivo de bloqueo | b/c | Stepper de **3 momentos** (1 · Traer de Gestión / 2 · Revisar pendientes / 3 · Calcular km) con los mismos 4 estados y el mismo tooltip de bloqueo. Decisión §4.b. | ✓ |
| M3 | Spinner "Revisando el estado de tu Tabla KM… (no consulta Google)" | b | Pantalla de apertura "Analizando tu Tabla KM…" con lista de chequeos en progreso (§3.0). | ✓ |
| M4 | Error "No se pudo leer el estado del asistente. Cerrá y volvé a abrir." | c | Se mantiene (mismo texto). | ✓ |
| M5 | Botones de pie "← Anterior" / "Siguiente →" / "Finalizar" | b | Se mantienen (3 momentos). "Finalizar" pasa a ser la pantalla de cierre (§3.4). | ✓ |
| M6 | Modal "Este paso quedó incompleto" con consecuencia concreta + "Quedarme y terminarlo" / "Continuar igual" | a | Se mantiene al salir de 2 → 3 con pendientes (mismos textos de consecuencia, adaptados a la bandeja). | ✓ |

### 2.2 Paso 1 · Diagnóstico — `tabla-km-wizard-diagnostico.tsx`

| # | Elemento actual | Clase | Destino | ✓ F2 |
|---|---|---|---|---|
| D1 | Intro "Esto es lo que el asistente encontró revisando tu Tabla KM contra Gestión. Nada de lo que ves acá gastó consultas de Google — el costo de cada acción se muestra antes de ejecutarla." | c | Una sola línea en la apertura: "Nada de esto consulta Google; el costo de cada acción se muestra antes." | ✓ |
| D2 | Renglón bloqueante "Este prestador no está vinculado a Gestión" + detalle de dónde se configura | a | Banner bloqueante en Momento 1 (mismo texto). | ✓ |
| D3 | Renglón bloqueante "Falta la sucursal base de despacho" + detalle | a | Banner bloqueante en Momento 1; además bloquea Momento 3 (igual que hoy). | ✓ |
| D4 | Renglón bloqueante "La sucursal base no tiene ubicación en Gestión" + detalle | a | Ídem D3. | ✓ |
| D5 | "N sucursales nuevas para importar desde Gestión" + botón "Ir a Importar" | b | Pasa a ser parte del resumen y del botón único de Momento 1 ("Traer de Gestión" importa las nuevas activas — §4.e). | ✓ |
| D6 | "N sucursales sin ubicación en el mapa" + "Sin ubicación no se les puede calcular km. Buscarlas cuesta ~K consultas a Google." + "Ir a Ubicar" | b/a | Ítem agrupado de la bandeja (tipo **U1**, §3.2) con el mismo botón de costo. | ✓ |
| D7 | "N direcciónes con más de un resultado posible" (sic, tilde de más) + "Resolver" | a | Ítems **U2** de la bandeja (uno por dirección). Se corrige el typo. | ✓ |
| D8 | "N filas de tu tabla no aparecen en Gestión" + detalle + "Ver cuáles" | a | Ítems **N1/N2** de la bandeja. | ✓ |
| D9 | "N filas sin km calculado" + "Calcular distancias cuesta ~K consultas…" + "Ir a Distancias" | b | Resumen del Momento 3 (mismo número y costo). | ✓ |
| D10 | "N pines del mapa que no coinciden con la dirección" + "El pin de Gestión está a más de 5 km…" + "Revisar pines" | a | Ítems **P3** de la bandeja. | ✓ |
| D11 | Renglón verde "Tu Tabla KM está completa" + "{filas} filas, todas con km y ubicación al día." | c | Estado de cierre (§3.4) y bandeja vacía ("No hay nada pendiente"). | ✓ |
| D12 | Botón primario "Siguiente paso recomendado: {acción} →" | d | Se elimina como botón aparte: el único CTA primario de cada pantalla ya es la acción recomendada. | ✓ |

### 2.3 Paso 2 · Importar — `tabla-km-wizard-importar.tsx`

| # | Elemento actual | Clase | Destino | ✓ F2 |
|---|---|---|---|---|
| I1 | Intro "Estas son las sucursales de clientes que este prestador atiende según Gestión. Al importarlas se crean en tu Tabla KM con km en 0 — el km se calcula después, en el paso Distancias. Este paso no consulta Google." | c | "ver detalle" del bloque Importar en Momento 1. | ✓ |
| I2 | Chips "N NUEVAS ACTIVAS" / "N EX-CLIENTES" / "N YA CARGADAS" | c | Una frase del resumen de Momento 1 ("427 sucursales nuevas con actividad; 66 ex-clientes no se importan"). Los números pasan a salir del listado **completo** (hoy solo de la primera página — bug §5.1). | ✓ |
| I3 | Toggle "Mostrar también ex-clientes (sin liquidaciones en 24 meses)" / "Ocultar ex-clientes" | a | Se mantiene dentro de "ver detalle" de Importar: "Incluir también N ex-clientes (sin liquidaciones en 24 meses)". Nunca automático. | ✓ |
| I4 | Lista scrolleable de sucursales nuevas (empresa · sucursal, domicilio · localidad · provincia, badge "sin actividad") | c | Plegada: "Ver las N sucursales ▾" dentro de Momento 1. | ✓ |
| I5 | Botón "Importar N sucursales nuevas" con progreso "Importando i/N…" | b | Absorbido por el botón único "Traer de Gestión" (progreso visible por sub-tarea). | ✓ |
| I6 | Mensajes "✓ N sucursales importadas…", "Todas las sucursales… ya están en la Tabla KM", "No hay clientes activos nuevos para importar. Usá 'Mostrar también ex-clientes'…" | c | Resumen post-acción de Momento 1 (§3.1). | ✓ |
| I7 | Error "No se pudieron cargar las sucursales desde Siges" | c | Se mantiene como error del bloque. | ✓ |

### 2.4 Paso 3 · Sin match — `tabla-km-wizard-matching.tsx`

| # | Elemento actual | Clase | Destino | ✓ F2 |
|---|---|---|---|---|
| S1 | Intro "Estas filas de tu Tabla KM no aparecen con el mismo nombre en Gestión — puede ser un símbolo distinto (Nº vs N°), una abreviatura, o que la sucursal cambió de nombre. Acá revisás candidato por candidato: nada se vincula sin que lo confirmes." | c | "ver detalle" del grupo de ítems **N2** en la bandeja. | ✓ |
| S2 | Tarjeta "3a · Vincular automáticamente (símbolo/abreviatura)" + descripción técnica + badge "NO USA GOOGLE" + botón "Vincular automáticamente" + chips "N vinculadas / N ya estaban al día" | b | Absorbido por "Traer de Gestión" (corre `auto-vincular-n1` después de refrescar). Resultado en el resumen: "vinculamos N automáticamente". | ✓ |
| S3 | Tarjeta "3b · Confirmar candidatos" + descripción | c | Encabezado del grupo N2 de la bandeja. | ✓ |
| S4 | Por fila: "{empresa} — {sucursal}" + por candidato: nombre, "{domicilio} · {motivo}", badge "{score}%", botones "Rechazar" / "Confirmar" | a | Ítem **N2** (§3.2): pregunta en llano, "Sí, es esta" / "No es esta"; score y motivo técnico en "ver detalle". Misma API (`confirmar` / `rechazar`). | ✓ |
| S5 | "✓ No hay candidatos pendientes de confirmación." | c | Estado vacío del grupo. | ✓ |
| S6 | (ausente hoy) filas sin match **sin** candidato N2: no se listan en ningún paso | — | Ítem **N1** de la bandeja usando `noEncontradasDetalle` de la respuesta de refrescar (§5.4). | ✓ |

### 2.5 Paso 4 · Ubicar — `tabla-km-wizard-geocodificar.tsx`

| # | Elemento actual | Clase | Destino | ✓ F2 |
|---|---|---|---|---|
| G1 | Tarjeta "2a · Actualizar datos desde Gestión" + "Trae el domicilio actual de cada sucursal y completa el vínculo con Gestión. No consulta Google." + badge + botón "Actualizar desde Gestión" | b | Absorbido por "Traer de Gestión" (primera sub-tarea). | ✓ |
| G2 | Chips resultado: "N direcciones actualizadas" / "N vinculadas a Gestión" / "N sin cambios" / "N no encontradas en Gestión" | c | Una frase en el resumen post-acción de Momento 1 + "ver detalle". | ✓ |
| G3 | Caja "¿Qué significa 'no encontradas en Gestión'?" + lista de filas | c | Ítems **N1** de la bandeja (la explicación va en "ver detalle"). | ✓ |
| G4 | Lista de cambios "{sucursal}: ~~antes~~ → después" | c | "Ver qué cambió ▾" en el resumen de Momento 1. | ✓ |
| G5 | Tarjeta "2b · Buscar ubicaciones faltantes" + descripción | c | Ítem agrupado **U1** de la bandeja. | ✓ |
| G6 | `BotonConsumoGoogle` "Buscar ubicaciones (N sucursales)" + badge "~K CONSULTAS A GOOGLE" / "SIN COSTO — TODO ESTÁ EN CACHÉ" + modal de confirmación | a | Se mantiene tal cual (mismo componente, mismo modal, mismo número antes). | ✓ |
| G7 | Chips resultado: "resueltas solas / para elegir en 2c / sin resultado / sin dirección escrita / consultas usadas / cortadas por tope" | c | Frase post-acción en el ítem U1 + los "sin resultado"/"sin dirección" aparecen como ítems **U3**. | ✓ |
| G8 | "✓ Todas las sucursales activas tienen ubicación — nada que buscar." | c | Estado vacío (U1 no aparece). | ✓ |
| G9 | Tarjeta "2c · Elegir la ubicación correcta" + "Google devolvió más de una opción…" | c | Encabezado del grupo **U2**. | ✓ |
| G10 | Por dirección ambigua: "{empresa} — {sucursal}", badge "ELEGÍ UNA OPCIÓN", dirección, `CandidatosPicker` (candidatos con formattedAddress, "lat, lon · LOCATION_TYPE · match parcial", link "VER EN MAPS", botón "Usar"; inputs "Latitud manual"/"Longitud manual" + "Usar manual") | a | Ítem **U2** (§3.2): mismas opciones y misma API; `locationType` traducido ("ubicación exacta" / "aproximada" / "centro de la zona"); lat/lon y tipo técnico en "ver detalle"; carga manual plegada en "Cargar coordenadas a mano ▾". | ✓ |
| G11 | "✓ No hay direcciones pendientes de elección." | c | Estado vacío. | ✓ |

### 2.6 Paso 5 · Distancias — `tabla-km-wizard-calcular.tsx`

| # | Elemento actual | Clase | Destino | ✓ F2 |
|---|---|---|---|---|
| C1 | Intro "Se van a calcular los km de ida y vuelta (con Google Maps) para N sucursales con ubicación. Primero ves el resultado; nada se guarda hasta que apliques." | a | Se mantiene como encabezado de Momento 3 (mismo texto). | ✓ |
| C2 | Gate "Hay N sucursales sin ubicación en el mapa" + "Si calculás ahora, esas N van a quedar sin km…" + "Ir a Ubicar primero (recomendado)" / "Calcular igual — las N quedan sin km" | a | Se mantiene; "Ir a Ubicar" pasa a "Resolverlas primero" (lleva a la bandeja filtrada en U1/U2). | ✓ |
| C3 | `BotonConsumoGoogle` "Calcular distancias" con `bloquearSobreTope` + mensaje "Esta acción necesitaría ~K consultas… el tope por corrida es T — no se puede ejecutar entera. Avisale al administrador si te pasa." | a | Se mantiene (mismo componente y bloqueo). Texto en llano, ver §3.3. Ver hallazgo §5.2 (SAN JUAN hoy está bloqueado). | ✓ |
| C4 | Chips preview: "N filas nuevas / N filas a actualizar / N sin ubicar / N sin ruta / N ex-clientes omitidos / N consultas usadas" | c | Frase resumen arriba de la tabla (mismos números). | ✓ |
| C5 | Tabla preview: Empresa · Sucursal · Actual · Ida · Vuelta · Total · Ubicación (Siges/Geocodificado/Manual) · Acción (nueva/actualiza) | a | **Se mantiene idéntica** (semántica de km fuera de alcance). "Ubicación" pasa a "Origen del pin" con valores "Gestión / Google / Manual". | ✓ |
| C6 | Botón "Aplicar a la Tabla KM…" + modal "¿Aplicar estos km a tu Tabla KM?" ("Se van a crear N filas nuevas y actualizar los km de M existentes." / "El umbral de viático y las observaciones de cada fila no se tocan. Esta acción no consulta Google…") | a | Se mantiene tal cual. | ✓ |
| C7 | "✓ Distancias aplicadas a tu Tabla KM. Podés continuar al paso de pines." | c | Reemplazado por la pantalla de cierre (§3.4). | ✓ |

### 2.7 Paso 6 · Pines — `tabla-km-wizard-pines*.tsx`

| # | Elemento actual | Clase | Destino | ✓ F2 |
|---|---|---|---|---|
| P1 | Tarjeta "1 · Geovalidación básica (Tier 0)" + "Coordenadas ausentes, fuera de Argentina, invertidas, pines compartidos entre sucursales distintas y muy lejos de la base. No consulta ningún servicio externo." + badge "NO USA GOOGLE" | c | Desaparece como sección; sus hallazgos se reparten en la bandeja: alta → **P1** (certeza), media → **P4** (a verificar), baja (sin coordenadas) → **U1**. La explicación va al "ver detalle" de cada ítem. | ✓ |
| P2 | Por hallazgo Tier 0: "{empresa} — {sucursal}", badge severidad "ALTA/MEDIA/BAJA", detalle técnico ("(lat, lon) fuera del rectángulo continental+insular", "cae fuera de Argentina; invertido cae dentro", "Mismo pin que otras N sucursal(es) con domicilio distinto"), link "VER PIN EN MAPS" | a/c | Ítems P1/P4 con texto llano ("El pin está fuera de Argentina", "Latitud y longitud parecen intercambiadas", "Comparte el pin con otras N sucursales de domicilio distinto"); detalle técnico y código plegados; link "Ver en el mapa" se mantiene. | ✓ |
| P3 | "✓ Ningún problema geométrico detectado." | c | Estado vacío de la bandeja. | ✓ |
| P4 | Tarjeta "1b · Provincia del pin vs. Gestión (Georef)" + descripción larga + badge "GRATIS, NO ES GOOGLE" + botón "Consultar Georef" + chips "N consultadas / N ya en cache / N pendientes — repetí la acción" | b | Corre solo en los chequeos automáticos de apertura (§4.a). Progreso y "quedan N por chequear" en la pantalla de apertura. Nombre "Georef" solo en "ver detalle". | ✓ |
| P5 | Por hallazgo Tier 1: badge "PROVINCIA DISTINTA" + "Declarada en Gestión: X — el pin cae en Y según Georef (dato oficial del Estado)" + link Maps | c/a | Ítem **P2b** (una sola fuente) — aparece solo si la segunda opinión no corrió todavía. | ✓ |
| P6 | "Sin discrepancias de provincia detectadas sobre lo ya consultado." | c | Estado vacío. | ✓ |
| P7 | Tarjeta "1c · Segunda opinión (Nominatim / OpenStreetMap)" + descripción + botón "Consultar Nominatim" + chips | b | Ídem P4 (automático). | ✓ |
| P8 | Por hallazgo Tier 1b: fondo destacado, badge "CONFIRMADO POR 2 FUENTES", "Declarada: X — Georef y Nominatim coinciden: el pin está en Y", link Maps, atribución "Data © OpenStreetMap contributors, ODbL 1.0 — http://osm.org/copyright" | a | Ítem **P2** ("El pin está en Y, pero su dirección dice X. Dos fuentes independientes lo confirman."). **Atribución ODbL se mantiene visible** al pie de la bandeja siempre que haya al menos un ítem P2/P2b (y en "ver detalle" de cada uno). | ✓ |
| P9 | "Sin confirmaciones de dos fuentes sobre lo ya consultado." | c | Estado vacío. | ✓ |
| P10 | Tarjeta "1d · Worklist final — a corregir en Gestión" + descripción técnica | c | Encabezado de cierre de Momento 2: "Para corregir en Gestión" (§3.2, bloque final). | ✓ |
| P11 | Botón "Exportar CSV para Gestión" | a | Se mantiene en el cierre de Momento 2 **y** en la pantalla final (§4.c). Mismo endpoint. | ✓ |
| P12 | `BotonConsumoGoogle` "Verificar todos los pines con Google" (~K consultas) | a | Se mantiene como acción secundaria "Más chequeos ▾ → Verificar todos los pines con Google (~K consultas)" (§4.c). | ✓ |
| P13 | Ítem certeza absoluta: badge "CORREGIR EN GESTIÓN", "{domicilio} · latlon_invertidas, fuera_de_argentina, pin_compartido" + link | a | Ítem **P1** con motivos traducidos. | ✓ |
| P14 | Ítem pin confirmado por Google: badge "{km} km de diferencia" (rojo si ROOFTOP), dirección, links "VER PIN DE GESTIÓN" / "VER DIRECCIÓN ESCRITA", botón "Usar la dirección escrita" | a | Ítem **P3** (mismos links y botón; `corregir-pin` sin cambios). | ✓ |
| P15 | "✓ Nada pendiente de corregir. Podés finalizar." / "Todavía no hay pines confirmados por Google. Auditá el residuo o el prestador completo para completar esta lista." | c | Estados vacíos del bloque de cierre. | ✓ |
| P16 | `BotonConsumoGoogle` "Auditar residuo con Google (N sucursales)" (~K consultas / "SIN COSTO — TODO ESTÁ EN CACHÉ") | a | Botón del ítem agrupado **P4** ("Verificar estas N con Google"). Mismo endpoint acotado por ids. | ✓ |

### 2.8 Fuera del modal

| # | Elemento | Destino | ✓ F2 |
|---|---|---|---|
| E1 | Botón "Asistente de KM →" en Tabla KM (tooltip "Guía paso a paso: geocodificar → calcular km → auditar pines") | Mismo botón y punto de entrada; tooltip pasa a "Traer sucursales de Gestión, revisar pendientes y calcular km". | ✓ |

Conteo: **66 elementos** inventariados; **0 sin destino**. Eliminado de verdad solo D12
(botón duplicado de la acción recomendada).

---

## 3. Propuesta de rediseño — 3 momentos

Principios (no negociables, salen del pedido): una acción principal por pantalla; lenguaje
llano por defecto (Tier/Georef/Nominatim/N1/N2/worklist/severidad/ROOFTOP solo en "ver
detalle"); lo gratis corre junto, lo pago siempre con su número antes (mismo
`BotonConsumoGoogle`); una sola bandeja de pendientes rankeada; cierre explícito.

Componentes: solo design system (`BrandModal`, `BrandButton`, `Badge`, `BrandInput`,
`Spinner`, `Tooltip`) y el patrón de fila/tarjeta que el wizard ya usa hoy (borde
`rounded-[8px]`, título + subtítulo, badge a la derecha, botones `size="sm"`). El
"ver detalle ▾" reusa el patrón de link subrayado que hoy tiene "Mostrar también
ex-clientes" (§4.i). **No se introduce ninguna tabla, gráfico ni KPI tile nuevo**
(la única tabla es la preview de km, que queda idéntica).

### 3.0 Apertura — introducción + chequeos

**Decidido**: el asistente se rehace por completo y **arranca siempre con una pantalla de
introducción** que explica en llano qué va a pasar en cada momento; un solo botón
"Empezar". Recién al apretarlo corren los chequeos que no modifican filas.

```
┌ Asistente de KM — SAN JUAN ──────────────────────────────────────────── ✕ ┐
│   ① Traer de Gestión ── ② Revisar pendientes ── ③ Calcular km              │
│                                                                             │
│   Este asistente deja tu Tabla KM al día en tres momentos:                  │
│                                                                             │
│   ① Traer de Gestión                                                        │
│     Actualiza domicilios y vínculos, importa las sucursales nuevas con      │
│     actividad y vincula sola las que solo difieren en un símbolo o una      │
│     abreviatura. No consulta Google.                                        │
│                                                                             │
│   ② Revisar pendientes                                                      │
│     Una sola lista con lo que necesita tu decisión: nombres por confirmar,  │
│     ubicaciones por elegir y pines que los chequeos automáticos marcaron    │
│     como rotos. Lo que haya que corregir en Gestión se exporta en un CSV.   │
│                                                                             │
│   ③ Calcular km                                                             │
│     Calcula ida y vuelta con Google Maps, te muestra el resultado y recién  │
│     cuando aplicás se guarda. El umbral de viático y las observaciones no   │
│     se tocan.                                                               │
│                                                                             │
│   Nada consulta Google sin mostrarte antes cuántas consultas cuesta.        │
│                                                                             │
│   [ Empezar ]                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

Al apretar "Empezar" corren en paralelo los GET de hoy (estado, propuestas, coordenadas,
tier0, tier1, tier1b, worklist, pines sospechosos) y los dos chequeos gratis que hoy son
botones (P4, P7: `consultar-georef`, `consultar-nominatim` — solo escriben su cache).
**Nada escribe en la Tabla KM** hasta el botón "Traer de Gestión" del Momento 1.

```
│   Analizando tu Tabla KM…                                                   │
│   ✓ Leímos tu Tabla KM y las sucursales de Gestión                          │
│   ✓ Chequeos de pines (sin costo)                                           │
│   ● Comparando la provincia de cada pin con datos oficiales… (sin costo)    │
│   ○ Segunda opinión sobre los pines dudosos                                 │
│   Nada de esto consulta Google; el costo de cada acción se muestra antes.   │
```

Si un chequeo gratis queda cortado por su tope interno (`pendientesPorTope > 0`), la
pantalla sigue a Momento 1 igual y deja una línea: "Quedan N pines por chequear —
[Seguir chequeando] (sin costo)". No bloquea nada.

### 3.1 Momento 1 · Traer de Gestión

Una acción principal: **"Traer de Gestión"**. Agrupa (en este orden, con progreso por
sub-tarea): `refrescar-datos-sucursales` → `auto-vincular-n1` → importar las sucursales
nuevas **con actividad** (`createTablaKm` por fila, como hoy). Todo gratis. Bloqueantes
(D2/D3/D4) se muestran como banner arriba y, salvo D2, no impiden traer de Gestión.

```
┌ Asistente de KM — SAN JUAN ──────────────────────────────────────────── ✕ ┐
│   ① Traer de Gestión ── ② Revisar pendientes ── ③ Calcular km              │
│                                                                             │
│   Gestión tiene 871 sucursales activas de este prestador.                   │
│   Tu Tabla KM tiene 616 filas.                                              │
│                                                                             │
│   Al traer de Gestión vamos a:                                              │
│   • actualizar domicilios y vínculos de las 616 filas                        │
│   • importar 427 sucursales nuevas con actividad        Ver las 427 ▾       │
│   • vincular automáticamente los nombres que solo difieren en un símbolo    │
│     o una abreviatura                                                       │
│   No consulta Google. Los ex-clientes (66) no se importan — ver detalle ▾   │
│                                                                             │
│   [ Traer de Gestión ]                                                      │
│                                                                             │
│   ver detalle ▾  (qué es "con actividad", incluir ex-clientes, qué cambia   │
│                   en cada fila)                                             │
│                                                                     Siguiente → │
└─────────────────────────────────────────────────────────────────────────────┘
```

Durante la corrida, el botón muestra "Actualizando domicilios…" → "Vinculando nombres…"
→ "Importando 120/427…". Al terminar:

```
│   ✓ Listo: actualizamos 616 filas, importamos 427 sucursales y vinculamos   │
│     {n1} automáticamente.                                                   │
│     {n2} nombres necesitan tu confirmación y {k} no aparecen en Gestión     │
│     → están en Revisar pendientes.                                          │
│     Ver qué cambió ▾   (lista "antes → después" de G4; no encontradas G3)  │
│                                                                             │
│   [ Revisar pendientes → ]                                                  │
```

Los números entre llaves salen de la respuesta de cada endpoint (hoy `vinculadas`,
`sinCambios`, `noEncontradas`, `noEncontradasDetalle`, `cambios`, `ResultadoAutoVinculoN1`).
No se estiman.

Variantes: si no hay nada que importar ni actualizar, el botón queda igual (refrescar es
idempotente) y el resumen dice "Todas las sucursales de Gestión ya están en tu Tabla KM.
Actualizamos domicilios: N cambios." Banner bloqueante PENTACOM (texto actual D3):
"Falta la sucursal base de despacho. Es el punto desde donde sale el técnico — sin ella no
se pueden calcular km. Se configura en Configuración → Prestadores → Cordoba - Pentacom
S.A., campo Sucursal base." (Momento 3 bloqueado con el mismo tooltip de hoy.)

### 3.2 Momento 2 · Revisar pendientes (la bandeja única)

Una lista, una decisión por ítem, lo grave primero. Encabezado con el resumen (texto, no
tiles) y un filtro por tipo (mismo `SegmentedControl` del dashboard Inicio — patrón ya
validado): **Todos · Pines rotos · Nombres · Ubicaciones**.

```
┌ Asistente de KM — SAN JUAN ──────────────────────────────────────────── ✕ ┐
│   ① Traer de Gestión ── ② Revisar pendientes ── ③ Calcular km              │
│                                                                             │
│   Quedan 265 pines rotos (van al CSV para Gestión), 61 nombres por          │
│   confirmar y 19 ubicaciones por resolver.                                  │
│   [ Todos ] [ Pines rotos ] [ Nombres ] [ Ubicaciones ]                     │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ Gobierno de San Juan — Escuela 20 de Junio           PIN FUERA DEL PAÍS │ │
│ │ El pin está en Madrid, España; la dirección dice La Madrid y Mendoza    │ │
│ │ S/N, San Juan.                                                          │ │
│ │ [Ver en el mapa]   Va al CSV para Gestión          ver detalle técnico ▾│ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │ CEVA — Córdoba                                     PIN EN OTRA PROVINCIA│ │
│ │ El pin está en La Pampa, pero su dirección dice Córdoba. Dos fuentes    │ │
│ │ independientes lo confirman.                                            │ │
│ │ [Ver en el mapa]   Va al CSV para Gestión          ver detalle técnico ▾│ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │ Gobierno de San Juan — ENI N.º 65                  2239 KM DE DIFERENCIA│ │
│ │ El pin de Gestión está a 2239 km de la dirección escrita                │ │
│ │ (Rio Gallegos S/N 52, Chimbas, San Juan). Según Google.                 │ │
│ │ [Ver pin de Gestión] [Ver dirección escrita] [Usar la dirección escrita]│ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │ ¿"Escuela ANTONIO QUARANTA" es esta sucursal de Gestión?     NOMBRE     │ │
│ │ Escuela Antonio Pulenta — Laprida e Independencia S/N                   │ │
│ │ [Sí, es esta] [No es esta]        Ver 2 candidatos más ▾   ver detalle ▾│ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │ Cepas Argentinas — San Juan                        ELEGÍ LA UBICACIÓN   │ │
│ │ Dirección: Rastreador Calivar 239, San Juan. Google encontró 2 opciones:│ │
│ │ ○ Rastreador Calivar Nte. 239, Rivadavia — ubicación exacta   [Usar]    │ │
│ │ ○ Rastreador Calivar Sur 239, Rivadavia — aproximada          [Usar]    │ │
│ │ Ver en el mapa · Cargar coordenadas a mano ▾                            │ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │ 299 sucursales comparten pin con otras o están muy lejos de la base     │ │
│ │ No se puede confirmar gratis si el pin está bien.                       │ │
│ │ [Verificar estas 299 con Google]  SIN COSTO — TODO ESTÁ EN CACHÉ        │ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │ 2 sucursales no tienen ubicación                                        │ │
│ │ Sin ubicación no se les puede calcular km.                              │ │
│ │ [Buscar ubicaciones]  SIN COSTO — TODO ESTÁ EN CACHÉ                    │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│   Datos de mapa © OpenStreetMap contributors (ODbL)                          │
│                                                                             │
│   Para corregir en Gestión: 265 sucursales  [Exportar CSV para Gestión]     │
│   Más chequeos ▾  (Verificar todos los pines con Google ~560 consultas)     │
│                                                         ← Anterior  Siguiente → │
└─────────────────────────────────────────────────────────────────────────────┘
```

Tipos de ítem, fuente de datos y acción (todo con endpoints existentes):

| Tipo | Fuente | Texto por defecto | Acción / destino | "ver detalle" |
|---|---|---|---|---|
| **P1** Pin imposible | `worklist.certezaAbsoluta` (+ Tier 0 alta) | "El pin está fuera de Argentina" / "Latitud y longitud parecen intercambiadas" | [Ver en el mapa] · "Va al CSV para Gestión" | código, coordenadas crudas |
| **P2** Pin en otra provincia, 2 fuentes | `tier1b` | "El pin está en {Y}, pero su dirección dice {X}. Dos fuentes independientes lo confirman." | [Ver en el mapa] · "Va al CSV para Gestión" | "Georef (API del Estado) y Nominatim/OpenStreetMap coinciden", atribución ODbL |
| **P2b** Pin en otra provincia, 1 fuente | `tier1` − `tier1b` | "Según datos oficiales el pin cae en {Y}, pero su dirección dice {X}. Falta la segunda opinión." | [Ver en el mapa] · [Pedir segunda opinión (sin costo)] → `consultar-nominatim` | ídem |
| **P3** Pin lejos de su dirección, según Google | `pines-sospechosos` | "El pin de Gestión está a {km} km de la dirección escrita ({dirección}). Según Google." Badge "{km} km de diferencia" | [Ver pin de Gestión] [Ver dirección escrita] [Usar la dirección escrita] → `corregir-pin` | precisión de Google (exacta/aproximada = `locationType`) |
| **P4** A verificar (agrupado) | `worklist.requiereVerificacion` | "{N} sucursales comparten pin con otras o están muy lejos de la base. No se puede confirmar gratis si el pin está bien." | `BotonConsumoGoogle` "Verificar estas {N} con Google" (~K) → `auditar-pines` con ids | lista de las N con motivo traducido |
| **N2** Nombre con candidato | `matching/propuestas` | "¿'{nombre local}' es esta sucursal de Gestión? {candidato} — {domicilio}" | [Sí, es esta] → `confirmar` · [No es esta] → `rechazar` · "Ver {n} candidatos más ▾" | score %, "difieren en: …" |
| **N1** Nombre sin candidato | `refrescar…noEncontradasDetalle` − propuestas (solo tras Traer de Gestión) | "No encontramos '{nombre}' en Gestión." | Texto: "Corregí el nombre en la Tabla KM (Editar fila) o dala de baja si ya no se atiende." | explicación de G3 |
| **U1** Sin ubicación (agrupado) | `estado.sinCoordenadas` / `estimacionGeocodificar` | "{N} sucursales no tienen ubicación. Sin ubicación no se les puede calcular km." | `BotonConsumoGoogle` "Buscar ubicaciones" (~K) → `geocodificar-faltantes` | resultado en llano (G7) |
| **U2** Elegí la ubicación | `coordenadas` estado `ambigua` | "Google encontró {n} opciones para {dirección}" | [Usar] por opción → `resolverCoordenadas` · "Cargar coordenadas a mano ▾" | lat/lon, tipo técnico, "match parcial" |
| **U3** Sin resultado | `coordenadas` estado `sin_resultados` / `sin_direccion` | "Google no encontró '{dirección}'" / "No tiene dirección escrita en Gestión" | "Cargar coordenadas a mano ▾" · "Corregí la dirección en Gestión" | — |

Orden por defecto: P1 → P2 → P3 → N2 → U2 → P2b → P4 → U1 → U3 → N1 (lo que ya se sabe
roto con certeza primero; después las decisiones del operador; después las acciones en
bloque; al final lo manual). Dentro de cada tipo, por empresa/sucursal.

"Va al CSV para Gestión" es un **estado**, no un botón: el CSV lo arma el backend a partir
de la evidencia (Tier 0 certeza + Tier 1b + pines confirmados por Google), no existe
endpoint de "marcar". Ver decisión §4.f.

Salida de Momento 2 con pendientes: modal M6 con la consecuencia concreta, p. ej.
"Quedan 61 nombres sin confirmar y 17 ubicaciones sin elegir: esas sucursales van a quedar
SIN km cuando calcules." / "Quedarme y terminarlo" / "Continuar igual".

### 3.3 Momento 3 · Calcular km

```
│   Se van a calcular los km de ida y vuelta (con Google Maps) para 869       │
│   sucursales con ubicación. Primero ves el resultado; nada se guarda hasta  │
│   que apliques.                                                             │
│                                                                             │
│   ⚠ 2 sucursales sin ubicación van a quedar sin km.                         │
│     [Resolverlas primero (recomendado)]  [Calcular igual — las 2 sin km]    │
│                                                                             │
│   [ Calcular km ]   ~1738 CONSULTAS A GOOGLE                                │
│   → modal actual "Esta acción consulta Google Maps… Se van a hacer          │
│     aproximadamente 1738 consultas (el tope por corrida es 200)…"            │
│                                                                             │
│   (tras el preview) 130 filas nuevas · 739 a actualizar · 2 sin ubicar ·    │
│   1738 consultas usadas                                                     │
│   [tabla preview idéntica: Empresa · Sucursal · Actual · Ida · Vuelta ·     │
│    Total · Origen del pin · Acción]                                          │
│   [ Aplicar a la Tabla KM… ]  → modal de confirmación actual (C6)           │
```

Si la estimación supera el tope (caso real SAN JUAN hoy), el botón queda deshabilitado con
el mismo bloqueo de `bloquearSobreTope`, texto en llano: "Calcular los km de estas 869
sucursales necesita ~1738 consultas a Google y el límite por corrida es 200. No se puede
hacer de una sola vez — avisale al administrador." (ver §5.2).

### 3.4 Cierre

Reemplaza C7 + "Finalizar":

```
│   ✓ Listo: tu Tabla KM quedó al día.                                        │
│     130 filas nuevas y 739 actualizadas. El umbral de viático y las         │
│     observaciones no se tocaron.                                            │
│                                                                             │
│   Quedan para corregir en Gestión: 265 sucursales                            │
│   [ Exportar CSV para Gestión ]                                             │
│   Pendientes que dejaste sin resolver: 61 nombres, 17 ubicaciones            │
│   (volvé a Revisar pendientes cuando quieras — el asistente recuerda todo)  │
│                                                              [ Cerrar ]     │
```

Los números salen de `AplicarDistanciasResult` (`creadas`, `actualizadas`), del `estado`
refrescado y de `worklist`/`tier1b`/`pines-sospechosos` (mismo criterio que el CSV).

---

## 4. Decisiones (tomadas con el usuario el 2026-08-20)

| # | Pregunta | Decidido | Por qué |
|---|---|---|---|
| a | ¿Qué corre automáticamente al abrir? | **El asistente se rehace entero y abre siempre con una intro que explica los 3 momentos + botón "Empezar". Tras "Empezar" corren solo los chequeos que no modifican filas** (GET de hoy + `consultar-georef` + `consultar-nominatim`, con progreso). Refrescar domicilios, auto-vincular N1 e importar quedan detrás del único botón "Traer de Gestión". | Abrir "para mirar" no cambia filas; la intro fija el modelo mental; Georef/Nominatim tardan (1 req/s) → progreso sin bloquear. |
| b | ¿3 momentos o stepper más corto? | **3 momentos** (Traer de Gestión / Revisar pendientes / Calcular km), mismos estados y bloqueos. | Modelo mental del operador. |
| c | ¿Dónde viven el CSV y la auditoría completa con Google? | **CSV al pie de Momento 2 y repetido en el cierre; auditoría completa como "Más chequeos ▾" al pie de Momento 2** (mismo `BotonConsumoGoogle`). | El CSV es parte del cierre; la auditoría completa (560 consultas en SAN JUAN) es secundaria pero accesible. |
| d | ¿Endpoint agregador o composición en frontend? | **Componer en frontend** (8 GET en paralelo). Se revisa solo si la apertura supera ~3 s medidos en Fase 2. | Cero backend. |
| e | ¿"Traer de Gestión" importa las nuevas con actividad? | **Sí**, con el número visible antes de apretar y la lista plegada. Ex-clientes nunca automáticos (toggle en "ver detalle"). | Es "traer de Gestión" en el modelo mental; hoy son 3 botones en 3 pasos. |
| f | "Marcar para corregir en Gestión" | **Estado "Va al CSV para Gestión"**, sin botón. | No hay endpoint; el CSV sale de la evidencia. |
| g | SAN JUAN bloqueado para distancias (1738 > tope 200) | **Se mantiene el bloqueo con texto llano. Se registra como pedido aparte: explorar ruteo gratuito sobre OpenStreetMap (OSRM / OpenRouteService)** — ver §5.2. | Georef/Nominatim no rutean; cambiar a OSM cambia la fuente de los km que hoy facturan → decisión de negocio fuera de este rediseño. Alternativas también registradas: subir `GOOGLE_MAPS_MAX_CALLS_PER_RUN` por `.env` (sin código) o preview por tandas (backend). |
| h | Bug de paginación en Importar (§5.1) | **Se corrige en Fase 1** (frontend, `fetchCatalogoCompleto` paginando de a 200). | Sin esto los números de Momento 1 son falsos. |
| i | Patrón "ver detalle ▾" | **Link subrayado que despliega** (patrón de "Mostrar también ex-clientes"), con `aria-expanded`. | Sin componente nuevo. |
| j | Filtro de la bandeja | **Reusar `SegmentedControl`** (Todos · Pines rotos · Nombres · Ubicaciones). | Precedente validado en Inicio. |

## 5. Hallazgos del relevamiento (además de la carga cognitiva)

1. **Importar solo lee la primera página.** `buscarSucursalesSiges` pide `size=200` y usa
   `page.items` sin paginar; el endpoint topea `size` en 200. SAN JUAN tiene 948 sucursales:
   la pantalla muestra "0 NUEVAS ACTIVAS / 27 EX-CLIENTES / 173 YA CARGADAS" (=200) mientras
   el diagnóstico dice 427 nuevas; PENTACOM muestra 34 nuevas activas contra 132 reales.
   Consecuencia visible: al apretar "Siguiente" desde Importar salta el modal "Quedan 427
   sucursales sin importar" en una pantalla que dice que no hay nada para importar.
   Capturas `sanjuan-02-importar.png`, `sanjuan-02c-modal-paso-incompleto.png`.
2. **SAN JUAN no puede calcular distancias.** El preview estima sobre todos los destinos
   ubicables (869 → 1738 consultas; `calcular_distancias_siges.py`, `_armar_destinos`) y
   `verificar_tope` rechaza la corrida entera si supera `GOOGLE_MAPS_MAX_CALLS_PER_RUN`
   (default 200); la UI lo bloquea con "Avisale al administrador". No es un problema de UI.
   Los km salen de Google Distance Matrix (US$5/1000 elementos, 10.000 gratis/mes por SKU —
   `INTEGRACIONES_EXTERNAS.md §11`): 1738 elementos ≈ US$8,70 de lista.
   **Pedido aparte registrado (decisión §4.g)**: evaluar ruteo gratuito sobre
   OpenStreetMap (OSRM / OpenRouteService). Condiciones a verificar antes de adoptarlo: el
   servidor público de OSRM no admite uso intensivo/productivo (habría que hostear o usar
   un tier con cuota), y la distancia por red vial de OSM **no coincide** con la de Google
   — cambia la fuente de los km que hoy se facturan (decisión de negocio, no técnica).
   Alternativas sin código: subir el tope por `.env` para la corrida; con backend: preview
   por tandas de 200. Captura `sanjuan-05b-distancias-calcular-igual.png`.
3. **Botones con estimación 0 ejecutan sin modal** (por diseño de `BotonConsumoGoogle`:
   todo en caché = sin gasto). Hoy en SAN JUAN "Buscar ubicaciones (2 sucursales)" y
   "Auditar residuo con Google (299 sucursales)" se ejecutan al primer clic. Correcto según
   la regla (no gastan), pero escriben resultados; en la propuesta el label lo dice igual
   ("SIN COSTO — TODO ESTÁ EN CACHÉ") y el ítem explica qué va a pasar. No se cambia la regla.
4. **Filas sin match y sin candidato no se ven en ningún paso** (29 en PENTACOM de las
   cuales solo 8 tienen candidato N2; SAN JUAN 66 vs 61). Solo aparecen en la caja
   "no encontradas" después de apretar "Actualizar desde Gestión" (G3). La bandeja las
   muestra como ítems N1 con esa misma fuente.
5. Typo en Diagnóstico: "17 direcciónes".
6. El diagnóstico dice "66 pines del mapa que no coinciden" y la lista trae 69: el
   diagnóstico cuenta solo sucursales con actividad reciente (`estado_asistente_km.py`
   salta ex-clientes) y `ListarPinesSospechosos` recorre todas las sucursales del
   prestador sin ese filtro (`pines_sospechosos.py`). La bandeja muestra el listado (69)
   y el resumen usa ese mismo número, para que no haya dos cifras distintas en pantalla.
7. Tooltip del botón de entrada desactualizado ("geocodificar → calcular km → auditar pines").
8. Texto técnico en la vista por defecto detectado en vivo: "Tier 0", "Georef", "Nominatim",
   "reverse geocoding", "latlon_invertidas", "fuera_de_argentina", "pin_compartido",
   "GEOMETRIC_CENTER", "ROOFTOP", "RANGE_INTERPOLATED", "match parcial", "worklist",
   "severidad ALTA/MEDIA", "rectángulo continental+insular", "N1/N2" (en docs y nombres de
   tarjeta 3a/3b), "score %". Todos tienen destino en "ver detalle" (§2).

---

## 6. Lo que NO cambia (reglas de producto conservadas)

- Toda acción paga pasa por `BotonConsumoGoogle`: número de consultas visible antes, modal
  de confirmación, tope por corrida, `bloquearSobreTope` donde corresponde.
- N2 jamás auto-confirma (cada ítem N2 es un clic humano; "Sí, es esta" = `confirmar`).
- El geocode nunca pisa un pin de Gestión ni una coordenada manual sin humano; "sin ubicar"
  sigue siendo estado explícito (U1/U3), nunca coordenadas inventadas.
- Cálculo masivo: preview con diff → aplicar (el apply no llama a Google); `umbral_viatico`
  y `observaciones` no se pisan; tabla de preview idéntica (Ida/Vuelta/Total intactos).
- Atribución ODbL visible en la bandeja siempre que haya ítems P2/P2b y en su detalle.
- Siges read-only: el CSV para Gestión es parte del cierre.
- Fuera de alcance: semántica de km (ida/vuelta/total), ALT002, cualquier cambio de backend.

---

## 7. Plan de Fase 1 (solo tras el OK)

El asistente se **rehace entero** (decisión §4.a); se conservan `BotonConsumoGoogle` y
`CandidatosPicker` tal cual. Archivos (todos ≤300 líneas, §4 de la guía):
`tabla-km-wizard.tsx` (marco + stepper de 3), `tabla-km-wizard-tipos.tsx`,
`tabla-km-wizard-intro.tsx` (intro + chequeos, 3.0), `tabla-km-wizard-traer.tsx`
(3.1), `tabla-km-wizard-bandeja.tsx` + `tabla-km-wizard-bandeja-items-*.tsx` (3.2, un archivo
por familia P/N/U), `tabla-km-wizard-bandeja-datos.ts` (composición de los GET + ranking,
funciones puras testeables), `tabla-km-wizard-calcular.tsx` (3.3, cambios mínimos),
`tabla-km-wizard-cierre.tsx` (3.4), `tabla-km-wizard-confirmar-google.tsx` (sin cambios).
Se eliminan los archivos de pasos que dejan de existir (diagnóstico, importar, matching,
geocodificar, pines-*), cuyo contenido queda redistribuido según §2.

Commits atómicos (`feat(liquidaciones): …`), specs `tabla-km-*.spec.ts` actualizados si
cambia un selector, capturas "después" en `capturas-e2e-wizard-2026-08-20/despues/`, y
actualización de las secciones de UI en `GEOVALIDACION_TABLA_KM.md` y
`MATCHING_SUCURSALES_TABLA_KM.md`.

Verificación Fase 2: checklist §2 ítem por ítem (columna ✓ F2), `tsc` + `eslint` +
Playwright verdes, recorrido e2e PENTACOM + SAN JUAN sin escrituras ni llamadas a Google
(mismo método que §0).

---

## 8. Fase 1 + Fase 2 — qué se hizo y cómo se verificó (2026-08-20)

**Código** (`frontend/src/features/liquidaciones/`, todos los archivos ≤300 líneas):
`components/tabla-km-wizard.tsx` (marco + stepper de 3 + modal de consecuencia),
`-tipos.tsx`, `-intro.tsx` (intro + pantalla de chequeos), `-traer.tsx`, `-bandeja.tsx`
(+ `-bandeja-pines.tsx`, `-bandeja-nombres.tsx`, `-bandeja-ubicaciones.tsx`), `-calcular.tsx`,
`-cierre.tsx`, `-ui.tsx` (VerDetalle, FilaBandeja, EnlaceMaps, Aviso), `-confirmar-google.tsx`
(sin cambios); `hooks/use-asistente-km.ts` (8 GET en paralelo + chequeos gratis);
`lib/asistente-km-bandeja.ts` (composición y ranking puros) y `lib/asistente-km-textos.ts`
(traducciones). `api/siges-api.ts`: `listarTodasSucursalesSiges` pagina de a 200 (fix §5.1).
Eliminados: `-diagnostico`, `-importar`, `-matching`, `-geocodificar`, `-pines*`.
`CandidatosPicker` (`tabla-km-lugar-modal.tsx`) se conserva intacto para el flujo por fila de la
Tabla KM; dentro del asistente las opciones se presentan traducidas (`ItemUbicacionElegir`).
Backend: cero cambios.

**Comandos y salidas reales** (host Windows, `frontend/`):
- `npx tsc --noEmit -p tsconfig.json` → sin errores.
- `npx eslint <archivos nuevos/cambiados>` → 0 errores, 0 warnings.
- `PW_PORT=3011 npx playwright test tests/tabla-km-wizard.spec.ts tests/tabla-km-layout.spec.ts tests/tabla-km-modal-maps.spec.ts` → **4 passed** (los 2 specs existentes + 2 nuevos). `PW_PORT` se agregó a
  `playwright.config.ts` porque el 3001 lo ocupa el contenedor `stc_api` de otro proyecto.
- Recorrido en vivo SAN JUAN (`capturas-e2e-wizard-2026-08-20/despues/`, 24 archivos): únicas
  requests no-GET de la sesión = `POST /api/auth/login`, `POST …/tier1/consultar-georef`,
  `POST …/tier1b/consultar-nominatim` (las dos últimas son los chequeos gratis que el diseño
  dispara tras "Empezar"; en SAN JUAN estaban cacheadas del piloto → cero llamadas externas). Cero
  Google, cero escrituras en la Tabla KM.

**Entorno (hallazgo de la sesión)**: los contenedores corren en WSL y montan una copia aparte del
repo (`/home/ivan/proyectos/helpdesk-manager`); los archivos de la rama se copiaron ahí para
rebuildear el frontend. Ver memoria `project_docker_runs_in_wsl_separate_repo_copy`.

**Recorrido en vivo PENTACOM** (autorizado por el usuario; "Empezar" hizo llamadas reales a Georef —
gratuitas, tope 200 por corrida — y la bandeja mostró "Quedan 267 pines por chequear (sin costo)" con
el botón "Seguir chequeando"): 20 archivos en `despues/pentacom-*`. Resultado real: "Quedan 16 pines
rotos (16 van al CSV para Gestión), 8 nombres por confirmar, 71 ubicaciones por resolver, 58 pines a
verificar"; Momento 3 bloqueado con el tooltip "Falta la sucursal base de despacho" (🔒), banner
bloqueante en Momento 1. Únicas requests no-GET: login + los dos chequeos gratis.

**Pendiente**: validación final del usuario con las capturas antes/después y decisión sobre el
merge de la rama.
