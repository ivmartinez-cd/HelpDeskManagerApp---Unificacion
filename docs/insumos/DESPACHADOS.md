# Insumos > Despachados

Seguimiento en OCA de los insumos despachados. La pantalla `/insumos/despachados` muestra el
estado de cada envío y alerta cuando OCA no pudo entregar, para actuar antes de que OCA
devuelva el envío al remitente.

- **De dónde salen los envíos**: remitos de insumos de Siges (solo lectura) despachados por
  OCA en los últimos 30 días.
- **De dónde sale el estado**: el webservice público de seguimiento de OCA (e-Pak), consultado
  por un job de fondo o con "Actualizar ahora".
- **Qué guarda HDM**: el último estado de cada guía, los cambios observados, las acciones que
  registra el operador y cada corrida del job. La pantalla lee solo de la base de HDM: nunca
  espera a OCA.
- **Fuera de alcance (v1)**: acciones automáticas en OCA (el reclamo lo envía el operador desde
  el formulario de OCA, ver "Reclamar en OCA"), avisos por WhatsApp o mail, retiro de vacíos,
  remitos sin guía ("FALTA").

## Arquitectura

Vive dentro del módulo `insumos` (backend `backend/src/modules/insumos`, frontend
`frontend/src/features/insumos`), con archivos propios de Despachados en cada capa:

| Capa | Qué hay | Dónde |
|---|---|---|
| Dominio | Reglas del semáforo, días hábiles, ventana horaria, seguimiento de cada guía (cambio de estado, reapertura de alerta) | `domain/services/despachados/`, `domain/value_objects/despachados/`, `domain/entities/despachados/` |
| Puertos | Siges, OCA, repositorios, lectura de la pantalla, calendario de feriados | `domain/repositories/{despachos_siges_gateway,oca_seguimiento_gateway,envios_despacho_repository,acciones_despacho_repository,consulta_despachos_repository}.py` |
| Aplicación | Sincronizar, registrar acción, cerrar alerta, consultas de la pantalla | `application/use_cases/despachados/`, `application/dtos/despachados.py` |
| Infraestructura | Consulta a Siges (pyodbc sobre el runner compartido de ORION), cliente OCA (httpx + ElementTree), repositorios SQLAlchemy, feriados de `vacaciones_feriado` | `infrastructure/siges/`, `infrastructure/oca/`, `infrastructure/repositories/*despach*`, `infrastructure/vacaciones/` |
| Presentación | Endpoints, job de fondo, "Actualizar ahora" | `presentation/despachados_router.py`, `presentation/despachados_acciones_router.py`, `presentation/despachados_jobs.py`, `presentation/dependencies/despachados.py` |
| Frontend | Pantalla, API, hooks, panel lateral (`BrandDrawer`), modales "Registrar acción" y "Reclamar en OCA" | `features/insumos/components/despachados/`, `features/insumos/api/despachados-api.ts`, `app/(app)/insumos/despachados/` |

Diseño aprobado: `Handsoff Mockups/design_handoff_insumos_despachados/` (mockup + README con las
decisiones de UI).

### Origen de datos en Siges (verificado el 2026-09-24)

- `dbo.Remito_Cab` con `TipoRemito = 'I'` (insumos; los `'R'` son repuestos y quedan afuera),
  `ID_Distribucion` en 3 OCA, 9 OCA SP o 10 OCA Prioritario, `Guia` de exactamente 19 dígitos
  (descarta "FALTA") y `Fecha_Remito` dentro de la ventana.
- El remito se une al pedido de insumos por `Incidente_Insumo_D.ID_Remito` →
  `Incidente_Insumo_C` (`NroIncidente`, `Nro_Incidente_Cliente`). Un remito puede llevar varios
  incidentes y una guía puede venir en más de un remito.
- Detalle de tablas y conteos en `docs/siges/SIGES_READONLY_CATALOGO_DATOS.md` §3.

### Persistencia (base de HDM, migración `f2c7a9d4b1e8`)

| Tabla | Qué guarda |
|---|---|
| `insumos_despacho_envio` | Una fila por guía: último estado de OCA (`oca_*`, NULL mientras OCA no la registra), color, alerta, abierto/cerrado, fecha límite, última consulta y último error, cierre de la alerta |
| `insumos_despacho_remito` / `insumos_despacho_incidente` | Remitos de Siges de cada guía y sus pedidos de insumos |
| `insumos_despacho_estado_historial` | Cada cambio de estado que el job observó |
| `insumos_despacho_accion` | Acciones del operador (solo se agregan) |
| `insumos_despacho_corrida` | Cada ejecución del job (programada o manual) |

## Cómo funciona la sincronización

Una corrida (`SincronizarDespachos`), programada o manual:

1. Toma un candado de Postgres (clave `1_001_003`) para que nunca corran dos a la vez. Si ya
   hay una en curso, la manual responde 409 y la programada se saltea.
2. Da por terminadas las corridas que quedaron abiertas por un reinicio.
3. Lee Siges y da de alta las guías nuevas con sus remitos. Si Siges falla, lo deja anotado en
   la corrida y sigue igual con el paso 4.
4. Consulta en OCA **solo los envíos abiertos**, de a uno, con 0,3 s entre llamadas. Un error de
   OCA en una guía queda registrado en esa guía y en el log, y **no corta el lote**. Antes de
   guardar cada guía la relee, para no pisar un cierre de alerta hecho durante la corrida.
5. Confirma después de cada guía y registra el resumen de la corrida.

Un envío que sale de la ventana de 30 días de Siges se sigue consultando hasta que OCA lo
cierre. Con el volumen de septiembre de 2026 la primera carga fueron 582 guías (3 min 40 s) y
después quedan del orden de 100 abiertas por corrida.

## Configuración

Variables de entorno (todas con default; documentadas en `.env.example`). Cambiarlas exige
recrear el contenedor: `docker compose up -d --force-recreate backend`.

| Variable | Default | Para qué |
|---|---|---|
| `DISABLE_DESPACHADOS_BACKGROUND_JOBS` | `true` | Apaga el job programado. Independiente de `DISABLE_INSUMOS_BACKGROUND_JOBS` |
| `DESPACHADOS_INTERVALO_MINUTOS` | `120` | Cada cuánto corre el job |
| `DESPACHADOS_DIAS_SEMANA` | `[0,1,2,3,4,5]` | Días en que corre (0 = lunes) |
| `DESPACHADOS_HORA_INICIO` / `DESPACHADOS_HORA_FIN` | `8` / `20` | Ventana horaria (hora argentina; fin excluido) |
| `DESPACHADOS_DIAS_VENTANA` | `30` | Días hacia atrás que se buscan remitos en Siges |
| `DESPACHADOS_DISTRIBUCIONES_OCA` | `[3,9,10]` | `Distribucion.Id` de los transportes OCA |
| `DESPACHADOS_DIAS_SIN_MOVIMIENTO` | `3` | Días hábiles sin cambio para pasar a amarillo |
| `OCA_URL_ESTADO_ACTUAL` | webservice e-Pak | Endpoint `GetEnvioEstadoActual` |
| `OCA_TIMEOUT_SEGUNDOS` | `15` | Timeout por consulta (con 2 reintentos cortos ante 5xx) |
| `OCA_PAUSA_SEGUNDOS` | `0.3` | Pausa entre consultas a OCA |
| `OCA_RECLAMO_CONTACTOS` | 26108… y 211… (ver "Reclamar en OCA") | Contacto que se precarga en el formulario de reclamos según el prefijo de la guía (JSON, reemplaza la lista entera) |

El plazo de retiro en sucursal (5 días hábiles) es una regla fija del dominio. Siges se lee con
la conexión compartida de ORION (`ORION_*`).

## Cómo correr el job

- **Programado**: poner `DISABLE_DESPACHADOS_BACKGROUND_JOBS=false` en `.env` y recrear el
  backend. En el log tiene que dejar de aparecer `background_jobs: despachados omitido …` y el
  conteo de jobs pasa a 9. El primer ciclo corre al arrancar, solo si cae dentro de la ventana.
- **Manual**: botón "Actualizar ahora" de la pantalla (`POST /api/insumos/despachados/actualizar`,
  permiso `insumos.update`). Responde enseguida (202); la pantalla sigue el avance en
  `GET /api/insumos/despachados/actualizacion` y refresca al terminar. Funciona aunque el job
  programado esté apagado.
- **Ver qué hizo**: `SELECT * FROM insumos_despacho_corrida ORDER BY id DESC;` o el log
  (`despachados`). Los estados que OCA informa fuera del catálogo se loguean como warning con
  la guía, el `IdEstado` y el texto.

## Endpoints (`/api/insumos`)

| Método y ruta | Permiso | Qué hace |
|---|---|---|
| `GET /despachados` | `insumos.view` | Listado paginado; filtros `texto`, `colores`, `operativa`, `remitoDesde`, `remitoHasta`; orden `orden` + `direccion` (ver abajo) |
| `GET /despachados/requieren-accion` | `insumos.view` | Rojo y naranja con alerta abierta (la pantalla ya no lo usa: se sacó la bandeja) |
| `GET /despachados/resumen` | `insumos.view` | Tarjetas y contadores del menú |
| `GET /despachados/actualizacion` | `insumos.view` | Corrida en curso y última terminada |
| `POST /despachados/actualizar` | `insumos.update` | "Actualizar ahora" (202 / 409) |
| `GET /despachados/{guia}` | `insumos.view` | Detalle: estado, remitos, cambios, acciones |
| `POST /despachados/{guia}/acciones` | `insumos.update` | Registrar acción (opcionalmente cierra la alerta) |
| `POST /despachados/{guia}/cerrar-alerta` | `insumos.update` | Cerrar la alerta (exige al menos una acción registrada) |
| `GET /despachados/{guia}/reclamo-oca` | `insumos.update` | Datos para precargar el formulario de reclamos de OCA (no escribe nada; 404 si la guía no se sigue) |

**Orden del listado** (`GET /despachados`): lo resuelve el backend en SQL, antes de paginar.

- `orden`: `urgencia` (defecto), `color`, `guia`, `remito`, `cliente`, `incidente`, `estado`,
  `sucursal`, `fecha_remito`, `fecha_estado`, `limite`. `direccion`: `asc` (defecto) o `desc`.
  Un valor fuera de la lista es un 400 `VALIDATION_ERROR`.
- `urgencia` es el orden de siempre (rojo por fecha límite, naranja y amarillo por la fecha de
  estado más vieja, el resto por la más nueva) e **ignora `direccion`**. `color` ordena solo por
  el rango del semáforo (rojo → cerrado), sin esos desempates.
- `remito` es el número del primer remito de la guía; `incidente`, el primer incidente de ese
  remito; `estado` y `sucursal`, el último estado y la sucursal que informó OCA; `limite`, la
  fecha límite. Los textos se comparan en minúsculas.
- Los vacíos (sin remito, sin incidente, sin estado de OCA, sin límite) van siempre al final,
  en las dos direcciones. A igual valor desempata la guía, ascendente.
- Pantalla: cada encabezado de "Todos los despachos" ordena por su columna (primer clic `asc`,
  segundo `desc`; "Fecha estado" arranca en `desc`). Al entrar no hay encabezado activo (orden
  por urgencia); "Limpiar filtros" vuelve a ese orden. Cambiar el orden vuelve a la página 1.
  `fecha_remito` está en la API pero la columna "Remito" ordena por número.

## Reclamar en OCA

Botón del panel lateral (solo con `insumos.update`). Abre un modal con el **formulario público
de reclamos para grandes cuentas de OCA** (https://int.oca.com.ar/grandescuentas/) incrustado y
ya completado; el operador lo revisa, adjunta lo que haga falta, pasa la verificación y lo
**envía él mismo**. HDM no envía nada a OCA ni guarda nada al abrirlo.

- **No es una API de OCA**: esa página solo incrusta un formulario CRM de Bitrix24 (formulario
  65 de `oca.bitrix24.es`). HDM incrusta el mismo formulario y lo completa con la función que
  trae Bitrix24 (`setValues`). No se puede precargar por URL.
- **Qué se precarga**: nombre y apellido del operador logueado (HDM guarda solo el nombre
  completo: la última palabra va como apellido y el resto como nombre; se corrige a mano si hace
  falta), empresa, CUIT y mail de la cuenta de Canal Directo que despachó, la guía, el motivo "Otros motivos" y un comentario armado con lo que HDM sabe del
  envío (estado y motivo de OCA, fecha y sucursal, fecha límite si está en rojo, cliente,
  incidentes, remitos y bultos). Teléfono no hay en ninguna cuenta.
- **Qué cuenta**: se reconoce por el **prefijo de la guía**, no por la operativa que informa
  OCA. Gana el prefijo más largo; si ninguno coincide, el contacto va vacío y el operador lo
  completa a mano (guía y comentario igual se precargan).

  | Prefijo | Cuenta OCA | Empresa | Mail | CUIT |
  |---|---|---|---|---|
  | `26108` | 434324 OCA CORREO | Canal Directo Soluciones de Impresión | ocacdsisa@canaldirecto.com.ar | 30709381101 |
  | `211` | 443913 OCA CLIENTE | Canal Directo SA | ocacd@canaldirecto.com.ar | 30683465840 |

  Las operativas 434305 y 436233 usan estos mismos prefijos, así que quedan cubiertas. Se
  cambia con `OCA_RECLAMO_CONTACTOS` (ver `.env.example`).
- **Si el formulario no carga** (OCA o Bitrix24 caídos, bloqueados por la red, o 15 s sin
  respuesta): el modal avisa y ofrece el link a la página de OCA y el comentario para copiar.
- **Al cerrar el modal** aparece un aviso que ofrece "Registrar acción" con el tipo "Reclamo a
  OCA" y el comentario como detalle; el operador lo revisa y guarda (no se registra solo).
- **Riesgo**: depende de un formulario de terceros. Si OCA cambia o reemplaza el formulario
  (otro id, otros nombres de campo, otro loader), el precargado deja de funcionar o completa
  campos equivocados. Todo lo que depende de Bitrix24 está en un solo archivo del frontend,
  `features/insumos/components/despachados/oca-reclamo-form.ts`; el respaldo (link + comentario
  copiable) sigue sirviendo mientras tanto.
- **Headers**: la app no emite Content-Security-Policy (`frontend/next.config.ts`), así que no
  hubo que habilitar nada para `cdn.bitrix24.es` / `oca.bitrix24.es`. Si algún día se agrega
  una CSP, tiene que permitir esos orígenes en `script-src`, `connect-src`, `style-src`,
  `img-src` y `font-src` (y `frame-src` si OCA vuelve a activar la verificación reCAPTCHA).

## Catálogo de estados OCA y semáforo

Relevado sobre 699 guías reales (26/08–24/09/2026). Se aplica en este orden de precedencia; el
primero que coincide gana.

| Orden | Color | Cuándo | Alerta | Abierto |
|---|---|---|---|---|
| 1 | Cerrado (azul) | `IdEstado` 8 (Entregado) o 56 (Acuse digitalizado); o, sin `IdEstado`, los textos "Acuse en Rendicion", "Envio a Rendir a Otra Suc", "Rendicion de Acuse Finalizado" | No | No |
| 2 | Gris | 13 (Devuelto al Remitente), con o sin motivo | No | No |
| 3 | Rojo | 45 (En Espera de Retiro por Sucursal). Fecha límite = 5 días hábiles contando el día de ingreso (o el hábil siguiente), sin sábados, domingos ni feriados | Sí | Sí |
| 3b | Verde "Por retirar" | Sin `IdEstado`, texto "Listo para programar en Drivin": la guía ya está en OCA y falta que pasen a retirarla (visto en despachos del día; después pasan a "Retirado en Origen"). Aviso "Pendiente de retiro por OCA"; con motivo, naranja; sin cambios en 3 días hábiles, amarillo | No | Sí |
| 4 | Naranja | 48 (Reprogramado para nueva visita), o cualquier motivo distinto de "Sin Motivo" (vacío cuenta como "Sin Motivo") | Sí | Sí |
| 5 | Gris | 49 (Retiro Cancelado): queda abierto para revisar | No | Sí |
| 6 | Amarillo | `IdEstado` fuera del catálogo → "Estado nuevo, revisar" (y warning en el log) | No | Sí |
| 7 | Verde / amarillo | 1, 2, 4, 10, 34, 44 y 35 sin motivo: verde; pasa a amarillo "Sin movimiento hace N días hábiles" si la `FechaEstado` no cambia en 3 días hábiles | No | Sí |

- **Guía que OCA todavía no conoce**: verde "Esperando ingreso en OCA" durante 3 días hábiles
  desde el remito; después, amarillo "Sin datos en OCA". Si OCA deja de informar una guía que
  ya tenía estado, se conserva el último conocido.
- **Alertas**: rojo y naranja sin cierre; se ven con las tarjetas "Visita fallida" / "En
  sucursal" y los contadores del menú (la bandeja "Requieren acción" se sacó). Un operador
  cierra la alerta registrando una acción (o con "Cerrar alerta", que exige alguna acción
  previa). Se **reabre sola** si OCA informa un estado distinto que vuelve a tener alerta.
- **Feriados**: los de la tabla `vacaciones_feriado` de HDM (los mismos que usa Vacaciones),
  contando también los puentes turísticos y el 24/12. Si falta cargar el año en curso (o el
  siguiente, cerca de fin de año), el job lo avisa en el log: hay que importarlo desde
  Vacaciones antes de diciembre.
- Los textos se comparan sin distinguir mayúsculas, tildes ni espacios.

## Pruebas

- Unit: `tests/unit/{domain,application,infrastructure,presentation}/insumos/` (archivos con
  `despach`, `semaforo`, `oca`, `dias_habiles`, `ventana_job`).
- Integración (base descartable): `tests/integration/infrastructure/insumos/*despach*`,
  `tests/integration/test_despachados_router.py`, `tests/integration/test_despachados_acciones_router.py`,
  `tests/integration/test_despachados_reclamo_router.py`.
- E2E: `frontend/tests/despachados.spec.ts` y `frontend/tests/despachados-reclamo-oca.spec.ts`
  (datos simulados con `page.route`; el de reclamo bloquea Bitrix24 y verifica el respaldo).
