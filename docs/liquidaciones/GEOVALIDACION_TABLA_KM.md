# Geovalidación de coordenadas (Fase 2)

Ver `docs/MASTER_PROMPT_MATCHING_SUCURSALES_GEOVALIDACION.md` para el plan completo.
Este doc cubre lo implementado hasta ahora: **Tier 0** (saneo geométrico puro),
**Tier 1** (reverse geocoding de Georef, solo la comparación de provincia — el geocode
de direcciones de Georef queda pendiente, ver más abajo) y **Tier 1b** (segunda opinión
de Nominatim, confirmación por dos fuentes). Tier 2 (Google) — no arrancado.

## Tier 0 — saneo puro, cero llamadas

`domain/services/geovalidacion_tier0.py`, corre sobre TODAS las sucursales activas del
PST (no solo las que ya tienen fila en Tabla KM). Reglas:

- `sin_coordenadas` (severidad baja): pin ausente, no parseable o en `(0, 0)`.
- `fuera_de_argentina` (alta): fuera de un rectángulo continental+insular grueso
  (`lat -55.5..-21.5`, `lon -73.6..-53.0`) — filtro de descarte rápido, no una frontera
  de precisión.
- `latlon_invertidas` (alta): el par tal cual está fuera de Argentina, pero invertido
  (`lat↔lon`) cae dentro — típico error de carga de columnas swapeadas.
- `pin_compartido` (media): mismo pin (redondeado a 5 decimales) compartido por 2+
  sucursales con domicilio distinto — patrón "todas cargadas al centro".
- `lejos_de_base` (media): distancia haversine a la sucursal base del PST mayor al
  umbral (`umbral_distancia_base_km`, default 300 km, **provisorio, sin calibrar**).

**Desviación consciente del texto del master prompt**: NO se implementó la regla
"provincia declarada incompatible con el pin a nivel bounding box provincial" en Tier 0.
Un bounding box por provincia hardcodeado de memoria es un dato geográfico de precisión
dudosa (riesgo de alucinación). El propio plan ya prevé algo mejor y gratuito para esto
en Tier 1: el reverse de Georef contra `DesProvincia`/`DesCiudad` es exacto (usa datos
oficiales del Estado) y no cuesta nada — se implementa ahí cuando arranque Tier 1.

## Resultado medido (SAN JUAN, 948 sucursales activas, 2026-08-19)

**663 hallazgos sobre 531 sucursales distintas**:

| Código | Cantidad | Nota |
|---|---:|---|
| `pin_compartido` | 432 | El cluster más grande: **55 sucursales comparten el pin `(-38.4160, -63.6166)`, el centroide geográfico de Argentina** — confirma exactamente el patrón "todas al centro" que predecía el plan. Un segundo cluster de 38 comparte otro pin. |
| `lejos_de_base` | 184 | En buena parte las mismas sucursales del cluster del centroide (600-1600 km "de distancia" porque el pin no es real). |
| `sin_coordenadas` | 43 | Sin pin cargado. |
| `fuera_de_argentina` | 3 | Incluye un caso real: la escuela "20 de Junio" tiene el pin en **Madrid, España** (`40.41, -3.70`); los otros dos en `(1.0, 1.0)`, placeholder obvio. |
| `latlon_invertidas` | 1 | Confirmado en datos reales: "Escuela Martin Yanzon". |

Scripts: `backend/scripts/medir_tier0_geovalidacion_san_juan.py` (medición inicial, uso
directo del dominio) — el endpoint real (`GET .../geovalidacion/tier0`) reproduce el
mismo total (663) contra el prestador San Juan (`eda1e000-b50f-4475-bf2c-4d1bc3cf116e`).

## API y UI

`GET /api/liquidaciones/siges/prestador/{id}/geovalidacion/tier0` — `Page[HallazgoTier0]`,
rankeado por severidad (alta primero), sin costo, se puede pedir en cada request sin
límite de llamadas (no hay proveedor externo de por medio). No persiste nada: Tier 0 es
barato de recalcular, así que no hace falta cachear ni una tabla de hallazgos.

UI: sección "Geovalidación básica (Tier 0)" arriba del paso "Pines" del wizard APB
(`tabla-km-wizard-pines.tsx`) — cada hallazgo con severidad, motivo legible y link a
Google Maps para verificar a ojo. Sin acción de "corregir" todavía: Tier 0 no tiene un
candidato sugerido (no llamó a ningún geocoder), así que la única acción es investigar
y corregir en Gestión o cargar un override local vía el flujo de coordenadas existente.

## Tier 1 — reverse geocoding de Georef (gratis, sin auth)

`domain/repositories/georeferenciacion_gateway.py` (puerto) +
`infrastructure/georef/httpx_georef_gateway.py` (adapter real, timeout 30s, backoff
acotado — 2 reintentos con espera 1s/2s — SOLO ante 429/5xx, sin retry ante 4xx no
reintentable ni error de conexión). Shape de la API verificado en vivo contra
`apis.datos.gob.ar/georef/api` antes de escribir el parser (no asumido de memoria):
`/ubicacion` con `provincia.nombre == null` es "sin cobertura" (HTTP 200, no error).

Cache propio (`georef_reverse_cache`, migración `b7e3f1a9d2c6`) por pin redondeado a 4
decimales (~11 m) — clave por PIN, no por sucursal: cuando muchas sucursales comparten
el mismo pin roto (el caso "todas al centro" de Tier 0), una sola llamada real resuelve
todo el grupo. `provincias_compatibles` (dominio puro,
`domain/services/geovalidacion_tier1.py`) normaliza y compara `DesProvincia` de Siges
contra la provincia real de Georef, con alias conocidos (CABA/Capital Federal ↔ "Ciudad
Autónoma de Buenos Aires").

Dos casos de uso separados (mismo criterio que Google/AuditarPines): `ConsultarGeoref
ReversePendientes` es la única que llama a la red (secuencial, pausa
`georef_pausa_segundos` = 0.2s, tope `georef_max_calls_per_run` = 200 por corrida — no
por costo, por duración del request HTTP); `ListarHallazgosTier1` es puramente de
lectura sobre lo ya cacheado.

### Resultado medido (SAN JUAN, piloto real 2026-08-19)

3 corridas de `consultar-georef` cubrieron las 948 sucursales activas: **472 llamadas
reales** a Georef (200 + 200 + 72) y **833 resueltas por cache** — la mayoría por el
efecto de pines compartidos ya visto en Tier 0 (una sola llamada real al pin del
centroide de Argentina resolvió las 55 sucursales que lo comparten). 43 sin
coordenadas (igual que Tier 0).

**192 sucursales con provincia incompatible** — confirmado por una fuente
independiente y oficial (no solo la heurística de bounding box de Tier 0) que el pin
cae en otra provincia: el cluster del centroide cae en **La Pampa**; otros pines caen
en Chubut, Tucumán, Buenos Aires, Neuquén, Santa Fe y Córdoba. Endpoints:
`POST .../geovalidacion/tier1/consultar-georef` (escribe cache) y
`GET .../geovalidacion/tier1` (`Page[HallazgoTier1]`, solo lectura).

UI: sección "Provincia del pin vs. Gestión (Georef)" en el paso "Pines" del wizard,
debajo de Tier 0 — botón "Consultar Georef" (repetirlo solo consulta lo pendiente) y
lista de discrepancias con el link a Maps.

## Tier 1b — segunda opinión de Nominatim (gratis)

`domain/repositories/nominatim_gateway.py` (puerto) +
`infrastructure/nominatim/httpx_nominatim_gateway.py` (adapter real). Cumple la
política de uso publicada (https://operations.osmfoundation.org/policies/nominatim/):
**1 req/s estricto** (lock + timestamp en la instancia singleton — todas las llamadas
del proceso pasan serializadas por el mismo gateway), User-Agent identificable propio
(`HelpDeskManager-CanalDirecto-Geovalidacion/1.0`), sin backoff agresivo ante error
(a diferencia de Georef: si Nominatim devuelve 5xx significa que estamos siendo
groseros con el rate limit, mejor fallar ese caso y no insistir). Atribución ODbL
obligatoria — viaja en cada hallazgo (`atribucion` en el schema) y se muestra en la UI.

**SOLO corre sobre lo que Tier 1 (Georef) ya marcó incompatible** — nunca sobre el
universo completo del PST (192 casos en San Juan, no 948). Cache propio
(`nominatim_reverse_cache`, migración `d4a8c2e6f931`), obligatoria por la política (no
solo cortesía). `confirmado_por_dos_fuentes` (dominio puro,
`domain/services/geovalidacion_tier1.py`): si Georef ya marcó incompatible Y Nominatim
coincide con Georef, es evidencia de dos fuentes independientes — el plan dice
explícitamente que "eso ya no necesita Google".

### Resultado medido (SAN JUAN, piloto real 2026-08-19)

2 corridas de `consultar-nominatim` cubrieron los 192 casos de Tier 1: **63 llamadas
reales** (60 + 3) a 1 req/s y **189 resueltas por cache** (mismo efecto de pines
compartidos). **Las 192 discrepancias de Tier 1 fueron confirmadas al 100% por
Nominatim** — coincidencia exacta de provincia en cada caso, sin una sola discrepancia
entre las dos fuentes (65 en Chubut, 59 en La Pampa, 16 en Buenos Aires, 10 en Santa
Fe, y el resto repartido en 12 provincias más). Endpoints:
`POST .../geovalidacion/tier1b/consultar-nominatim` y
`GET .../geovalidacion/tier1b` (`Page[HallazgoTier1b]`).

UI: sección "Segunda opinión (Nominatim / OpenStreetMap)" en el paso "Pines", debajo de
Tier 1 — cada hallazgo confirmado se muestra con fondo distinto (severidad alta) y la
atribución ODbL visible.

## Pendiente

- Calibrar `umbral_distancia_base_km` de Tier 0 con evidencia real (300 km es
  provisorio — el propio San Juan tiene sucursales del Gobierno provincial hasta
  1600 km, posiblemente el umbral deba ser más generoso o dividirse por tipo de
  empresa).
- Tier 1, geocode de direcciones (`/direcciones` de Georef): no implementado en esta
  ronda — ya se había confirmado cobertura pobre de calles para San Juan en la
  medición de Fase 0 (0 resultados en 4 pruebas reales), así que su valor inmediato es
  bajo frente al reverse. El reverse (implementado) es "la validación más barata y
  contundente" que preveía el plan.
- Tier 2 (Google): solo residuo tras Tier 0/1/1b, cero llamadas sin autorización
  explícita del usuario. Con las 192 sucursales ya confirmadas por dos fuentes
  gratuitas, el residuo real que necesitaría Google es chico (los 43 `sin_coordenadas`
  de Tier 0 y los casos que Georef no pudo cubrir).
- Worklist final combinada (Tier 0 + 1 + 1b + 2) con export CSV para Gestión.
