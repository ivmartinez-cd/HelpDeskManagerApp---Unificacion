# ADR-041: Bandeja de notificaciones in-app, módulo transversal

## Estado: Aceptado (2026-09-30)

## Contexto

Cada módulo que quería avisar algo armó su propio mecanismo: WATI (toast + modal + sonido,
"visto" en `sessionStorage`), modificaciones del prestador en Liquidaciones (toast + sonido,
"visto" en el servidor, ADR-038) e Insumos (notificación de escritorio, preferencia en
`localStorage`). Consecuencias: con dos pestañas o dos PCs los avisos se repiten o se pierden,
lo que llega mientras nadie mira desaparece sin registro, y cada aviso nuevo reinventa consulta,
"visto", toast y sonido. El pedido que lo destapó: avisar en la app cuando un caso de Mesa de
Ayuda tiene una visita de técnico en marcha en la misma sucursal.

## Decisión

Módulo `notificaciones` (backend + frontend), transversal:

- **Lo detecta el backend, no el navegador.** Un job o caso de uso publica `NuevaNotificacion`
  por el puerto `PublicadorNotificaciones`, desde su propia `infrastructure` y en su misma
  sesión de DB: la notificación se confirma o se descarta junto con el resto del ciclo.
- **Idempotente por `clave`** (única en la tabla; `ON CONFLICT DO NOTHING`): el productor no
  necesita recordar qué avisó.
- **Audiencia** = función concedida (ADR-032) o permiso de módulo, guardada como texto
  (`funcion:<clave>` / `permiso:<módulo>.<acción>`). Listar las de un usuario es un `IN` sobre
  sus audiencias, sin joins contra `auth`; el superadmin ve todas.
- **Lectura por usuario** (`notificaciones_lecturas`), no global.
- **Frontend**: un poller por pestaña (30 s y al volver a la pestaña), campanita en el header
  con badge e historial, toast + sonido + aviso de escritorio (opcional) solo para lo que llega
  con la pestaña abierta.
- Router con repositorio directo, sin use case (mismo criterio que ADR-038): no hay regla de
  negocio más allá de filtrar por audiencia y paginar.

Contratos de import-linter: `notificaciones` no importa ningún módulo de negocio y de `auth`
solo en `presentation`; el `domain`/`application` de `sla` no importa `notificaciones`.

## Qué queda afuera, a propósito

- **WebSockets/SSE**: para una app interna alcanza con 30 s de demora.
- **Preferencias por usuario por tipo de aviso** y **purga de viejas**: cuando haga falta.
- **Migrar WATI**: su modal escalonado depende del turno y de minutos de espera en vivo, no es
  un evento que se publica una vez.
- **Notificaciones de Windows desde otras PCs**: el navegador solo las permite en HTTPS o
  `localhost`; por `http://<ip>:3000` el interruptor aparece deshabilitado con el motivo.

## Consecuencias

- Un aviso nuevo es: elegir clave y audiencia, y publicar desde `infrastructure`.
- En el aviso de visita en sucursal, un par registrado cuenta como avisado por todos los canales:
  si el mail (`MESA_AYUDA_ALERTA_MAIL_TO`) se configura después, no se mandan por mail los pares
  que ya estaban en la campanita.

## Migraciones

- **Modificaciones del prestador (Liquidaciones, ADR-038)** — 2026-09-30. El toast persistente
  con sonido por liquidación pasa a ser una notificación de la campanita por liquidación y por
  tanda registrada, para `liquidaciones.view`. La publica un decorador del repositorio de
  modificaciones (`ModificacionesConAviso`, infrastructure) armado en la reconciliación; el
  caso de uso no cambia. El "visto" de la liquidación (`vista_en`, badge del menú, "marcar
  vistas" del detalle) sigue igual y es independiente del leído de la campanita, que es por
  usuario. Las modificaciones anteriores a la migración no generan aviso: siguen en el badge.
- **Alertas de solicitudes sin cargar (Insumos)** — 2026-09-30. Antes el dashboard de Insumos
  armaba en el navegador una notificación de escritorio para cada alerta escalada, solo para
  quien tuviera la pantalla abierta y el aviso prendido. Ahora `RequestAlertsConAviso`
  (decorador de `RequestAlertRepository`, infrastructure) publica en la campanita una
  notificación por alerta cada vez que escala, para `insumos.view`; cubre los dos caminos que
  escalan (`ListAlerts` al pollear la pantalla y el job `SyncPendingAlerts`). La preferencia de
  notificaciones de escritorio queda una sola (la de la campanita, que respeta la vieja de
  Insumos si estaba prendida); la card "Preferencias del navegador" de Insumos solo muestra el
  estado, prueba y diagnostica. Con el job de Insumos apagado (dev, mientras el legacy siga
  productivo), las alertas solo escalan cuando alguien tiene abierta la pantalla de Insumos.
