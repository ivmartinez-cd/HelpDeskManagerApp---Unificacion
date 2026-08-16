# Geolocalización y km ida/vuelta en Tabla KM

Definición operativa de la feature (2026-08-15). Decisiones de Fase 0 validadas con el
usuario contra datos reales de la DB de dev (sembrada desde producción).

## Convención de km (LA regla de negocio)

**Todos los prestadores facturan ida y vuelta.**

| Campo | Significado |
|---|---|
| `kms_ida` | Tramo real base→cliente medido por Google (Distance Matrix, driving) |
| `kms_vuelta` | Tramo real cliente→base — puede diferir de la ida por manos únicas/ruteo |
| `kms_recorrido` | **Total** ida+vuelta (la convención histórica de las filas manuales) |
| `kms_a_facturar` | = `kms_recorrido` si `kms_recorrido > umbral_viatico`, si no 0 |
| `umbral_viatico` | Se compara contra el TOTAL; nunca lo pisa un recálculo |

Evidencia de Fase 0: cruzando incidentes 2025+ contra filas manuales, la mediana
cobrado/tabla es 1,000 en los 14 prestadores; las filas manuales de BAHIA son ≈2× la ida
de Google (ej. Coronel Suárez 367 manual vs. 181,8 ida). El cálculo automático original
(solo ida) generó en BAHIA esperados a la mitad — esas filas se corrigen con la primera
corrida preview→apply. ALT002 no cambió: los esperados manuales ya eran ida+vuelta.

`url_maps` representa el viaje completo: `origin=base`, `destination=base`,
`waypoints=cliente`.

## Procedencia de coordenadas (`coords_origen`)

- `siges`: pin cargado en Siges (fuente primaria; Siges es solo lectura para el módulo).
- `geocode`: elegido de candidatos de Google Geocoding — automático solo si el candidato
  es único e inequívoco (ROOFTOP/RANGE_INTERPOLATED o intersección exacta, sin
  partial_match); un resultado tipo `route` (centro geométrico de "Ruta X KM Y") jamás se
  auto-elige.
- `manual`: lat/lon pegadas a mano por el usuario.

Reglas duras: el geocode **solo llena vacíos** — nunca pisa un pin de Siges ni una
coordenada manual sin confirmación humana. Una sucursal que ni Siges ni el geocoding
pueden ubicar queda explícitamente "sin ubicar" (contada y visible), sin coords
inventadas ni km calculados.

Las resoluciones para sucursales sin pin en Siges viven en `sucursal_coordenadas`
(clave `siges_sucursal_id`); los estados se derivan: `resuelta`, `ambigua` (candidatos a
revisar), `sin_resultados`, `sin_direccion`, `pendiente` (aún no consultada).

## Flujos

1. **Geocodificar faltantes** (`POST /siges/prestador/{id}/geocodificar-faltantes`):
   recorre sucursales cliente sin pin, geocodifica su domicilio normalizado (sufijos
   "Piso: Dpto:" y altura " 0" fuera; query `domicilio, localidad, provincia,
   Argentina`), auto-resuelve inequívocos y deja el resto en cola de revisión.
2. **Revisión de ambiguos** (`GET/PUT .../coordenadas`): el usuario elige candidato o
   pega coords manuales.
3. **Cálculo masivo en dos pasos** (`POST .../calcular-distancias/preview` →
   `.../aplicar`): el preview llama a Google (ida y vuelta, lotes de 25) y persiste la
   propuesta con diff por fila (km actual → nuevo, crear/actualizar); el apply
   materializa SIN re-llamar a Google y descarta el preview. Solo el último preview del
   prestador es aplicable. `umbral_viatico` y `observaciones` de filas existentes se
   preservan siempre.
4. **Por fila** (`POST /tabla-km/{id}/buscar-lugar`, `PUT /tabla-km/{id}/coordenadas`,
   `POST /tabla-km/{id}/recalcular-km`): candidatos + elección con procedencia +
   recálculo directo (2 elementos, sin preview — decisión de Fase 0).
5. **Pines sospechosos** (`POST .../auditar-pines` + `GET .../pines-sospechosos`): la
   auditoría geocodifica domicilios de sucursales CON pin (cache mediante); el listado
   cruza pin vs. geocode con haversine y marca discrepancias > **5 km** (umbral calibrado
   con muestreo n=20: urbano mediana 22 m; casos reales rotos: Telecom Carcarañá 330 km,
   JRASA Saladillo 158 km). `location_type` acompaña para distinguir pin roto seguro de
   geocode rural impreciso.

## Control de costo (key corporativa)

Cache `geocode_cache` por dirección normalizada (ZERO_RESULTS incluido), tope
`GOOGLE_MAPS_MAX_CALLS_PER_RUN` (default 200 unidades facturables por corrida) y
contador de llamadas en cada resultado. Repetir un listado o un preview aplicado no
llama a Google. Ver `docs/INTEGRACIONES_EXTERNAS.md` §11.
