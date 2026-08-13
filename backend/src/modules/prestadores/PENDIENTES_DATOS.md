# Pendientes de datos — módulo Prestadores (operador/Siges)

Gaps conocidos que quedaron documentados dentro de las migraciones de carga de la
planilla real de seguimiento operador↔PST (`f8522ce8b61f`, `b241c9c3a464`,
`9139ff95a2d6`, `7fa2e507b087`, 2026-08-13). Se centralizan acá para que no se pierdan
en los docstrings de cada migración.

## Datos aproximados que se podrían corregir si aparece la fuente real

- **Fecha de inicio del tramo "operador anterior" (`2020-01-01`)**: en los PST donde se
  registró el tramo previo a la salida de mpollero/amaldonado (`hasta=2024-02-29`), la
  fecha de `desde` real de ese tramo anterior no está documentada en ninguna planilla —
  se usó `2020-01-01` como marca de "desde antes de tener registro". Si en algún momento
  aparece la fecha real, corregir con un `UPDATE` puntual (no hace falta migración nueva,
  no afecta el tramo vigente).
- **Nombres completos de mpollero y amaldonado**: se crearon como `app_user` inactivos
  (sin acceso — el login los rechaza igual que a cualquier usuario inactivo) solo para
  poder referenciar su nombre en el historial de asignaciones en vez de perderlo como
  `NULL`. El `full_name` cargado (`"Pollero (ex-operador, placeholder histórico)"` /
  `"Maldonado (ex-operador, placeholder histórico)"`) es un placeholder explícito, no el
  nombre real — no está documentado en ningún lado de este repo. Corregir si alguien lo
  sabe.
- **Chacabuco y Junín**: no traen valor de `equipos` en la planilla — quedan `NULL` a
  propósito, no es un olvido.
- **Tandil y SM de Tucumán**: idem, sin `equipos` ni operador anterior documentado en la
  planilla (columna "Operador hasta 29/02/2024" = "-").

## Tramos vigentes que las migraciones NO tocaron a propósito

El mismo día de esta carga (2026-08-13) alguien hizo cambios manuales desde la UI que
las migraciones respetan sin pisar — si se vuelve a tocar el historial de estos PST,
tener en cuenta que el tramo vigente actual es intencional, no un dato viejo:

- **Reconquista** (`siges_empresa_id=765`): reasignado manualmente a "sin operador"
  (tramo vigente sin `operador_id`). La migración `7fa2e507b087` solo agregó el tramo
  histórico de amaldonado (anterior a 2024-02-29), no tocó el vigente.
- **Córdoba/Pentacom** (`siges_empresa_id=137`): se reabrió manualmente un tramo de
  marodriguez (cerró el de `2025-09-04`, abrió uno nuevo `2026-08-12`). La planilla no
  documenta cambio de operador para este PST — la migración solo agregó `equipos=760`.

## Fuera del alcance de esta carga de datos

Estos son pendientes preexistentes del módulo, no de esta tanda de migraciones — ver
`INTEGRACION_APPS_PLAN.md` (Fase 3 — Contadores, que es la fase que engloba este
submódulo de operador/Siges):
- Correr en paralelo con la app vieja antes de apagarla.
- Apagar el módulo Contadores de la app vieja.
- Actualizar `PROJECT_CONTEXT.md` del padre.
