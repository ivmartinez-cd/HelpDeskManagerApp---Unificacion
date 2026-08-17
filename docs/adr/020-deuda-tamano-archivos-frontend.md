# ADR-020: Deuda aceptada de tamaños (§4) extendida al frontend

## Estado: Aceptado (2026-08-16)

## Contexto

ADR-017 congeló como deuda documentada el inventario de violaciones §4 de
`ARCHITECTURE_GUIDE.md` medido en `backend/src`, pero dejó al frontend sin registro
equivalente. La pasada de optimización del 2026-08-16 (`docs/OPTIMIZACION.md`) midió
`frontend/src` con `wc -l`: **14 archivos .ts/.tsx superan las 300 líneas**, todos de
módulos ya portados, verificados visualmente contra el design handoff y en uso:

| Archivo | Líneas |
|---|---|
| `features/insumos/components/dashboard/consumable-detail-modal.tsx` | 459 |
| `features/insumos/components/shared/date-range-picker.tsx` | 450 |
| `features/turnos/components/admin/casillas-manager.tsx` | 428 |
| `features/contadores/components/client-picker-process-modal.tsx` | 395 |
| `features/preventivos/components/preventivos-view.tsx` | 380 |
| `features/liquidaciones/types/liquidaciones.ts` | 380 |
| `features/insumos/components/dashboard/dashboard-modals.tsx` | 375 |
| `features/insumos/hooks/use-order-actions.ts` | 371 |
| `shared/components/sidebar.tsx` | 349 |
| `features/liquidaciones/components/incidentes-seccion.tsx` | 325 |
| `features/vacaciones/components/reportes-view.tsx` | 317 |
| `features/sla/components/sla-detail.tsx` | 312 |
| `features/vacaciones/components/solicitudes-view.tsx` | 308 |
| `features/liquidaciones/components/liquidacion-detalle.tsx` | 301 |

(`features/liquidaciones/api/liquidaciones-api.ts`, 412 líneas al momento de la
medición, ya fue partido en sub-clientes por responsabilidad en esta misma pasada y
no integra el inventario.)

Es el mismo fenómeno que diagnosticaron ADR-016/017 para el backend: JSX declarativo
y árboles de props infladas por diseño pixel-fidelity sobreestiman la complejidad
real; los bugs de estos módulos aparecieron en la integración con los backends
legacy, no en componentes largos.

## Decisión

Se aplica al frontend el mismo criterio de ADR-017:

1. **El inventario de arriba queda aceptado como deuda documentada.** No se abre un
   workstream de refactor en bloque: partir componentes verificados píxel a píxel
   contra el handoff solo para satisfacer un conteo agrega riesgo de regresión visual
   sin reducir complejidad real.
2. **Refactor oportunista**: la próxima vez que cualquiera de estos archivos se toque
   por otro motivo, ese cambio lo baja del límite (extraer sub-componentes, hooks o
   sub-clientes por responsabilidad, como se hizo con `liquidaciones-api.ts`).
3. **El límite §4 sigue plenamente vigente para todo archivo nuevo o reescrito.**
   La auditoría periódica compara contra este inventario: todo caso nuevo es
   violación, no deuda.

## Consecuencias

- La desviación §4 del frontend queda con registro explícito (una excepción sin ADR
  es una violación, per CLAUDE.md) y con línea de base para detectar deuda nueva.
- Riesgo asumido: igual que en ADR-017, "oportunista" puede volverse "nunca". La
  línea de base de esta tabla permite medirlo en cada pasada de auditoría.
