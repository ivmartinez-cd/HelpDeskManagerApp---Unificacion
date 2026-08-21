# Plan de cobertura — Vacaciones de Maria Jose Vela (semana del 24 al 28/08/2026)

Generado el 2026-08-20. Cubre las casillas **INSUMOS** y **ST** sin Majo, con las reglas duras
confirmadas por Ivan (jornadas, almuerzos, restricción de casilla por operador). Hay **dos
versiones**, ambas verificadas programáticamente contra esas reglas (0 violaciones):

- **Versión A**: Mariano abre INSUMOS a las 8:30 y hace también la tarde (6:30 de mesa).
- **Versión B** (pedida por Ivan el 2026-08-20): Mariano solo cubre INSUMOS 13–17:30 — su
  mañana queda libre de mesa. El costo se traslada a Luna/Victor e INSUMOS abre 9:00.

Si las vacaciones se extienden más allá del 28/08, el mismo esquema vale para los días extra —
solo ajustar la fecha de reversión.

## Decisión final y estado cargado (2026-08-20)

- **Se carga la Versión A sin el refuerzo de Mariana**: Mariana queda fuera de la cobertura
  (decisión de Ivan, 2026-08-20). ST abre 9:00 como hoy; INSUMOS queda sin atender 8:00–8:30 a
  propósito, igual que en la versión A original.
- Grilla vigente del 24 al 28/08 (igual L–V):
  **INSUMOS** 8:30–11 Mariano · 11–13 Luna · 13–17 Mariano · 17–18 Victor ·
  **ST** 9–14 Victor · 14–18 Luna.
- Está cargada en la app como **grilla de vacaciones** (modo vacaciones, ADR-025):
  `/admin/turnos` → pestaña *Modo vacaciones* → "Vacaciones M. J. Vela", id
  `e35e7d21-09d8-4224-911c-7d6378779278`, 30 franjas (6 × L–V), estado Programada hasta el
  lunes 24. La grilla titular no se tocó. El lunes 24 "Turnos del día" pasa solo a esta grilla y
  el **lunes 31 vuelve sola a la titular** — no hay paso de reversión. Si hiciera falta ajustar
  algo durante la semana, se edita desde la misma pestaña (✎) o se cancela (⊘).
- La app avisa las 5 advertencias esperadas (INSUMOS 8:00–8:30, una por día); ninguna otra.

---

## Reglas duras (confirmadas, no se tocan)

| Operador | Jornada | Almuerzo | Restricción |
|---|---|---|---|
| Mariano | 8:30 – 17:30 | 12 – 13 | Solo hace INSUMOS |
| Luna | 9 – 18 | 13 – 14 | — |
| Victor | 9 – 18 | 14 – 15 | — |
| Mariana | (refuerzo puntual) | — | Solo toma ST, de 8 a 9 — **finalmente no participa** (2026-08-20) |
| Majo (ausente) | 8 – 17 | 12 – 13 | — |

## Grilla actual (con Majo) — referencia

| INSUMOS | | ST | |
|---|---|---|---|
| 8:00 – 11:00 | Majo | 9:00 – 13:00 | Victor |
| 11:00 – 13:00 | Luna | 13:00 – 15:00 | Majo |
| 13:00 – 17:00 | Mariano | 15:00 – 18:00 | Luna |
| 17:00 – 18:00 | Victor | | |

## Versión A — Mariano abre INSUMOS

### INSUMOS — abre 8:30 (media hora más tarde)

| Franja | Operador | Horas | Cambio vs. hoy |
|---|---|---|---|
| 8:30 – 11:00 | **Mariano** | 2:30 | Nueva — toma la franja de Majo al ingresar |
| 11:00 – 13:00 | **Luna** | 2:00 | Sin cambio |
| 13:00 – 17:00 | **Mariano** | 4:00 | Sin cambio |
| 17:00 – 18:00 | **Victor** | 1:00 | Sin cambio |

### ST — abre 9:00 (como hoy)

| Franja | Operador | Horas | Cambio vs. hoy |
|---|---|---|---|
| ~~8:00 – 9:00~~ | ~~Mariana~~ | — | Refuerzo propuesto, **descartado el 2026-08-20** — no se carga |
| 9:00 – 14:00 | **Victor** | 5:00 | Extiende 1 h (antes 9–13) |
| 14:00 – 18:00 | **Luna** | 4:00 | Extiende 1 h (antes 15–18) |

## Por qué la versión A es (casi) la única posible con Mariano a la mañana

Las reglas duras fuerzan la mayoría de las decisiones — no hay margen de discusión en estas
franjas, y eso es bueno: nadie puede objetar el reparto.

- **ST 13–14 → Victor obligado.** Luna almuerza 13–14 y Mariano no hace ST. Es la única
  persona disponible para la primera hora del hueco que deja Majo (ST 13–15).
- **ST 14–15 → Luna obligada.** Victor almuerza 14–15. Luna vuelve de almorzar justo a las 14.
- **INSUMOS 8:30–9 → Mariano obligado.** Luna y Victor ingresan 9:00; Mariana solo toma ST.
  Nadie más está en el edificio para abrir INSUMOS.
- **INSUMOS 12–13 → Luna obligada.** Mariano almuerza 12–13 y Victor está en ST hasta las 14.
  Coincide con la franja 11–13 que Luna ya tiene hoy: cero disrupción.

Los dos únicos grados de libertad reales eran (a) quién hace ST 15–18 y (b) quién cierra
INSUMOS 17–18 — se mantienen como hoy (Luna y Victor) para cambiar lo mínimo.

## Carga resultante (versión A)

| Operador | Mesa hoy | Mesa propuesta | Jornada neta | Queda fuera de mesa |
|---|---|---|---|---|
| Mariano | 4:00 | 6:30 | 8:00 | 1:30 (11–12 y 17–17:30) |
| Luna | 5:00 | 6:00 | 8:00 | 2:00 (9–11) |
| Victor | 5:00 | 6:00 | 8:00 | 2:00 (15–17) |
| Mariana | — | — (refuerzo descartado) | — | — |
| **Total** | 19:00 | **18:30** | | |

Mariano es quien más absorbe (+2:30) — inevitable: es el único presente antes de las 9 y el
único que puede sostener INSUMOS mientras los demás rotan por ST.

## Trade-offs de la versión A

1. **INSUMOS descubierto 8:00–8:30**: los correos de esa media hora esperan a que Mariano
   ingrese. Alternativa descartada: que Mariana abriera INSUMOS (solo puede ST).
2. ~~ST gana la franja 8–9 (Mariana)~~ → **descartado**: ST abre 9:00 como siempre. Efecto neto
   sobre el servicio: −0:30 de INSUMOS, ST sin cambios de horario.
3. **Victor hace 5 h corridas de ST (9–14)**: es 1 h más que su bloque actual de 4 h. Forzado
   por el almuerzo de Luna.
4. **Mariano absorbe 6:30 de mesa** y le queda 1:30 para la carga de solicitudes de insumos.

## Versión B — Mariano solo cubre INSUMOS 13:00–17:30

Pedida por Ivan (2026-08-20) para liberar la mañana de Mariano. Verificada: 0 violaciones.

### INSUMOS — abre 9:00 (una hora más tarde que hoy)

| Franja | Operador | Horas | Cambio vs. hoy |
|---|---|---|---|
| 9:00 – 13:00 | **Luna** | 4:00 | Absorbe la mañana completa (hoy hace 11–13) |
| 13:00 – 17:30 | **Mariano** | 4:30 | Su único bloque; extiende 30 min hasta su egreso |
| 17:30 – 18:00 | **Victor** | 0:30 | Cierra (hoy 17–18) |

### ST — abre 8:00

| Franja | Operador | Horas | Cambio vs. hoy |
|---|---|---|---|
| 8:00 – 9:00 | **Mariana** | 1:00 | Refuerzo acordado |
| 9:00 – 14:00 | **Victor** | 5:00 | Extiende 1 h (antes 9–13) |
| 14:00 – 18:00 | **Luna** | 4:00 | Extiende 1 h (antes 15–18) |

### Carga resultante (versión B)

| Operador | Mesa propuesta | Jornada neta | Queda fuera de mesa |
|---|---|---|---|
| Mariano | 4:30 | 8:00 | **3:30** (8:30–12) |
| Luna | **8:00** | 8:00 | **0:00** |
| Victor | 5:30 | 8:00 | 2:30 (15–17:30) |
| Mariana | 1:00 | — | — |
| **Total** | **19:00** | | |

### Trade-offs de la versión B (además de los de la A)

1. **INSUMOS pierde también la franja 8:30–9:00**: sin Mariano a la mañana, nadie puede
   abrir antes de las 9 (Luna y Victor ingresan 9:00; Mariana solo toma ST). El hueco de
   apertura pasa de 30 min a 1 h.
2. **Luna queda al 100 % en mesa**: 8 h de mesa sobre 8 h netas — cero margen para tickets u
   otras tareas, todos los días de la semana. Es la consecuencia aritmética de sacarle 2 h a
   Mariano con la misma demanda. Si eso no es sostenible, usar la sub-variante B2.
3. Victor cierra INSUMOS 17:30–18 (30 min, antes 1 h).

### Sub-variante B2 — misma regla para Mariano, carga repartida

Reparte la tarde de ST para que Luna respire, a costa de más cortes:

| INSUMOS | | ST | |
|---|---|---|---|
| 9:00 – 13:00 | Luna | 8:00 – 9:00 | Mariana |
| 13:00 – 17:30 | Mariano | 9:00 – 14:00 | Victor |
| 17:30 – 18:00 | Luna | 14:00 – 16:00 | Luna |
| | | 16:00 – 18:00 | Victor |

Cargas: Mariano 4:30 · Luna 6:30 (libre 16–17:30) · Victor 7:00 (libre solo 15–16) ·
Mariana 1:00. Verificada: 0 violaciones. Costo: Luna con 3 bloques y vuelta a INSUMOS al
cierre; Victor casi sin margen.

### Franjas forzadas comunes a B y B2

Con Mariano acotado a la tarde, entre las 9 y las 13 Luna y Victor quedan obligados a estar
los dos en mesa a la vez (uno por casilla) — no hay tercera persona. ST 13–14 sigue siendo de
Victor (Luna almuerza) y ST 14–15 de Luna (Victor almuerza), igual que en la versión A.

## Cómo quedó cargado en la app (modo vacaciones, ADR-025)

Este plan motivó el **modo vacaciones** de Turnos: las coberturas temporales (ADR-013,
`/api/turnos/overrides`) reemplazan *quién* atiende una franja pero no pueden cambiar horarios
ni crear/eliminar franjas, y esta grilla re-corta 8–11 → 8:30–11, 9–13 → 9–14, 15–18 → 14–18 y
elimina ST 13–15. Con el modo vacaciones (`docs/adr/025-modo-vacaciones-grilla-variante-turnos.md`)
ya **no hace falta editar la grilla titular ni revertirla**:

- La Versión A sin refuerzo está cargada como grilla de vacaciones (ver "Decisión final y estado
  cargado" arriba): `/admin/turnos` → *Modo vacaciones* → "Vacaciones M. J. Vela", 24–28/08.
- Desde ahí se puede **ver la grilla** (👁, mismo timeline que "Turnos del día", para compartir
  con los operadores), **editar** (✎, reemplazo completo de franjas) o **cancelar** (⊘, única
  reversión anticipada; queda en el historial).
- **Reversión**: automática. El lunes 31/08 `/api/turnos/current` y la home vuelven a la grilla
  de referencia sin que nadie toque nada. Si las vacaciones se extienden, editar la grilla y
  correr `hasta`.
- Si alguna vez se quisiera la Versión B/B2 en lugar de la A, se carga del mismo modo: es otra
  grilla de vacaciones (o la edición de esta), nunca cambios sobre los slots titulares.
