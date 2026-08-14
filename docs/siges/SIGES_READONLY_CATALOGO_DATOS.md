# Catálogo de datos disponibles en SigesReadOnly

Referencia acumulada de lo que efectivamente se sabe sobre el esquema de Siges/MERCURIO, para
no tener que re-explorar desde cero la próxima vez que un módulo necesite un dato que podría
vivir ahí. Nace de la investigación de `ADR-012` (validar si Siges podía reemplazar el scraping
del Calendario de Contadores — ver `SIGES_READONLY_PLANIFICACION_VALIDACION.md` para esa
investigación puntual), pero este documento es de alcance general: cualquier módulo que
necesite datos de Siges debería mirar acá antes de armar una consulta de exploración nueva.

Cada tabla está marcada con su nivel de confianza:
- **[USADA]** — ya consultada por código productivo en este repo, patrón verificado en producción.
- **[CONFIRMADA]** — inspeccionada por `INFORMATION_SCHEMA` y verificada con al menos una fila
  de dato real durante esta sesión.
- **[CANDIDATA]** — columnas inspeccionadas por `INFORMATION_SCHEMA`, sentido de negocio
  razonable, **sin fila real verificada todavía**. Confirmar con dato real antes de construir
  sobre esto (ver §5 para el patrón de confirmación).
- **[DESCARTADA]** — se investigó puntualmente para un caso de uso y no aplicaba; se documenta
  igual para no volver a perder tiempo re-descubriéndolo.

## 1. Acceso

- Host: `MERCURIO.cdsa.com.ar` (env `SLA_MERCURIO_HOST`). Base: `Siges` (env
  `SLA_MERCURIO_DATABASE`, visible en `DB_NAME()` como `SiGes`).
- Cuenta de solo lectura: `SLA_MERCURIO_USER=SiGesReadOnly` — **no es una instancia separada**,
  es la misma base que ya usa el módulo `sla` en producción, con una cuenta distinta.
  Verificado con `IS_ROLEMEMBER`/`fn_my_permissions` (2026-08-13): `db_datareader=True`,
  `db_datawriter=False`, `db_owner=False`, `db_ddladmin=False`, cero permisos de
  `INSERT`/`UPDATE`/`DELETE`/`ALTER`/`CREATE`/`CONTROL` a nivel base. Solo lectura real, no solo
  de nombre.
- Patrón de conexión: `build_mercurio_connection_string` (`backend/src/shared/infrastructure/
  mercurio/connection.py`) + `pyodbc.connect(...)`, conexión efímera por consulta, igual que
  `PyodbcSlaQueryGateway` (`backend/src/modules/sla/infrastructure/mercurio/
  pyodbc_sla_query_gateway.py`). Todo SQL parametrizado con `?`, nunca interpolado
  (`ARCHITECTURE_GUIDE.md` §8). Errores de `pyodbc.Error` envueltos en `ExternalServiceError`.
- Script de exploración reusable: `backend/scripts/explore_siges_planificacion.py` (mismo
  patrón, `autocommit=True`, `close()` explícito en `finally`) — partir de ahí para cualquier
  investigación nueva en vez de escribir un cliente pyodbc desde cero.
- 444 tablas/vistas visibles en total para esta cuenta (214 `BASE TABLE` + ~230 `VIEW`) —
  listado completo en §6.

## 2. Tablas ya usadas en producción [USADA]

Confirmadas por código real ya desplegado — la fuente de verdad es el código, no este
documento, pero se resume acá para tener todo en un solo lugar.

| Tabla/vista | Módulo que la usa | Para qué |
|---|---|---|
| `dbo.Incidente` | `sla` | Incidentes de soporte — base de `INCIDENTES_SLA_SQL` |
| `dbo.Estado_Incidente` | `sla` | Estado del incidente (`EI.Descripcion`) |
| `dbo.Tipo_Incidente` | `sla` | Tipo del incidente (`TI.Descripcion`), filtrado a `(101, 108)` |
| `dbo.Maquina` | `sla` | Equipo asociado al incidente |
| `dbo.Articulo` | `sla` | Artículo de la máquina |
| `dbo.ArtGen` | `sla` | Modelo genérico del artículo |
| `dbo.Sucursal` (VIEW) | `sla` | Sucursal del incidente |
| `dbo.Empresa` (VIEW) | `sla`, `prestadores` | Cliente **y** técnico/PST — se distinguen por el rol del join (`E`=cliente, `E1`=técnico en `INCIDENTES_SLA_SQL`); `prestadores` la consulta por `ID_Empresa` para sincronizar `den_comercial`/`razon_social`/`cuit` |
| `dbo.IncidenteTiempo` | `sla` | Tiempos de resolución, base de los cálculos de SLA |
| `dbo.Contadores` | `contadores` | Tomas de contadores por máquina — base del análisis "equipos sin contador real" (ver §3) |
| `dbo.Tipo_Toma` | `contadores` | Catálogo del tipo de toma (real vs estimada, ver §3) |
| `dbo.Estado_Maquina` | `contadores` | Estado operativo de la máquina (también §3 del 2026-08-14) |
| `dbo.Tecnologia` | `contadores` | Mono/Color del modelo (`ArtGen.Id_Tecnologia`) |

## 3. Confirmadas con dato real en esta sesión [CONFIRMADA]

### `dbo.UsuariosWeb`

Catálogo real de usuarios/login de la app web (con altísima probabilidad, el mismo login que
usa Gestión, `gestion.cdsa.com.ar` — confirmado con `login='vipaez'` → `nombre='Victor'`,
`apellido='Paez'`, `activo=True`, `color='#888200'`, exactamente la identidad esperada).

| Columna | Tipo | Notas |
|---|---|---|
| `id_usuario` | int | PK |
| `login` | varchar | username (ej. `vipaez`) |
| `pass` | varchar | hash de contraseña — nunca leer/loguear esto |
| `id_tipo` | int | tipo de usuario, sin catalogar todavía |
| `id_empresa` | int | FK a `Empresa` — `1` en el caso confirmado (probable "Canal Directo" interno, sin confirmar) |
| `admin` | bit | |
| `activo` | bit | filtro de vigencia — confirmado `True` para un usuario real |
| `id_sucursal` | int | FK a `Sucursal`, nullable |
| `id_sector` | int | |
| `email`, `otrosEmails` | varchar | |
| `token`, `fcmToken` | varchar | tokens de sesión/push — no persistir |
| `fechaSync`, `fechaLogin` | datetime | |
| `apellido`, `nombre` | varchar | identidad real — reemplaza la heurística `operador_matcher` de `contadores` |
| `cargo`, `telefono`, `interno`, `movil` | varchar | |
| `color` | varchar | **identidad real de color**, ej. `#888200` — reemplaza la aproximación de `Operador.color` en `contadores` |
| `usuarioMod`, `fechaMod` | varchar/smalldatetime | auditoría |

Uso concreto ya decidido: reemplaza `GestionPlanificacionClient.get_operadores()` (scraping del
`<select>` de `/planificacion/ver`) — ver ADR-012.

### `dbo.CostoServicio` — tarifario de PST (confirmado 2026-08-13, paridad exacta)

Es **el tarifario por prestador** que alimenta las planillas de las que hoy sale el CSV del
módulo `liquidaciones` — verificado con paridad exacta contra el tarifario local de PENTACOM
(6 vigencias, `correctivo`+`CostoKm` idénticos, ver
`SIGES_READONLY_LIQUIDACIONES_VALIDACION.md`). 1329 filas, 96 `ID_Empresa` distintos, ~41 con
vigencia del trimestre actual.

| Columna | Notas |
|---|---|
| `ID_Empresa` / `Nombre_Empresa` | FK al PST en `Empresa` + nombre desnormalizado |
| `correctivo`, `preventivo`, `instalacion`, `inclusion_a_contrato`, `relevamiento`, `presupuesto`, `PreCorrectivo`, `guardia`, `taller`, `sistemas` | costos por tipo de servicio en **formato wide** |
| `CostoKm` | precio por km |
| `fecha_vigencia` | inicio de vigencia (cadena trimestral) |
| `descripcion` | **la zona del tarifario** (`'Genérica'`, `'General Roca / Rio Negro / Neuquen / Cipoletti'`, `'GSJ - GI Centro Civico'`, …; filtrar `'DE BAJA'`/`'Sin servicio'`) |
| `prestador_id`, `habilitado` | `prestador_id` = `ID_Empresa` en todas las filas vistas |

Los SPST **no** tienen filas propias — las tarifas zonales van por `descripcion` del PST padre.

### `dbo.Liquidacion` / `dbo.Estado_Liquidacion` / `dbo.IncidenteCosto` — dominio de liquidaciones vivo

Confirmadas con dato real 2026-08-13: `Liquidacion` (3245 filas, última mod ese mismo día;
`ID_Liquidacion`, `ID_Estado_Liquidacion`, `ID_Prestador`→`Empresa`, `FacturaNro`,
`Extra`/`DetalleExtra`), `Estado_Liquidacion` (`Preliquidada`/`Recibida`/`Aprobada`/
`Observada`/`Cerrada`), `IncidenteCosto` (`ID_Incidente`, `ID_Liquidacion`, `CostoServicio`,
`CostoKm`, `CantidadKm` — lo cobrado por incidente). La numeración del módulo `liquidaciones`
local es `ID_Liquidacion` + dígito verificador módulo-10 (la liq local `3876-6` es la `3876`
de Siges, 111/111 incidentes verificados vía wsAyC `getLiquidationDetails`).

### `dbo.Empresa` — nota adicional: también cataloga PST/SPST

Además de clientes y técnicos (§2), contiene los prestadores del dominio liquidaciones con
convención de prefijo en `Den_Comercial`: `'PST %'` (53) y `'SPST%'` (41). Los 4 grandes y
los chicos muestreados matchean 1:1 con el catálogo local. **⚠️ `Estado` está invertido
respecto de la intuición: `0`=activo, `1`=inactivo** — confirmado con dato real
(2026-08-13) en `Empresa` (los 40 PST con vigencia tarifaria actual: todos `Estado=0`; los
83 registros `'NO USAR'`: todos `Estado=1`) y en `Sucursal` (las 1358 sucursales con
incidentes desde 2026-07-01: todas `Estado=0`). `Sucursal.ID_Prestador` (FK al PST) da los
pares cliente-sucursal→PST vigentes (762 activos para PENTACOM); `Sucursal` no tiene
ninguna columna de km esperado (solo `Longitud`/`Latitud` texto y `CostoViaticos` int).

### `dbo.Maquina` + `dbo.Estado_Maquina` — parque de impresoras por PST (confirmado 2026-08-14, paridad exacta)

El parque de equipos asignado a un PST se obtiene con `Sucursal.ID_Prestador` →
`Maquina.ID_Sucursal`, y el detalle de modelo con la cadena ya conocida de `sla`
(`Maquina.ID_Articulo` → `Articulo.Id_ArtGen` → `ArtGen.Descripcion`). Verificado contra el
reporte legacy `sitesphp.cdsa.com.ar/laprida/Operaciones/MaquinasPorPrestador/RUN.php` para
PST Villa Mercedes (`ID_Empresa=740`, `'PST Villa Mercedes - Infomac'`): **paridad exacta,
841 equipos** con la definición de "máquina activa" del legacy:

```sql
WHERE S.ID_Prestador = ?          -- sucursales asignadas al PST
  AND S.Estado = 0                -- sucursal activa (0=activo, ver §3 Empresa)
  AND M.Estado = 0                -- fila de máquina vigente
  AND M.ID_Estado_Maquina NOT IN (2, 8)   -- excluye 'De Baja' y 'Backup Fijo'
```

Columnas útiles de `Maquina` (38 en total): `ID_Maquina` (PK), `Nro_Serie`, `ID_Articulo`
(FK→modelo), `ID_Empresa` (FK cliente), `ID_Sucursal`, `ID_Estado_Maquina`, `sla`/`heredaSla`,
`Direccion_IP`, `Fecha_Cpra`/`Fecha_Gtia`, `ID_UFisica`, `Estado`, `Fecha_Mod`/`Usuario_Mod`.

Catálogo `Estado_Maquina` (17 estados): 1 `Activa en Cliente`, 2 `De Baja`, 3 `Backup`,
4 `Para Limpiar`, 5 `Para Reparar`, 6 `En Demo`, 7 `Desguace`, 8 `Backup Fijo`,
9 `Backup Prestador`, 10 `Lista para salida`, 11 `Nueva`, 99 `Sólo Facturación`,
200 `Baja Solicitada`, 210 `Alta Solicitada`, 211 `En Garantia`, 254 `No Localizado`,
255 `Falta CI Real`.

Ojo con la doble condición de baja: hay máquinas con `ID_Estado_Maquina=2` (`De Baja`) que
siguen con `Maquina.Estado=0` (87 en el caso verificado) — para replicar el conteo del legacy
hacen falta **los dos** filtros, no alcanza con uno. Script de exploración:
`backend/scripts/explore_siges_parque_pst.py`.

### `dbo.Contadores` + `dbo.Tipo_Toma` — tomas de contadores (confirmado 2026-08-14, paridad exacta)

Fuente del análisis "equipos sin contador real" del módulo `contadores` (migra el reporte
legacy `sitesphp/.../Operaciones/EquiposSinContadorReal/RUN.php`). Verificado contra ese
reporte con paridad exacta: mismo TOP por meses serial por serial, mismas fechas de último
real, mismos IM-1..3. Script: `backend/scripts/explore_siges_contadores_reales.py`; consulta
productiva: `contadores/infrastructure/siges/equipos_sin_real_query.py`.

- `Contadores`: una fila por toma — `ID_Contador` (PK), `ID_Maquina`, `ID_ClaseContador`
  (catálogo `ClaseContador`: 10 Mono, 20 Color, 30 Digitalización, 40 Contador Total),
  `Secuencia`, `FechaTomaContador`, `Contador` (valor acumulado), `ID_TipoToma`,
  `Para_Facturar`, `ID_Factura`, `ID_MotivoEstimado`, `Estado` (0=vigente).
- `Tipo_Toma` (21 filas): **"toma real" = `ID_TipoToma NOT IN (8, 13, 14, 19)`** (8 Contador
  Inicial, 13 Contador Final, 14 Estimado, 19 Promedio Instalación). El resto (Teléfono, Mail,
  Fax, Informe S. Técnico, Automático, Semi-Automático, WebCliente, Whatsapp, SDS HP, VPN,
  Print Screen, …) cuenta como real.
- FechaUltCDOR del legacy = `MAX(FechaTomaContador)` de tomas reales; si el equipo **nunca**
  tuvo una real, cae a `MIN(FechaTomaContador)` de cualquier tipo (fecha de instalación) —
  verificado exacto con los dos PrintBox más viejos del reporte.
- IM-n del legacy = diferencia de `Contador` entre tomas mensuales consecutivas (clases
  10+20), de la más reciente hacia atrás; `ImpProm3M` = promedio de IM-1..3 **truncado**
  (no redondeado). Reproducido exacto (194/232/992 → 472).
- Universo del legacy: máquinas `Estado=0`, `ID_Estado_Maquina IN (1, 3, 8, 200, 254)` y con
  alguna toma dentro del último mes ("sigue facturando"). Con eso el TOP matchea 1:1 pero los
  conteos dan ~15% más que el legacy (180 vs 157 en >=60 meses) — el filtro restante no se
  identificó y la divergencia quedó documentada como decisión en
  `equipos_sin_real_query.py`. Además se excluyen los `ArtGen` `PrintBox %` (cajas de
  monitoreo, no impresoras; el legacy sí las lista) por pedido del usuario. Ojo: los PrintBox
  están en `Rubro` 4 `'Impresoras'` igual que las impresoras reales, el rubro no alcanza para
  distinguirlos. `Propiedad` = `Maquina.ID_Propietario` → `Empresa`; `Observaciones` =
  `Maquina.Observ` (la tabla `Observacion` es solo de `ObjetoBalance`).

## 4. Candidatas exploradas — columnas confirmadas, dato real pendiente [CANDIDATA]

Útiles para casos de uso futuros que no sean el Calendario de Contadores. Ninguna de estas fue
confirmada con una fila real todavía — el nivel de evidencia es "columnas con sentido de
negocio", igual que tenía `UsuariosWeb` antes de la ronda 4 de la investigación de ADR-012.

### `dbo.Remito_Cab` / `dbo.Remito_Det` / `dbo.Remito_Maquina`

Logística de remitos (**confirmado que es de insumos/repuestos, no de facturación** — ver §5).
Útil si algún módulo necesita rastrear entregas de insumos/repuestos por cliente.

`Remito_Cab`: `Id_Remito` (PK), `Remito_Local`, `Remito_Nro`, `Fecha_Remito`, `Id_Empresa` (FK
cliente), `Id_Sucursal`, `Id_Estado_Remito`, `Id_Proveedor`, `Entrega_a`, `Imprimio`,
`Fecha_Entrega`, `Firmante`, `ID_Distribucion` (FK `Distribucion`), `Guia`, `Bultos`,
`NroFCDistribucion`, `CostoDistribucion`, `CostoSeguro`, `TipoRemito` (`'I'`=Insumos,
`'R'`=Repuestos — inferido por el patrón de datos, no documentado formalmente), `Estado`,
`Fecha_Mod`, `Usuario_Mod`.

`Remito_Det`: `Id_Remito` (FK), `Item`, `Id_Articulo`, `Cantidad`, `Descripcion_Articulo`,
`Estado`, `Fecha_Mod`, `Usuario_Mod`.

`Remito_Maquina`: `Id_Remito_Cab` (FK), `Id_Maquina` (FK), `Item` — vincula un remito a
máquinas específicas.

### `dbo.Distribucion`

Catálogo simple de transportistas/distribuidoras: `Id` (PK), `Descripcion`, `Cuit`,
`RequerirNroGuia`, `Estado`, `Fecha_Mod`, `Usuario_Mod`.

### `dbo.Vendedor`

Catálogo de vendedores: `Id_Vendedor` (PK), `Descripcion`, `Abreviada`, `Mail`, `Tipo`,
`Estado`, `Fecha_Mod`, `Usuario_Mod`. Referenciado por `Contrato.Id_Vendedor`,
`Factura_Vendedor.Id_Vendedor`, `ContratoVendedor.ID_Vendedor`, `Reservas.IDVendedor`.

### `dbo.UsuariosWebPerfil` / `dbo.UsuariosWebPermiso`

Tablas de relación de `UsuariosWeb`: `UsuariosWebPerfil(idUsuarioWeb, idPerfil)`,
`UsuariosWebPermiso(idUsuarioWeb, idPermiso)` — sin explorar qué son `Perfil`/`Permiso` en
detalle, pero es la forma obvia de un modelo de roles/permisos de la app web.
(`UsuariosWebEmpresa` ya fue investigada y descartada como cartera por operador — ver §5.)

### `dbo.Reservas`

Reserva de stock de un modelo (`ArtGen`) para un cliente: `IDReserva` (PK), `IDArtGen`,
`IDVendedor`, `IDCliente`, `Notas`, `Fecha`, `Cantidad`. Dominio de ventas, no de asignación de
operadores.

## 5. Investigadas y descartadas para el caso de uso original [DESCARTADA]

Documentadas para no perder tiempo re-explorándolas si alguien busca lo mismo en el futuro.

- **`Remito_Cab`/`Remito_Det`/`Remito_Maquina` como fuente de "eventos de facturación" de
  Gestión**: descartado con dato real. `TipoRemito` es `'I'`/`'R'` (Insumos/Repuestos), y
  `Fecha_Remito` es siempre `<= hoy` (entregas ya despachadas) mientras que los eventos de
  facturación de Gestión son planificación futura (hasta +90 días) — nunca podrían cruzar en el
  tiempo, sin importar el cliente. Verificado con 3 clientes reales (`YKK`, `EDERSA`, `YAGUAR`)
  y 15 remitos reales. Siguen siendo **[CANDIDATA]** válida para otro caso de uso (logística de
  insumos/repuestos en sí), solo descartadas para planificación de facturación.
- **`Reservas`, `MaquinaInstalacion`, `Objeto_Balance`, `Instancia`/`Instancia_Motivos` como
  vínculo operador↔cliente/evento**: inspeccionadas por columna completa, ninguna tiene una
  columna que asigne un `UsuariosWeb` como responsable de un cliente/evento hacia adelante (solo
  `Usuario_Mod`, que es auditoría de quién editó, no asignación).
  - `MaquinaInstalacion`: solo `ID_UFisica`, `NroInstala` — un contador, no un evento.
  - `Objeto_Balance`: movimiento de stock de insumos (`Id_Empresa`, `Id_Sucursal`, `Id_ArtGen`,
    `Cantidad`, `ID_Distribucion`) — inventario, no planificación.
  - `Instancia`/`Instancia_Motivos`: visitas técnicas sobre un incidente (`ID_Incidente`,
    `ID_Tecnico`, `Fecha`, `Tareas`) — dominio de soporte técnico, no de facturación.
- **Ninguna tabla/vista de las 444 visibles contiene la asignación operador↔evento** que hoy
  scrapea `GET /planificacion/ajax-by-rango` de Gestión — búsqueda exhaustiva por palabra clave
  sobre las 352 columnas candidatas (`operador`/`usuario`/`facturac`/`planific`/`evento`/etc.)
  no encontró ninguna columna de asignación fuera de `UsuariosWeb` mismo. Ver ADR-012 para el
  detalle completo.
- **`UsuariosWebEmpresa` como cartera de clientes por operador de facturación** (investigación
  card de Contadores, 2026-08-14): descartada con dato real. Es el alcance de visibilidad de
  usuarios web (qué empresas ve cada usuario en Gestión/portal), no una asignación de
  responsabilidad: los operadores de contadores (`vipaez`, `mpollero`) tienen 0 filas; los que
  tienen cientos son usuarios comerciales/admin de Canal Directo (614/461 empresas), y los
  usuarios con mail de dominio de cliente (`@galeno.com.ar`) tienen ~10-12 (las empresas de su
  propio grupo). Refuerza la conclusión de ADR-012: la asignación operador↔cliente de
  facturación vive solo en la app de Gestión (eventos de planificación scrapeados), no en la
  réplica de Siges. Script: `backend/scripts/explore_usuariosweb_empresa.py`.
- **`ListaCostosServicios` / `ListaCostosDistribucion` como tarifario de PST** (investigación
  liquidaciones, 2026-08-13): descartadas — listas de costos globales históricas (una fila por
  fecha desde 1900/2007), sin relación por PST. El tarifario real es `CostoServicio` (§3).
  `Tiempos` también descartada (catálogo trivial `Id`/`Horas`).
- **Km esperado por par cliente-sucursal** (para la Tabla KM de liquidaciones): no existe en
  ninguna tabla — búsqueda por columna `%km%`/`%kilom%`/`%dist%` en todo el esquema solo
  devuelve `IncidenteCosto.CantidadKm`/`CostoKm` (lo cobrado, no lo esperado) y
  `CostoServicio.CostoKm` (precio por km). Es dato manual del acuerdo comercial.

## 6. Inventario completo de tablas/vistas visibles (444, capturado 2026-08-13)

Lista cruda de `INFORMATION_SCHEMA.TABLES` para búsqueda rápida por nombre — antes de escribir
una consulta de exploración nueva, buscar acá primero si el nombre ya apareció.

<details>
<summary>214 tablas base (`BASE TABLE`)</summary>

Actividad, Agrupacion, Agrupacion_ArtGen, AnexoMovimientoLog, Area, ArtGen, ArtGen_Articulo,
ArtGen_ClaseContador, Articulo, ArticulosParametrizacion, Auditlog, Bitacora, Bonificacion,
ClaseContador, Contadores, ContratoVendedor, Debito, Devolucion_Maquina, DireccionesMailSiGes,
Distribucion, dtproperties, EmpresaIngrBrutos, Estado_Incidente, Estado_Incidente_Insumo,
Estado_Incidente_ST_Correlatividad, Estado_Liquidacion, Estado_Maquina, Estado_Objeto,
Estado_Remito, EstadoMaquina_TipoIncidente, Etiqueta, Etiqueta_CodBarras, Factura_Anexo,
Factura_Cabecera, factura_cabecera_log, Factura_Contador, Factura_Debito, Factura_Detalle,
Factura_Empresa, Factura_Error, Factura_Escala_C, Factura_Escala_D,
Factura_Impresion_Concepto, Factura_MaquinasFueraDeProceso, Factura_Renta,
Factura_SubProceso, Factura_TipoCotizacion, Factura_Vendedor, Familia, Feriado, Forma_Pago,
Frecuencia, Incidente, Incidente_Insumo_C, Incidente_Insumo_D, IncidenteCausa,
IncidenteContenido, IncidenteCosto, IncidenteInsumoEmail, IncidenteOrigen,
IncidentePreventivo, IncidenteRepuesto, IncidenteRepuestoLog, IncidenteTiempo,
Informe_Factura, Instancia, Instancia_Motivos, IntranetNovedades, InventarioGlpi,
Liquidacion, ListaCostosDistribucion, ListaCostosServicios, Maquina, MaquinaBackup,
MaquinaClaseContador, MaquinaContacto, MaquinaEstadoDocumental, MaquinaHist,
MaquinaInstalacion, MaquinaModoOper, MaquinaModoOper_ClaseContador, MaquinaMotivoMov,
MaquinaSituacionContractual, MaquinaUFisica, Marca, Mensaje, Motivo, Motivo_Articulo,
Motivo_ContadorEstimado, Motivo_ST, MotivoFinalizacion, MotivoFinalizacionRenta,
MSpeer_conflictdetectionconfigrequest, MSpeer_conflictdetectionconfigresponse, MSpeer_lsns,
MSpeer_originatorid_history, MSpeer_request, MSpeer_response, MSpeer_topologyrequest,
MSpeer_topologyresponse, MSpub_identity_range, NC, NCConcepto, Objeto, Objeto_Anulacion,
Objeto_Aviso, Objeto_Balance, Objeto_Comprobante, Objeto_Devolucion_Atributo,
Objeto_Devolucion_C, Objeto_Devolucion_C_Atributo, Objeto_Devolucion_D,
Objeto_Devolucion_D_Atributo, Objeto_Etiqueta, Objeto_Partes, Objeto_Reclamo,
Objeto_ReclamoMotivo, ObjetoHist, Observacion, ObservacionTabla, OLD_Anexo,
OLD_AnexoRevision, OLD_Categoria_Iva, OLD_CentroCosto, OLD_Ciudad, OLD_Contacto,
OLD_Contrato, OLD_ContratoEmpresa, OLD_Costos_C, OLD_Costos_D, OLD_CostoServicio,
OLD_Cotizacion, OLD_Devolucion_Cab, OLD_Devolucion_Det, OLD_Empresa, OLD_EscalaPrecios_C,
OLD_EscalaPrecios_D, OLD_EscalaPrecios_D_Hist, OLD_Estado_Anexo, OLD_Estado_Contrato,
OLD_Factura_FormaEmision, OLD_Factura_Modalidad, OLD_Forma_Facturacion, OLD_GrupoEconomico,
OLD_Leyenda, OLD_Mantenimiento, OLD_MetodoActualizacion, OLD_Moneda, OLD_Pais, OLD_Sector,
OLD_Sucursal, OLD_Tipo_Empresa, Orden_Compra_C, Orden_Compra_D, OrigenReclamo, Parametro,
Perfil, Permiso, PesadasArticuloExcluido, PesadasArticuloParametrizacion, PesadasBorradas,
PesadasFalla, PesadasFallaSubItem, PesadasParametrizacion, PesadasPlanta,
PesadasPlanta_FallaSubItem, PesajeEstadistica, PesajeTabla, Precios_Articulo,
ProyeccionStocks, prueba, RegistroHW_C, RegistroHW_D, Remito_Cab, Remito_Det,
Remito_Maquina, Renta, Reservas, Rubro, sysarticlecolumns, sysarticles, sysarticleupdates,
sysdiagrams, syspublications, sysreplservers, sysschemaarticles, syssubscriptions,
systranschemas, Tecnologia, Tiempos, Tipo_Comprobante, Tipo_Incidente, Tipo_Toma,
TipoConexion, TipoContenido, TipoCosto, TipoDebito, TipoFalla, TipoHopper,
TipoHopperTipoWaste, TipoRenta, TipoUsuarioWeb, TipoWaste, TMP_Contadores_Cartocor,
tmpSeriesToner, Unidad_Medida, Usuarios, UsuariosPlanta, UsuariosWeb, UsuariosWebAuditoria,
UsuariosWebEmpresa, UsuariosWebPerfil, UsuariosWebPermiso, Vendedor.

</details>

<details>
<summary>~30 vistas de negocio (`VIEW`, excluidas ~200 `syncobj_0x...` de replicación — ruido, no datos)</summary>

Anexo, AnexoAjuste, AnexoGestion, Categoria_Iva, CentroCosto, Ciudad, ClienteTransa_Applysys,
Comprobante, Contacto, Contrato, contrato_anexo_impresion_concepto, ContratoEmpresa,
CostoServicio, Cotizacion, **Empresa**, EscalaPrecios_C, EscalaPrecios_D, Estado_Anexo,
Estado_Contrato, Factura_Applysys, factura_contrato_anexo_generico, Factura_FormaEmision,
Factura_Modalidad, Forma_Facturacion, GrupoEconomico, Leyenda, Mantenimiento, Moneda,
ObjetoUnion, Pais, Sector, **Sucursal**, SucursalTipoInsumo, sysextendedarticlesview,
TipoInsumo, TipoPreventivo, VW_CuotasPagasDebito, VW_CuotasPagasRenta, VW_Factura_Cabecera,
VW_ImpresorasInstaladasPorArticulo, VW_Informe_Insumo, VW_Informe_Insumo_Reporte,
VW_InformeBalanceToner, VW_InformeIncidenteST, VW_InformeReclamoToner, VW_InformeResumen,
VW_PPP, VW_UltimoPrecio.

(`Empresa` y `Sucursal` están en negrita porque son las dos que ya usa `sla` en producción —
en esta réplica de solo lectura están expuestas como vistas, no como tablas base.)

</details>

Objetos de replicación (`MSpeer_*`, `MSpub_*`, `sys*`, `syncobj_0x...`) — ruido de la
infraestructura de replicación de SQL Server, no datos de negocio. Confirma que esta base es un
suscriptor de replicación (consistente con ser una réplica de solo lectura).

## 7. Advertencias / lo que falta verificar

- `UsuariosWeb.id_empresa=1` — probable "Canal Directo" como empresa interna, sin confirmar
  contra `Empresa`.
- `Remito_Cab.TipoRemito` (`'I'`/`'R'`) — el significado "Insumos"/"Repuestos" es una inferencia
  razonable por el patrón de datos, no está documentado en ningún lado ni confirmado contra un
  catálogo (`Estado_Remito` tiene `Descripcion`, pero no se verificó si cubre `TipoRemito`).
- El listado del §6 es una foto del 2026-08-13 — si se necesita para algo crítico, re-confirmar
  que no cambió (`INFORMATION_SCHEMA.TABLES`), sobre todo porque esta es una réplica y podría
  haber objetos que aparecen/desaparecen según el estado de sincronización.
- Ninguna tabla nueva de este catálogo fue inspeccionada más allá de sus columnas — antes de
  construir un gateway pyodbc real sobre cualquiera de las **[CANDIDATA]**, repetir el patrón de
  confirmación con dato real que se usó para `UsuariosWeb` (ver ADR-012, ronda 4).
