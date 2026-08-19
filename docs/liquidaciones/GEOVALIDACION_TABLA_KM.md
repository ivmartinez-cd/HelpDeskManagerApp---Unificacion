# Geovalidación de coordenadas (Fase 2)

Ver `docs/MASTER_PROMPT_MATCHING_SUCURSALES_GEOVALIDACION.md` para el plan completo.
Este doc cubre lo implementado hasta ahora: **Tier 0** (saneo geométrico puro). Tier 1
(Georef), Tier 1b (Nominatim) y Tier 2 (Google) — no arrancados.

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

## Pendiente

- Calibrar `umbral_distancia_base_km` con evidencia real (300 km es provisorio — dado
  que el propio San Juan tiene sucursales del Gobierno provincial hasta 1600 km,
  posiblemente el umbral deba ser más generoso o dividirse por tipo de empresa).
- Tier 1 (Georef): puerto `GeoreferenciacionGateway`, reverse por pin + geocode por
  domicilio, cache, política de uso (secuencial, pausa, backoff 429/5xx).
- Tier 1b (Nominatim): segunda opinión solo para lo que Georef no resuelve — política
  dura de 1 req/s, User-Agent propio, atribución ODbL.
- Tier 2 (Google): solo residuo tras tiers gratis, cero llamadas sin autorización
  explícita del usuario.
- Worklist final combinada (Tier 0 + 1 + 1b + 2) con export CSV para Gestión.
