# Validación de fuentes — automatización de config de Liquidaciones (Fase 1)

Entregable de la Fase 1 de `MASTER_PROMPT_AUTOMATIZACION_FUENTES_LIQUIDACIONES.md`:
¿wsAyC y/o SigesReadOnly contienen los datasets que hoy se cargan por CSV/Excel en el
módulo `liquidaciones` (prestadores/SPSTs, tarifarios, tabla KM)? Validado con dato
real el **2026-08-13**, solo lectura, contra:

- **SigesReadOnly**: `MERCURIO.cdsa.com.ar` / base `SiGes`, cuenta `SiGesReadOnly`
  (re-verificado en esta sesión: `db_datareader=True`, `db_datawriter=False`).
  Script: `backend/scripts/explore_siges_liquidaciones.py` (2 rondas).
- **wsAyC**: `https://wsg.cdsisa.com.ar/wsAyC_server.php` (WSDL real, 110 operaciones;
  respuestas JSON-en-string, mismo contrato que usa `insumos`). Solo operaciones `get*`.
  Script: `backend/scripts/explore_wsayc_liquidaciones.py`.

Referencia local contra la que se cruzó (helpdesk-db, datos reales migrados del legacy):
36 prestadores, 55 SPSTs activos, 4832 tarifarios, 1644 tabla_kms, liquidación real
`3876-6` (111 incidentes).

## Veredicto ejecutivo

| Dataset | SigesReadOnly | wsAyC |
|---|---|---|
| Prestadores | ✅ **DISPONIBLE** — `dbo.Empresa`, prefijo `'PST '` en `Den_Comercial` | ✅ DISPONIBLE — `getTechnicians` (IDs = `ID_Empresa`) |
| SPSTs | ✅ **DISPONIBLE** — `dbo.Empresa`, prefijo `'SPST'` (41 filas) | ✅ DISPONIBLE — mismos IDs en `getTechnicians` |
| Tarifarios | ✅✅ **DISPONIBLE CON PARIDAD EXACTA** — `dbo.CostoServicio` (cadena de vigencias idéntica a la local; zona = `descripcion`) | ⚠️ INDIRECTO — no hay operación de catálogo; `getLiquidationDetails` trae la tarifa aplicada por incidente |
| Tabla KM — pares empresa/sucursal | ⚠️ PARCIAL — `dbo.Sucursal.ID_Prestador` da los pares vigentes, sin km | ⚠️ PARCIAL — `getSucursales(idEmpresa)` por cliente, sin km |
| Tabla KM — **valor de km esperado** | ❌ **NO DISPONIBLE** | ❌ **NO DISPONIBLE** |
| (Bonus) La preliquidación en sí | ✅ `dbo.Liquidacion` + `dbo.IncidenteCosto` (dominio vivo) | ✅✅ `getLiquidationById/Details/Resume` — **111/111 incidentes vs la liq local `3876-6`**, mismas columnas que el CSV |

Conclusión: la automatización es viable para **tarifarios** (fuente ideal: SigesReadOnly,
paridad exacta ya demostrada) y para **prestadores/SPSTs** (ambas fuentes). Para tabla KM
solo se pueden prepoblar los **pares** (el km esperado es un dato del acuerdo comercial
que no existe en ninguna fuente — se confirma el diseño `kms_pendientes` que insinuaba la
rama legacy). Hallazgo no buscado: el reemplazo del CSV **completo** de preliquidaciones
por WS es factible hoy — `getLiquidationDetails` devuelve exactamente las columnas que el
parser CSV importa.

## Evidencia por dataset

### 1. Tarifarios → `dbo.CostoServicio` [CONFIRMADA con paridad exacta]

18 columnas: `id`, `ID_Empresa` (FK al PST en `Empresa`), `Nombre_Empresa`
(desnormalizado), costos por tipo de servicio en **formato wide** (`correctivo`,
`preventivo`, `instalacion`, `inclusion_a_contrato`, `relevamiento`, `presupuesto`,
`PreCorrectivo`, `guardia`, `taller`, `sistemas`), `CostoKm`, `fecha_vigencia`,
`prestador_id` (= `ID_Empresa` en todas las filas vistas), `descripcion`, `habilitado`.

**Paridad exacta con el tarifario local de PENTACOM** (`ID_Empresa=137`, las 6 últimas
vigencias, columna `correctivo` + `CostoKm`):

| Siges `fecha_vigencia` | Siges `correctivo`/`CostoKm` | Local `vigencia_desde` | Local `costo_servicio`/`costo_km` |
|---|---|---|---|
| 2026-07-01 | 67820.00 / 758.96 | 2026-07-01 | 67820 / 758.96 |
| 2026-04-01 | 63522.00 / 710.85 | 2026-04-01 | 63522 / 710.85 |
| 2026-01-01 | 58042.00 / 649.53 | 2026-01-01 | 58042 / 649.53 |
| 2025-10-01 | 53814.00 / 602.22 | 2025-10-01 | 53814 / 602.22 |
| 2025-07-01 | 50780.00 / 568.27 | 2025-07-01 | 50780 / 568.27 |
| 2025-04-01 | 47901.00 / 536.05 | 2025-04-01 | 47901 / 536.05 |

Coincidencia completa — la planilla Excel de la que sale el CSV/maestro se alimenta de
(o alimenta a) esta tabla. **Siges es fuente de verdad utilizable para tarifarios.**

- Volumen: 1329 filas, 96 `ID_Empresa` distintos (incluye PSTs históricos). ~41 PSTs
  con `MAX(fecha_vigencia) = 2026-07-01` (trimestre vigente) — cobertura completa de
  los 35 prestadores reales locales.
- **Zona = `descripcion`**: INFOMAC (`740`) tiene grupos por zona
  (`'General Roca / Rio Negro / Neuquen / Cipoletti'`, `'Rincon de los Sauces - Chos
  Malal - Barrancas - Buta Ranquil'`, `'Ushuaia - Infomac'`, `'Villa Mercedes / Rio IV
  /Sgo Estero /Bs.As.'`) que se corresponden con las zonas locales (`'Gral. Roca /
  Neuquén'`, `'Rincon de los Sauces - ...'`, `'Ushuaia'`, `'Villa Mercedes'`) — **los
  nombres NO son idénticos**, el sync necesita una tabla de mapeo zona-Siges → zona-local
  (o adoptar el nombre Siges). San Juan (`504`) tiene `'GSJ - Escuelas Valle Fertil'`,
  `'GSJ - GI Centro Civico'`; PENTACOM solo `'Genérica'` (zona local vacía). Valores
  especiales a filtrar: `'DE BAJA'`, `'Sin servicio'`.
- Mapeo wide→long para el modelo local (`tipo_servicio` por fila): `correctivo`→
  `correctivo`, `preventivo`→`preventivo`, `instalacion`→`instalacion_desinstalacion`,
  `PreCorrectivo`→`pre_correctivo`, `guardia`→`guardia`, `sistemas`→`sistemas`. Las
  columnas `inclusion_a_contrato`/`relevamiento`/`presupuesto`/`taller` no tienen
  equivalente local (el CSV nunca las trajo) — decidir en Fase 2 si se ignoran.
- SPSTs **no** tienen filas propias (verificado con 868, 1079, 138, 140, 150, 905,
  1143: 0 filas) — las tarifas zonales van por `descripcion` del PST padre, consistente
  con el modelo local (tarifario por prestador+zona, no por SPST).

### 2. Prestadores y SPSTs → `dbo.Empresa` [CONFIRMADA con salvedad de `Estado`]

Convención de nomenclatura en `Den_Comercial`: `'PST <zona> - <nombre>'`,
`'SPST <pst> - <localidad>'` (y `'PR ...'` en `razon_social` para puntos de reventa).
Cruce por nombre de los prestadores locales: los 4 grandes matchean uno a uno
(`PENTACOM`→137, `SUPERNOVA`→600, `INFOMAC`→740, `GESTION INTEGRAL`→504) y los chicos
muestreados también (`MICROHARD`→1278, `COPYTEC`→1102, `LLEDOS`→1303). Campos útiles:
`ID_Empresa`, `Den_Comercial`, `razon_social`, `cuit` (mismos campos que ya sincroniza
el módulo `prestadores` — otro catálogo, sin FK con este).

Inventario: 53 empresas `'PST %'` y 41 `'SPST%'`. **⚠️ La semántica de `Empresa.Estado`
no es la esperada**: filtrando `Estado=1` quedan 13 PST y son justamente los viejos/
`'NO USAR'` (ej. `'PST Chaco (NO USAR) - Pixel'`), mientras los PST reales vigentes
(Pentacom, Supernova, etc.) **no** están en ese grupo. O `Estado=0` significa activo en
esta tabla, o `Estado` codifica otra cosa. **Pendiente de confirmar en Fase 2**; el
filtro práctico que sí funciona hoy es "tiene vigencia actual en `CostoServicio`"
(los ~41 PST con `MAX(fecha_vigencia)=2026-07-01` son exactamente los reales).

También hay PSTs en Siges que no existen en el catálogo local (Esquel, Gral Pico,
Rafaela, Reconquista, Tres Arroyos, Santiago del Estero, `'PST Tucuman - NAPA'`) —
refuerza la política ya establecida en el módulo `prestadores`: **el sync actualiza,
nunca auto-crea** (el legacy creó ~29 prestadores fuera de alcance por auto-creación).

Por wsAyC: `getTechnicians(tipoTecnico='')` devuelve un dict `{id: nombre}` cuyos IDs
son los mismos `ID_Empresa` de Siges (137, 600, 504, 740 y los SPST 138, 140, 868…),
mezclados con técnicos internos `'CD - …'` (a filtrar por prefijo). Mismo dato, con
menos campos (sin cuit/razón social) — SigesReadOnly es superior para este dataset.

### 3. Tabla KM → pares sí, km no [PARCIAL en ambas fuentes]

- `dbo.Sucursal` tiene `ID_Prestador` (FK al PST de `Empresa`): la asignación
  sucursal-de-cliente → PST vigente existe y es consultable. **Corrección de la Fase 2
  (2026-08-13)**: la semántica de `Estado` es `0`=activo (verificada cruzando contra
  actividad real: las 1358 sucursales con incidentes desde 2026-07-01 tienen todas
  `Estado=0`; la primera lectura de "86 pares activos" filtraba `Estado=1` y contaba
  los **inactivos** — por eso la muestra traía 'Cencosud Viejo'). El número real:
  **762 pares vigentes** para PENTACOM contra **276 en la tabla KM local**, y la
  muestra activa matchea pares locales literalmente (`'Achiras'`→`'CP Achiras'`).
  La tabla local es un **subconjunto curado** de los pares de Siges (la TL solo carga
  los que efectivamente facturan km) — un prepoblado masivo metería ~500 filas sin uso
  por PST.
- **El km esperado por par NO existe en ninguna fuente**: `Sucursal` solo tiene
  `Longitud`/`Latitud` (texto) y `CostoViaticos` (int); la búsqueda por columna
  `%km%`/`%kilom%`/`%dist%` sobre todo el esquema solo devuelve
  `IncidenteCosto.CantidadKm`/`CostoKm` (lo **cobrado** por incidente, no el esperado)
  y `CostoServicio.CostoKm` (el precio por km, ya cubierto por tarifarios). En wsAyC,
  `getLiquidationDetails` trae `CantidadKm` por incidente — mismo carácter.
- Consecuencia de diseño para Fase 2: sync de tabla KM = **prepoblar pares nuevos con
  km pendiente de carga manual** (el diseño `kms_pendientes` de la rama legacy era
  correcto). El valor km sigue siendo dato manual del acuerdo comercial. Alternativa a
  evaluar aparte: calcular un km sugerido por `Longitud`/`Latitud` — solo como
  sugerencia, nunca como valor autoritativo.

### 4. Bonus (fuera del alcance pedido, cambia el panorama): la preliquidación entera está en las fuentes

- `dbo.Liquidacion` (3245 filas, última modificación 2026-08-12 23:39 — **dominio
  vivo**): `ID_Liquidacion`, `ID_Estado_Liquidacion`, `ID_Prestador`, `FacturaNro`,
  `Extra`/`DetalleExtra`. `dbo.Estado_Liquidacion`: `Preliquidada`, `Recibida`,
  `Aprobada`, `Observada`, `Cerrada` — el workflow que la Team Leader replica a mano.
- **La numeración local es el `ID_Liquidacion` de Siges + dígito módulo-10**: la liq
  local `3876-6` es la `3876` de Siges. Verificado end-to-end por wsAyC:
  `getLiquidationById(3876)` → PST San Juan - Gestion Integral, estado `Cerrada`, y
  `getLiquidationDetails(3876)` → **111 incidentes, exactamente los 111 de la liq local**,
  con columnas `id`, `CostoServicio`, `CostoKm`, `CantidadKm`, `Tipo`, `FechaCierre`,
  `NroSerie`, `Empresa`, `Sucursal`, `Rubro` — **las mismas que el CSV que hoy sube la
  TL**. `getLiquidationResume(id)` da el resumen por tipo; `getTopLiquidations
  (IdEmpresa, IdEstado, OrderBy, Top)` lista por PST con estado y `CostoTotal`.
- `dbo.IncidenteCosto` (`ID_Incidente`, `ID_Liquidacion`, `CostoServicio`, `CostoKm`,
  `CantidadKm`) es la tabla subyacente, también viva (filas del 2026-08-13).
- Esto habilita, como fase futura separada, importar la preliquidación por WS en lugar
  del CSV manual — el objetivo real de la rama legacy `feature/ws-ayc-liquidaciones`.
  Queda explícitamente para después de automatizar la config (alcance de este master
  prompt), y arrastra el riesgo documentado de pisado de estado local (caracterización
  §4) que exige diseño propio.

### 5. Operaciones wsAyC con parámetro no resuelto (no bloquea)

`getEmpresasPrestador(usuario_id=137)` y `getPayableIncidents(IdUsuario=137)`
devolvieron `[]`: el parámetro es un id de `UsuariosWeb` (usuario logueado del portal),
no un `ID_Empresa`. No se insistió — no hacen falta para los datasets validados.

## Descartadas en esta investigación

- `dbo.ListaCostosServicios` / `dbo.ListaCostosDistribucion`: listas de costos
  globales históricas (una fila por fecha, valores 2007-…), sin relación por PST —
  no son el tarifario de prestadores.
- `dbo.Tiempos`: catálogo trivial `Id`/`Horas`, sin relación con este dominio.

## Pendientes que pasaban a Fase 2 — resueltos en ADR-014 (2026-08-13)

Todos cerrados en `docs/adr/014-fuente-siges-para-config-de-liquidaciones.md`:

1. ~~Semántica de `Empresa.Estado`/`Sucursal.Estado`~~ → **`0`=activo, `1`=inactivo**,
   verificado con dato real para ambas tablas (PST con vigencia actual / sucursales con
   incidentes recientes: todos `Estado=0`; los 83 `'NO USAR'`: todos `Estado=1`).
2. Mapeo de zonas y tipos wide sin equivalente → tabla de mapeo con confirmación manual;
   `inclusion_a_contrato`/`relevamiento`/`presupuesto`/`taller` se ignoran.
3. Vínculo persistente → `siges_empresa_id` en `prestadores`/`spsts` (patrón del módulo
   `prestadores`), sin matching por nombre en runtime.
4. Fuente elegida → SigesReadOnly para los tres datasets; wsAyC reservado para el futuro
   import de preliquidaciones.
5. Estrategia → sync manual por botón con dry-run first-class, sin job de fondo; el sync
   nunca borra/recrea ni pisa ediciones manuales; para tabla KM, alta asistida on-demand
   (no prepoblado masivo — ver corrección del §3).

## Método (reproducibilidad)

Scripts en `backend/scripts/` (`explore_siges_liquidaciones.py`,
`explore_wsayc_liquidaciones.py`), corridos dentro del contenedor
`helpdesk-manager-backend` (con `DISABLE_BACKGROUND_JOBS=true` verificado) el
2026-08-13. Solo lectura: SQL parametrizado sobre la cuenta `SiGesReadOnly` (permisos
re-verificados en cada corrida) y operaciones SOAP `get*` exclusivamente. La referencia
local salió de `helpdesk-db` (datos reales migrados del legacy el 2026-08-13).
`SIGES_READONLY_CATALOGO_DATOS.md` quedó actualizado con las tablas nuevas confirmadas.
