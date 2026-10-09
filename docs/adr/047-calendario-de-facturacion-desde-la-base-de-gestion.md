# ADR-047: Calendario de facturación desde la base de Gestión en ORION (fin del scraping)

## Estado: Aceptado e implementado (2026-10-09)

Reemplaza la parte de ADR-012 que mantenía el scraping de eventos
(`GET /planificacion/ajax-by-rango`). El catálogo de operadores de ADR-012
(`SiGes.dbo.UsuariosWeb`) no cambia.

## Contexto

El Calendario de Contadores se sincronizaba entrando a la web de Gestión con el usuario y la
contraseña de una persona (`GESTION_WEB_USERNAME`/`GESTION_WEB_PASSWORD`). El 2026-10-09 esa
contraseña cambió y el job `calendario_refresh` empezó a fallar en cada ciclo: Symfony
redirigía al login y el refresher lo tomaba como login exitoso. ADR-012 había mantenido el
scraping porque la asignación operador↔evento no estaba en ninguna tabla de la base `SiGes`,
y dejó escrito revisar la decisión "si aparece acceso de lectura a la base propia de Gestión".

Esa base existe: `Gestion`, en el mismo SQL Server ORION, y la cuenta de solo lectura que ya
usa el backend (`ORION_USER`) tiene acceso (`HAS_DBACCESS('Gestion') = 1`). Las búsquedas de
ADR-012 nunca la vieron porque se hicieron solo dentro de `SiGes`.

### Validación (2026-10-09, ejecutada por Iván dentro del contenedor backend)

Contra los 828 eventos que la web había bajado a `contadores_calendar_events` en la ventana
±90 días (sincronización de ese mismo día):

- `Gestion.dbo.calendario_evento`: `id`, `fecha`, `titulo`, `descripcion`, `periodicidad`,
  `tipo_evento`, `evento_padre_id`, `realizado`, `usuario_operador_facturacion_id`. Los `id`
  son los mismos que devolvía la web. `tipo_evento = 'F'` es facturación.
- El operador es `Gestion.dbo.usuario` (`username`, `nombre`, `apellido`,
  `color_calendario_planificacion`, `habilitado`). **No** es `SiGes.dbo.UsuariosWeb`: los ids
  no coinciden (1246 es `vipaez` en `Gestion.usuario` y otro usuario en `UsuariosWeb`).
- Filtro de la web: se probaron cuatro reglas de agrupamiento contra lo que mostraba la web.
  La que coincide exacto (828 de 828, 0 faltantes, 0 sobrantes) es: agrupar por
  `evento_padre_id` (o el propio id si no tiene padre) + día, tomar el evento de menor id y
  mostrar el grupo solo si ese evento no está realizado. Gestión tiene filas duplicadas por
  padre y fecha (277 grupos con más de una fila); la web las devolvía como un solo evento con
  lista de ids, y el cliente viejo se quedaba con el primero.
- Campos, comparados uno por uno en 5 eventos de 5 operadores: `cliente` y `tittle_tooltip` =
  `titulo`; `title` = `"(Facturación) " + titulo`; `content_tooltip` = `descripcion` (idéntico);
  `start` = `fecha` con offset de Argentina (`2026-10-09T00:00:00-03:00`); `type = 'E'`,
  `stringTipoEvento = 'Facturación'`, `allDay = true`; color de fondo y borde = color del
  operador, y `#FACC2E` cuando el operador no tiene (vipaez, 189 eventos). Vendedor,
  sucursales, contactos y bultos venían siempre vacíos en facturación.

## Decisión

- `PyodbcGestionCalendarioGateway` (`contadores/infrastructure/siges/`) implementa
  `CalendarPort` con una consulta a `Gestion.dbo.calendario_evento` + `Gestion.dbo.usuario`
  por nombre de tres partes, sobre el `OrionQueryRunner` compartido (ADR-018/039). La regla
  de agrupamiento va en el SQL (`ROW_NUMBER()`), documentada en
  `gestion_calendario_query.py`.
- El job `calendario_refresh` y el botón "Sincronizar" usan ese gateway. Se borran
  `GestionPlanificacionClient`, `gestion_session_refresher`, los scripts de exploración de la
  web y las settings `GESTION_WEB_*`/`GESTION_SESSION_FILE` (`extra="ignore"`: si quedan en
  un `.env` no rompen nada).
- `CalendarPort.get_events` queda en `(start_date, end_date)`: los filtros por operador y
  tipo eran parámetros de la web que nadie usaba.
- El nombre del operador sigue resolviéndose contra `UsuariosWeb` por `login` y el color sigue
  saliendo del color dominante de sus eventos (que ahora es el `color_calendario_planificacion`
  de `Gestion.usuario`): sin cambios en `SyncCalendarEventsUseCase`.

## Consecuencias

- Positivas: el calendario deja de depender de la contraseña de una persona, de la pantalla de
  login y del JSON de Symfony; una consulta en vez de dos requests HTTP y un login.
- Negativas: depende del esquema de la base de Gestión, que nadie de este proyecto controla.
  Si renombran columnas, la consulta falla con `ExternalServiceError` y el job lo loguea
  (no corrompe la copia local: el reemplazo del rango corre recién con la consulta OK).
- La regla de agrupamiento es inferida de la salida de la web, no del código de Gestión. Hoy
  coincide exacto; si en algún momento difiere, revisar con el mismo método (comparar contra
  lo que muestra la web en el mismo rango).
