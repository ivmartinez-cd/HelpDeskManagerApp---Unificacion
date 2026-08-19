# Master Prompt — Matching asistido de sucursales Gestión↔Tabla KM y geovalidación de bajo costo (piloto: SAN JUAN)

Resolver dos problemas encadenados de la Tabla KM de liquidaciones, con SAN JUAN como
piloto (~133 sucursales reportadas sin match) pero con mecanismo genérico para los 35 PSTs:

1. **Matching**: hoy el cruce Tabla KM ↔ sucursales de Gestión (Siges) es igualdad exacta
   del par `(empresa, sucursal)` normalizado con `normalizar_nombre`. Una fila que no
   matchea queda sin domicilio, sin vínculo Siges y sin posibilidad de geocodificarse —
   el wizard la cuenta (`no_encontradas_en_siges`) pero no ofrece ninguna forma de
   resolverla. Caso real que disparó esto: un nombre difiere solo en el símbolo `º`.
2. **Geovalidación**: validar direcciones y coordenadas que Gestión tiene cargadas para
   TODAS las sucursales del prestador, gastando lo mínimo posible en APIs de Google
   (fuentes gratuitas primero: API Georef del Estado argentino y Nominatim/OSM como
   segunda opinión; Google solo para el residuo) y con el mínimo trabajo de operadores
   (solo llegan a revisión humana los casos con evidencia de problema).

Generado el 2026-08-19 a partir del análisis del código real del monorepo. El bug del `º`
está **confirmado ejecutando la normalización vigente**, no supuesto (ver Notas al final).

---

```text
[ROL]
Actuá como arquitecto/desarrollador senior full-stack del monorepo HelpDeskManager-Unificacion
(FastAPI + SQLAlchemy async + Alembic + Next.js App Router, arquitectura módulo→capa
domain/application/infrastructure/presentation). Conocés y aplicás ARCHITECTURE_GUIDE.md,
CLAUDE.md, ADR-014 y ADR-018 como reglas obligatorias. Respondés en español de Argentina,
directo y sin relleno. Cero alucinaciones: comportamientos de normalización Unicode, cobertura
de geocoders y estados de cuentas/APIs se confirman ejecutando código y contra documentación
oficial, nunca se asumen.

[CONTEXTO]
Lo que YA existe, verificado contra el código (no supuesto):

- Matching vigente: `normalizar_nombre` en `liquidaciones/domain/services/vinculacion_siges.py`
  — NFD sin combinantes + lowercase + todo carácter no alfanumérico → espacio + drop del
  prefijo inicial pst/spst/pr. La clave de cruce es el par
  `(normalizar_nombre(empresa), normalizar_nombre(sucursal))` y el match es igualdad EXACTA
  (lookup de dict). Lo usan: `RefrescarDatosSiges`
  (`application/use_cases/tabla_km_refrescar_siges.py`, endpoint
  `POST /siges/prestador/{id}/refrescar-datos-sucursales`, reporta
  `no_encontradas`/`no_encontradas_detalle` y NO las toca), `DiagnosticarAsistenteKm`
  (`estado_asistente_km.py`, campo `no_encontradas_en_siges` del wizard, endpoint
  `GET /siges/prestador/{id}/asistente-km/estado`, read-only y sin costo Google) y
  `BuscarSucursalesSiges` (badge `ya_cargada`).
- BUG CONFIRMADO ejecutando esa normalización (2026-08-19): `º` (U+00BA, categoría Unicode
  Lo) y `ª` (U+00AA) son alfanuméricos para Python y NFD no los descompone → SOBREVIVEN a la
  normalización; en cambio `°` (U+00B0, signo de grado, categoría So) sí se elimina.
  Resultado: `"Sucursal Nº 5"` normaliza a `"sucursal nº 5"` ≠ `"sucursal n 5"`, y dos
  nombres que solo difieren en `Nº` (ordinal) vs `N°` (grado) — visualmente idénticos —
  tampoco matchean entre sí. NFKD sí mapea `º→o` y `ª→a`.
- No hay fallback: sin match exacto no hay domicilio, ni `siges_sucursal_id`, ni
  `id_costo_servicios` (campos ya existentes en la entidad `TablaKm` y en
  `update_vinculo_siges` del repo), y la fila queda afuera del pipeline de
  geocodificación/cálculo de km. El docstring de `RefrescarDatosSiges` ya lo admite:
  "puede ocurrir si el nombre cambió en Gestión".
- Números conocidos: SAN JUAN tiene 487 filas de tabla_km
  (`LIQUIDACION_PRESTADORES_MIGRACION_ESTADO.md`); el usuario reporta ~133 sucursales del
  prestador de San Juan que "no migran de Gestión" por falta de match. El número exacto y
  su composición se miden en Fase 0 — no se asume.
- Datos disponibles de Gestión (Siges) por sucursal (`SUCURSALES_DE_PRESTADOR_SQL` en
  `liquidaciones/infrastructure/siges/query.py`): `Id_Sucursal`, `Den_Comercial` (empresa),
  `descripcion` (sucursal), `Domicilio` (con ruido de plantilla "Piso: Dpto:" / altura " 0"
  que `normalizar_domicilio` ya limpia), `DesCiudad`, `DesProvincia`, `Latitud`/`Longitud`
  (varchar con coma decimal, se parsean con `parse_latlon_siges`), `Cuadricula`,
  `IDCostoServicios`. La cuenta es `SiGesReadOnly` (db_datareader): **Gestión/Siges es solo
  lectura** — ninguna corrección de pin o dirección puede escribirse ahí desde este sistema;
  lo que sí existe localmente es `sucursal_coordenadas` (resoluciones con procedencia
  'geocode'/'manual'; en `_resolver_destino` una resolución resuelta tiene prioridad sobre
  el pin de Siges — verificar ese orden antes de apoyarse en él).
- Infra de geolocalización existente (reusar, no duplicar): puertos `GeocodingGateway` y
  `GoogleMapsGateway` + adapters httpx (timeout 30 s, sin retry, `ExternalServiceError`),
  `geocode_cache` por dirección normalizada (incluye ZERO_RESULTS), auditoría de pines
  sospechosos (`auditar-pines` + `pines-sospechosos`, umbral 5 km calibrado con muestreo
  real n=20: urbano mediana 22 m; pines rotos reales de 158-330 km), `armar_direccion`,
  `haversine_km`, tope `GOOGLE_MAPS_MAX_CALLS_PER_RUN` (default 200) y flujo
  preview→apply. Wizard frontend: `tabla-km-wizard*.tsx`.
- Costo Google (INTEGRACIONES_EXTERNAS.md §11, verificado 2026-08-15): key corporativa
  PAGA de Canal Directo, $5/1000 requests de Geocoding y por elemento de Distance Matrix,
  10.000 gratis/mes por SKU (pricing marzo 2025). Geocoding ✓ y Distance Matrix ✓ (legacy)
  habilitadas; Routes API y Places (New) NO habilitadas (403). Regla vigente del repo:
  cero llamadas Google sin autorización explícita del usuario.
- Fuentes gratuitas verificadas contra su documentación oficial (2026-08-19):
  · API Georef (https://apis.datos.gob.ar/georef/api/, doc en
    https://datosgobar.github.io/georef-ar-api/): servicio oficial del Estado argentino,
    "completamente gratuito y no requiere autenticación" (FAQ oficial).
    `GET /direcciones?direccion=...&provincia=san juan&max=N` normaliza la dirección y
    devuelve `ubicacion.lat/lon` (altura interpolada) cuando puede;
    `GET /ubicacion?lat=...&lon=...` hace reverse: provincia/departamento/municipio con
    IDs. PROBADO EN VIVO (2026-08-19): el reverse funciona para San Juan —
    `lat=-31.5375&lon=-68.5364` → provincia "San Juan" (id 70), departamento "Capital"
    (70028), municipio "San Juan" (700028); en cambio `/direcciones` devolvió 0
    resultados en 2 consultas de prueba de calles de la capital sanjuanina — la
    cobertura de calles (datos INDEC) para San Juan hay que medirla en Fase 0 antes de
    contar con el geocoding directo; el reverse, que es la validación más valiosa acá,
    ya está confirmado. La doc pública no declara rate limit — igual tratarla con
    cortesía: secuencial, pausa configurable entre llamadas, backoff ante 429/5xx,
    cache local obligatoria.
  · Nominatim/OSM (https://operations.osmfoundation.org/policies/nominatim/): gratuito con
    política DURA: máximo absoluto 1 request/segundo, User-Agent propio identificable (no
    el default de httpx), un solo thread/una sola máquina, resultados cacheados
    obligatoriamente, tareas bulk sostenidas (más de un día) limitadas a 4 req/min,
    atribución ODbL. Una corrida one-shot de cientos de direcciones a 1 req/s entra en
    política; un job periódico masivo no.
- Volúmenes: ~500-800 sucursales por PST grande y 487 filas locales en SAN JUAN. El
  matching difuso es O(filas × sucursales) ≈ 3·10⁵ comparaciones por corrida — `difflib`
  de la stdlib alcanza de sobra para una acción de wizard; NO hace falta dependencia nueva.

[OBJETIVO]

FASE 0 — MEDICIÓN (bloqueante, 0 llamadas a Google, sin escrituras):
  1. Cuantificar el problema real de SAN JUAN en las DOS puntas del join:
     a. filas de tabla_km sin match en Gestión (`no_encontradas_en_siges` del
        diagnóstico + `no_encontradas_detalle`; ojo: `RefrescarDatosSiges` ESCRIBE
        cuando matchea — para listar el detalle sin efectos usar un script/consulta
        read-only o un modo dry-run nuevo), y
     b. sucursales de Gestión sin fila local (`sucursales_nuevas_por_importar`,
        separando activas de ex-clientes).
     Confirmar contra el ~133 reportado por el usuario y dejar el número real escrito.
  2. Clasificar a mano una muestra representativa (30-50 pares no matcheados, elegidos
     con ayuda de un fuzzy exploratorio en script): % por símbolo º/°/ª, % por
     abreviatura (Nº/N°/Nro/Núm/N; Bº/B°/Bo/Barrio; Av/Avda/Avenida; Gral; Sta/Sto;
     Dpto; Esq; s/n; etc.), % typo real, % renombre genuino, % inexistente en Gestión.
     La lista de equivalencias de Fase 1 sale de ESTA muestra — cada regla nace de un
     caso real, no de imaginación.
  3. Calibrar con esa muestra los umbrales de score del matching difuso (qué ratio
     separa "candidato creíble" de ruido) — números medidos, no mágicos.
  4. DECISIONES a validar con el usuario antes de codear (proponer default, no decidir
     en silencio):
     a. Igualdad exacta bajo normalización FUERTE (nivel N1, determinística: NFKD +
        equivalencias) ¿se auto-vincula? Default propuesto: sí, en bloque con reporte
        detallado y reversible — es el mismo nivel de confianza que el matching actual,
        solo que sin el bug del º. Todo lo difuso (N2) SIEMPRE pasa por confirmación
        humana (pedido explícito del usuario: "que nos dé la oportunidad de elegir").
     b. Dónde vive la revisión: default, paso nuevo del wizard APB ("Sucursales sin
        match") + acceso desde el resultado del refrescar.
     c. Alcance: mecanismo genérico para todos los PSTs; SAN JUAN es el piloto de
        verificación.
     d. Qué se persiste de un rechazo (para no re-proponer el mismo candidato en cada
        corrida). Default: tabla chica de descartes (fila, siges_sucursal_id, quién,
        cuándo).

FASE 1 — MATCHING MULTINIVEL CON CONFIRMACIÓN (backend + UI):
  - Dominio puro, junto a `vinculacion_siges.py` (sin tocar la semántica de
    `normalizar_nombre` ni de `proponer_vinculos`, que otros flujos ya usan — cualquier
    cambio ahí es regresión potencial de `ya_cargada`/refresco/diagnóstico):
    · `normalizar_nombre_fuerte` (N1): NFKD (mapea º→o, ª→a y elimina el resto de
      compatibilidad) + lowercase + no-alfanumérico→espacio + prefijos + tabla de
      equivalencias por regex con límites de palabra (\bn(?:ro|º|o)?\b→"n", barrio→"b",
      avenida/avda→"av", …) construida desde la muestra 0.2, ordenada y con test unitario
      por CADA regla (entrada real → forma canónica).
    · Comparador difuso (N2): sobre pares normalizados N1, score compuesto de
      `difflib.SequenceMatcher.ratio()` del string compacto + comparación de tokens
      orden-insensible (token set), con el umbral calibrado en la Fase 0.3 (medido, no
      mágico). Solo stdlib — nada de dependencias
      nuevas sin medición que lo justifique (si alguna vez hiciera falta rapidfuzz, va
      con ADR).
    · `proponer_matches_tabla_km(filas_sin_match, sucursales_siges) -> propuestas`:
      por fila, top-N candidatos rankeados con score, nivel (N1/N2) y motivo legible
      ("difieren en: º", "abreviatura Nº↔Nro", "typo: 1 carácter"). Unicidad en ambas
      direcciones como `proponer_vinculos`: un candidato conflictivo entre dos filas no
      se auto-elige jamás — se muestran ambos como ambiguos.
  - Application: `ProponerVinculosTablaKm` (read-only), `ConfirmarVinculoTablaKm`
    (persiste vía `update_vinculo_siges` + refresca domicilio/localidad/provincia como
    `_actualizar_fila` del refresco, registrando quién/cuándo/score/nivel),
    `RechazarPropuestaTablaKm` (persiste el descarte). El auto-vínculo N1 (si 0.4.a
    queda en sí) reusa el mismo camino de confirmación, marcado como 'auto'.
  - Presentation: endpoints bajo el config router existente de liquidaciones (mismos
    permisos view/update que ya gatean la Tabla KM; colecciones con `Page[T]`).
    Integrar el conteo al diagnóstico del wizard (`propuestas_pendientes`).
  - Frontend (wizard APB + pantalla Tabla KM): paso/panel "Sucursales sin match" con
    lado a lado fila local ↔ candidato Siges, score y DIFF VISUAL del nombre (resaltar
    exactamente qué difiere — que el operador vea el º de un vistazo), acciones
    Confirmar / Elegir otro candidato / Rechazar / "no existe en Gestión" (queda como
    alta manual vía el flujo "Agregar desde Siges" existente o baja de la fila, decisión
    del operador). Estados vacíos honestos; mismo lenguaje visual del repo.

FASE 2 — GEOVALIDACIÓN ESCALONADA DE DIRECCIONES Y COORDENADAS (San Juan completo):
  Principio: cada tier filtra; a Google solo llega el residuo; al operador solo llegan
  casos con evidencia. Todo resultado de proveedor externo se cachea localmente.
  - Tier 0 — saneo puro, 0 llamadas (dominio puro + tests, corre para TODAS las
    sucursales del PST): coordenadas ausentes/no parseables/(0,0); fuera de bounding box
    de Argentina; lat/lon permutadas (heurística: el par invertido cae en Argentina y el
    original no); pin idéntico compartido por N sucursales con domicilios distintos
    (típico "todas al centro"); distancia a la base del PST > umbral configurable;
    provincia declarada (`DesProvincia`) incompatible con el pin a nivel bounding box
    provincial. Salida: flags por sucursal con severidad.
  - Tier 1 — Georef (gratis): adapter httpx nuevo detrás de un puerto propio de dominio
    (p.ej. `GeoreferenciacionGateway`, junto a los puertos Google existentes; timeout
    30 s, sin retry, `ExternalServiceError`, pausa entre llamadas y backoff ante
    429/5xx):
    · reverse `/ubicacion` por cada pin (CONFIRMADO en vivo para San Juan) →
      ¿provincia/departamento del pin coinciden con `DesProvincia`/`DesCiudad`
      declaradas? (normalizar nombres para comparar) — es la validación más barata y
      contundente: un pin de una sucursal sanjuanina que cae en otra provincia o en
      otro departamento es un hallazgo seguro, sin gastar un centavo;
    · `/direcciones` con el domicilio normalizado (`armar_direccion` existente, más
      `provincia` como parámetro estructurado) → si devuelve `ubicacion`, haversine
      contra el pin y marcar con `es_pin_sospechoso` (umbral 5 km ya calibrado). Es
      best-effort: las 2 consultas de prueba sobre San Juan capital dieron 0 resultados
      — medir cobertura real en Fase 0 y no bloquear el pipeline si no resuelve.
    Cache: extender `geocode_cache` con columna `proveedor` (migración Alembic
    reversible) o tabla hermana — decisión chica a documentar; ZERO_RESULTS también se
    cachea (patrón existente).
  - Tier 1b — Nominatim (gratis, segunda opinión): SOLO para pines que Georef no pudo
    resolver o donde Georef y el pin discrepan (desempate). Cumplir la política textual:
    1 req/s máximo, User-Agent identificable propio, secuencial, cache obligatoria,
    atribución ODbL visible donde se muestre el dato. Si dos fuentes independientes
    (Georef + Nominatim) coinciden entre sí a <1 km y ambas quedan lejos del pin, el pin
    es sospechoso CONFIRMADO (severidad alta) — eso ya no necesita Google.
  - Tier 2 — Google (pago, residuo): únicamente casos aún ambiguos tras los tiers
    gratis. Reusar `HttpxGeocodingGateway` + `geocode_cache` + tope
    `GOOGLE_MAPS_MAX_CALLS_PER_RUN` + candidatos con confirmación humana (flujo de
    resolución existente). Cero llamadas sin autorización explícita del usuario, con
    estimación previa visible (patrón del diagnóstico del wizard).
  - Salida operativa: worklist rankeada por severidad (pin fuera de provincia >
    discrepancia >5 km confirmada por 2 fuentes > discrepancia por 1 fuente > sin
    coordenadas y sin geocode posible > solo dirección sucia), cada ítem con la
    evidencia (tier, distancias, provincia detectada, links a Maps/OSM para verificar a
    ojo) y las dos acciones posibles: registrar override local (resolución manual
    existente en `sucursal_coordenadas`, procedencia 'manual'/'geocode') y/o exportar
    CSV "para corregir en Gestión" (Siges es read-only: la corrección real la hace un
    humano en Gestión; el CSV con Id_Sucursal + pin actual + pin sugerido + evidencia
    minimiza ese trabajo). Los OK no aparecen — solo se revisa lo que tiene evidencia.

FASE 3 — VERIFICACIÓN (parte del entregable, con números reales):
  - Gates en contenedor: `uv run lint-imports` · `uv run ruff check src tests` ·
    `uv run mypy src` · `uv run pytest tests/unit -q`; frontend `tsc` + `eslint`
    (regla de CLAUDE.md — si algo falla, no está terminado).
  - Unit de dominio con los casos REALES de la muestra 0.2, incluido textual el caso º
    ("Sucursal Nº 5" ↔ "Sucursal N 5") y el par trampa Nº(U+00BA)↔N°(U+00B0); cada
    regla de equivalencia con su test; el comparador difuso con positivos y negativos
    (nombres parecidos que NO deben proponerse).
  - Regresión de matching: para las filas que HOY sí matchean (N0), el pipeline nuevo
    propone exactamente el mismo vínculo (cero cambios en `ya_cargada`, refresco y
    diagnóstico sobre un PST de control, p.ej. PENTACOM 247/276).
  - Piloto SAN JUAN end-to-end: no_encontradas antes → después, desglosado en
    auto (N1) / confirmadas por operador / rechazadas / sin candidato; revisión muestral
    de vínculos confirmados sin falsos positivos detectados; tiempo de operador acotado
    (la meta es minutos revisando candidatos, no horas buscando a mano).
  - Geovalidación SAN JUAN completa: conteo de llamadas POR PROVEEDOR (Georef /
    Nominatim / Google) y costo Google en $ (esperado: $0 o ínfimo — dentro del free
    tier mensual); demostrar que re-correr la validación no re-llama a nadie (cache).
  - ALT002 y kms intactos: esta feature no toca `kms_recorrido`/`kms_a_facturar`; un
    reanálisis de una liquidación real de SAN JUAN da hallazgos idénticos antes/después.

[FORMATO]
- Todo texto al usuario en español de Argentina, directo, sin cortesías (CLAUDE.md).
- Commits atómicos en inglés (`feat(liquidaciones): ...`); matching y geovalidación en
  commits/fases separadas. Migraciones Alembic reversibles.
- ADR corto si: se agrega una dependencia de matching (no debería hacer falta), se
  cambia la semántica de `normalizar_nombre` compartida, o se decide auto-vincular N1.
- Documentar en `docs/liquidaciones/` la definición operativa (niveles N0/N1/N2,
  umbrales medidos, flujo de confirmación/rechazo, tiers de geovalidación y su orden) y
  agregar Georef y Nominatim a `docs/INTEGRACIONES_EXTERNAS.md` (URL, timeout, sin
  retry, política de uso, cache, tope) — que no les pase lo del hueco de Google Maps en
  el inventario ADR-018.
- Al cierre: resumen con comandos y salidas reales (números de Fase 0, resultado del
  piloto, conteo de llamadas por proveedor, gates en verde).

[RESTRICCIONES]
Operativas (innegociables, de CLAUDE.md):
- La DB de dev tiene datos reales de producción; la Tabla KM alimenta liquidaciones
  reales. Fase 0 no escribe nada; toda escritura posterior pasa por confirmación o por
  un modo auto explícitamente aprobado y reversible (vínculos, nunca kms).
- Siges/Gestión: SOLO SELECT (cuenta read-only) — jamás intentar corregir un pin o un
  domicilio en origen desde acá. Cero escrituras SOAP/wsAyC (fuera de alcance).
- `DISABLE_BACKGROUND_JOBS=true` verificado si se toca cualquier código que un job
  ejecute; sin hot reload: restart de contenedor + verificación con curl.
- Google Maps es key corporativa PAGA: cero llamadas sin autorización explícita; cache y
  tope por corrida siempre; ninguna prueba puede geocodificar el padrón entero.
- Nominatim: respetar la política publicada al pie de la letra (1 req/s, User-Agent
  propio, single-thread, cache, atribución) — incumplirla hace banear por IP.
- Georef: sin abuso — secuencial con pausa, backoff ante 429/5xx, cache; si el servicio
  está caído o sin cobertura para un caso, ese caso pasa al tier siguiente, no se
  reintenta en loop.

De arquitectura (ARCHITECTURE_GUIDE.md):
- Puertos en `liquidaciones/domain/repositories/`, adapters httpx en
  `liquidaciones/infrastructure/` — nada de llamar APIs desde use cases o routers. El
  matching y las validaciones Tier 0 son dominio puro con tests (las llamadas externas
  se mockean en unit).
- Toda escritura pasa por use case; `Page[T]` en colecciones; sin `except Exception`
  silencioso; tamaños §4 (archivo ≤300, clase ≤200, función ≤20); SQL parametrizado.

De negocio:
- El matching difuso NUNCA vincula solo: propone con score y motivo, el humano decide
  (requisito explícito del usuario). Solo N1 (determinístico) puede auto-vincular, y
  únicamente si la decisión 0.4.a lo aprueba.
- Un rechazo se recuerda: el mismo candidato no se re-propone en cada corrida.
- Ninguna regla de equivalencia entra sin un caso real de la muestra que la respalde y
  su test. La lista es configurable/extensible, no hardcodeo creciente sin evidencia.
- El geocode/la geovalidación jamás pisa coordenadas manuales ni de Siges sin
  confirmación humana (regla vigente de GEOLOCALIZACION_TABLA_KM.md); una sucursal que
  ninguna fuente puede ubicar queda explícitamente "sin ubicar", nunca con coords
  inventadas.
- No cambiar la semántica de km ni tocar ALT002 — fuera de alcance total.

[EJEMPLO]
Nota de cierre esperada:

  Matching sucursales + geovalidación SAN JUAN — cerrado y verificado:
  - Fase 0: no_encontradas_en_siges reales = <N> (usuario reportaba ~133); composición
    de la muestra: <a>% símbolo º/ª/°, <b>% abreviaturas, <c>% typos, <d>% renombres,
    <e>% inexistentes; umbral difuso calibrado = <s>.
  - Matching: N1 auto-vinculó <n1> (aprobado en 0.4.a, reporte adjunto); el operador
    confirmó <n2>, rechazó <n3>, quedaron <n4> sin candidato (alta manual/baja).
    no_encontradas: <antes> → <después>. Regresión PENTACOM: 247/276 idéntico.
  - Geovalidación: <T> sucursales procesadas; Tier 0 marcó <x> (…); Georef resolvió
    <y> reverse + <z> geocodes; Nominatim desempató <w>; Google usado en <g> casos
    (<$> gastados). Worklist final: <k> casos con evidencia, CSV para Gestión
    exportado; <m> overrides locales registrados.
  - Llamadas totales: Georef <n>, Nominatim <n> (1 req/s, política OK), Google <n>.
    Re-corrida: 0 llamadas nuevas (cache).
  - lint-imports · ruff · mypy · pytest unit (+<n>) · tsc · eslint — verde.
    Reanálisis liquidación <id> de SAN JUAN: hallazgos idénticos (ALT002 intacta).
```

---

## Notas de contexto para quien use este prompt (fuera del prompt en sí)

- **El bug del `º` es real y está demostrado, no inferido**: se ejecutó la función
  `normalizar_nombre` vigente del repo con Python 3: `'º'` es categoría Unicode `Lo`
  (letra), así que `isalnum()` da `True` y el filtro "no alfanumérico → espacio" no lo
  elimina; NFD tampoco lo descompone (solo NFKD lo mapea a `o`). Resultado verificado:
  `normalizar_nombre("Sucursal Nº 5") == "sucursal nº 5"` ≠ `"sucursal n 5"`. Bonus
  trampa: `N°` con SIGNO DE GRADO (U+00B0, categoría `So`) sí se elimina — dos strings
  visualmente idénticos (`Nº`/`N°`) normalizan distinto entre sí. Cualquier solución que
  no arranque por acá va a seguir perdiendo matches "invisibles".
- **Por qué niveles y no "un regex"**: un solo regex arregla el º y deja vivos Nro/Av/
  Bº/typos. El diseño por niveles da lo que el usuario pidió: N1 determinístico (arregla
  símbolo + abreviaturas conocidas, confianza de auto-vínculo), N2 difuso (propone
  candidatos con score y el humano elige). Y la lista de equivalencias sale de medir los
  ~133 reales (Fase 0.2), así que ninguna regla es inventada.
- **Por qué difflib y no una dependencia de fuzzy matching**: el volumen por corrida es
  ~487 filas × ~700 sucursales ≈ 3·10⁵ comparaciones, una vez por acción de wizard —
  stdlib sobra. Agregar rapidfuzz sería optimizar sin medición (y requeriría ADR).
- **Por qué Georef + Nominatim antes que Google**: Georef es oficial, gratuita y sin
  key (normaliza direcciones argentinas y hace reverse a provincia/departamento — justo
  la validación "¿este pin está donde dice estar?"); Nominatim es la segunda opinión
  independiente. Con dos fuentes gratis coincidentes, Google solo hace falta para el
  residuo ambiguo: el costo esperado del piloto completo es $0 (dentro de las 10.000
  gratis/mes por SKU incluso si el residuo existe). El punto no es solo plata: es que la
  key corporativa tiene regla de autorización explícita y esto escala a 35 PSTs.
- **Límites honestos de las fuentes gratis, con dato real**: se probó Georef en vivo el
  2026-08-19: el reverse `/ubicacion` respondió perfecto para coordenadas de San Juan
  capital (provincia/departamento/municipio con IDs), pero `/direcciones` devolvió 0
  resultados en 2 consultas de calles reales de la capital — la cobertura de calles de
  Georef para San Juan puede ser floja, y Nominatim (cuya cobertura depende de OSM en la
  zona) no pudo probarse desde acá. Por eso el diseño apoya la validación masiva en el
  reverse (confirmado) y trata el geocoding directo gratuito como best-effort medido en
  Fase 0 — son *validadores* (flags con evidencia), no fuente de verdad. Lo que ninguna
  fuente resuelve queda "sin ubicar" explícito, que ya es política del módulo.
- **Gestión no se corrige desde acá**: la cuenta Siges es de solo lectura por diseño
  (verificado en ADR-012/014). Por eso la salida de la geovalidación es doble: override
  local (mecanismo `sucursal_coordenadas` que ya existe y el cálculo de km ya respeta) y
  CSV de evidencia para que la corrección de fondo se haga en Gestión, una sola vez y
  con el trabajo ya masticado.
- **Fuentes consultadas (2026-08-19)**: doc oficial Georef
  (https://datosgobar.github.io/georef-ar-api/ y FAQ en argentina.gob.ar/georef —
  "completamente gratuito y no requiere autenticación"), política de uso de Nominatim
  (https://operations.osmfoundation.org/policies/nominatim/), pricing Google del propio
  repo (`docs/INTEGRACIONES_EXTERNAS.md` §11, verificado 2026-08-15 contra la consola).
