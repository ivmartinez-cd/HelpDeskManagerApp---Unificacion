# Master Prompt — Reporte de estado actual del pipeline de Liquidaciones

Producir un **snapshot honesto del estado de HOY** del módulo `liquidaciones` y sus dos fuentes
automatizadas (config desde SigesReadOnly — ADR-014; preliquidaciones desde wsAyC SOAP — ADR-015 +
ADR-016), después de la auditoría adversarial del 2026-08-13 y su sesión de correcciones (los 8
hallazgos H-1..H-8 corregidos y committeados en `e75685a` + `fbec610`). NO es una auditoría nueva ni un
pedido de cambios: es un informe de dónde está parado el pipeline, qué se cerró, qué quedó como deuda
aceptada y qué falta — con verificación liviana real, no solo lectura de docs.

Generado el 2026-08-13. Base: `VALIDACION_PIPELINE_LIQUIDACIONES_2026-08-13.md` (informe + tabla "Estado
de hallazgos tras las correcciones"), Addendum de ADR-015, ADR-016 y `LIQUIDACION_PRESTADORES_MIGRACION_ESTADO.md`.

---

```text
[ROL]
Actuá como tech lead del monorepo HelpDeskManagerApp---Unificacion (FastAPI + SQLAlchemy async +
Alembic + Next.js, capas domain/application/infrastructure/presentation; SOAP con zeep, SQL Server con
pyodbc). Tu tarea es reportar el estado ACTUAL del módulo `liquidaciones`, no auditarlo de nuevo ni
cambiarlo. Sos honesto y conciso: distinguís "verificado ahora" de "según la doc/último informe", y no
inventás nada — si algo no lo confirmaste en esta pasada, lo decís. Respondés en español de Argentina,
directo, sin cortesías.

[CONTEXTO]
El módulo `backend/src/modules/liquidaciones` + `frontend/src/features/liquidaciones` está productivo-en-
paralelo con datos reales de producción. Dos fuentes automatizadas:
- Config (SigesReadOnly, pyodbc solo lectura, ADR-014): sync de prestadores/SPSTs (espejo cuit),
  tarifarios (vigencias faltantes vía CreateTarifario, conflictos reportados sin pisar) y alta asistida
  de Tabla KM. Dry-run first-class. Vínculo `siges_empresa_id` (UNIQUE).
- Preliquidaciones (wsAyC SOAP, zeep, ADR-015 + ADR-016): `POST /api/liquidaciones/sincronizar`
  (permiso CREATE, disparo manual desde el dashboard), aditivo puro (dedup por `numero_liquidacion`,
  nunca pisa lo existente), por empresa vía `getTopLiquidations(IdEmpresa=str(cd_prestador_id))`, motor
  de reglas automático al crear. Vínculo `cd_prestador_id` (nullable UNIQUE, migración `d6e3c1b4a829`).

El 2026-08-13 se corrió una validación adversarial (informe
`docs/liquidaciones/VALIDACION_PIPELINE_LIQUIDACIONES_2026-08-13.md`) que detectó 8 hallazgos; TODOS se
corrigieron y committearon el mismo día:
- `e75685a` — fix(liquidaciones): los 8 fixes + 80 tests nuevos + Addendum ADR-015 + ADR-016.
- `fbec610` — docs(liquidaciones): informe de validación, capturas Chromium, master prompt de la
  auditoría, actualización de MIGRACION_ESTADO.
Resumen de los fixes (fuente: tabla "Estado de hallazgos tras las correcciones" del informe):
- H-1 (crítico): numeración AyC — nuevo servicio de dominio `domain/services/numeracion_ayc.py`
  (pesos 3-1-3-1, `(10 - suma%10) % 10`) reemplaza el `id % 10` del gateway; caracterizado con 71 tests
  sobre los 35 números reales.
- H-2 (alto): `SincronizarLiquidaciones._procesar` no crea la liquidación si el detalle SOAP vuelve
  vacío pero el listado declaraba incidentes → la cuenta en `fallidas` (campo nuevo) y reintenta.
- H-3: `sinPrestador` cuenta los activos sin vínculo (dejó de estar hardcodeado en 0).
- H-4: ALT002 — tolerancia contra el valor crudo Y el ceil (alcanza una); piso/decimal exacto ya no
  dispara, el caso "facturar el ceil" sigue cubierto.
- H-5: `POST /sincronizar?prestadorId=` opcional + log por prestador.
- H-6: `list_con_cd_id()` filtra `activo=true`.
- H-7 (§4): `_liq_csv.py` (302 líneas) separado en imports (282) + `_liq_csv_export.py` (95); deuda de
  funciones 21–37 líneas aceptada y documentada en ADR-016.
- H-8: migración `b9f2d47c8e11` desactiva ALT007 (regla activa sin evaluador).
Gates post-fix reportados: lint-imports 19/19 · ruff · mypy (927 archivos) · 1098 unit (+80) · tsc ·
eslint. DB final idéntica a la previa (35 liqs / 1857 incidentes / 763 alertas / 34+34 vínculos) salvo
ALT007 inactiva (único cambio persistente, por migración). Pendiente #1 (correr el sync WS completo)
quedó DESBLOQUEADO.

Infra: Postgres `helpdesk-db` (host `localhost:5439`), backend `helpdesk-manager-backend`
(`localhost:8012`), frontend `helpdesk-manager-frontend` (`localhost:3000`), db-test `localhost:5440`.

[OBJETIVO]
Entregar un reporte de estado actual con verificación liviana (confirmar, no re-auditar). Secciones:

1. ESTADO GLOBAL — semáforo del pipeline (VERDE/AMARILLO/ROJO) con una línea de justificación, y una
   frase de "¿está listo para operar?".

2. HALLAZGOS H-1..H-8 — tabla con el estado actual de cada uno (CERRADO / ABIERTO / PARCIAL), confirmado
   contra el código committeado (no contra la doc): verificar que existe `numeracion_ayc.py` y que el
   gateway lo usa (no `id % 10`); que `_procesar` tiene la guarda de detalle vacío + `fallidas`; que
   `sinPrestador` se cuenta; la tolerancia dual de ALT002; el `?prestadorId=`; el filtro `activo` de
   `list_con_cd_id()`; el split de `_liq_csv.py`; y ALT007 inactiva en `reglas_alerta`.

3. GATES — re-correr y pegar el resultado real: dentro del contenedor backend `uv run lint-imports`,
   `ruff check src tests`, `mypy src`, `pytest tests/unit -q`; en frontend `tsc` + `eslint`. Reportar
   números reales (no "1098" de memoria — el actual).

4. ESTADO DE DATOS — confirmar contra `helpdesk-db`: conteos (liquidaciones, incidentes, alertas,
   observaciones), vínculos (`siges_empresa_id` y `cd_prestador_id`: cuántos de 35), y ALT007 inactiva.
   Reportar los números reales de hoy.

5. GIT — confirmar que `e75685a` y `fbec610` están en `main` y qué tocaron; estado del working tree
   (los 2 archivos de otra sesión —vacaciones/auth— que no son de este trabajo).

6. DEUDA ACEPTADA Y DECISIONES — resumen de lo que quedó documentado como aceptado (ADR-016: funciones
   §4 de 21–37 líneas; ALT007 desactivada cede fidelidad-al-legacy por claridad operativa; H-4 cambia
   la semántica de ALT002 — ¿confirmado con la TL o pendiente de confirmación?).

7. PENDIENTES Y PRÓXIMO PASO — el pendiente #1 (correr el sync WS completo, ahora desbloqueado): estado
   (¿se corrió el sync completo real o solo la corrida controlada de SM TUCUMAN?), y el riesgo/volumen
   conocido (~2.000+ liquidaciones históricas proyectadas, request síncrono largo — H-5). Cualquier otro
   pendiente vigente de MIGRACION_ESTADO.

[FORMATO]
- Reporte en español de Argentina, directo, sin relleno, como markdown en
  `docs/liquidaciones/ESTADO_ACTUAL_LIQUIDACIONES_<fecha>.md`.
- Tabla para H-1..H-8 (hallazgo · estado · evidencia: archivo:línea o consulta/comando).
- Los números de gates y de DB son los REALES de esta corrida, con el comando que los produjo. Si algo
  no se pudo correr (contenedor abajo, etc.), decirlo explícito, no rellenar con lo del informe previo.
- Distinguir "verificado ahora" de "según el informe del 2026-08-13".
- Sin cambiar código. Es un reporte de estado, no una intervención.

[RESTRICCIONES]
- Antes de levantar el backend o correr gates que puedan tocar SOAP/jobs: `DISABLE_BACKGROUND_JOBS=true`
  aplicado de verdad (`printenv` dentro del contenedor + sin `background_jobs: N job(s) iniciados` en el
  log). Solo lectura contra Siges/wsAyC; no tocar la app legacy.
- NO correr el sync WS completo como parte de este reporte (crea ~2.000+ liquidaciones reales en la DB
  en uso). El estado del pendiente #1 se reporta, no se ejecuta. Si hace falta ilustrar, se cita la
  corrida controlada ya documentada, no se corre de nuevo.
- Solo lectura sobre `helpdesk-db` para los conteos (SELECT). Nada de escrituras para este reporte.
- Cero alucinaciones: número que no se verificó, no se afirma.

[EJEMPLO]
Fila esperada de la tabla de hallazgos:

  | H | Estado | Evidencia (verificada ahora) |
  |---|--------|------------------------------|
  | H-1 numeración 3-1-3-1 | CERRADO | `domain/services/numeracion_ayc.py` existe; `zeep_cd_liquidaciones_gateway.py:NN` llama al servicio, no `id%10`; `pytest tests/unit/.../test_numeracion_ayc.py` → K passed |

Encabezado esperado del estado global:

  ESTADO GLOBAL: VERDE — los 8 hallazgos cerrados y verificados; gates en verde (lint-imports 19/19,
  ruff, mypy N archivos, M unit, tsc/eslint limpios); DB consistente (35 liqs, 34+34 vínculos, ALT007
  inactiva). Listo para operar salvo el pendiente #1 (sync WS completo), que es una decisión de la TL
  por su volumen (~2.000+ liqs), no un bloqueo técnico.
```

---

## Notas de contexto para quien use este prompt (fuera del prompt en sí)

- **Es un reporte, no una auditoría.** La validación adversarial ya se hizo y cerró; este prompt sirve
  para tener una foto verificada del "ahora" — útil para mostrarle a la TL o para decidir cuándo correr
  el sync completo. La verificación que pide es liviana (confirmar que los fixes están en el código
  committeado + re-correr gates + conteos de DB), no volver a buscar contraejemplos.
- **El único cambio de datos persistente es ALT007 inactiva.** Todo lo demás de la corrida de validación
  se revirtió; la DB volvió a `35/1857/763/22` con 34+34 vínculos. Si el reporte encuentra otra cosa,
  es un hallazgo real que hay que marcar.
- **El pendiente #1 es el próximo paso real y es una decisión, no un bug.** Con H-1/H-2 corregidos, el
  sync WS completo ya no duplica ni deja vacías, pero traería ~2.000+ liquidaciones históricas en un
  request largo (H-5): correrlo es una decisión operativa de la TL. El reporte debe dejar claro que el
  bloqueo técnico se levantó y que lo que queda es esa decisión.
- **Dos cosas quedaron para confirmar con la TL**, no con código: si la nueva semántica de ALT002 (H-4,
  alertar cuando el PST factura el piso/decimal exacto) es la deseada, y si conviene reintroducir un
  dry-run en el sync WS ahora que "no hay nada que proteger" quedó refutado. El reporte las lista como
  decisiones abiertas, no como fallas.
