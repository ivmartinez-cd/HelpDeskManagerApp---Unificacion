# Matching de sucursales Tabla KM ↔ Siges (Fase 1)

Ver `docs/MASTER_PROMPT_MATCHING_SUCURSALES_GEOVALIDACION.md` para el plan completo
(Fase 0 medición, Fase 1 matching — este doc —, Fase 2 geovalidación de coordenadas
— no arrancada, Fase 3 verificación). Este doc define el comportamiento operativo del
matching: niveles, umbrales medidos, flujo de confirmación/rechazo.

## Por qué hace falta

El join local↔Siges (`normalizar_nombre` en `vinculacion_siges.py`, N0) es igualdad
exacta tras normalizar acentos/mayúsculas/prefijo. Medido en SAN JUAN (2026-08-19, 616
filas locales, 948 sucursales activas en Siges): **151 filas sin match**. 98% de esas
tienen la empresa exacta — el problema es de nombre de sucursal, no de empresa.

Causa raíz confirmada: `unicodedata.normalize("NFD", ...)` **no** descompone el símbolo
ordinal `º` (U+00BA) — sobrevive a la normalización como letra suelta si no se limpia
aparte. Además `°` (signo de grado, U+00B0) y `º` (ordinal) se usan indistintamente en
los datos reales para escribir "número" (`Nº`, `N°`, `N.º`, `Nro`), y las siglas
institucionales con puntos (`E.N.I.`, `E.E.E.`, `E.P.E.T.`) tokenizan letra por letra
tras el paso puntuación→espacio, sin igualar nunca a su forma plana (`ENI`, `EEE`).

## Niveles

- **N0** (existente, sin cambios): `normalizar_nombre` — NFD + minúsculas + prefijo
  PST/SPST/PR. Sigue siendo responsabilidad de `RefrescarDatosSiges`.
- **N1** (`normalizar_nombre_fuerte`, `domain/services/matching_sucursales_tabla_km.py`):
  NFKD (mapea `º`→`o`, `ª`→`a`) + reglas de símbolo de número (`Nº`/`N°`/`N.º`/`Nro`→
  `N `, aplicadas ANTES de NFKD porque NFKD ya convierte `º` en letra suelta) + siglas
  con puntos (`E.N.I.`→`ENI`, `E.E.E.`→`EEE`, `E.P.E.T.`→`EPET`) + abreviaturas de
  palabra confirmadas en la muestra real (Secundaria→Sec, Superior→Sup, Provincia/
  Provincial/Prov→Pcia, Nacional→Nac, Primaria→Prim, Republica→Rep, Presidente→Pte,
  Tecnica→Tec, General→Gral, Escuela→Esc). Igualdad exacta bajo esta normalización
  **se auto-vincula** (decisión de negocio 0.4.a, mismo nivel de confianza que N0).
- **N2** (`proponer_matches_tabla_km`): score compuesto (ratio de secuencia +
  solapamiento de tokens/Jaccard, promedio), candidatos anclados por empresa exacta
  (N1) y por número de sucursal cuando ambos lados lo tienen — **un número distinto
  nunca se propone**, es el ancla más confiable del dataset. Umbral `UMBRAL_N2 = 0.45`.
  **N2 SIEMPRE requiere confirmación humana — no hay excepción, no auto-vincula nunca**,
  ni siquiera con score 1.0 por texto (solo N1, que es estructuralmente distinto:
  igualdad exacta bajo la normalización determinística, no un score).

## Por qué el umbral prioriza recall

Medido contra las 151 filas reales de SAN JUAN con el comparador de producción: el
ratio de secuencia simple NO separa bien candidatos correctos de falsos — hay falsos
positivos con ratio 0.85-0.92 (ej. `Escuela ANTONIO QUARANTA` vs `Escuela Antonio
Pulenta`, personas distintas) y correctos genuinos con ratio tan bajo como 0.45-0.55
(ej. `Escuela Sec. Dr. Juan Carlos Navarro` vs `Escuela Dr. J. C. Navarro`, score 0.49).
Como el costo de un falso positivo en N2 es bajo (el operador lo descarta con un
vistazo — el motivo ya dice qué difiere) y el costo de no proponer nada es alto (buscar
a mano en Siges), el umbral se calibró para recall, no precisión. `UMBRAL_N2 = 0.45`
capturó ese caso real sin introducir ruido evidente en la revisión manual completa de
las 151 propuestas (script `backend/scripts/calibrar_matching_sucursales_san_juan.py`).

## Resultado medido (SAN JUAN, pipeline completo)

De 151 filas sin match: **82 auto-vinculables por N1 (54%)**, **64 con candidato N2
para confirmar (42%)**, **5 sin candidato (3%, alta manual o baja)**.

## Flujo de confirmación/rechazo

- `POST /siges/prestador/{id}/matching/auto-vincular-n1`: aplica N1 en bloque
  (idempotente — re-ejecutarlo sobre filas ya vinculadas no hace nada). Trae
  domicilio/localidad/provincia + vínculo, igual que `RefrescarDatosSiges._actualizar_fila`.
- `GET /siges/prestador/{id}/matching/propuestas`: candidatos N2 pendientes,
  read-only, excluye descartados.
- `POST /tabla-km/{id}/matching/confirmar` (body `sigesSucursalId`): confirma un
  candidato — mismo camino de escritura que N1.
- `POST /tabla-km/{id}/matching/rechazar` (body `sigesSucursalId`): persiste el
  descarte en `matching_descartes_tabla_km` (migración `9c3e5a71f2d4`) — el mismo
  candidato no vuelve a proponerse para esa fila en corridas futuras (decisión 0.4.d).

UI: paso "Sin match" del wizard APB (`tabla-km-wizard-matching.tsx`), entre Importar y
Ubicar — resolver el matching primero evita intentar geocodificar con datos de una fila
que en realidad ya tiene domicilio real en Siges, solo que bajo otro símbolo/abreviatura.

## Alcance y decisiones tomadas (2026-08-19)

Mecanismo genérico para cualquier PST — SAN JUAN es el piloto de verificación, no un
caso especial en el código. Confirmado con el usuario antes de implementar (0.4.a-d):
auto-vincular N1, paso nuevo del wizard, alcance genérico, tabla de descartes.

## Pendiente

- Piloto end-to-end real (ejecutar N1 + revisar N2 sobre SAN JUAN en producción de
  dev) — no corrido todavía, queda a criterio del usuario disparar la escritura real.
- Fase 2 (geovalidación de coordenadas con Georef/Nominatim/Google) — no arrancada.
- Regresión formal contra PENTACOM (control N0) — pendiente de correr y documentar.
