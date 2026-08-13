# ADR-014: SigesReadOnly como fuente de sync para la configuración de Liquidaciones; wsAyC reservado para preliquidaciones

## Estado: Propuesto (pendiente de revisión del usuario antes de implementar la Fase 3)

## Contexto

El módulo `liquidaciones` carga hoy su configuración (prestadores/SPSTs, tarifarios,
tabla KM) por tres vías manuales: import CSV por entidad, import del Excel maestro de
PST (`ImportarPrestadorMaestro`) y ABM en las 4 pantallas de configuración. El master
prompt `MASTER_PROMPT_AUTOMATIZACION_FUENTES_LIQUIDACIONES.md` pide reemplazar/
complementar esa carga con una fuente automatizada: wsAyC (SOAP) o SigesReadOnly
(SQL Server MERCURIO, cuenta de solo lectura).

La Fase 1 (`SIGES_READONLY_LIQUIDACIONES_VALIDACION.md`, 2026-08-13) validó ambas
fuentes con dato real. Lo determinante:

- **`dbo.CostoServicio` es el tarifario real por PST**, con paridad exacta contra el
  catálogo local (6 vigencias de PENTACOM idénticas número por número), formato wide
  (una columna por tipo de servicio), zona en `descripcion` y cadena trimestral de
  `fecha_vigencia`. ~41 PST con vigencia del trimestre actual cubren los 35 locales.
- **`dbo.Empresa` cataloga PST y SPST** (prefijos `'PST '`/`'SPST'` en `Den_Comercial`)
  con `cuit`/`razon_social`, y los 7 prestadores muestreados matchean 1:1 con el
  catálogo local. Semántica de `Estado` confirmada con consulta dirigida (2026-08-13):
  **`0`=activo, `1`=inactivo** (los 40 PST con vigencia tarifaria actual tienen todos
  `Estado=0`; los 83 registros `'NO USAR'` tienen todos `Estado=1`).
- **El km esperado por par cliente-sucursal no existe en ninguna fuente** — solo los
  pares (`dbo.Sucursal.ID_Prestador` → PST) y lo cobrado por incidente
  (`IncidenteCosto.CantidadKm`). Es dato manual del acuerdo comercial.
- **wsAyC expone el mismo universo con menos campos** para config (`getTechnicians`
  devuelve `{id: nombre}` con los mismos `ID_Empresa`), pero expone además la
  preliquidación completa: `getLiquidationDetails(3876)` devolvió los 111 incidentes
  exactos de la liq local `3876-6` con las mismas columnas del CSV que hoy sube la
  Team Leader. La numeración local es `ID_Liquidacion` de Siges + dígito módulo-10.

Antecedentes de diseño que esta decisión hereda:

- ADR-012: patrón ya aceptado de consultar SigesReadOnly con pyodbc parametrizado,
  conexión efímera, `ExternalServiceError` (como `PyodbcSlaQueryGateway`).
- Módulo `prestadores` (otro catálogo, sin FK con este): política "el sync actualiza,
  nunca auto-crea" tras el incidente del legacy que auto-creó ~29 prestadores fuera de
  alcance. En Siges hay PSTs que no existen en el catálogo local de liquidaciones
  (Esquel, Gral Pico, Rafaela, Reconquista, Tres Arroyos, etc.) — el riesgo es real
  también acá.
- Caracterización §4: el sync de la rama legacy `feature/ws-ayc-liquidaciones` pisa
  estado local (delete+recreate con cascade que pierde observaciones) — anti-patrón
  explícito a no repetir.

## Decisión

**SigesReadOnly es la fuente de sync para los tres datasets de configuración. wsAyC no
se usa en esta iteración** (queda como fuente natural del futuro import de
preliquidaciones, fase separada con diseño propio de reconciliación de estado).
Razones: más campos (`cuit`, `razon_social`, `fecha_vigencia`, zona), sin capa SOAP
intermedia ni parsing JSON-en-string, paridad ya demostrada con dato real, y patrón de
acceso ya aceptado (ADR-012) y productivo (`sla`, `prestadores`).

### Por dataset

1. **Prestadores y SPSTs** — sync desde `dbo.Empresa` (`Estado=0`, prefijos
   `'PST '`/`'SPST'`): **solo actualiza** `nombre`/`cuit`/vigencia de filas ya
   vinculadas, **nunca crea ni desactiva** (misma política que
   `SyncPrestadoresDesdeSiges` del módulo `prestadores`). Los PST de Siges sin
   equivalente local se reportan como "disponibles, no vinculados" en el resultado del
   sync — el alta sigue siendo decisión explícita de la UI.
2. **Tarifarios** — sync desde `dbo.CostoServicio`: pivot wide→long
   (`correctivo`→`correctivo`, `preventivo`→`preventivo`,
   `instalacion`→`instalacion_desinstalacion`, `PreCorrectivo`→`pre_correctivo`,
   `guardia`→`guardia`, `sistemas`→`sistemas`; se ignoran `inclusion_a_contrato`,
   `relevamiento`, `presupuesto`, `taller` — el CSV nunca los trajo y el motor de
   reglas no los usa). Crea solo vigencias faltantes por grupo
   (prestador, tipo_servicio, zona); toda alta entra por `CreateTarifario`, que
   recadena vigencias — el sync no toca repos directo.
3. **Tabla KM** — **alta asistida on-demand desde `dbo.Sucursal`, NO prepoblado
   masivo**. La verificación de Fase 2 mostró que Siges tiene 762 pares vigentes para
   PENTACOM (`ID_Prestador=137`, `Estado=0`) contra 276 en la tabla local: la tabla
   local es un subconjunto curado por la Team Leader (solo los pares que efectivamente
   facturan km) — un prepoblado masivo agregaría ~500 filas sin uso por PST y
   degradaría la pantalla. En cambio: al dar de alta un par (desde la pantalla de
   Tabla KM, o al resolver una alerta ALT009 "par no encontrado"), la UI ofrece
   búsqueda/autocompletado contra las sucursales vigentes del PST en Siges y precarga
   `empresa_nombre`/`sucursal_nombre`/`domicilio`/`localidad` — **el valor de km sigue
   siendo manual**, el sync jamás lo escribe ni lo sugiere como autoritativo. La
   semántica de `Sucursal.Estado` quedó verificada con dato real: `0`=activo (las 1358
   sucursales con incidentes desde 2026-07-01 tienen todas `Estado=0`).

### Vínculo persistente y mapeo de zonas

- Se agrega **`siges_empresa_id` (nullable, UNIQUE) a `prestadores` y `spsts`** de
  liquidaciones — mismo patrón que el módulo `prestadores`. El vínculo inicial se hace
  una sola vez desde la UI (propuesta automática por matching de nombre, confirmación
  manual); el sync posterior solo opera sobre filas vinculadas. Sin vínculo, la fila
  queda fuera del sync — nunca matching por nombre en runtime (los nombres difieren:
  `'PST Cordoba - Pentacom S.A.'` vs `'Cordoba - Pentacom S.A.'`).
- **Mapeo de zonas**: `CostoServicio.descripcion` no coincide literalmente con la
  `zona` local (`'General Roca / Rio Negro / Neuquen / Cipoletti'` vs
  `'Gral. Roca / Neuquén'`). Se persiste una tabla de mapeo por prestador
  (`descripcion_siges` → `zona_local`), poblada igual que el vínculo de prestadores:
  propuesta automática, confirmación manual la primera vez. `descripcion` con valores
  `'DE BAJA'`/`'Sin servicio'` se excluyen del sync.

### Estrategia de ejecución y convivencia

- **Sync manual por botón** en las pantallas de configuración, con **dry-run
  first-class**: el endpoint devuelve siempre el detalle
  creados/actualizados/omitidos/conflictos, y solo escribe con `dryRun=false`
  explícito. **Sin job de fondo en esta iteración** — si algún día se automatiza,
  requiere ADR propio y respeta `DISABLE_BACKGROUND_JOBS`.
- **Política de conflictos**: el sync nunca borra ni recrea filas. Si una fila local
  vinculada difiere de Siges en un campo que el sync gestiona (ej. un costo de una
  vigencia ya existente), se **reporta como conflicto sin escribir** — la resolución
  es manual desde la UI. Los datos editados a mano nunca se pisan sin confirmación.
- **El import CSV/Excel y el ABM manual se mantienen intactos** como fallback hasta
  que el sync acumule un período de convivencia validado por la Team Leader; recién
  entonces se decidirá (con el usuario) si se retira alguna vía manual.

## Consecuencias

- Positivas: se elimina la dependencia de planillas intermedias para tarifarios — el
  dato sale de la misma tabla que alimenta esas planillas, con paridad demostrada; el
  recadenado de vigencias queda garantizado por construcción (todo pasa por los use
  cases existentes); la numeración módulo-10 confirmada habilita, a futuro, el import
  de preliquidaciones por WS sin romper la dedup de ALT004.
- Negativas / deuda asumida: `liquidaciones` pasa a depender de MERCURIO (tercer
  módulo, tras `sla` y `prestadores`) — caída de MERCURIO significa sync no disponible
  (el fallback manual mitiga); el vínculo `siges_empresa_id` y el mapeo de zonas
  requieren una pasada manual inicial de la Team Leader/usuario; el km esperado sigue
  siendo manual por inexistencia de fuente (limitación del negocio, no de esta
  decisión); la tabla KM no gana un sync propiamente dicho sino un alta asistida — la
  curaduría de qué pares existen sigue siendo humana, a propósito.
- El import de preliquidaciones por wsAyC (el objetivo real de la rama legacy) queda
  explícitamente fuera: antes exige diseñar la reconciliación estado-TL vs estado-AyC
  (hoy una sola columna `estado`) que la caracterización §4 marca como no resuelta.
- Revisar esta decisión si aparece una fuente para el km esperado (ej. si el negocio
  lo carga en Siges) o si wsAyC agrega una operación de catálogo de tarifas con más
  campos que `CostoServicio`.
