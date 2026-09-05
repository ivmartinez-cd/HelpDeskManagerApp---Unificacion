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
