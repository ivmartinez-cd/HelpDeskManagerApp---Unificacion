# Master Prompt — Rediseño UX del Asistente de KM (Tabla KM, liquidaciones)

Rediseñar el **Asistente de KM** (wizard APB de la pantalla
`/liquidaciones/configuracion/tabla-km`) para que deje de marear: hoy expone la maquinaria
interna (niveles de matching, tiers de geovalidación, fuentes Georef/Nominatim/Google) como
pasos y secciones que el usuario tiene que entender y operar. El trabajo real del usuario son
tres cosas: **traer las sucursales del prestador desde Gestión con sus datos y coordenadas,
resolver lo que necesita su decisión, y calcular los km**. El asistente tiene que estar
organizado alrededor de eso.

Generado el 2026-08-20 a partir de los docs reales del repo
(`GEOVALIDACION_TABLA_KM.md`, `GEOLOCALIZACION_TABLA_KM.md`,
`MATCHING_SUCURSALES_TABLA_KM.md`), las capturas e2e
(`docs/liquidaciones/capturas-e2e-wizard-2026-08-17/`) y feedback textual del usuario:
*"ya el primer paso te da un montón de opciones para tocar y te marea, y hay tantas
vinculaciones, chequeos y cosas que realmente marea"*.

**Es un rediseño de presentación, no de lógica**: el backend está verificado con datos
reales (piloto SAN JUAN 2026-08-19) y no se toca.

---

```text
[ROL]
Actuá como Senior Product Designer + Frontend Engineer del monorepo
HelpDeskManager-Unificacion (Next.js App Router + TypeScript + Tailwind, design system propio
en frontend/src/shared/components/ui/), con expertise en UX writing en lenguaje llano y en
reducción de carga cognitiva en flujos operativos. Conocés y aplicás ARCHITECTURE_GUIDE.md y
CLAUDE.md como reglas obligatorias. Respondés en español de Argentina, directo y sin relleno.
Cero alucinaciones: todo dato que muestre la UI sale de los endpoints reales, y toda
afirmación sobre el wizard actual se verifica recorriéndolo en vivo, no de memoria.

[CONTEXTO]
Qué es el Asistente de KM (verificado contra docs y capturas, re-verificar en vivo en Fase 0):

- Wizard modal que se abre desde el botón "Asistente de KM →" de la pantalla Tabla KM
  (liquidaciones). Pasos según los docs al 2026-08-19: Diagnóstico → Importar → Sin match →
  Ubicar → Distancias → Pines (el paso "Sin match" se agregó el 19-08; las capturas e2e del
  17-08 muestran 5 pasos).
- Componentes: frontend/src/.../tabla-km-wizard-*.tsx — entre ellos
  tabla-km-wizard-matching.tsx (Sin match) y el paso Pines dividido en 4 archivos
  (tabla-km-wizard-pines*.tsx: -tier0, -tier1, -worklist y el orquestador PasoPines).
- Backend que el wizard consume (NO se modifica): refresh/vinculación desde Siges, matching
  (auto-vincular-n1, propuestas, confirmar/rechazar), geocodificar-faltantes, coordenadas
  (revisión de ambiguos), calcular-distancias preview/aplicar, geovalidación tier0 / tier1 /
  tier1b / worklist (+ export CSV), auditar-pines / pines-sospechosos. Todo verificado en
  real con SAN JUAN (2026-08-19).

El problema (la queja es del usuario real del asistente):

- El paso 1 (Diagnóstico) ya abre con ~4 hallazgos y 3 CTAs distintos ("Ir a Importar",
  "Ir a Ubicar", "Ver cuáles") más "Siguiente" — demasiadas opciones antes de entender nada.
- El paso Ubicar apila subsecciones 2a/2b/2c con 4 chips de conteo simultáneos
  (ej. "0 direcciones actualizadas / 334 vinculadas a Gestión / 334 sin cambios /
  153 no encontradas en Gestión") y cajas de texto explicativo largas.
- El paso Pines acumuló 4 secciones apiladas (Geovalidación básica Tier 0, Provincia del pin
  vs. Gestión (Georef), Segunda opinión (Nominatim), Worklist final Tier 2) con jerga técnica
  (tier, severidad, atribución ODbL) y evidencia extensa siempre visible.
- El usuario tiene que entender la implementación (qué es N1 vs N2, qué tier corre primero,
  qué fuente confirma a cuál) para saber qué botón tocar. Su modelo mental real es:
  1) traer/actualizar las sucursales del prestador desde Gestión, 2) validar que cada una
  tenga una ubicación confiable, 3) que los km salgan calculados.

Reglas de producto YA establecidas que el rediseño conserva sí o sí:

- Nada gasta Google sin confirmación previa con el número de consultas visible ANTES
  (modal BotonConsumoGoogle + tope GOOGLE_MAPS_MAX_CALLS_PER_RUN + cache).
- El geocode nunca pisa un pin de Siges ni una coordenada manual sin confirmación humana;
  los matches N2 SIEMPRE requieren confirmación humana; "sin ubicar" es un estado explícito
  y visible, jamás coordenadas inventadas.
- El cálculo masivo de distancias es preview con diff → aplicar (el apply no re-llama a
  Google). umbral_viatico y observaciones nunca se pisan.
- Atribución ODbL obligatoria donde se muestren datos derivados de Nominatim/OpenStreetMap
  (obligación de la política de uso, no estética).
- Siges es read-only: la corrección final de datos rotos se hace en Gestión — el CSV de
  worklist para Gestión es parte del cierre del flujo, no un extra.

[OBJETIVO]

FASE 0 — RELEVAMIENTO + PROPUESTA UX (bloqueante; se valida con el usuario antes de codear):

  1. INVENTARIO REAL: recorrer el wizard EN VIVO (contenedores levantados) con PENTACOM y
     SAN JUAN, pantalla por pantalla. Producir una tabla con CADA elemento visible (botón,
     chip, contador, texto, sección) clasificado en: (a) decisión humana imprescindible,
     (b) maquinaria automatizable (puede correr sola o agrupada en un solo botón),
     (c) información plegable a "ver detalle", (d) redundante/eliminable. Esta tabla es
     además la lista de paridad funcional que Fase 2 verifica.
  2. PROPUESTA DE REDISEÑO organizada por el modelo mental del usuario, en 3 momentos:
     "Traer de Gestión" → "Revisar pendientes" → "Calcular km". Wireframes textuales por
     pantalla CON los textos finales propuestos (UX writing real, no placeholder) y tabla de
     mapeo "elemento actual → dónde queda en la propuesta" (nada desaparece sin destino
     explícito).
  3. El norte obligatorio de la propuesta (el diseño exacto sale del relevamiento, esto no
     se negocia):
     - UNA acción principal por pantalla; el resto plegado o secundario visualmente.
     - Lenguaje llano: cero "Tier / Georef / Nominatim / N1 / N2 / worklist / severidad" en
       la vista por defecto — hablar de "chequeos automáticos", "dos fuentes independientes
       coinciden", "según Google". Los nombres técnicos pueden vivir en el "ver detalle".
     - Todo lo GRATIS corre junto, con un solo botón (o solo al abrir el asistente, a
       validar en 0.4): actualizar desde Gestión + auto-vincular inequívocos + chequeos
       tier0/1/1b cacheados. Lo PAGO (Google) siempre aparte, con costo visible y
       confirmación — regla existente que no cambia.
     - UNA bandeja única de pendientes rankeada en vez de hallazgos repartidos por
       secciones: cada ítem = una decisión con su acción clara ("¿Este nombre es esta
       sucursal de Gestión? Sí/No", "Elegí la ubicación correcta", "Usar la dirección
       escrita", "Marcar para corregir en Gestión").
     - Estado de cierre explícito: el asistente dice cuándo está todo listo y qué quedó
       pendiente ("N sucursales para corregir en Gestión — exportá el CSV").
  4. DECISIONES a validar con el usuario (proponer default, no decidir en silencio):
     a. ¿Los chequeos gratis corren automáticamente al abrir el asistente, o con un botón
        "Analizar" único? (default propuesto: automático al abrir, con indicador de
        progreso — nada de eso gasta Google).
     b. ¿Los 6 pasos actuales colapsan a los 3 momentos, o se mantiene un stepper más corto?
        (default: 3 momentos).
     c. Dónde viven el export CSV para Gestión y la auditoría completa con Google (default:
        dentro del cierre de "Revisar pendientes", no como sección aparte).
     d. Si la bandeja única necesita un endpoint agregador de solo lectura o se compone en
        el frontend con los endpoints existentes (default: componer en frontend; un
        endpoint nuevo solo si la latencia lo justifica, y es read-only).
  Entregable de Fase 0: docs/liquidaciones/REDISENO_UX_ASISTENTE_KM.md con inventario,
  propuesta, mapeo y decisiones. FRENAR ahí hasta el OK del usuario.

FASE 1 — IMPLEMENTACIÓN (recién después del OK):
  - Sobre los componentes existentes del wizard (refactor de tabla-km-wizard-*.tsx), mismo
    punto de entrada (el botón "Asistente de KM" abre la versión nueva — no conviven dos
    asistentes).
  - Backend intacto. Si 0.4.d aprobó un endpoint agregador: read-only, Page[T], permisos
    existentes del módulo, y es lo ÚNICO que se agrega.
  - Design system compartido (Button/Input/Modal/Badge y tokens semánticos), tamaños §4
    (archivo ≤300 líneas — el paso Pines ya se dividió una vez por esto), textos EXACTOS del
    doc de propuesta aprobado.

FASE 2 — VERIFICACIÓN (parte del entregable):
  - Paridad funcional contra el inventario de 0.1: toda capacidad actual sigue accesible
    (aunque viva plegada). Checklist ítem por ítem en el doc.
  - Recorrido e2e en vivo con PENTACOM y SAN JUAN, capturas nuevas en
    docs/liquidaciones/capturas-e2e-wizard-<fecha>/ (antes/después comparables).
  - tsc + eslint verdes; specs Playwright existentes de tabla-km
    (frontend/tests/tabla-km-*.spec.ts) verdes — si un selector cambió, se actualiza el
    spec en el mismo cambio.
  - CERO datos modificados y CERO llamadas nuevas a Google durante la verificación de UI:
    los chequeos gratis están cacheados del piloto; cualquier acción paga se muestra pero
    no se ejecuta.
  - Validación final con el usuario mirando las capturas: la medida de éxito es que el
    flujo se entienda sin explicación ("abro, veo qué falta, decido, calculo, listo").

[FORMATO]
- Todo texto al usuario en español de Argentina, directo, sin cortesías (regla de CLAUDE.md).
  Los textos de la UI, en lenguaje llano de operador, no de desarrollador.
- Fase 0 entrega UN doc (docs/liquidaciones/REDISENO_UX_ASISTENTE_KM.md) y espera
  aprobación. Fase 1 en commits atómicos en inglés (feat(liquidaciones): ...).
- Al cerrar: actualizar las secciones de UI de GEOVALIDACION_TABLA_KM.md y
  MATCHING_SUCURSALES_TABLA_KM.md para que no describan pantallas que ya no existen, y
  resumen final con comandos y salidas reales (tsc, eslint, Playwright) + capturas.

[RESTRICCIONES]
Operativas (innegociables, de CLAUDE.md):
- La DB de dev tiene datos reales de producción. Este rediseño es de PRESENTACIÓN: ninguna
  corrida que escriba datos (importar, aplicar distancias, auditar) se ejecuta en real
  durante el desarrollo sin acuerdo explícito.
- Google Maps es API PAGA: no escribir pruebas ni efectos que geocodifiquen o auditen de
  verdad; la UI se verifica con el cache existente del piloto SAN JUAN.
- Sin hot reload: docker restart del frontend (build completo — esperar el 200) y verificar
  con curl que el cambio esté servido antes de dar por buena una captura.
- DISABLE_BACKGROUND_JOBS=true si se toca cualquier cosa que un job ejecute.

De producto:
- NINGUNA capacidad actual desaparece: se reorganiza, se agrupa o se pliega. La tabla de
  mapeo de 0.2 es el contrato.
- Toda acción paga conserva el modal de costo previo con el número visible ANTES de
  ejecutar. N2 jamás auto-confirma. El geocode jamás pisa un pin sin humano. El preview→apply
  del cálculo masivo se mantiene. La atribución ODbL queda visible en cualquier vista que
  muestre datos derivados de Nominatim, aunque el detalle técnico esté plegado.
- La semántica de km (ida/vuelta/total) y ALT002 están FUERA de alcance: no se toca ni un
  campo ni un texto que cambie su significado.

De arquitectura/UI:
- Design system de shared/components/ui/ y tokens semánticos — nada de colores Tailwind
  literales ni componentes reimplementados dentro del módulo.
- Tamaños §4; accesibilidad real: label/aria en cada control interactivo.
- Los conteos y números que muestre la UI salen SIEMPRE de las respuestas de los endpoints —
  jamás hardcodeados ni estimados. Cero dependencias npm nuevas sin justificación explícita.

[EJEMPLO]
Reescritura tipo (números del piloto real SAN JUAN, solo como referencia de tono):

ANTES (paso Pines, sección "Segunda opinión (Nominatim / OpenStreetMap)"):
  "Hallazgo severidad alta — provincia del pin incompatible confirmada por reverse
   geocoding. Atribución ODbL: © OpenStreetMap contributors."

DESPUÉS (mismo dato, en la bandeja de pendientes):
  "El pin de esta sucursal está en La Pampa, pero su dirección dice San Juan.
   Dos fuentes independientes lo confirman.
   [Ver en el mapa]  [Marcar para corregir en Gestión]      ver detalle técnico ▾"
  (al pie de la lista: "Datos de mapa © OpenStreetMap contributors")

Flujo objetivo de referencia (el definitivo sale de Fase 0):
  1 · Traer de Gestión   "Actualizamos los datos de 334 sucursales y vinculamos 82
                          automáticamente. 64 nombres necesitan tu confirmación."
  2 · Revisar pendientes  Una lista, una decisión por ítem, lo grave primero
                          (ej. "El pin de 'Escuela 20 de Junio' está en Madrid, España").
  3 · Calcular km         Preview con diff → Aplicar. "Listo: tu Tabla KM quedó al día.
                          Quedan 4 sucursales para corregir en Gestión → Exportar CSV."
```

---

## Notas de contexto para quien use este prompt (fuera del prompt en sí)

- **La queja es del usuario real y es de carga cognitiva, no de bugs**: la lógica funciona y
  está verificada en real (piloto SAN JUAN: 663 hallazgos Tier 0, 192 confirmados por dos
  fuentes gratis, 69 pines confirmados por Google, CSV de 265 filas para Gestión). Lo que
  falla es que la UI cuenta la historia de la implementación (matching N1/N2, tiers 0/1/1b/2,
  qué fuente confirma a cuál) en vez de la historia del usuario (traer → validar → calcular).
- **Por qué "propuesta primero"**: el usuario eligió explícitamente validar la propuesta UX
  antes de codear. Fase 0 es bloqueante de verdad — el error caro acá sería rediseñar en una
  dirección que a él también lo maree, pero distinto.
- **Por qué "simple por defecto"**: también elegido explícitamente por el usuario. La
  evidencia técnica no se borra: se pliega. El operador avanzado la sigue teniendo a un click.
- **El inventario de 0.1 es el seguro contra pérdida de funcionalidad**: el riesgo típico de
  "simplificar" es que desaparezca algo que alguien usaba (export CSV, auditoría completa,
  re-consultar fuentes). Por eso el mapeo "elemento actual → destino" es contrato y la Fase 2
  lo verifica ítem por ítem.
- **Costo Google**: el wizard existente ya resolvió bien la disciplina de costo (estimación
  previa, cache, topes). El rediseño la hereda tal cual; ninguna prueba de UI debería generar
  una sola llamada nueva — todo lo gratis del piloto está cacheado.
- **Los 6 pasos actuales no son sagrados**: Diagnóstico/Importar/Sin match/Ubicar/Distancias/
  Pines es la secuencia de construcción de la feature, no el flujo mental del operador. Que
  la propuesta los colapse a 3 momentos es el default esperado, salvo que el relevamiento de
  Fase 0 muestre una razón real para no hacerlo.
