# ADR-024: Reconciliación de liquidaciones pendientes contra wsAyC

## Estado: Aceptado e implementado (2026-08-19). Supersede parcialmente ADR-015 y ADR-016.

## Contexto

ADR-015 definió el sync de liquidaciones (`SincronizarLiquidaciones`, botón
"Sincronizar CD") como **aditivo puro**: crea liquidaciones que faltan, nunca
toca las que ya existen. La justificación era evitar el anti-patrón del legacy
(`feature/ws-ayc-liquidaciones`), que reimportaba borrando y recreando con
cascade, perdiendo el estado de revisión de la TL. ADR-016 sumó un backfill de
`estado`, pero acotado a liquidaciones en `abierta` y como comando manual
separado — "la decisión de la TL tiene prioridad sobre el estado remoto en
cualquier escenario de conflicto".

En la práctica, esa política dejó a las liquidaciones **congeladas en el
momento del import**, sin ninguna vía para que un cambio posterior en AyC
(el prestador corrige un costo, agrega/saca kilómetros, o alguien aprueba la
liquidación directamente en Web Agentes) llegara a la app. El usuario reportó
el síntoma: el detalle de una liquidación en Web Agentes (legacy) mostraba
"Recibida"; la app nueva mostraba "Observada" para la misma liquidación, y
"Sincronizar CD" no corregía nada.

Verificado contra wsAyC de producción (`wsg.cdsisa.com.ar`) el 2026-08-18, tres
liquidaciones reales con drift:

| Liquidación | Estado AyC | Incid. AyC | Costo AyC | Estado local | Incid. local | Importe local |
|---|---|---|---|---|---|---|
| 3907-5 | Recibida | 113 | $113 | Observada | 109 | $109 |
| 3906-6 | Recibida | 20 | $20 | Observada | 24 | $24 |
| 3905-7 | Recibida | 250 | $11.321.136 | Observada | 250 | $10.416.937 |

3905-7 es el caso más claro: misma cantidad de incidentes en ambos lados,
$904.199 de diferencia de importe — cambios de costo/km del prestador que
nunca llegaron a la app. El universo total de liquidaciones pendientes
(no `aprobada`/`cerrada`) en producción es chico: 5 en toda la base al momento
de este ADR.

## Decisión

Se agrega **reconciliación**: además de crear liquidaciones nuevas, el sync
ahora también actualiza in-place las liquidaciones pendientes que ya existen,
contra lo que reporta AyC — costos/km de sus incidentes y su `estado`.

### 1. Nunca borrar y recrear — actualizar in-place

`alertas.incidente_id` es `ON DELETE CASCADE`, y `conciliar_alertas` (el
mecanismo que preserva el triage de la TL entre reanálisis, ya usado por
`ReanalizarLiquidacion`) indexa por `incidente_id`. Recrear un incidente que
sigue existiendo en AyC se llevaría su triage por la cascada. Por eso:

- `domain/services/reconciliar_incidentes.py` — servicio de dominio puro que
  diffea incidentes locales vs. lo que reporta AyC, clasificando en `altas`,
  `cambios` (UPDATE in-place, preserva `id`), `bajas` y `ambiguos`.
- Clave de matching: la **parte numérica** de `numero_incidente`, no el string
  crudo. Verificado contra datos reales: liquidaciones cargadas por el sync
  SOAP usan el id crudo (`"838937"`); liquidaciones cargadas por CSV traen el
  dígito verificador módulo-10 (`"839551-5"`, mismo algoritmo de
  `numeracion_ayc.py`). Sin esta normalización, un desajuste de formato
  produciría 100% bajas + 100% altas — borrado y recreación masiva.
- `IncidenteRepository` gana `update_cobrados` (UPDATE in-place) y
  `delete_by_ids`. Validado contra Postgres real (no un fake): `update_cobrados`
  no cascadea alertas; `delete_by_ids` sí, sin `IntegrityError`.
- Comparación por tolerancia para floats (`abs(a-b) > 0.005`, evita ruido de
  redondeo) y `None`≡`""` para strings (asimetría de nullability entre
  `Incidente` e `IncidenteImportado`).

### 2. Mapa canónico de estados

`domain/services/estados_ayc.py` reemplaza los cuatro lugares que antes tenían
esta info por separado y podían desincronizarse (`_ESTADO_NOMBRE_A_ID` del
gateway, `_ESTADOS_AYC_VALIDOS` del backfill, las constantes `ESTADO_*`, los
literales hardcodeados de `aprobar`/`observar_liquidacion`). Mapa bidireccional
`estado_id` numérico ↔ constante local, con fallback al nombre (case-insensitive)
cuando `estado_id` no viene. `abierta` es local-only — sin id ni nombre AyC.

**Cambio de política respecto de ADR-016**: AyC pasa a mandar siempre sobre el
`estado` de una liquidación pendiente, no solo mientras siga en `abierta`. La
reconciliación puede mover una liquidación directo a un estado terminal
(`aprobada`/`cerrada`) si AyC ya la reportaba así — el guard de estado terminal
de `ReconciliarLiquidacion` se evalúa contra el estado local *previo* a la
corrida, así esa última reconciliación de incidentes todavía se aplica antes de
congelarla.

### 3. `ReconciliarLiquidacion` — el colaborador central

Orden fijo por liquidación: bajas → cambios → altas → recálculo de totales →
pisar estado → reanálisis (el motor de reglas corre al final, sobre el set de
incidentes ya reconciliado — si corriera antes de las bajas, regeneraría
alertas para incidentes que está por borrar).

**Guards**, en orden — el primero que no pasa aborta esa liquidación sin
aplicar nada:

1. Estado local terminal → no se le pide ni el detalle SOAP.
2. `len(remotos) != cd_liq.cant_incidentes` → detalle SOAP incompleto o
   fallido, no reconciliar (mismo criterio que ADR-015 usa para `fallidas`).
3. `bajas / locales > 50%` → sospecha de mismatch masivo de formato de
   matching (no un cambio real en AyC) — abortar es más seguro que borrar en
   masa.
4. `get_incidentes` deja de devolver `[]` en un fallo real — ahora levanta
   `ExternalServiceError`. Antes, `[]` era ambiguo entre "no hay incidentes" y
   "no se pudo consultar"; con reconciliación destructiva de por medio, esa
   ambigüedad es peligrosa, no solo imprecisa.

### 4. Tres disparadores, ninguno pisa datos sin que alguien lo sepa

- **Botón "Sincronizar CD"** (`POST /api/liquidaciones/sincronizar`): igual que
  antes, pero ahora también reconcilia las pendientes existentes.
- **Al abrir el detalle**: `ReconciliarLiquidacionIndividual` — reconcilia
  best-effort solo esa liquidación. Nunca falla por un motivo esperado (sin
  vínculo AyC, estado terminal, SOAP caído): abrir el detalle no puede
  romperse por esto. Endpoint `POST /{id}/reconciliar`, permiso `VIEW` (es un
  refresh de fondo, no una escritura explícita).
- **Job de fondo cada 120 min** (`LIQUIDACIONES_RECONCILIAR_INTERVAL_MINUTES`):
  mismo caso de uso que el botón, pero con `permitir_eliminar_anuladas=False`
  — **nunca borra**. La detección de anuladas (que sí borra liquidaciones
  enteras, ver §5) queda exclusiva del botón/endpoint manual, con un usuario
  mirando. Corre bajo `DISABLE_BACKGROUND_JOBS` como todos los jobs del repo.

### 5. Regularización: `_detectar_y_eliminar_anuladas` nunca tuvo ADR propio

El sync ya borraba localmente liquidaciones que AyC dejó de reportar (código
presente desde antes de este ADR), pero ADR-015 la describe como "aditivo
puro... nunca modifica ni borra las existentes" sin ninguna excepción
documentada. Este ADR regulariza esa función como parte formal del diseño: es
la única vía de borrado, exclusiva del disparo manual (nunca del job de
fondo), con sus propios guardas (SOAP vacío → no toca nada; window acotado por
el id máximo devuelto por AyC; solo toca estados no terminales).

## Qué se pierde conscientemente

- **Triage de incidentes dados de baja**: si AyC deja de reportar un incidente
  (se anuló del lado del prestador), se borra junto con sus alertas —
  incluido el triage que la TL le hubiera hecho. No hay tabla de auditoría;
  se loguea la baja pero el trabajo de la TL sobre ese incidente puntual no
  queda registrado en ningún lado.
- **Alertas ALT003/ALT004 stale en liquidaciones vecinas**: esas reglas
  comparan contra el histórico completo del prestador (`list_by_prestador`),
  no solo contra la liquidación reconciliada. Si reconciliar la liquidación A
  cambia un incidente que había disparado ALT003/ALT004 en la liquidación B,
  la alerta de B queda desactualizada hasta que B se reconcilie o reanalice
  también. Efecto de segundo orden, no resuelto en este ADR.
- ~~Selector de estado local (`estado-selector.tsx`, `PATCH /{id}/estado`)
  podía generar drift si alguien lo usaba sobre una liquidación con vínculo
  AyC~~ **Cerrado el mismo día — ver Addendum al final.**

## Consecuencias positivas

- Los tres casos de drift medidos (3907-5, 3906-6, 3905-7) se corrigieron en
  producción real al desplegar este ADR — importe, cantidad de incidentes y
  estado, verificado contra la DB y contra los logs de la corrida SOAP real.
- El costo SOAP es proporcional al universo real de pendientes (5 liquidaciones
  al momento de este ADR), no al histórico completo — la reconciliación pide
  detalle solo para liquidaciones no terminales.
- `estados_ayc.py` deja un solo lugar para razonar sobre el mapeo de estados,
  en vez de cuatro que podían (y llegaron a) desincronizarse.

## Consecuencias negativas / limitaciones asumidas

- El sync deja de ser "aditivo puro" — ADR-015 §1 y ADR-016 (protección total
  de cualquier estado ≠ `abierta`) quedan parcialmente superados. La garantía
  que sobrevive de ADR-015 es el dedup por `numero_liquidacion` para
  liquidaciones **nuevas**; la de ADR-016 (mapeo por nombre) queda reemplazada
  por `estados_ayc.py`.
- Si el `estado_id` de AyC cambia de significado en el futuro (renumeración
  del lado de AyC), `estados_ayc.py` tiene un solo lugar para corregirlo, pero
  ningún mecanismo de detección automática de esa renumeración — un mapeo
  silenciosamente incorrecto se manifestaría como estados pisados mal, no
  como un error visible.
- El job de fondo, aunque nunca borra, sí escribe (`update_cobrados`,
  `update_estado`) sin supervisión humana en el momento. Mitigado por los
  guards de §3 y por el volumen bajo del universo pendiente, pero es el primer
  job de este módulo que escribe sobre datos financieros reales sin un click
  explícito de por medio.

## Rollback

Poner en `False` (o eliminar) `LIQUIDACIONES_RECONCILIAR_INTERVAL_MINUTES` no
alcanza para deshacer esto — el job se apaga con `DISABLE_BACKGROUND_JOBS=true`
(ya es el default de este repo), pero el botón y el disparador del detalle
seguirían reconciliando. Revertir de verdad implica volver
`SincronizarLiquidaciones`/`ReconciliarLiquidacion*` al comportamiento previo
(aditivo puro) — no hay migración de datos que deshacer: los valores que trajo
la reconciliación son los reales de AyC, no hay estado "anterior correcto" al
que volver.

## Addendum (2026-08-19, mismo día): selector de estado local restringido

El punto que este ADR dejaba deliberadamente pendiente ("Qué se pierde
conscientemente") se cerró la misma sesión, apenas confirmado:

- **Backend**: `ActualizarEstadoLocal` (caso de uso nuevo) reemplaza la
  escritura directa al repositorio que tenía `PATCH /{id}/estado`. Si la
  liquidación tiene `numero_liquidacion` (vínculo AyC), levanta
  `LiquidacionConVinculoAycError` (409, `LIQUIDACION_CON_VINCULO_AYC`) en vez
  de escribir. Verificado en vivo contra una liquidación real vinculada
  (3907-5): `PATCH` devuelve 409 con el mensaje explicando que hay que usar
  Aprobar/Observar/Anular, y el estado en la DB queda intacto.
- **Frontend**: el selector "Cambiar estado" de `liquidacion-detalle.tsx` se
  oculta cuando `liquidacion.numeroLiquidacion` está presente — queda
  únicamente la barra de acciones AyC (que ya se ocultaba a la inversa, sin
  vínculo). Nunca las dos a la vez, nunca ninguna.
- Sin liquidaciones sin vínculo AyC en producción hoy, este camino queda sin
  ejercitar en la práctica — pero listo para el día que exista una importada
  por CSV/Excel manual.
