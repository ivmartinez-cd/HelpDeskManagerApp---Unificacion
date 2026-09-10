# ADR-038: Modificaciones del prestador fuera del motor de alertas

## Estado: Aceptado

## Contexto

La TL revisa alertas ALT00X que genera el motor de reglas sobre una liquidación (`domain/
services/motor_reglas/motor.py`) y, cuando encuentra un problema, le pide al prestador que
corrija un valor. Hasta ahora, cuando el prestador reenvía la liquidación corregida vía AyC:

- `ReconciliarLiquidacion._aplicar()` (`application/use_cases/_reconciliar_liquidacion.py`)
  actualiza los incidentes in-place (`update_cobrados`) y el valor anterior se pierde: no hay
  `updated_at`, ni versión, ni snapshot, ni el payload SOAP crudo persistido.
- El diff que arma `domain/services/reconciliar_incidentes.py` ya sabía exactamente qué campo
  cambió (`_difiere()`, hoy `campos_modificados_incidente.py`), pero descartaba el detalle:
  devolvía un `bool` y solo se usaba para decidir si había que actualizar.
- Las alertas no sirven como aviso persistente de esto: el motor regenera el set completo en
  cada reanálisis (`replace_for_liquidacion`), y `conciliar_alertas.py` documenta que una
  alerta ya trabajada por la TL que el motor deja de generar **desaparece** ("el dato que la
  causaba se corrigió"). Es decir: si la TL le pidió al prestador que corrija algo y el
  prestador lo corrige, la alerta se borra sola — la TL nunca se entera de que el cambio
  ocurrió ni puede verificar que se haya hecho bien.

Se evaluó modelar esto como una `Alerta` más (un código `ALT0xx` nuevo que compare contra el
valor anterior). Se descartó: una `Alerta` es un **hallazgo recalculable sobre el estado
actual** — el motor la regenera entera en cada corrida y el reemplazo completo
(`replace_for_liquidacion`) es parte de su contrato. Lo que hay que registrar acá es un
**evento histórico** ("el 10/09 14:03 el prestador cambió km de 45 a 32") que ya no es
derivable de los datos actuales en cuanto se aplica el diff — meterlo en el motor lo haría
desaparecer en el siguiente reanálisis (las alertas `pendiente` no sobreviven a
`conciliar_alertas`) y mezclaría dos contratos distintos (recalculable vs. histórico) en la
misma tabla.

Existe una entidad `Resolucion` (`domain/entities/resolucion.py`, tabla `resoluciones`
creada en la migración `0468811de473`) con `DECISION_SOLICITAR_CORRECCION`, pensada
aparentemente para esto, pero sin ningún use case ni router que la use, y con FK
`ON DELETE CASCADE` a `alertas` — cualquier fila que se escribiera ahí se borraría en el
próximo reanálisis (mismo `replace_for_liquidacion`). No se reutiliza en esta decisión.

## Decisión

Tabla propia `modificaciones_prestador`, sin relación con `alertas`/`reglas_alerta`:

- Un evento por campo modificado (`tipo_cambio` ∈ `alta | baja | modificacion`,
  `campo`/`valor_anterior`/`valor_nuevo` para modificaciones), poblado en
  `application/use_cases/_registrar_modificaciones.py`, llamado desde `_aplicar()` **antes**
  de `update_cobrados`/`delete_by_ids` — momento en que el valor viejo todavía existe.
- Sin FK al incidente (solo `numero_incidente` desnormalizado): el registro de una baja tiene
  que sobrevivir al borrado del incidente.
- "Visto" es un campo (`vista_en`) que se pisa explícitamente
  (`POST /modificaciones/marcar-vistas`), no algo que el motor de reglas recalcule o
  regenere — nadie lo borra.
- Guard de reenvío masivo (`_UMBRAL_RESUMEN` en `_registrar_modificaciones.py`): si el
  prestador reenvía toda la liquidación, un evento por campo por incidente sería ruido —
  se registra un único evento resumen.

## Consecuencias

- Positivas: el evento sobrevive a cualquier cantidad de reanálisis futuros; el motor de
  reglas no se entera de esto y no cambia su contrato de "regenerar todo en cada corrida".
- Negativas: hay dos tablas con forma similar ("algo pasó con este incidente") y ninguna
  relación entre una alerta y la modificación que eventualmente la resuelve — la TL las
  correlaciona a mano (mismo incidente, mismo período de tiempo). Formalizar ese vínculo
  queda para si se necesita en el futuro.
- La entidad `Resolucion` queda igual de huérfana que antes de este ADR — no se tocó.
