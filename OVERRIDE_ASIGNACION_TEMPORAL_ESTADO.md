# Estado — Override temporal de asignación (ADR-013) y fuente de datos de planificación (ADR-012)

Cierre de sesión 2026-08-13. Referencia rápida de qué quedó hecho y qué falta, para no
tener que reconstruir el hilo desde los commits.

## Hecho y verificado

- **ADR-012** (fuente de datos de planificación): investigación cerrada en 5 rondas contra
  `SigesReadOnly` real. Veredicto: el catálogo de operadores se reemplaza por
  `dbo.UsuariosWeb` (implementado, `PyodbcOperadorGateway`); la asignación operador↔evento y
  la logística del evento (`bultos`/`costo_seguro`/`fecha_entrega`) **no están en Siges** —
  `Remito_Cab` fue investigado y descartado con dato real (es logística de insumos/repuestos,
  dominio distinto). El scraping de `GET /planificacion/ajax-by-rango` de Gestión se mantiene
  íntegro. Ver `docs/adr/012-...md` y `SIGES_READONLY_PLANIFICACION_VALIDACION.md`.
- **ADR-013** (override temporal), implementado y verificado en vivo contra el backend real en
  los tres módulos que tenían que verlo:
  - **`contadores`**: ABM (`POST/GET /api/contadores/calendario/overrides`,
    `POST .../cancelar`) + integración de lectura en `GetCalendarEventsUseCase` (resuelve por
    evento, con la fecha propia de cada evento).
  - **`prestadores`**: ABM (`POST/GET /api/prestadores/overrides`, `POST .../cancelar`) +
    integración en `ListPrestadoresAgrupados` (agrupa por operador efectivo a la fecha de
    consulta, default hoy).
  - **`sla`**: `SqlAlchemyPrestadorLookup.get_siges_ids_por_operador` ahora suma los PST
    cubiertos por override activo a los propios.
- Migraciones reversibles (`upgrade`/`downgrade`/`upgrade` probado a mano en los dos módulos).
- `lint-imports`/`ruff`/`mypy`/`pytest` en verde (816 tests) en cada commit.
- Verificado en vivo contra la DB de dev real: catálogo de operadores desde Siges (`vipaez` →
  Victor Paez, color real), ABM de overrides en ambos módulos (crear/listar/solapamiento
  409/cancelar), tablero de `prestadores` moviendo un PST real de grupo al activar/cancelar un
  override, `PrestadorLookup` de `sla` sumando y quitando los 12 PST reales de un operador
  cubierto.

## Pendiente

1. **UI**: no hay handoff visual para ningún patrón nuevo de esta sesión (catálogo de
   operadores no cambia de UI, pero el ABM de overrides en `contadores` y `prestadores` no
   tiene ninguna pantalla — hoy solo existe como API). Regla del proyecto: no inventar diseño
   sin mockup/handoff — pedirlo antes de tocar frontend.
2. **`contadores`, integración de lectura sin verificar en vivo**: `GetCalendarEventsUseCase`
   está cubierto por unit tests (con mocks que reproducen el escenario exacto), pero no se probó
   contra el backend real porque requiere loguearse como un usuario regular (no superadmin)
   cuyo `full_name` matchee un operador real de Gestión — no tengo credenciales de ningún
   empleado real y no corresponde intentar conseguirlas. Si en algún momento se consigue login
   de prueba de un usuario regular, vale la pena repetir el smoke test que sí se hizo para
   `prestadores`/`sla`.
3. **`ListPrestadoresAgrupados` no expone `fecha` por API todavía**: el caso de uso ya acepta un
   parámetro `fecha: date | None` (default hoy, ya usado por los tests), pero
   `GET /api/prestadores` no tiene un query param para pedir el agrupado "a tal fecha" — hoy
   siempre se resuelve a hoy. No fue pedido; queda como extensión natural si en algún momento se
   quiere planificar coberturas a futuro desde la UI en vez de solo ver el estado actual.
4. **Validación de invariantes solo en la capa de aplicación, no en el schema de Postgres**: el
   no-solapamiento de overrides para un mismo operador ausente se valida en el caso de uso
   (`CreateAsignacionOverride`), no con un constraint de DB — se evaluó un `EXCLUDE USING gist`
   y se descartó (ver ADR-013, el alcance por cliente/PST vive en tabla hija, no es expresable
   limpio). Ventana de carrera aceptada a propósito (ABM de baja frecuencia). Documentado, no es
   un olvido.
5. **`operador_ausente_id`/`operador_reemplazante_id` de `contadores` sin validar contra el
   catálogo vigente al crear el override**: son strings libres (usernames de Gestión) sin FK a
   `contadores_operadores` (esa tabla se poda en cada sync, ver ADR-013) — un typo en el
   username crea igual el override, sin error, y simplemente nunca matchea ningún evento real.
   Aceptado por diseño, pero vale la pena tenerlo presente si en algún momento se arma la UI del
   ABM (ahí sí conviene validar contra el catálogo local antes de enviar el request).

## No pendiente (cerrado, no reabrir sin evidencia nueva)

- Reemplazo de `Remito_Cab`/`bultos`/`costo_seguro`/`fecha_entrega`/`costo_recambio` por Siges:
  descartado con dato real (ADR-012 ronda 5). No tiene sentido re-investigar sin que aparezca
  una fuente nueva (ej. acceso a la base propia de Gestión, si existe y es distinta de Siges).
