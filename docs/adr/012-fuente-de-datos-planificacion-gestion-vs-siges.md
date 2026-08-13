# ADR-012: SigesReadOnly reemplaza el catálogo de operadores; el scraping de eventos se mantiene

## Estado: Aceptado

## Contexto

El Calendario de Contadores (`backend/src/modules/contadores`) obtiene hoy toda la
planificación operador↔cliente por scraping en vivo de `gestion.cdsa.com.ar` (app Symfony):
`GestionPlanificacionClient.get_events` contra `GET /planificacion/ajax-by-rango` (eventos de
facturación, con `operador`, `cliente`, sucursales de entrega/instalación/despacho, colores,
tooltips, `bultos`, `costo_seguro`, `costo_recambio`) y `get_operadores` contra
`GET /planificacion/ver`, extrayendo por regex el `<select id="planificacion_filter_operador_
facturacion">`. Es frágil por diseño: depende del HTML/rutas de Symfony, de una sesión
`PHPSESSID` que hay que refrescar con login automático, y de una heurística de nombre
(`operador_matcher`) para resolver el nombre visible de cada username.

Se validó `SigesReadOnly` (host `MERCURIO.cdsa.com.ar`, login `SiGesReadOnly`, base `SiGes` —
**no es una instancia separada, es la misma base que ya usa `sla` en producción, con una cuenta
de solo lectura**) en cinco rondas, todas ejecutadas por el usuario dentro del contenedor
backend con `backend/scripts/explore_siges_planificacion.py`, un script ad-hoc con el mismo
patrón que `PyodbcSlaQueryGateway` (conexión efímera, `autocommit=True`, `close()` explícito):

1. **Permisos reales de la cuenta**: `IS_ROLEMEMBER`/`fn_my_permissions` confirmaron
   `db_datareader=True`, `db_datawriter=False`, `db_owner=False`, `db_ddladmin=False`, sin
   `INSERT`/`UPDATE`/`DELETE`/`ALTER`/`CREATE`/`CONTROL` a nivel base — de solo lectura de
   verdad, no solo de nombre.
2. **Inventario completo**: 444 tablas/vistas visibles (214 `BASE TABLE` + ~230 `VIEW`).
   `Empresa`/`Sucursal` (que sí usa `sla` en producción) aparecen como **vistas**, no tablas
   base — el filtro inicial que solo pedía `BASE TABLE` las había pasado por alto.
3. **Búsqueda por palabra clave** sobre las 352 columnas que matchean
   `operador`/`usuario`/`facturac`/`planific`/`evento`/`bulto`/`seguro`/`recambio`/`deposito`/
   `vendedor`/`remito`/`cliente`/`distribuc`/`zona`: cero columnas con "operador"/"planific"/
   "evento" en cualquier tabla o vista, pero aparecieron `UsuariosWeb` (columnas
   `login`/`nombre`/`apellido`/`color`/`activo`/`email`/`id_sucursal`) y `Remito_Cab`/
   `Remito_Det`/`Remito_Maquina` (`Bultos`/`CostoSeguro`/`Fecha_Entrega`/`Id_Empresa`/
   `Id_Sucursal`) por nombre completo de tabla.
4. **Confirmación de `UsuariosWeb` con dato real**: `SELECT ... FROM UsuariosWeb WHERE login =
   'vipaez'` (el username citado en el encargo original) devolvió `nombre='Victor'`,
   `apellido='Paez'`, `activo=True`, `color='#888200'` — coincide exactamente con la identidad
   esperada.
5. **`Remito_Cab` descartado con dato real**: el usuario sospechó, con razón, que `Remito_Cab`
   fuera logística de insumos/repuestos y no facturación. Se cruzaron tres clientes reales de
   eventos "(Facturación)" ya sincronizados (`YKK`, `EDERSA`, `YAGUAR`, `event_date` 2026-11-10/
   11) contra `dbo.Empresa`/`Remito_Cab`: los 15 remitos encontrados tienen `TipoRemito` en
   `'I'`/`'R'` (Insumos/Repuestos) y `Fecha_Remito` siempre `<= hoy` (2026-08-13) — mientras que
   los eventos de facturación son planificación **futura** (hasta +90 días). Dos dominios de
   negocio distintos que además nunca podrían cruzar en el tiempo. Descartado. Dato de contexto
   adicional, verificado en la DB local propia: los 828 eventos ya sincronizados en
   `contadores_calendar_events` tienen `bultos`/`costo_seguro`/`costo_recambio` siempre en
   `NULL` — no hay indicio de que Gestión los popule nunca en la práctica.

Ninguna de las 444 tablas/vistas, ni las candidatas más fuertes inspeccionadas por columna
completa (`Reservas`, `MaquinaInstalacion`, `Objeto_Balance`, `Instancia`, `Instancia_Motivos`,
`Remito_Cab`), tiene una columna que vincule "este cliente/evento" con "este `UsuariosWeb` como
responsable" — las únicas columnas de usuario en las tablas candidatas son `Usuario_Mod`
(auditoría de quién editó la fila, no asignación hacia adelante).

## Decisión

**Reemplazo parcial, confirmado con datos reales — no solo esquema:**

- **El catálogo de operadores de facturación (`GET /planificacion/ver`) se reemplaza** por un
  `SELECT` parametrizado contra `dbo.UsuariosWeb` (login, nombre, apellido, color, activo),
  siguiendo el patrón de `PyodbcSlaQueryGateway`. Esto elimina el punto más fresco de rotura del
  scraping actual (el regex sobre un `<select>` de HTML) y además resuelve una debilidad real de
  hoy: `operador_matcher` es una heurística de nombre que puede fallar por ambigüedad y cae al
  username crudo; con `nombre`/`apellido` reales de `UsuariosWeb`, esa heurística deja de ser
  necesaria. El `color`, hoy aproximado como "el `background_color` más frecuente entre los
  eventos del operador" (ver docstring de `Operador`), pasaría a ser la identidad real.
- **El scraping de eventos (`GET /planificacion/ajax-by-rango`) NO se reemplaza, en ningún
  campo.** La asignación operador↔cliente/evento — el dato central que hace útil al Calendario de
  Contadores — no está en ninguna tabla ni vista visible para esta cuenta, después de cinco
  rondas de búsqueda dirigida. Es razonable asumir que esa asignación vive en la base propia de
  la app Symfony de Gestión (no en Siges/MERCURIO), construida sobre catálogos compartidos como
  `UsuariosWeb`, pero esto es una inferencia razonable, no un hecho verificado — no hay acceso a
  esa base desde acá.
- **`Remito_Cab`/`Remito_Det`/`Remito_Maquina` descartados con dato real**: es logística de
  insumos/repuestos (`TipoRemito` `'I'`/`'R'`), un dominio de negocio distinto al de facturación,
  y sus fechas (siempre pasadas) nunca podrían cruzar con eventos de facturación (siempre
  futuros). `bultos`, `costo_seguro`, `costo_recambio` y `fecha_entrega` del evento quedan sin
  fuente confirmada en Siges — y como en la práctica vienen siempre `NULL` en los 828 eventos ya
  sincronizados, no hay evidencia de que valga la pena seguir buscándoles reemplazo.

## Consecuencias

- Positivas: se elimina la parte más fea y frágil del scraping actual (regex sobre HTML de
  Symfony para el catálogo de operadores) sin esperar a resolver el resto; `operador_matcher`
  deja de hacer falta como heurística de fallback; el color de operador deja de ser una
  aproximación. El veredicto está respaldado por una fila real confirmada, no por una hipótesis
  de nombres de columna.
- Negativas: el scraping de eventos (`ajax-by-rango`) se mantiene íntegro — con todas sus
  fricciones ya conocidas (timeouts en rangos anchos, sesión que vence, rotura si Symfony cambia
  el JSON) — porque ni la asignación operador↔evento ni la logística del evento están en Siges.
  El reemplazo del catálogo
  agrega una segunda fuente de verdad para operadores (`UsuariosWeb` vs. lo que siga trayendo
  `ajax-by-rango` en el campo `operador`, que debería seguir siendo el username/`login` para que
  ambas fuentes seguirán casando por esa clave) — hay que verificar que el join por username siga
  siendo consistente si algún día `UsuariosWeb.login` cambia de formato.
- El override temporal de asignaciones (ADR-013) sigue diseñado para operar sobre la copia
  sincronizada local — no depende de esta decisión, se implementa igual sea cual sea el estado
  del reemplazo del catálogo.
- Revisar esta decisión si en algún momento aparece acceso de lectura a la base propia de
  Gestión (si existe y es distinta de Siges): ahí sí valdría la pena repetir esta misma
  investigación contra esa base para buscar la asignación operador↔evento.
