# Revisión de liquidaciones — por qué "aplicar una tarifa" son 4 pasos en 3 módulos

Fecha: 2026-09-05. Reconstruido desde la DB de dev (`helpdesk-db`, datos reales, solo
`SELECT`) y el código del módulo. Caso disparador: INFOMAC, 2026-09-04, liquidación
3952-5 (agosto 2026, 89 incidentes, estado Recibida).

## 1. Cómo resuelve el motor la tarifa de un incidente

```
incidente (empresa, sucursal, tipo, fecha_cierre)
  → fila de Tabla KM del PST con ese par empresa+sucursal      (si no existe: ALT009 si cobró km)
  → spst_id de esa fila                                         (puede ser NULL)
  → tarifario del PST para (tipo, fecha) con ese spst_id
    o con spst_id NULL ("Genérica")                             (si no hay ninguno: ALT008)
```

`_resolucion.py::_tarifario_aplica` acepta la tarifa del SPST de la fila **o** la
genérica. Es decir: una fila sin SPST solo resuelve si el PST tiene tarifa genérica.

Las tarifas entran por el sync de Siges (`dbo.CostoServicio`, una fila por zona
descripta en texto) y cada zona se mapea a mano a un SPST **o a "Genérica"**
(`tarifario_zona_maps.spst_id NULL`).

## 2. Qué pasó con INFOMAC

| Dato | Valor |
|------|-------|
| PSTs con tarifa genérica vigente | 33 de 34 |
| INFOMAC: tarifas vigentes por SPST / genéricas | 24 / **0** |
| Zona Siges "Villa Mercedes / Rio IV / Sgo Estero / Bs.As." mapeada a | SPST Infomac - Villa Mercedes (no a Genérica) |
| Filas de Tabla KM de INFOMAC sin SPST | 117 de 390 (Buenos Aires 55, Río Negro 19, Neuquén 16, La Pampa 10, …) |
| 2026-09-04 14:38 | sync creó 150 vigencias, todas colgadas del SPST Villa Mercedes |
| 2026-09-04 15:56 | se tocaron las 390 filas de Tabla KM (`updated_at`) |
| Hoy, 3952-5 | 17 ALT008 pendientes; 16 tienen fila KM, 14 de ellas sin SPST |

Villa Mercedes es la sede del PST: esa zona de Siges es la tarifa base de INFOMAC y
debió mapearse a Genérica. Al mapearla a un SPST, toda sucursal sin SPST en Tabla KM
(Santa Rosa, Trenque Lauquen, General Pinto, Santiago del Estero…) quedó sin tarifa
resoluble aunque la tarifa estuviera cargada. "Vincular SPST por localidad"
(`proponer_vinculos_spst`) no propone nada porque "Santa Rosa" no es substring de
"Villa Mercedes", y no mira la provincia. Y una fila que sí se vinculó ayer (Dia %
Tienda 0353 General Pinto) sigue con ALT008 porque nadie volvió a Reanalizar.

Los precios sí difieren por zona (correctivo: Villa Mercedes 57.926, Gral. Roca
61.958, Norte Neuquén/Ushuaia 68.505), así que la zona importa para ALT001; pero la
zona base tiene que existir como genérica para que el resto resuelva.

Los 4 pasos / 3 módulos de ayer: Tarifarios (mapear zona, sincronizar) → SPSTs
(entender qué zona es cuál) → Tabla KM (vincular SPST, sin propuesta útil) →
Liquidación (Reanalizar). Ninguna pantalla dice "INFOMAC no tiene tarifa genérica y
117 sucursales no tienen zona; por eso 17 incidentes no tienen precio".

## 3. Arreglo del dato de INFOMAC — HECHO 2026-09-05

Ejecutado vía API con backup previo (`backups/helpdesk-db_2026-09-05_1631_infomac-tarifa-generica.dump`):
zona remapeada a Genérica, sync creó 150 vigencias genéricas (0 conflictos), reanálisis de
3952-5: 33 → 26 alertas, **0 ALT008**. Las 11 ALT001 que quedaron son reales y precisas:
Santa Rosa/La Pampa cobrada a precio Gral. Roca (30.975 vs 28.965 genérico), Cipolletti
ídem, Zapala cobrada a precio Norte Neuquén (68.505 vs 61.958). Decidir con la TL a qué zona
pertenece cada una (o aceptar la diferencia); son 3 localidades, no 17 incidentes sueltos.

Pasos que se hicieron:

1. Tarifarios → Sincronizar desde Siges → remapear la zona "Villa Mercedes / Rio IV /
   Sgo Estero /Bs.As." a **Genérica** → sincronizar. Crea las 6 vigencias genéricas
   (el sync solo agrega vigencias faltantes por grupo).
2. Reanalizar 3952-5. Las ALT008 de sucursales sin SPST desaparecen.
3. Cipolletti (Río Negro) va a dar ALT001 (61.958 esperado por Gral. Roca vs 57.926
   genérico): vincular esa fila al SPST Gral. Roca, o dejarlo como excepción.
4. Opcional: las 89 filas de Tabla KM hoy vinculadas al SPST Villa Mercedes pueden
   pasar a NULL y borrar ese SPST (`ON DELETE SET NULL` en `tabla_kms` y
   `tarifarios`; nada se pierde) — es el mismo caso que documenta
   `DEUDA_SPSTS_CREADOS_COMO_PST.md`, solo que sin el prefijo "PST " que el script
   de limpieza busca.

## 4. Cambios de producto para que no vuelva a pasar (chicos, en el lugar del problema)

Estado 2026-09-05: **1 (aviso), 2, 3, 4 y 5 implementados** (commits `b52423b` y el
siguiente del mismo día) — 2 y 5 en su versión mínima, dentro de patrones que ya existían:

- 2: en el modal "Gestionar" de una ALT008 sin zona aparece el bloque "Zona de la
  sucursal" (Genérica / SPSTs del prestador) + "Asignar zona y reanalizar"
  (`PUT /tabla-km/zona-sucursal`, `AsignarZonaSucursal`). Como todos los incidentes de la
  sucursal comparten la fila de Tabla KM, se resuelven juntos; el modal dice cuántos.
  Probado en vivo: Cartocor / Oficina Cipolletti → Gral. Roca, reanálisis automático,
  la ALT001 de Cipolletti desapareció (26 → 25 alertas en 3952-5). La vista agrupada por
  localidad ("Santa Rosa: 3 sucursales, 9 incidentes") sigue pendiente de mockup.
- 5: banner "N incidentes sin precio resoluble por configuración incompleta" arriba del
  ítem extra, derivado en el cliente de las alertas pendientes (ALT008 sin/con SPST,
  ALT009), con la acción de cada caso. Sin endpoint nuevo.

- 3 quedó como propuesta **opt-in**: el dry-run de INFOMAC mostró que la provincia no
  siempre es la zona tarifaria (Plottier/Neuquén → propondría Norte Neuquén, pero factura
  por Gral. Roca). Cada propuesta lleva `criterio` (localidad/provincia); las de provincia
  se aplican solo con el checkbox "Incluir propuestas por provincia" del modal.
- 4: `ReanalizarLiquidacionesAbiertas` corre al crear/editar/borrar/importar tarifarios
  y Tabla KM, al vincular SPST y tras el sync de tarifarios de Siges (solo si creó algo).
  Best-effort, logueado (§6). El botón Reanalizar queda como respaldo.
- 1 (parcial): el sync de Siges devuelve `prestadoresSinGenerica` y el modal lo muestra
  en rojo. Falta la propuesta automática de "Genérica" para la zona de la sede.

1. **Tarifa base obligatoria.** Al mapear zonas de Siges, proponer Genérica para la
   zona cuya descripción contiene la localidad del PST, y avisar (en el modal de
   sync y en Tarifarios) cuando un PST vinculado no tiene ninguna tarifa genérica
   vigente: "las sucursales sin zona no van a tener precio".
2. **Asignar zona desde la alerta, agrupado por localidad.** ALT008 con `spst_id`
   null hoy manda a Tabla KM con un buscador. En su lugar, en el detalle: "Santa
   Rosa, La Pampa — 3 sucursales, 9 incidentes → Zona: [Genérica ▾ / Gral. Roca /
   Norte Neuquén / Ushuaia]" y al confirmar escribe `tabla_kms.spst_id` de esas
   filas y reanaliza. Un paso, un lugar. Backend: `VincularFilasTablaKmASpst`
   (lote por ids) + reanálisis.
3. **Propuesta por provincia.** `proponer_vinculos_spst` compara solo
   localidad/cobertura. Agregar `spst.provincia == tabla_km.provincia_cliente`
   como criterio (Río Negro/Neuquén → Gral. Roca) y "sin candidato = Genérica" como
   propuesta explícita, no como "sin propuesta".
4. **Reanálisis automático** de las liquidaciones no terminales del PST al cambiar
   tarifas, mapeo de zona o `spst_id` de Tabla KM. Elimina el paso "acordate de
   Reanalizar", que es el que dejó la alerta de General Pinto colgada.
5. **Diagnóstico de configuración en el detalle de la liquidación.** Un bloque
   arriba de los incidentes, calculado en el backend: "N incidentes sin precio
   resoluble: sin tarifa genérica (sí/no), M sucursales sin zona, K pares fuera de
   Tabla KM", cada uno con su acción inline (punto 2). Es lo que ayer nadie pudo
   ver.

Orden: 3 y 4 son backend puro y chicos; 2 y 5 necesitan una decisión de UI (mockup)
pero son un componente nuevo en una pantalla existente, no un rediseño; 1 es una
validación más una propuesta.

## 5. Chequeo del resto de los prestadores (2026-09-05, solo lectura)

Consultas sobre `helpdesk-db` + `GET /siges/zonas` + dry-run del sync de tarifarios:

- **Ningún otro prestador tiene el problema de INFOMAC**: los 34 vinculados tienen tarifa
  genérica y las 41 zonas de Siges están mapeadas (0 sin mapear).
- **Vigencias que cierran el 2026-09-30** (tarifa `2026-07-01` con `vigencia_hasta`
  cargada, en vez de abierta): SM TUCUMAN (6/6 tipos), VENADO (4/6), CHACO (3/6). Desde
  el 1 de octubre todo incidente de esos PST da ALT008 hasta que alguien corra
  "Sincronizar desde Siges" — y Siges todavía no publicó ninguna vigencia posterior a
  julio para ningún PST (dry-run: 0 a crear en todos). ~~El sync trimestral es manual: no
  hay job que lo corra.~~ **Cerrado el mismo día**: job `liquidaciones_sync_tarifarios`
  (diario, `LIQUIDACIONES_SYNC_TARIFARIOS_INTERVAL_MINUTES=1440`) que aplica el sync para
  todos los vinculados, solo crea vigencias faltantes, loguea conflictos como WARNING y
  reanaliza las abiertas si creó algo. Primer ciclo real: creadas=0, conflictos=26.
- **Conflictos local ≠ Siges que el sync nunca pisa** — resueltos el mismo día (backup
  `backups/helpdesk-db_2026-09-05_1909_tarifas-conflictos-siges.dump`):
  - TUCUMAN: no era un dato mal cargado. Sus dos zonas de Siges ("TMTA122 - TUCUMAN" y
    "TMTA122 - SGO DEL ESTERO") estaban mapeadas a la misma genérica con distinto costo de
    km (433,9 vs 454,9, y así en cada trimestre); el 2026-08-13 se había dejado Sgo del
    Estero sin mapear a propósito y alguien la mapeó a Genérica el 08-14. Primero se le
    dio un SPST propio; al confirmar el usuario que **NAPA ya no atiende Santiago del
    Estero**, se desarmó (tarifas, mapeo y SPST borrados) y la zona vuelve a quedar **sin
    mapear a propósito**, como el 08-13. El sync diario la va a listar como "1 zona sin
    mapear" (Siges todavía la publica); si molesta, agregar una marca "zona ignorada".
    La genérica conserva los valores de Tucumán. 0 conflictos.
  - SAN JUAN instalación 92.252: **se mantiene** — es la "regla del doble" confirmada por el
    usuario el 2026-08-13 (`LIQUIDACION_PRESTADORES_MIGRACION_ESTADO.md`, decisiones ADR-014).
    Sigue apareciendo como 1 conflicto en cada sync a modo de recordatorio.
  - VENADO instalación 2026-07: corregido a 66.749 (valor de Siges; la diferencia de $45
    era una carga manual). 0 conflictos.
- SPSTs con filas de Tabla KM pero sin tarifa propia (PENTACOM 8, SUPERNOVA 2) caen a la
  genérica y Siges solo tiene una zona para esos PST: no es un problema.
- Las liquidaciones con ALT001 en el 100 % de los incidentes son del prestador, no de
  config: SAN JUAN 3944-6/3946-4 cobró $1 por incidente; 3945-5 mezcla precio viejo
  (50.231), doble (108.800) y zona; SALTA 3960-4/3954-3 cobró otro precio.

## 6. Liquidaciones de abono (2026-09-05)

SAN JUAN factura por contrato mensual: cierra todos los incidentes a $1 en AyC y carga el
importe real como ítem extra (tres conceptos por mes: Mantenimiento Técnico Centro Cívico
5,1–7,66 M; Recursos adicionales Escuelas / Depósito ~1,91 M; Adicional Factura Servicios
Cívico 1.499.999). 31 liquidaciones reales desde enero con exactamente ese patrón; el CSV
legacy ya las etiquetaba `cc`/`preco`. El sync de AyC las creaba como `regular` y el motor
generaba una ALT001 por incidente (105 por mes) que nadie miraba. **SALTA no es este caso**:
cobró precios distintos de verdad, sus alertas son legítimas.

Decisiones del usuario (mismo día): detección **automática** ("todos los incidentes a $1",
opción 1A); **sin alerta por monto** (el abono varía siempre); lo único a controlar es que
el extra esté cargado.

Implementado:
- `TIPO_ABONO = "abono"` + `domain/services/tipo_abono.py` (`es_abono`,
  `tipo_segun_incidentes`, `reglas_aplicables`). El sync lo fija al crear y la
  reconciliación lo recalcula con los incidentes ya reconciliados (`update_tipo_liquidacion`).
- `ReanalizarLiquidacion` corre solo `reglas_aplicables(tipo)`: en un abono se apagan
  ALT001/002/003/005/008/009; quedan los duplicados (ALT004/ALT010). Las alertas viejas ya
  trabajadas por la TL se preservan (misma semántica que desactivar la regla).
- Migración `a9c4e2f7b1d3`: backfill de las 31 existentes (todas SAN JUAN). Reanálisis en
  vivo: 3944-6 20 → 0 alertas; 3946-4 113 → 8 (solo ALT010, duplicados reales).
- UI: banner "Liquidación de abono" en el detalle, en naranja si falta el extra ("no aprobar
  hasta entonces"), con los últimos 6 abonos del prestador (período, monto, concepto) para
  comparar a ojo. La etiqueta de tipo del encabezado ya muestra "abono".

## 7. Acuerdos de precio por cliente (2026-09-05)

Corrección al §5: las ALT001 de SALTA no son errores del prestador sino arreglos por
cliente que la TL resolvía a mano cada mes con el mismo motivo: mineras (Minera del
Altiplano, Sal de Vida, Sales de Jujuy) al doble ("Costo doble aprobado por AO", 32 alertas
resueltas así), Refinor a 78.119/53.180, YAGUAR al precio viejo 46.073.

Implementado (commit del mismo día): tabla `acuerdos_precio_cliente` (prestador + cliente
+ tipo opcional + factor o precio fijo + motivo + vigencia), pantalla Configuración >
Acuerdos por cliente, y ALT001 toma el precio del acuerdo como esperado
(`resolver_acuerdo` + `evaluar_alt001(…, acuerdo)`): sin alerta si cobra lo acordado, y si
cobra otra cosa la alerta dice "difiere del acuerdo con X (motivo)". Toda escritura
reanaliza las abiertas del prestador. Atajo desde el modal Gestionar de una ALT001:
"Cargar acuerdo de precio para {cliente}" con cliente/tipo/precio cobrado precargados.
Probado en vivo con ida y vuelta sobre 3960-4 (acuerdo Refinor correctivo 78.119: 20 → 13
ALT001; borrado: 20 de nuevo). Los acuerdos reales los carga la TL.

## 8. Tabla KM — cuatro mejoras (2026-09-05)

Datos al arrancar: 2.748 filas, 1.229 usadas por alguna liquidación de 2026, 1.660 sin km
esperado (solo 75 usadas en 2026), 2.576 sin coordenadas. En las liquidaciones abiertas, 45
ALT002 pendientes: 19 "fila sin km" (esperado 0), 21 "cobró 0 km" (mismo viaje), 5 reales.

1. **La tabla se completa desde las liquidaciones.** ALT002 sobre una fila sin km ya no dice
   "km incorrectos": marca `sin_referencia` y el modal Gestionar ofrece "Tomar N km como
   referencia" (`PUT /tabla-km/km-referencia`, `FijarKmReferencia`, reanálisis automático).
   Cuenta en el banner de configuración incompleta. Probado con ida y vuelta.
2. **Ruta compartida en un clic.** ALT002 con 0 km cobrados y sin corredor que matchee lleva
   `candidatos` (incidentes del mismo día que sí cobraron km, hasta 5); el modal ofrece
   "Mismo viaje que #N" + "Confirmar ruta compartida" (resuelve con "Km asociado a otro
   incidente" y el vínculo). Tras reanalizar las abiertas: 19 sin referencia, 10 posible ruta
   compartida, 16 diferencias reales. La vista agrupada por día sigue pendiente de mockup.
3. **Distancias con OpenStreetMap.** Proveedor `osrm` (`HttpxOsrmGateway`, servicio `table`
   con `annotations=distance`, mismo puerto que Google) elegido por `DISTANCIAS_PROVEEDOR`
   en `.env` (activado en dev; tope propio `OSRM_MAX_CALLS_PER_RUN=4000`, así SAN JUAN con
   1.738 rutas ya no queda bloqueado). Preview real de BAHIA: 58 filas en 8 s, 4 sin ruta (un
   pin de Gestión en California). **Nada aplicado**: aplicar pisa `kms_a_facturar` de las
   filas existentes (706 tienen km medido ≠ facturado) — correr el asistente por prestador y
   revisar el preview antes de aplicar. El servidor público de OSRM es un demo sin SLA;
   `OSRM_BASE_URL` permite uno propio. Pendiente: los textos del asistente siguen diciendo
   "consumo Google".
4. **Archivado.** Columna `tabla_kms.archivada` (migración `c3e8f1a9d2b4`) con backfill de
   las 1.519 filas sin actividad en 2026; la pantalla las oculta por default ("Mostrar N
   archivadas"), botón Archivar/Restaurar por fila, el motor no las distingue.

## 9. Direcciones de Tabla KM con OpenStreetMap (2026-09-05)

Pedido del usuario: arreglar todas las direcciones sin depender de Google. Los flujos ya
existían (geocodificar sucursales sin pin, auditar pines contra la dirección, corregir pin,
bandeja del Asistente de KM) atados a Google; se agregó Nominatim/OpenStreetMap detrás del
mismo puerto (`GEOCODING_PROVEEDOR=osm`, activo en dev, commit `8e770f02`), con segundo
intento por nombre del cliente (nunca se auto-resuelve) y reuso de la caché de direcciones
(4.817 → 6.462 tras la pasada).

Pasada completa sobre los 34 prestadores vinculados (dos tandas; la primera perdió los
últimos 24 por respuestas vacías transitorias y se repitió con códigos HTTP, todos 200):

| Resultado | Total |
|---|---|
| Sucursales sin pin resueltas solas (candidato único y preciso) | 92 |
| Sucursales con candidatos para que la TL elija (bandeja) | 68 |
| Sucursales sin ningún resultado (ni dirección ni nombre) | 26 |
| Pines de Gestión sospechosos (> 5 km de su dirección) | 516 |
| Consultas nuevas a Nominatim (1/s, con User-Agent propio) | 1.615 |

Los más cargados: PENTACOM (43 resueltas, 23 a revisar, 70 pines), SAN JUAN (100 pines
sospechosos, tope del listado), SUPERNOVA (8/10/60), MENDOZA (7/6/44). Nada se aplicó sobre
pines existentes: la auditoría los lista y la TL confirma cada corrección desde el
asistente (Momento 2, "pines a verificar" / "ubicaciones por resolver"). Las 92 resoluciones
automáticas sí quedaron guardadas (`sucursal_coordenadas`, procedencia `geocode`) y las
usa el cálculo de km. Pendiente: los textos del asistente siguen hablando de Google.

## 10. Pelotón de agentes sobre los pendientes de geolocalización (2026-09-05)

Seis agentes en paralelo, un grupo de prestadores cada uno, con reglas mecánicas escritas
en un archivo compartido y sin acceso a servicios externos (solo los cuatro endpoints del
backend: listar pines sospechosos, corregir pin, listar coordenadas pendientes, elegir
candidato). Backup previo `backups/helpdesk-db_2026-09-05_2129_pre-peloton-geoloc.dump`.

Reglas: corregir un pin solo si está a ≥ 50 km de su dirección, el geocode es preciso
(ROOFTOP) y la localidad coincide; elegir candidato solo si hay exactamente uno preciso en
la localidad; nunca coordenadas manuales. Ajuste descubierto por el grupo 2 y propagado a
todos antes de escribir: cuando la localidad se llama igual que la provincia (Córdoba,
Mendoza, Salta, San Juan, Santa Fe…) la coincidencia literal daba por buena cualquier ciudad
de la provincia; se exigió que la localidad aparezca dos veces (ciudad + provincia). Sin ese
ajuste se habrían movido mal ~45 pines correctos de capitales.

| Resultado | Total |
|---|---|
| Casos evaluados | 1.135 |
| Pines corregidos (override en `sucursal_coordenadas`) | 82 |
| Coordenadas elegidas | 11 |
| Dejados con motivo | 1.006 |
| Errores de escritura | 0 |

Dejados, por qué: 388 con discrepancia < 50 km (rural, puede estar bien); 218 con geocode
impreciso entre 50 y 1.000 km; **141 "PIN ROTO en Gestión"** (pin en California
36.78/-119.42, en Madrid, en Chubut para sucursales de Rawson-San Juan, o en el centroide de
Argentina: valores por defecto de Gestión) — lista para corregir en Gestión en
`geoloc-2026-09-05-pines-rotos-para-gestion.tsv`; 131 coordenadas ambiguas o sin candidatos
(`geoloc-2026-09-05-coordenadas-para-la-tl.tsv`); 72 frenados por el ajuste de provincia.
Las correcciones aplicadas están en `geoloc-2026-09-05-correcciones-aplicadas.tsv`; dos
escrituras de SAN JUAN hechas antes del ajuste (14169 Centro Cívico, 322) quedan marcadas
REVISAR aunque mejoran lo que había. Candidatos a corregir a mano que la regla no permitió:
INFOMAC 11046/8341/14297 (Neuquén capital, el geocoder omite la provincia), MENDOZA 10646
(Mendoza Plaza Shopping), SAN LUIS 7019 (Credicoop, pin en Rosario).

Fix derivado: `ListarPinesSospechosos` ya no lista los pines con override (antes los 82
corregidos seguían apareciendo con su discrepancia original).

## 11. Segunda pasada del pelotón (búsqueda en el mapa) y km para toda la Tabla KM (2026-09-05/06)

**Pelotón 2**: seis agentes sobre los 277 casos que la primera pasada dejó (141 pines rotos,
131 coordenadas ambiguas, 5 recomendados), buscando cada sucursal por su cuenta: dirección de
Gestión en OpenStreetMap con variantes, búsqueda web del cliente, y validación por
geocodificación inversa antes de escribir. Puente `osm.sh` de carril único (flock + 1 req/s
para todos los agentes) y endpoint nuevo `PUT …/sucursal/{id}/pin-manual` (coordenadas +
fuente, rechaza fuera de Argentina). Resultado: **153 sucursales ubicadas con fuente citable**
(`geoloc-2026-09-06-pines-manuales-cargados.tsv`; SAN JUAN 74, con el Mapa Educativo
Nacional y GEOSanJuan como corroboración de las escuelas) y **66 dejadas con el mejor
indicio** (`geoloc-2026-09-06-dejados-para-gestion.tsv`): casi todas plantas o estaciones
sobre rutas ("RN9 km 1471") que OSM no tiene mapeadas, o direcciones con la provincia
equivocada en Gestión. Lección: el agente del grupo 5 se trabó 4 h leyendo notas de diario;
se cortó y se relanzó con tope de 4 consultas por caso. Los agentes de búsqueda necesitan
tope de consultas y de tiempo desde el arranque.

**Km para toda la tabla** (`AplicarCalcularDistancias` con `soloSinKm`, commit `c393336e`):
- 25 prestadores no tenían base de despacho: se fijó desde Gestión (única sede con
  coordenadas; CHACO → Resistencia).
- Pasada sobre los 34 prestadores con OpenStreetMap: 982 filas creadas (sucursales con
  actividad que no estaban en la tabla), 1.290 completadas, 767 negociadas sin tocar.
- Dos errores detectados y corregidos: (a) INFOMAC medía todo desde Villa Mercedes porque
  Gestión tiene 18 SPST de Infomac con sede propia y nosotros 4 → se crearon los 15 que
  faltaban con su sede, se vincularon 29 sucursales por localidad y el cálculo pasó a medir
  **desde la sede más cercana** (varias sedes comparten zona tarifaria, así que
  `id_costo_servicios` no alcanzaba); (b) 7 resoluciones automáticas de la pasada 1 cayeron
  en otra ciudad (la trampa localidad = provincia otra vez) → revertidas. Los km medidos
  desde base equivocada o con pin roto (328 filas) se volvieron a cero antes de recalcular.
- Regla ALT002: "cobró 0 km" sin ningún viaje ese día ya no alerta (nunca es sobrecobro);
  antes, al llenar la tabla, cada cliente lejano al que el prestador no viajó daba "cobró 0
  vs 1.560 km" (195 ALT002 pendientes en abiertas → 50 tras la regla y la corrección).

Estado final de la Tabla KM: 3.847 filas (2.328 activas), 2.208 con km medido, 1.104 con km
facturable (el resto en cero por la regla de viático), 1.813 con pin; 400 sucursales con
coordenadas resueltas localmente (247 por geocode, 153 manuales con fuente). Los pines de
Gestión no se tocan: las correcciones viven en `sucursal_coordenadas` y tienen prioridad.
