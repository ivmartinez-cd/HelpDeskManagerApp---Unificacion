# Master Prompt — Geolocalización asistida y cálculo de KM ida/vuelta en la Tabla KM

Mejorar la búsqueda de direcciones de clientes en Google Maps para la **Tabla KM de
liquidaciones**: que el sistema encuentre solo el lugar correcto (hoy, si la sucursal no tiene
coordenadas en Siges o el pin está mal, todo es manual), y que calcule el kilometraje real del
técnico **base → cliente → base**.

Generado el 2026-08-14 a partir del análisis del código real. **La mitad de la feature ya
existe**: hay un cálculo automático de distancias por Google Maps (Distance Matrix, batch 25,
upsert a `tabla_km`) con la base del prestador salida de Siges. Lo que NO existe es geocoding
(las sucursales sin coordenadas se saltean y quedan en un contador `sinCoords`), validación de
pines dudosos, y la vuelta a base. Y hay una mina enterrada: cambiar la semántica de los km
rompería la regla ALT002 del motor de liquidaciones — por eso la Fase 0 es bloqueante.

---

```text
[ROL]
Actuá como arquitecto/desarrollador senior full-stack del monorepo HelpDeskManagerApp---Unificacion
(FastAPI + SQLAlchemy async + Alembic + Next.js App Router, arquitectura módulo→capa
domain/application/infrastructure/presentation). Conocés y aplicás ARCHITECTURE_GUIDE.md, CLAUDE.md
y ADR-018 como reglas obligatorias. Respondés en español de Argentina, directo y sin relleno.
Cero alucinaciones: semánticas de negocio y estados de APIs de Google se confirman con datos
reales / documentación oficial, no se asumen.

[CONTEXTO]
Lo que YA existe, verificado contra el código (no supuesto):

- Entidad `TablaKm` (`liquidaciones/domain/entities/tabla_km.py`): kms esperados por par
  Empresa+Sucursal del prestador, con `domicilio_cliente`/`localidad_cliente`/
  `provincia_cliente`, `kms_recorrido`, `kms_a_facturar`, `umbral_viatico` (default 30.0,
  configurable por excepción), `aplica_viatico`, `url_maps`, `latitud_destino`/
  `longitud_destino`. Los nombres empresa/sucursal son texto libre que se matchea
  case-insensitive contra `Incidente` — no hay FK.
- Cálculo automático EXISTENTE (`application/use_cases/calcular_distancias_siges.py` +
  endpoint `POST /siges/prestador/{id}/calcular-distancias` en `config_routers/siges.py`):
  base = coordenadas de la sucursal base del prestador en Siges (`siges_base_sucursal_id`;
  error si falta o no tiene coords), destinos = sucursales cliente del PST con coords en Siges,
  Distance Matrix API en batches de 25, y upsert: crea filas nuevas o pisa `kms_recorrido`/
  `aplica_viatico`/`kms_a_facturar`/`url_maps`/coords destino (preserva `umbral_viatico`).
  Las sucursales SIN coords en Siges se saltean y solo se cuentan (`sinCoords` en el modal).
  ⚠️ El upsert pisa SIN previsualización: una corrida cambia la base de facturación esperada.
- Gateway (`infrastructure/google_maps/httpx_google_maps_gateway.py`): Distance Matrix API,
  modo driving, httpx timeout 30 s, errores → `ExternalServiceError`. UNA operación:
  `distancias_km(origin, destinations) -> list[float | None]` — es DISTANCIA DE IDA (un solo
  tramo A→B); hoy nada calcula la vuelta. Settings: `google_maps_api_key` (existe). ⚠️ Esta
  integración NO figura en `docs/INTEGRACIONES_EXTERNAS.md` (se le escapó al inventario del
  refactor ADR-018) — hay que agregarla.
- Datos de dirección disponibles desde Siges (`infrastructure/siges/query.py`): `S.Domicilio`,
  `Ciudad.DesCiudad` (localidad), `Ciudad.DesProvincia`, `S.Latitud`/`S.Longitud` (texto, con
  coma decimal — se parsean con replace(",", ".")).
- Motor de reglas ALT002 (`domain/services/motor_reglas/alt002_km.py`): compara los km
  COBRADOS por el PST en cada incidente contra `tabla_km.kms_a_facturar` (acepta el valor raw
  o su ceil, con tolerancia). ⚠️ ESTA es la mina: si `kms_recorrido`/`kms_a_facturar` cambian
  de convención (ida → ida y vuelta), TODOS los esperados se duplican y ALT002 alertaría en
  masa contra facturas históricas. Cualquier cambio de semántica es una decisión de negocio
  explícita, jamás un efecto colateral del cálculo nuevo.
- UI actual: pantalla `/liquidaciones/configuracion/tabla-km` (`tabla-km-config.tsx`,
  `tabla-km-modales.tsx` — el modal "Editar entrada Tabla KM" del screenshot del usuario, con
  URL Maps + "Abrir en Maps" + "Ver pin" + coords Siges readonly), modal de base del prestador
  (`prestador-base-sucursal-modal.tsx`, muestra creadas/actualizadas/sinCoords).
- Dato de referencia real (del screenshot): BAHIA (Bahía Blanca) → Adecoagro Las Horquetas,
  Ruta Nacional 33 KM 167, Guaminí: kms_recorrido = 199,294 — consistente con UNA ida
  Bahía Blanca→Guaminí, lo que sugiere que la convención vigente es POR TRAMO (confirmar en
  Fase 0, no asumir).

[OBJETIVO]

FASE 0 — INVESTIGACIÓN Y DECISIONES (bloqueante):
  1. CONFIRMAR LA CONVENCIÓN DE KM VIGENTE con datos reales, no con intuición: tomar 5-10
     filas de `tabla_km` de 2-3 prestadores y cruzarlas contra `cant_km_cobrado` de incidentes
     reales de liquidaciones ya analizadas (la DB de dev tiene datos reales). Si los PST
     facturan ≈1× la tabla, la convención de negocio es "por tramo/ida" y se mantiene para
     `kms_a_facturar`; si facturan ≈2×, la tabla ya representa ida y vuelta. Salida escrita:
     qué representa HOY cada campo y qué campo/columna nueva representa la vuelta (ver 5.a).
  2. ESTADO DE LA CUENTA GOOGLE: verificar contra la documentación oficial y la consola qué
     APIs tiene habilitadas la key (`google_maps_api_key`) y su pricing vigente — en
     particular si Distance Matrix clásica sigue disponible para esta cuenta o si corresponde
     migrar a Routes API `computeRouteMatrix` (Google la viene señalando como sucesora;
     verificar el estado real al momento de ejecutar, no asumirlo), y qué API de geocoding
     conviene (Geocoding API vs Places Text Search) para direcciones rurales argentinas tipo
     "Ruta Nacional 33 KM 167, Guaminí". Documentar costo por 1000 requests de cada una.
  3. MUESTREO DE CALIDAD: para ~20 sucursales con coords en Siges, geocodificar el domicilio
     (`Domicilio + DesCiudad + DesProvincia + Argentina`) y medir la distancia entre el pin de
     Siges y el geocode. Con esa distribución, calibrar el umbral de "pin sospechoso" (default
     propuesto: >5 km = revisar). Contar además cuántas sucursales del total NO tienen coords
     (los `sinCoords` reales por prestador) — es el tamaño del problema que el geocoding viene
     a resolver.
  4. DECISIONES a validar con el usuario (proponer default, no decidir en silencio):
     a. Dónde vive la vuelta. Default propuesto: `kms_recorrido`/`kms_a_facturar` CONSERVAN la
        convención confirmada en 0.1 (no se rompe ALT002 ni el histórico); se agregan columnas
        `kms_ida` y `kms_vuelta` (la vuelta calculada como tramo B→A real, no ida×2 — puede
        diferir por rutas/manos únicas) y la UI muestra "ida", "vuelta" y "total recorrido
        técnico". Si el usuario decide que la facturación pasa a ida+vuelta, eso es un cambio
        de negocio con migración de datos + ajuste de ALT002 + aviso a la TL — hacerlo en fase
        propia, jamás mezclado con el geocoding.
     b. Procedencia y autoridad de coordenadas. Default: campo `coords_origen`
        ('siges' | 'geocode' | 'manual') + `geocode_formatted_address` + fecha; el geocode
        NUNCA pisa coords Siges o manuales automáticamente — solo llena vacíos automático, y
        para discrepancias propone con confirmación humana.
     c. Previsualización obligatoria del cálculo masivo. Default: sí — el bulk pasa a dos
        pasos (preview con diff km viejo→nuevo por fila, sin persistir; apply confirma lo
        previsualizado sin re-llamar a Google). El per-fila puede ser directo.
     d. Control de costo. Default: cache local de geocodes (dirección normalizada → resultado,
        no re-consultar si no cambió el domicilio), tope de llamadas por corrida
        (`GOOGLE_MAPS_MAX_CALLS_PER_RUN`, default 200) y contador visible en el resultado.
  Validar 0.1-0.4 con el usuario antes de codear.

FASE 1 — BACKEND (módulo liquidaciones, sobre lo existente — no crear módulo nuevo):
  - domain: puerto nuevo `GeocodingGateway` (`geocode(direccion) -> list[GeocodeCandidato]`
    con formatted_address, lat/lon, tipo/precisión) junto al `GoogleMapsGateway` existente
    (que suma la vuelta: `distancias_km_ida_vuelta` o equivalente según 0.2 — si se migra a
    Routes API, adapter nuevo detrás del MISMO puerto). Servicio de dominio puro para:
    normalización de dirección (armado del query con domicilio+localidad+provincia+país),
    elección de candidato automático solo si hay uno inequívoco, y cálculo de discrepancia
    pin-vs-geocode (haversine — sin llamar a Google para validar).
  - application: use cases `GeocodificarSucursales` (llena vacíos: sucursales sin coords →
    candidatos; auto-resuelve inequívocos, deja ambiguos para revisión), `ResolverCoordenadas`
    (guardar la elección humana: candidato o coords manuales, con procedencia),
    `PreviewCalcularDistancias` / `AplicarCalcularDistancias` (el two-step de 0.4.c —
    refactor del `CalcularDistanciasSiges` actual conservando su semántica de upsert y el
    respeto del `umbral_viatico`), y `RevisarPinesSospechosos` (lista discrepancias > umbral).
  - infrastructure: adapter httpx del geocoding (misma key, timeout 30 s, errores →
    `ExternalServiceError`, sin retries); tabla de cache de geocodes + columnas nuevas de
    `tabla_km` (ida/vuelta, procedencia, formatted_address) con migración Alembic reversible;
    si 0.2 dictó Routes API, adapter nuevo y el viejo se retira en el mismo commit (no
    conviven dos vías de cálculo).
  - presentation: endpoints bajo el router de config de liquidaciones existente
    (permisos del módulo liquidaciones que ya gatean la Tabla KM — no inventar permisos
    nuevos): geocodificar por prestador, resolver coords de una fila, preview/apply del
    cálculo, listado de pines sospechosos. Colecciones con `Page[T]` y tope de `size`.
  - `docs/INTEGRACIONES_EXTERNAS.md`: agregar la entrada Google Maps que faltaba (APIs
    usadas, key, timeout, sin retry, tope por corrida, cache) — corrige el hueco del
    inventario ADR-018.

FASE 2 — FRONTEND (sobre las pantallas existentes de Tabla KM):
  - En el modal "Editar entrada Tabla KM": botón "Buscar lugar" → modal de candidatos
    (formatted_address + coords + link "ver en Maps" por candidato; elegir uno guarda coords
    + procedencia 'geocode'; opción de pegar coords manuales → 'manual'); botón
    "Recalcular KM" por fila (ida y vuelta según 0.4.a); badge de procedencia de coords y
    aviso si la fila está en la lista de pines sospechosos.
  - En la pantalla de Tabla KM: acción "Geocodificar faltantes" (muestra cuántas resolvió
    solo y cuántas quedaron ambiguas para revisar, con acceso directo a resolverlas) y el
    flujo bulk en dos pasos: "Calcular distancias" → tabla de preview con diff por fila
    (km actual → km nuevo, coords nuevas, filas a crear) → "Aplicar" / "Cancelar".
  - `url_maps` regenerada para reflejar el viaje completo si 0.4.a lo pide (origin=base,
    destination=base, waypoint=cliente) — o se mantiene ida si la convención queda por tramo.
  - Mismo lenguaje visual del repo; `react-hooks/set-state-in-effect` con promise-chain.

FASE 3 — VERIFICACIÓN (parte del entregable):
  - Verde en contenedor: `uv run lint-imports` · `ruff check src tests` · `mypy src` ·
    `pytest tests/unit -q` (unit del servicio de normalización/elección de candidato y del
    cálculo de discrepancia, con fixtures de direcciones reales argentinas incluyendo la
    rural del screenshot). Frontend: `tsc` + `eslint`.
  - REGRESIÓN ALT002 obligatoria: re-analizar una liquidación real ya procesada ANTES y
    DESPUÉS de los cambios → mismos hallazgos exactos (si la convención se mantuvo, nada
    puede moverse). Si algo se movió, la Fase 0.1 estuvo mal — frenar y corregir.
  - Caso de paridad del screenshot: BAHIA → Adecoagro Las Horquetas (Guaminí): la ida
    recalculada tiene que dar ≈199 km (tolerancia por cambio de ruteo de Google); la vuelta
    B→A reportada aparte; el pin de Siges (-37.022209, -62.378251) contra el geocode de
    "Ruta Nacional 33 KM 167, GUAMINI, Buenos Aires" con su discrepancia medida.
  - Geocoding real de 2-3 sucursales sin coords en Siges: candidatos coherentes, elección
    persiste con procedencia, y el cálculo de km ahora las incluye (bajó `sinCoords`).
  - Costo: reporte de llamadas consumidas en toda la verificación (geocoding + matrix), y
    demostrar que repetir un preview NO re-llama a Google (cache + propuesta persistida).

[FORMATO]
- Todo texto al usuario en español de Argentina, directo, sin cortesías (regla de CLAUDE.md).
- Commits atómicos en inglés (`feat(liquidaciones): ...`); el two-step preview/apply y el
  geocoding pueden ser commits separados.
- Migraciones Alembic reversibles. ADR corto si se migra de Distance Matrix a Routes API o si
  cambia la convención de km (decisión 0.4.a alternativa).
- Documentar en `docs/liquidaciones/` la definición operativa nueva (qué campo es ida, qué es
  vuelta, procedencia de coords, flujo de resolución de ambiguos) y actualizar
  `INTEGRACIONES_EXTERNAS.md`.
- Al cierre: resumen con comandos y salidas reales, incluida la regresión ALT002, el caso
  BAHIA y el conteo de llamadas a Google consumidas.

[RESTRICCIONES]
Operativas (innegociables, de CLAUDE.md):
- La DB de dev tiene datos reales de producción: la Tabla KM alimenta el análisis de
  liquidaciones reales. NADA de recalcular en masa sin preview aplicado a conciencia durante
  las pruebas — trabajar sobre un prestador de prueba acordado o dejar los valores exactamente
  como estaban al terminar la verificación.
- Google Maps es una API PAGA: toda prueba cuenta llamadas. Usar el cache, respetar el tope
  por corrida, y no escribir loops de prueba que geocodifiquen todo el padrón.
- Cero escrituras SOAP/wsAyC (esta feature no las necesita — si aparece la tentación, está
  fuera de alcance). Siges solo SELECT. `DISABLE_BACKGROUND_JOBS=true` si se toca cualquier
  cosa que un job ejecute. Sin hot reload: restart de contenedor + verificación con curl.

De arquitectura (ARCHITECTURE_GUIDE.md + ADR-018):
- Google Maps/geocoding: puertos en `liquidaciones/domain/repositories/`, adapters httpx en
  `liquidaciones/infrastructure/google_maps/` — mismo patrón que el gateway existente. Nada de
  llamar APIs desde use cases o routers. Si en el futuro otro módulo necesita geocoding, ahí
  se evalúa subirlo a shared (dejarlo anotado), no ahora.
- Toda escritura pasa por use case; el preview no persiste nada salvo su propia propuesta;
  `umbral_viatico` y `observaciones` de filas existentes NUNCA se pisan (comportamiento actual
  a conservar). SQL parametrizado; `Page[T]`; sin `except Exception` silencioso; tamaños §4.
- El cálculo de discrepancia y la elección de candidato son dominio puro con tests — las
  llamadas a Google se mockean en unit.

De negocio:
- LA CONVENCIÓN DE KM NO SE CAMBIA POR ACCIDENTE: `kms_a_facturar` sigue significando lo que
  la Fase 0.1 confirme, y ALT002 tiene que dar idéntico antes/después. La vuelta del técnico
  se AGREGA como información (campos nuevos), salvo decisión explícita del usuario de cambiar
  la facturación — que va en fase propia con su migración.
- El geocode nunca pisa una coordenada existente sin confirmación humana; los ambiguos quedan
  en cola de revisión, no se eligen "al azar" por score.
- Una sucursal que ni Siges ni el geocoding pueden ubicar queda explícitamente "sin ubicar"
  (visible en la UI), nunca con coords inventadas ni km calculados de aire.

[EJEMPLO]
Nota de cierre esperada:

  Geolocalización y KM ida/vuelta en Tabla KM — cerrado y verificado:
  - Fase 0: convención confirmada = <ida / ida+vuelta> (evidencia: <N> filas vs km cobrados,
    ratio ≈<X>); APIs de la key: <lista>; <Distance Matrix vigente / migrado a Routes API>;
    geocoder elegido: <cuál> a $<precio>/1000; muestreo de 20 pines: mediana <X> m, umbral
    sospechoso = <Y> km; sinCoords totales: <N> sucursales en <M> prestadores.
  - Backend: GeocodingGateway + adapter, cache de geocodes, columnas kms_ida/kms_vuelta/
    coords_origen (migración up/down), preview/apply en dos pasos, pines sospechosos.
  - Frontend: "Buscar lugar" con candidatos, "Recalcular KM" por fila, "Geocodificar
    faltantes", preview con diff antes de aplicar, badges de procedencia.
  - lint-imports · ruff · mypy · pytest unit (+N) · tsc · eslint — verde.
  - Regresión ALT002: liquidación <id> re-analizada → hallazgos idénticos (N=N). Caso BAHIA:
    ida <X> km (tabla: 199,294), vuelta <Y> km, discrepancia pin-geocode <Z> m.
  - Geocoding real: <n> sucursales resueltas (<a> automáticas, <b> por elección), sinCoords
    <antes>→<después>. Llamadas Google consumidas en total: <n> (preview repetido: 0 nuevas).
```

---

## Notas de contexto para quien use este prompt (fuera del prompt en sí)

- **La mitad de la feature ya existe y hay que construir SOBRE ella, no al lado**: el cálculo
  base→cliente por Distance Matrix con la base del prestador tomada de Siges ya funciona
  (`CalcularDistanciasSiges` + `HttpxGoogleMapsGateway` + `google_maps_api_key`). Los gaps
  reales son: geocoding para las sucursales sin coords (hoy se saltean), validación de pines
  dudosos, la vuelta a base, y que el bulk pisa la tabla sin previsualización.
- **La mina es ALT002**: el motor de liquidaciones compara lo que el PST facturó contra
  `kms_a_facturar`. El dato del screenshot (199,294 km Bahía Blanca→Guaminí) sugiere que la
  tabla guarda la IDA — si el cálculo nuevo guardara ida+vuelta en el mismo campo, todos los
  esperados se duplican y el próximo re-análisis llena de alertas falsas las liquidaciones.
  Por eso el default es: campos NUEVOS para ida/vuelta, convención vieja intacta, y regresión
  ALT002 obligatoria en el cierre.
- **La vuelta no es ida×2 por definición**: rutas con manos únicas o trazas distintas pueden
  dar B→A ≠ A→B. Por eso se calcula el tramo real de vuelta. En la práctica rural van a ser
  casi iguales — mejor: el dato es barato de calcular bien.
- **Por qué preview obligatorio en el bulk**: la corrida actual hace upsert directo; en una
  tabla que alimenta facturación, "recalculé y cambió todo" sin diff visible es un incidente
  esperando fecha. El two-step además evita pagar dos veces: el apply usa la propuesta
  persistida, no re-llama a Google.
- **Google Maps no está en `INTEGRACIONES_EXTERNAS.md`**: el inventario del refactor ADR-018
  no lo listó (quedó entre los "9 archivos httpx" sin nombre propio). Este prompt lo corrige —
  y es un buen recordatorio de que el inventario vale lo que su última actualización.
- **Distance Matrix vs Routes API**: Google viene empujando Routes API (`computeRouteMatrix`)
  como sucesora de Distance Matrix. No lo doy por hecho: el prompt manda verificar el estado
  real para ESTA cuenta/key en la doc oficial al momento de ejecutar, y migrar solo si
  corresponde — detrás del mismo puerto, así el resto del código ni se entera.
- **Direcciones rurales argentinas son el caso difícil** ("Ruta Nacional 33 KM 167"): el
  geocoder puede devolver el pueblo, el kilómetro exacto o nada. Por eso candidatos con
  confirmación humana en vez de auto-elegir por score, y por eso el muestreo de Fase 0.3
  calibra con datos propios en vez de confiar en la precisión nominal del geocoder.
