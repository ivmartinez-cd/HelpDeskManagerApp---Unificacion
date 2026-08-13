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

1. ~~UI del ABM~~ — **hecho (2026-08-13, tarde)** sobre el handoff
   `design_handoff_reasignacion_temporal/` que entregó el usuario ese mismo día:
   `frontend/src/features/coberturas/` (un solo `CoberturasView`/`CoberturaModal`
   parametrizado por `entityType`, como pide el handoff), rutas
   `/contadores/coberturas` y `/prestadores/coberturas` + entradas "Coberturas" en ambos
   submenús, primitivos nuevos `SearchableSelect` y `SegmentedControl` en
   `shared/components/ui/`, 8 tests Playwright (`frontend/tests/coberturas.spec.ts`).
   **Desvíos conscientes del handoff, por contrato real del backend (ADR-013):**
   - La variante PST del handoff planteaba "un PST cubre a otro PST" — el dominio real es
     *operador cubre a operador*, con alcance en PST. Labels adaptados; el resto del diseño
     se respetó.
   - Sin acción "Editar": el backend no expone update de overrides a propósito (solo
     crear/cancelar). Se omite hasta que exista el endpoint, si algún día se pide.
   - El solapamiento es un 409 del backend (hard block), no el warning no bloqueante del
     handoff — se muestra el error del server en el banner del modal.
   - Vigencia con dos `BrandInput type="date"` (patrón ya establecido en todo el DS), no el
     `DateRangePicker` custom del handoff; modales por estado local, no por ruta
     (`/nueva`, `/:id/editar`), como el resto de la app.
   - Los estados Programada/Vencida se derivan por fecha en el cliente (la DB solo persiste
     ACTIVA/CANCELADA).
   ~~**Fase 2 pendiente**~~ — **hecho (2026-08-13, noche)**: capa de indicadores del
   Calendario (§3.3 del handoff) con backend nuevo.
   **Contrato elegido**: `GET /calendario` anota cada evento con
   `cobertura: CoberturaEventoSchema | null` (override_id, ausente id/nombre, reemplazante
   id/nombre/color, vigencia, `alcance_total`) — el evento conserva siempre su
   `operador_id` real. El switch "efectivo/real" es **solo render del cliente** (un único
   contrato, sin re-fetch ni cambio del set de eventos). Semántica por rol:
   - **Usuario regular**: sus eventos cubiertos por otro **ya no desaparecen** de su vista
     (cambio deliberado sobre la fase 1, por el principio del handoff "el operador real
     nunca desaparece") — viajan anotados; además sigue viendo, anotados, los eventos que
     él cubre.
   - **Superadmin**: ahora sí resuelve overrides (anota todo con `list_activos()`); el
     filtro por operador sigue siendo por asignación cruda (vista administrativa).
   Implementación: `resolver_override_aplicable` en `domain/services/operador_efectivo.py`,
   anotador en `application/use_cases/cobertura_evento_anotador.py`, DTO
   `CalendarEventAnotado`. UI: `SegmentedControl` "Ver por" en el header, badge
   "CUBIERTO POR XX" / "↩ XX cubre" en el pill, `Tooltip` nuevo en `shared/components/ui/`
   (portal + delay 200ms, hovereable, Escape cierra) con link a `/contadores/coberturas`,
   leyenda bajo la grilla. Tests: unit backend (850 en verde) +
   `frontend/tests/calendario-cobertura.spec.ts` (3 specs; suite completa 39/39).
2. ~~**`contadores`, integración de lectura sin verificar en vivo**~~ **Resuelto
   (2026-08-13, noche)**: smoke test en vivo contra el backend real, con usuarios de prueba
   creados vía `/api/admin/users` con `full_name` matcheando operadores reales del catálogo
   (borrados de la DB al terminar, junto con la cancelación del override de prueba):
   - **Reemplazante** (usuario "Victor Paez" → operador `vipaez`): vio sus 49 eventos propios
     de agosto + los 6 de `mjvela` dentro de la vigencia del override (14→17 ago), esos 6
     anotados con `cobertura` completa (nombres y color reales del catálogo). El filtro
     `?operador_id=` de otro operador se ignoró correctamente.
   - **Ausente** (usuario "Maria Jose Vela" → operador `mjvela`): conservó sus 56 eventos
     (ninguno desapareció — comportamiento nuevo de fase 2), con exactamente los 6 de la
     vigencia anotados.
   - **Superadmin**: 6 eventos anotados / 191 con `cobertura: null` sobre el mismo rango.
   Nota operativa: `POST /admin/users/{id}/password-reset` dispara un mail real por SMTP
   (se usó una sola vez, destinatario `@example.com` — dominio reservado, rebote inofensivo);
   para el segundo usuario se seteó el hash argon2 directo en `app_user` para no enviar más
   mails. El login de prueba se logró sin credenciales de empleados reales.
3. ~~**`ListPrestadoresAgrupados` no expone `fecha` por API todavía**~~ **Resuelto
   (2026-08-13)**: `GET /api/prestadores` acepta `?fecha=YYYY-MM-DD` (query param opcional,
   default hoy) y lo pasa al caso de uso, que ya lo soportaba.
4. **Validación de invariantes solo en la capa de aplicación, no en el schema de Postgres**: el
   no-solapamiento de overrides para un mismo operador ausente se valida en el caso de uso
   (`CreateAsignacionOverride`), no con un constraint de DB — se evaluó un `EXCLUDE USING gist`
   y se descartó (ver ADR-013, el alcance por cliente/PST vive en tabla hija, no es expresable
   limpio). Ventana de carrera aceptada a propósito (ABM de baja frecuencia). Documentado, no es
   un olvido.
5. ~~**`operador_ausente_id`/`operador_reemplazante_id` de `contadores` sin validar contra el
   catálogo vigente al crear el override**~~ **Resuelto (2026-08-13)**:
   `CreateAsignacionOverride` valida ambos usernames contra `contadores_operadores` (el mismo
   `list_operadores()` que ya usaba para armar el DTO, ahora consultado antes de crear) y
   rechaza con `OperadorNoEncontradoError` (400, `OPERADOR_NO_ENCONTRADO`) si alguno no existe.
   Sigue sin FK en el schema (la tabla se poda en cada sync, ver ADR-013) — un override ya
   creado cuyo operador desaparece del catálogo en un sync posterior queda igual que antes;
   solo el alta valida.

## No pendiente (cerrado, no reabrir sin evidencia nueva)

- Reemplazo de `Remito_Cab`/`bultos`/`costo_seguro`/`fecha_entrega`/`costo_recambio` por Siges:
  descartado con dato real (ADR-012 ronda 5). No tiene sentido re-investigar sin que aparezca
  una fuente nueva (ej. acceso a la base propia de Gestión, si existe y es distinta de Siges).
