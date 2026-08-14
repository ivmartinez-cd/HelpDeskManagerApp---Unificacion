# ADR-016: Backfill del estado real de liquidaciones desde wsAyC

## Estado: Aceptado (2026-08-14)

## Contexto

ADR-015 define el sync de liquidaciones como "aditivo puro" — nunca modifica
liquidaciones existentes. Esa restricción protege el estado de revisión de la TL
y las observaciones del motor de reglas.

Las 2.415 liquidaciones importadas el 2026-08-13 están todas en `estado='abierta'`
porque ADR-015 §6 decidió ignorar el campo `Estado` del SOAP ("la liquidación nace
`abierta` independientemente de su estado en AyC"). Hoy la Fase 2 del módulo agrega
acciones que escriben en wsAyC (`setLiquidationStatus`, `voidLiquidation`). Para que
esas acciones sean útiles, la TL necesita ver el estado real de cada liquidación en
lugar de un `abierta` universal que no refleja nada.

El campo `Estado` ya viaja en `getTopLiquidations` y el gateway ya lo parsea en
`CdLiquidacion.estado` — el backfill no requiere llamadas SOAP nuevas por liquidación.

## Decisión

Se agrega el comando de backfill `POST /api/liquidaciones/backfill-estado` (use case
`BackfillEstadoLiquidaciones`) que actualiza el campo `estado` de las liquidaciones
existentes con su estado real en AyC.

**Restricciones que preservan las garantías de ADR-015:**

1. **Solo el campo `estado`**: ningún otro campo (incidentes, importes, alertas,
   observaciones, extras) se toca. El backfill no es un re-import ni una
   sincronización estructural.

2. **Solo las que siguen en `abierta`**: liquidaciones con `estado != 'abierta'`
   se saltan. La TL que cambió el estado manualmente tomó una decisión sobre ese
   registro — el backfill no la pisa. Las 758 observaciones del motor de reglas
   (tabla `observaciones`, FK `observaciones.liquidacion_id → liquidaciones.id`
   sin `ondelete='CASCADE'`) no son afectadas: actualizar `estado` en `liquidaciones`
   no las cascadea.

3. **`dry_run` obligatorio como default**: `?dryRun=true` es el valor por defecto.
   El endpoint requiere pasar `?dryRun=false` explícitamente para ejecutar. Esto
   compensa la ausencia de dry-run en ADR-015 §5 (que se justificó por el carácter
   aditivo puro del sync); acá esa justificación no aplica.

4. **Disparo manual**: `POST /api/liquidaciones/backfill-estado` requiere permiso
   `CREATE`. Sin job automático — mismo criterio que el sync.

5. **Alcance acotable por prestador**: `?prestadorId=<uuid>` permite acotar la
   corrida (igual que el sync, hallazgo H-5 de ADR-015).

6. **Mapeo trivial**: el literal del campo `Estado` del SOAP (ej. `'Aprobada'`) se
   mapea a minúsculas (`.lower()`) para obtener el estado local. Los estados
   desconocidos se saltan y se loguean en warning, sin error fatal.

## Consecuencias positivas

- Las 2.415 liquidaciones reflejan su estado real en AyC después del backfill.
- El workflow de revisión de la TL empieza desde un estado real, no desde `abierta`
  universal.
- La garantía de ADR-015 §1 ("si `numero_liquidacion` ya está en la DB, se saltea")
  se mantiene intacta para el sync. El backfill es una operación separada e
  independiente.

## Consecuencias negativas / limitaciones asumidas

- Las liquidaciones con `estado != 'abierta'` (cambio manual de la TL) pueden quedar
  inconsistentes con AyC si el estado de AyC difiere. Esto es intencional: la decisión
  de la TL tiene prioridad sobre el estado remoto en cualquier escenario de conflicto.
- `Top=500` en `getTopLiquidations` puede no cubrir el historial completo de prestadores
  con muchas liquidaciones. El backfill solo actualiza las que caen dentro de la ventana
  devuelta por AyC.

## Rollback

El downgrade reseta `estado = 'abierta'` para todas las liquidaciones que no estén
en `abierta`. Solo ejecutar en desarrollo/staging — en producción pierde el trabajo de
revisión de la TL posterior al backfill. Ver migración `52c62b06f716`.
