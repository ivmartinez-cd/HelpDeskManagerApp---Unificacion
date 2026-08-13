# Validación — ¿SigesReadOnly puede reemplazar el scraping de Gestión?

Validación en 5 rondas, todas ejecutadas por el usuario dentro del contenedor backend con
`backend/scripts/explore_siges_planificacion.py` (mismo patrón que `PyodbcSlaQueryGateway`:
conexión efímera, `autocommit=True`, `close()` explícito). Ver ADR-012 para la decisión que se
apoya en este documento.

`SigesReadOnly` **no es una instancia separada**: es la misma base (`SLA_MERCURIO_HOST=
MERCURIO.cdsa.com.ar`, `SLA_MERCURIO_DATABASE=Siges`, visible como `db=SiGes`) que ya usa `sla`
en producción, con una cuenta distinta (`SLA_MERCURIO_USER=SiGesReadOnly`).

## 1. Qué se scrapea hoy (inventario exacto)

`GET /planificacion/ajax-by-rango` devuelve, por evento (`GestionPlanificacionClient._to_event`,
mapeado a `CalendarEvent`): `id`, `title`, `start`, `operador` (username), `allDay`,
`backgroundColor`, `borderColor`, `type`, `tittle_tooltip`, `content_tooltip`,
`stringTipoEvento`, `cliente`, `vendedor`, `fecha_entrega`, `fecha_entrega_deseada`,
`sucursal_entrega`, `sucursal_instalacion`, `sucursal_despacho`, `contacto_entrega`,
`contacto_instalacion`, `bultos`, `costo_seguro`, `costo_recambio`.

`GET /planificacion/ver` expone, vía el `<select id="planificacion_filter_operador_
facturacion">`, el catálogo de operadores de facturación: pares `(username, nombre completo)`.

## 2. Ronda 1 — permisos y verificación de que "solo lectura" es real

```sql
SELECT IS_ROLEMEMBER('db_datareader') AS es_datareader,
       IS_ROLEMEMBER('db_datawriter') AS es_datawriter,
       IS_ROLEMEMBER('db_owner') AS es_owner,
       IS_ROLEMEMBER('db_ddladmin') AS es_ddladmin;

SELECT permission_name FROM fn_my_permissions(NULL, 'DATABASE')
WHERE permission_name IN ('INSERT','UPDATE','DELETE','ALTER','CREATE TABLE','CONTROL');
```

Resultado real: `db_datareader=True`, el resto `False`, cero filas de permisos de escritura.
**Confirmado: cuenta de solo lectura de verdad**, no solo por convención de nombre.

## 3. Ronda 2 — inventario completo y búsqueda por palabra clave

```sql
SELECT TABLE_NAME, TABLE_TYPE FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE IN ('BASE TABLE', 'VIEW') ORDER BY TABLE_TYPE, TABLE_NAME;
```

444 objetos visibles (214 `BASE TABLE` + ~230 `VIEW`). Hallazgo importante: `Empresa` y
`Sucursal` — que sí usa `sla` en producción — aparecen como **`VIEW`**, no `BASE TABLE`; una
primera corrida que solo pedía `BASE TABLE` las había pasado por alto.

```sql
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS
WHERE COLUMN_NAME LIKE '%operador%' OR COLUMN_NAME LIKE '%usuario%' OR COLUMN_NAME LIKE '%facturac%'
   OR COLUMN_NAME LIKE '%planific%' OR COLUMN_NAME LIKE '%evento%' OR COLUMN_NAME LIKE '%bulto%'
   OR COLUMN_NAME LIKE '%seguro%' OR COLUMN_NAME LIKE '%recambio%' OR COLUMN_NAME LIKE '%deposito%'
   OR COLUMN_NAME LIKE '%vendedor%' OR COLUMN_NAME LIKE '%remito%' OR COLUMN_NAME LIKE '%cliente%'
   OR COLUMN_NAME LIKE '%distribuc%' OR COLUMN_NAME LIKE '%zona%'
ORDER BY TABLE_NAME, COLUMN_NAME;
```

352 columnas candidatas. Cero con "operador"/"planific"/"evento" en cualquier tabla o vista.
Hallazgos por nombre de tabla completo: `Vendedor`, `UsuariosWeb`/`UsuariosWebEmpresa`/
`UsuariosWebPerfil`/`UsuariosWebPermiso`, `Remito_Cab`/`Remito_Det`/`Remito_Maquina`.

## 4. Ronda 3 — columnas completas de las tablas candidatas

`UsuariosWeb` (24 columnas): `id_usuario`, **`login`**, `pass`, `id_tipo`, `id_empresa`,
`admin`, `activo`, `id_sucursal`, `id_sector`, `email`, `otrosEmails`, `token`, `fechaSync`,
`fechaLogin`, **`apellido`**, **`nombre`**, `cargo`, `telefono`, `interno`, `movil`, **`color`**,
`usuarioMod`, `fechaMod`, `fcmToken`. Tiene toda la forma de ser el login real de la app Symfony
de Gestión (`login`/`pass`/`fechaLogin`/`token` son columnas de sesión web, no de Siges/
incidentes).

`Remito_Cab` (21 columnas, entre ellas `Id_Empresa`, `Id_Sucursal`, `Fecha_Entrega`, `Bultos`,
`CostoSeguro`, `CostoDistribucion`, `TipoRemito`) — candidato fuerte para la logística del
evento, **sin confirmar con fila real** (ver §6).

Candidatos adicionales inspeccionados y descartados por columna completa: `Reservas`
(reserva de stock de un modelo para un cliente, con `IDVendedor`/`IDCliente` — no es el dominio
de planificación de facturación), `MaquinaInstalacion` (solo `ID_UFisica`/`NroInstala`, un
contador), `Objeto_Balance` (movimiento de stock de insumos), `Instancia`/`Instancia_Motivos`
(visitas técnicas sobre un incidente, con `ID_Tecnico` — dominio de soporte, no de facturación).
Ninguna de estas cinco tiene columna que vincule cliente/evento con un `UsuariosWeb` responsable.

## 5. Ronda 4 — confirmación con dato real

```sql
SELECT id_usuario, login, nombre, apellido, activo, id_empresa, id_sucursal, color
FROM UsuariosWeb WHERE login = ?;
```

Con `login = 'vipaez'` (username citado en el encargo original):

```
id_usuario=1586 login='vipaez' nombre='Victor' apellido='Paez' activo=True
id_empresa=1 id_sucursal=None color='#888200'
```

**Coincide exactamente** con la identidad esperada. Confirmado con dato real, no solo por forma
de columnas: `UsuariosWeb` es la fuente de identidad de los operadores que hoy se scrapean.

## 6. Ronda 5 — `Remito_Cab` descartado con dato real

El usuario dudó, con razón, de que `Remito_Cab` fuera el mismo dominio que los eventos de
facturación — hipótesis: entrega de insumos/repuestos, no facturación. Dato de contexto
verificado primero en la DB local propia (`contadores_calendar_events`, 828 eventos
sincronizados, ventana ±90 días desde 2026-08-13): `bultos`/`costo_seguro`/`costo_recambio`
están **siempre en `NULL`** en los eventos reales — no hay valor de negocio para comparar por
monto, solo queda cruzar por cliente/fecha.

```sql
SELECT ID_Empresa, Den_Comercial, razon_social FROM dbo.Empresa WHERE Den_Comercial LIKE ?;

SELECT TOP 5 Id_Remito, Remito_Nro, Fecha_Remito, Fecha_Entrega, Bultos, CostoSeguro, TipoRemito
FROM Remito_Cab WHERE Id_Empresa = ? ORDER BY Fecha_Remito DESC;
```

Con tres clientes reales de eventos "(Facturación)" ya sincronizados (`event_date` 2026-11-10/
11): `YKK`, `EDERSA`, `YAGUAR`. Resultado real — 15 remitos entre los tres clientes, todos con
`Fecha_Remito <= 2026-08-13` (hoy) y `TipoRemito` en `'I'`/`'R'` (Insumos/Repuestos).

**Descartado, confirmado con dato real.** Dos motivos, ambos concluyentes:

1. **`TipoRemito` = `'I'`/`'R'`**: es logística de insumos/repuestos, no facturación — como
   sospechaba el usuario.
2. **Las fechas nunca pueden cruzar**: `Remito_Cab.Fecha_Remito` es siempre `<= hoy` (entregas ya
   despachadas), mientras que los eventos "(Facturación)" de Gestión son planificación **futura**
   (hasta +90 días, ej. 11 de noviembre visto desde el 13 de agosto). Son dos momentos distintos
   del proceso de negocio — nunca van a coincidir en el tiempo, sin importar el cliente.

`bultos`/`costo_seguro`/`costo_recambio`/`fecha_entrega` del evento scrapeado **no tienen fuente
confirmada en Siges** — quedan como scraping residual permanente (y, dado que en la práctica
siempre vienen `NULL` en los eventos reales, es dudoso que valga la pena seguir intentando
reemplazarlos).

## 7. Tabla de cobertura final

| Dato scrapeado hoy | Origen actual | Candidato en SigesReadOnly | Estado |
|---|---|---|---|
| Catálogo de operadores de facturación (username + nombre) | `<select>` de `/planificacion/ver` | `dbo.UsuariosWeb` (`login`, `nombre`, `apellido`, `activo`, `color`) | **cubierto — confirmado con fila real** |
| Colores/identidad del operador (hoy `Operador.color`, aproximado) | heurística sobre eventos | `UsuariosWeb.color` | **cubierto — confirmado con fila real** |
| Operador de facturación asignado a un evento (`operador` del evento) | `ajax-by-rango` | ninguno encontrado tras 4 rondas sobre 444 tablas/vistas | **no encontrado** |
| Cliente del evento | `ajax-by-rango` | `dbo.Empresa` (vista) — reutilizado por SLA | parcial / a verificar con dato real si se llega a necesitar |
| Sucursales de entrega/instalación/despacho | `ajax-by-rango` | `dbo.Sucursal` (vista) | parcial / a verificar |
| `bultos`, `costo_seguro`, `fecha_entrega` | `ajax-by-rango` | ~~`Remito_Cab`~~ — descartado, es logística de insumos/repuestos (`TipoRemito` I/R), fechas nunca cruzan con eventos futuros | **no encontrado, descartado con dato real** |
| `costo_recambio`, `tipo_zona`, `fecha_entrega_deseada` | `ajax-by-rango` | sin candidato en ninguna ronda | no encontrado |
| `backgroundColor`/`borderColor`/tooltips/`type` | `ajax-by-rango` | sin candidato — artefactos de UI de Gestión/FullCalendar | no encontrado (esperable: no son dato de negocio) |

## 7. Veredicto

**Reemplazo parcial, confirmado con datos reales en ambos sentidos** (lo que sí cubre y lo que
explícitamente no). El catálogo de operadores de facturación se reemplaza por un `SELECT`
parametrizado contra `dbo.UsuariosWeb` — esto elimina el regex sobre HTML de `/planificacion/ver`
y la heurística `operador_matcher`. Todo lo demás del evento (operador asignado, `bultos`,
`costo_seguro`, `costo_recambio`, `fecha_entrega`, tooltips/colores) **no está en Siges** — el
scraping de `ajax-by-rango` se mantiene íntegro para eso, con todas sus fricciones actuales. Ver
ADR-012 para la decisión completa y el plan de qué se implementa.
